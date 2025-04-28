import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from utils import logger, get_webdriver, transform_text_to_features, save_article_to_db, load_model_and_features, get_db_connection
from datetime import datetime
from dateutil.parser import parse
import time

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

def scrape_vietnamplus_articles(limit=20, driver=None):
    url = "https://www.vietnamplus.vn/topic/tin-moi-nhan-111.vnp"
    articles = []
    try:
        logger.info(f"Scraping VietnamPlus articles from {url}")
        
        # Thiết lập UserAgent để tránh block
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        })
        
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#content-list, .content-list"))
            )
        except TimeoutException:
            logger.error("Timeout waiting for content-list element. Saving page source for debugging.")
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return articles

        # Scroll để load thêm bài viết
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        news_list = (soup.find("div", id="content-list") or 
                     soup.find("div", class_="content-list") or 
                     soup.find("div", class_="timeline"))
        if not news_list:
            logger.warning("No news list found on the page")
            return articles
        
        article_items = news_list.find_all("article", class_="story")
        logger.info(f"Found {len(article_items)} article items in total")

        collected_articles = 0
        for article in article_items:
            logger.debug(f"Processing article with data-id: {article.get('data-id', 'No ID')}")
            
            heading_tag = article.find("h2", class_="story__heading")
            if not heading_tag:
                logger.debug(f"Skipping article due to missing heading: {article.get('data-id', 'No ID')}")
                continue

            # Loại trừ bài có icon audio hoặc video
            icon_tag = heading_tag.find("i", class_=["ic-audio", "ic-video"])
            if icon_tag:
                logger.debug(f"Skipping article with {icon_tag['class'][0]}: {heading_tag.text.strip()}")
                continue

            link_tag = heading_tag.find("a", class_="cms-link")
            if not link_tag:
                logger.debug(f"Skipping article due to missing link tag: {article.get('data-id', 'No ID')}")
                continue
            
            href = link_tag.get("href", "")
            logger.debug(f"Found href: {href}")
            if not href:
                logger.debug(f"Skipping article due to empty href: {article.get('data-id', 'No ID')}")
                continue
            
            article_url = href if href.startswith("http") else "https://www.vietnamplus.vn" + href
            title = link_tag.get("title", "No title").strip()

            time_tag = article.find("time", class_="time")
            time_posted = time_tag.text.strip() if time_tag else "Unknown time"

            img_tag = article.find("img")
            thumbnail_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

            articles.append({
                "title": title,
                "url": article_url,
                "time_posted": time_posted,
                "thumbnail_url": thumbnail_url
            })
            collected_articles += 1
            logger.debug(f"Scraped article: {title} - {article_url}")

            if collected_articles >= limit:
                break

        logger.info(f"Collected {collected_articles} articles without ic-audio or ic-video")
        return articles
    except WebDriverException as e:
        logger.error(f"WebDriver error scraping VietnamPlus articles from {url}: {e}")
        return articles
    except Exception as e:
        logger.error(f"Unexpected error scraping VietnamPlus articles from {url}: {e}")
        return articles

def fetch_article_content(article_url, clf, features, driver):
    try:
        logger.info(f"Fetching article content from: {article_url}")
        if not article_url.startswith("http"):
            logger.warning(f"Invalid URL format: {article_url}")
            return None
        
        driver.get(article_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.article__body, article"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Tiêu đề
        title_tag = soup.find("h1") or soup.find(class_="article__title")
        title = title_tag.text.strip() if title_tag else "No title"
        logger.debug(f"Found title: {title}")

        # Mô tả
        description_tag = soup.find("div", class_="article__sapo cms-desc")
        if description_tag:
            p_tag = description_tag.find("p")
            description = p_tag.text.strip() if p_tag else description_tag.text.strip()
        else:
            description = "No description"
        logger.debug(f"Found description: {description}")

        # Nội dung bài viết
        content_div = soup.select_one("div.article__body")
        if not content_div:
            logger.warning(f"No content found at {article_url}")
            return None
        logger.debug(f"Processing content from article: {article_url}")

        # Loại bỏ các thẻ không mong muốn
        for unwanted in content_div.select('div.article-relate, div.article__source, #sdaWeb_SdaArticleAfterBody'):
            unwanted.decompose()
        logger.debug("Removed unwanted tags from content_div")

        plain_content = ""
        html_content = '<div class="article-contents">\n'
        image_urls = []

        # Xử lý các thẻ figure
        for elem in soup.find_all("figure"):
            logger.debug(f"Processing figure with classes: {elem.get('class', ['No class'])}")
            img_tag = elem.find("img")
            caption_tag = elem.find("figcaption")
            if caption_tag:
                plain_content += f"{caption_tag.get_text(strip=True)}\n"
            if img_tag:
                img_classes = img_tag.get("class", [])
                logger.debug(f"Image classes: {img_classes}")
                if "cms-photo" not in img_classes:
                    logger.debug(f"Skipping image without cms-photo class: {img_tag.get('src', 'No src')}")
                    continue
                img_src = img_tag.get("src", "")
                if not img_src or not img_src.startswith("http"):
                    logger.debug(f"Skipping invalid image src: {img_src}")
                    continue
                img_alt = img_tag.get("alt", "")
                html_content += (
                    f'<figure class="article-figure">\n'
                    f'  <img src="{img_src}" alt="{img_alt}" class="article-image" />\n'
                )
                image_urls.append(img_src)
            if caption_tag:
                html_content += f'  <figcaption class="article-caption">{caption_tag.get_text(strip=True)}</figcaption>\n'
            if img_tag and "cms-photo" in img_classes:
                html_content += '</figure>\n'

        # Xử lý các thẻ khác trong content_div
        for elem in content_div.find_all(["p", "h2", "h3"]):
            text = elem.get_text(strip=True)
            if elem.name in ["h2", "h3"]:
                plain_content += f"{text}\n"
                html_content += f'<{elem.name} class="article-subheading">{text}</{elem.name}>\n'
            else:
                plain_content += f"{text}\n"
                html_content += f'<p class="article-paragraph">{text}</p>\n'
        html_content += '</div>'

        # Dự đoán loại bài viết bằng model học máy
        X = transform_text_to_features([plain_content], features)
        predicted_type = clf.predict(X)[0]
        logger.debug(f"Predicted article type: {predicted_type}")

        # Tác giả và ngày đăng
        meta_div = soup.find("div", class_="article__meta")
        if meta_div:
            author_tag = meta_div.find("span", class_="author cms-author")
            author = " ".join(author_tag.text.split())[:255] if author_tag else "Unknown author"
            date_tag = meta_div.find("time", class_="time")
            date_posted = format_date(date_tag.text.strip() if date_tag else None)
        else:
            author = "Unknown author"
            date_posted = format_date(None)
        logger.debug(f"Found author: {author} | date_posted: {date_posted}")

        # Video
        video_urls = [video["src"] for video in soup.find_all("video") if "src" in video.attrs]
        logger.debug(f"Found {len(image_urls)} images and {len(video_urls)} videos")

        if not plain_content.strip():
            logger.warning(f"Empty content at {article_url}")
            return None

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
    except TimeoutException:
        logger.error(f"Timeout fetching {article_url}")
        return None
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
        articles = scrape_vietnamplus_articles(limit=20, driver=driver)
        for article in articles:
            article_data = fetch_article_content(article["url"], clf, features, driver)
            if article_data:
                save_article_to_db(article_data, cursor, conn)
    
    cursor.close()
    conn.close()
    logger.info("VietnamPlus scraping completed")

if __name__ == "__main__":
    main()