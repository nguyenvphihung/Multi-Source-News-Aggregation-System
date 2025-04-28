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

def scrape_nld_articles(limit=20, driver=None):
    url = "https://nld.com.vn/tin-24h.htm"
    articles = []
    try:
        logger.info(f"Scraping NLD articles from {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "box-category-middle"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        news_list = soup.find("div", class_="box-category-middle")
        if not news_list:
            logger.warning("No news list found on NLD page")
            return articles
        
        article_items = news_list.find_all("div", class_="box-category-item")[:limit]
        logger.info(f"Found {len(article_items)} article items")
        
        for article in article_items:
            try:
                link_tag = article.find("a")
                if not link_tag or "href" not in link_tag.attrs:
                    logger.debug(f"No valid link found in article: {article}")
                    continue
                article_url = "https://nld.com.vn" + link_tag["href"]
                title = link_tag.text.strip() if link_tag.text.strip() else link_tag.get("title", "No title")
                img_tag = article.find("img")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None
                time_tag = article.find("span", class_="date")
                date_posted = time_tag.text.strip() if time_tag else "Unknown"
                
                articles.append({
                    "title": title,
                    "url": article_url,
                    "image_url": image_url,
                    "date_posted": date_posted
                })
            except Exception as e:
                logger.error(f"Error parsing NLD article: {e}")
                continue
        
        logger.info(f"Scraped {len(articles)} articles from NLD")
        return articles
    
    except Exception as e:
        logger.error(f"Error scraping NLD {url}: {e}")
        return articles

def fetch_article_content(article_url, clf, features, driver):
    try:
        logger.info(f"Fetching NLD article: {article_url}")
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

        # Extract plain text content
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

        # Predict article type using model
        X = transform_text_to_features([plain_content], features)
        predicted_type = clf.predict(X)[0]

        # Build HTML content
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

        author_div = soup.find(class_="author-info")
        author = " ".join(author_div.text.split())[:255] if author_div else "Unknown author"

        date_tag = soup.find(class_="date")
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
        articles = scrape_nld_articles(limit=20, driver=driver)
        for article in articles:
            article_data = fetch_article_content(article["url"], clf, features, driver)
            if article_data:
                save_article_to_db(article_data, cursor, conn)
    
    cursor.close()
    conn.close()
    logger.info("NLD scraping completed")

if __name__ == "__main__":
    main()