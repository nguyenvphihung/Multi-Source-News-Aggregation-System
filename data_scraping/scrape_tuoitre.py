import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import logger, get_webdriver, transform_text_to_features, save_article_to_db, load_model_and_features, get_db_connection
from datetime import datetime
from dateutil.parser import parse

def format_date(date_string, default_date=None):
    default_date = default_date or datetime.now()
    default_format = "%Y-%m-%d %H:%M:%S"
    if not date_string:
        return default_date.strftime(default_format)
    try:
        cleaned_date = date_string.replace(" GMT+7", "").strip()
        parsed_date = parse(cleaned_date, dayfirst=True)
        return parsed_date.strftime(default_format)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return default_date.strftime(default_format)

def scrape_tuoitre_articles(limit=20, driver=None):
    url = "https://tuoitre.vn/tin-moi-nhat.htm"
    articles = []
    try:
        logger.info(f"Scraping Tuoi Tre articles from {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "load-list-news"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        news_list = soup.find("div", id="load-list-news", class_="box-category-middle")
        if not news_list:
            logger.warning("No news list found on Tuoi Tre page")
            return articles
        
        article_items = news_list.find_all("div", class_="box-category-item")[:limit]
        logger.info(f"Found {len(article_items)} article items")
        
        for article in article_items:
            try:
                link_tag = article.find("a", class_="box-category-link-with-avatar")
                if not link_tag or "href" not in link_tag.attrs:
                    continue
                article_url = "https://tuoitre.vn" + link_tag["href"]
                title = link_tag.get("title", "No title")
                articles.append({"title": title, "url": article_url})
            except Exception as e:
                logger.error(f"Error parsing Tuoi Tre article: {e}")
                continue
        return articles
    except Exception as e:
        logger.error(f"Error scraping Tuoi Tre: {e}")
        return articles

def fetch_article_content(article_url, clf, features, driver):
    try:
        logger.info(f"Fetching Tuoi Tre article: {article_url}")
        driver.get(article_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.find("h1") or soup.find(class_="title")
        title = title_tag.text.strip() if title_tag else "No title"

        description_tag = soup.find("h2") or soup.find(class_="description")
        description = description_tag.text.strip() if description_tag else "No description"

        content_div = soup.select_one("div.detail-content.afcbc-body")
        if not content_div:
            logger.warning(f"No content found at {article_url}")
            return None

        # Plain text content cho dự đoán loại bài viết
        plain_content = ""
        for elem in content_div.find_all(["p", "h2", "h3", "figure"]):
            if elem.name in ["h2", "h3"]:
                plain_content += f"{elem.get_text(strip=True)}\n"
            elif elem.name == "figure":
                caption_tag = elem.find("figcaption")
                if caption_tag:
                    plain_content += f"{caption_tag.get_text(strip=True)}\n"
            else:
                plain_content += f"{elem.get_text(strip=True)}\n"

        X = transform_text_to_features([plain_content], features)
        predicted_type = clf.predict(X)[0]

        # Xây dựng HTML content
        html_content = '<div class="article-contents">\n'
        for elem in content_div.find_all(["p", "h2", "h3", "figure"]):
            if elem.name in ["h2", "h3"]:
                html_content += f'<{elem.name} class="article-subheading">{elem.get_text(strip=True)}</{elem.name}>\n'
            elif elem.name == "figure":
                img_tag = elem.find("img")
                caption_tag = elem.find("figcaption")
                if img_tag:
                    html_content += (
                        f'<figure class="article-figure">\n'
                        f'  <img src="{img_tag["src"]}" alt="{img_tag.get("alt", "")}" class="article-image" />\n'
                    )
                if caption_tag:
                    html_content += f'  <figcaption class="article-caption">{caption_tag.get_text(strip=True)}</figcaption>\n'
                if img_tag:
                    html_content += '</figure>\n'
            else:
                html_content += f'<p class="article-paragraph">{elem.get_text(strip=True)}</p>\n'
        html_content += '</div>'

        author_div = soup.find("div", class_="detail-author")
        author = " ".join(author_div.text.split())[:255] if author_div else "Unknown author"

        date_tag = soup.select_one('[data-role="publishdate"]')
        date_posted = format_date(date_tag.get_text(strip=True) if date_tag else None)

        image_urls = [img["src"] for img in content_div.find_all("img") if "src" in img.attrs]
        video_urls = [video["src"] for video in soup.find_all("video") if "src" in video.attrs]

        return {
            "title": title,
            "description": description,
            "content": html_content,
            "date_posted": date_posted,
            "author": author,
            "source_url": article_url,
            "status": "published",
            "predicted_type": predicted_type,
            "image_urls": image_urls,
            "video_urls": video_urls,
        }
    except Exception as e:
        logger.error(f"Error fetching {article_url}: {e}")
        return None

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    clf, features = load_model_and_features()
    if not clf or not features:
        logger.error("Failed to load model or features")
        return

    with get_webdriver() as driver:
        articles = scrape_tuoitre_articles(limit=20, driver=driver)
        for article in articles:
            article_data = fetch_article_content(article["url"], clf, features, driver)
            if article_data:
                save_article_to_db(article_data, cursor, conn)
    
    cursor.close()
    conn.close()
    logger.info("Tuoi Tre scraping completed")

if __name__ == "__main__":
    main()