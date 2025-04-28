import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import logger, get_webdriver, transform_text_to_features, save_article_to_db, load_model_and_features, get_db_connection

def format_date(date_string, default_date=None):
    default_date = default_date or datetime.now()
    default_format = "%Y-%m-%d %H:%M:%S"
    if not date_string:
        return default_date.strftime(default_format)
    try:
        # Xóa phần tên ngày trong tuần (Thứ hai, Thứ ba, v.v.) và "GMT+7"
        cleaned_date = re.sub(r'Thứ [a-zA-Zàáảãạăắằẳẵặâầấẩẫậ]+, ', '', date_string)
        cleaned_date = cleaned_date.replace(" (GMT+7)", "").strip()
        # Phân tích định dạng "19/3/2025, 19:54"
        parsed_date = datetime.strptime(cleaned_date, "%d/%m/%Y, %H:%M")
        return parsed_date.strftime(default_format)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return default_date.strftime(default_format)

def scrape_vnexpress_articles(limit=20, driver=None):
    url = "https://vnexpress.net/tin-tuc-24h"
    articles = []
    try:
        logger.info(f"Scraping VnExpress articles from {url}")
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "list-news-subfolder"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        news_list = soup.find("div", class_="list-news-subfolder")
        if not news_list:
            logger.warning("No news list found on VnExpress page")
            return articles
        
        article_items = news_list.find_all("article", class_="item-news")
        logger.info(f"Found {len(article_items)} article items")
        
        for article in article_items:
            try:
                thumb_art = article.find("div", class_="thumb-art")
                if not thumb_art:
                    logger.debug(f"Skipping article without image: {article.find('h3', class_='title-news').text.strip() if article.find('h3', class_='title-news') else 'No title'}")
                    continue
                
                link_tag = article.find("h3", class_="title-news").find("a") if article.find("h3", class_="title-news") else None
                if not link_tag or "href" not in link_tag.attrs:
                    logger.debug("No valid link found in article")
                    continue
                article_url = link_tag["href"]
                title = link_tag.get("title", link_tag.text.strip()) if link_tag.text.strip() else "No title"
                
                time_tag = article.find("span", class_="time-count")
                date_posted = time_tag.find("span").text.strip() if time_tag and time_tag.find("span") else "Unknown"
                
                img_tag = thumb_art.find("img")
                image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None
                
                articles.append({
                    "title": title,
                    "url": article_url,
                    "date_posted": date_posted,  # Giá trị này sẽ được cập nhật khi fetch content
                    "image_url": image_url
                })
                
                if len(articles) >= limit:
                    break
            
            except Exception as e:
                logger.error(f"Error parsing VnExpress article: {e}")
                continue
        
        logger.info(f"Scraped {len(articles)} articles with images from VnExpress")
        return articles
    
    except Exception as e:
        logger.error(f"Error scraping VnExpress {url}: {e}")
        return articles

def fetch_article_content(article_url, clf, features, driver):
    try:
        logger.info(f"Fetching VnExpress article: {article_url}")
        driver.get(article_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.find("h1", class_="title-detail")
        title = title_tag.text.strip() if title_tag else "No title"

        description_tag = soup.find("p", class_="description")
        description = description_tag.text.strip() if description_tag else "No description"

        content_div = soup.select_one("article.fck_detail")
        if not content_div:
            logger.warning(f"No content found at {article_url}")
            return None

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

        author_tag = content_div.find("p", style="text-align:right;")
        if author_tag:
            strong_tag = author_tag.find("strong")
            author = strong_tag.text.strip() if strong_tag else author_tag.text.strip()
        else:
            author = "Unknown author"

        date_tag = soup.find("span", class_="date")
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
        articles = scrape_vnexpress_articles(limit=20, driver=driver)
        for article in articles:
            article_data = fetch_article_content(article["url"], clf, features, driver)
            if article_data:
                save_article_to_db(article_data, cursor, conn)
    
    cursor.close()
    conn.close()
    logger.info("VnExpress scraping completed")

if __name__ == "__main__":
    main()