import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from utils import logger, get_webdriver, transform_text_to_features, save_article_to_db, load_model_and_features, get_db_connection

def format_date(date_string, default_date=None):
    default_date = default_date or datetime.now()
    default_format = "%Y-%m-%d %H:%M:%S"
    if not date_string:
        return default_date.strftime(default_format)
    try:
        cleaned_date = re.sub(r'Thứ [a-zA-Zàáảãạăắằẳẵặâầấẩẫậ]+, ', '', date_string, flags=re.UNICODE)
        cleaned_date = cleaned_date.replace(" (GMT+7)", "").strip()
        logger.debug(f"Cleaned date string: '{cleaned_date}'")
        parsed_date = datetime.strptime(cleaned_date, "%d/%m/%Y, %H:%M")
        return parsed_date.strftime(default_format)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return default_date.strftime(default_format)

def scrape_dantri_articles(limit=20, driver=None):
    url = "https://dantri.com.vn/tin-moi-nhat.htm"
    articles = []
    seen_urls = set()  # Để tránh trùng lặp bài viết
    try:
        logger.info(f"Scraping Dân trí articles from {url}")
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "article-newest"))
        )

        # Cuộn trang để tải thêm bài viết
        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(articles) < limit:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("No more articles loaded, stopping scroll")
                break
            last_height = new_height

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            news_list = soup.find("div", class_="article-newest")
            if not news_list:
                logger.warning("No news list found on Dân trí page")
                break
            article_items = news_list.find_all("article", class_="article-newest-item")
            logger.info(f"Found {len(article_items)} article items after scrolling")
            for article in article_items:
                try:
                    thumb = article.find("div", class_="article-thumb")
                    if thumb:
                        link_tag = thumb.find("a")
                        img_tag = thumb.find("img")
                    else:
                        img_tag = article.find("img")
                        link_tag = article.find("a") if img_tag else None
                    if not link_tag or "href" not in link_tag.attrs or not img_tag or "src" not in img_tag.attrs:
                        logger.debug("Skipping article without image or link")
                        continue
                    article_url = link_tag["href"]
                    if not article_url.startswith("https://dantri.com.vn"):
                        article_url = "https://dantri.com.vn" + article_url
                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)
                    title_tag = article.find("h2", class_="article-title") or article.find("h3", class_="article-title")
                    title = title_tag.find("a").text.strip() if title_tag and title_tag.find("a") else "No title"
                    time_tag = article.find("div", class_="article-time")
                    date_posted = time_tag.text.strip() if time_tag else "Unknown"
                    image_url = img_tag["src"]
                    articles.append({
                        "title": title,
                        "url": article_url,
                        "date_posted": date_posted,
                        "image_url": image_url
                    })
                    if len(articles) >= limit:
                        break
                except Exception as e:
                    logger.error(f"Error parsing Dân trí article: {e}")
                    continue
            if len(articles) >= limit:
                break
        logger.info(f"Scraped {len(articles)} articles from Dân trí")
        return articles
    except Exception as e:
        logger.error(f"Error scraping Dân trí {url}: {e}")
        return articles

def fetch_article_content(article_url, clf, features, driver):
    try:
        logger.info(f"Fetching Dân trí article: {article_url}")
        driver.get(article_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title_tag = soup.find("h1", class_="title-page")
        title = title_tag.text.strip() if title_tag else "No title"
        description_tag = soup.find("h2", class_="singular-sapo")
        description = description_tag.text.strip() if description_tag else "No description"
        content_div = soup.select_one("div.singular-content")
        if not content_div:
            logger.warning(f"No content found at {article_url}")
            return None
        # Loại bỏ các phần không cần thiết
        for unwanted in content_div.find_all(["div"], class_=["box-taitro", "related-articles"]):
            unwanted.decompose()
        plain_content = ""
        image_urls_list = []
        html_content = '<div class="article-contents">\n'
        for elem in content_div.find_all(["p", "h2", "h3", "figure"]):
            if elem.name in ["h2", "h3"]:
                plain_content += f"{elem.get_text(strip=True)}\n"
                html_content += f'<{elem.name} class="article-subheading">{elem.get_text(strip=True)}</{elem.name}>\n'
            elif elem.name == "figure" and "image" in elem.get("class", []) and "align-center" in elem.get("class", []):
                img_tag = elem.find("img")
                caption_tag = elem.find("figcaption")
                image_url = None
                if img_tag:
                    if "data-original" in img_tag.attrs:
                        image_url = img_tag["data-original"].strip()
                    elif "src" in img_tag.attrs:
                        image_url = img_tag["src"].split(',')[0].strip()
                    if image_url and image_url.endswith(('.jpg', '.jpeg', '.png')) and image_url not in image_urls_list:
                        image_urls_list.append(image_url)
                        logger.info(f"Found image in figure: {image_url}")
                alt_text = img_tag.get("alt", "") if img_tag else ""
                if image_url:
                    html_content += (
                        f'<figure class="article-figure">\n'
                        f'  <img src="{image_url}" alt="{alt_text}" class="article-image" />\n'
                    )
                if caption_tag:
                    html_content += f'  <figcaption class="article-caption">{caption_tag.get_text(strip=True)}</figcaption>\n'
                if image_url:
                    html_content += '</figure>\n'
                plain_content += f"[Image] "
            else:
                plain_content += f"{elem.get_text(strip=True)}\n"
                html_content += f'<p class="article-paragraph">{elem.get_text(strip=True)}</p>\n'
        html_content += '</div>'
        html_soup = BeautifulSoup(html_content, 'html.parser')
        image_urls = [img["src"] for img in html_soup.find_all("img") if "src" in img.attrs]
        # Dự đoán loại bài viết với model học máy
        X = transform_text_to_features([plain_content], features)
        predicted_type = clf.predict(X)[0]
        author_tag = soup.find("div", class_="author-name")
        author = author_tag.text.strip() if author_tag else "Unknown author"
        logger.info(f"Author found: {author}")
        date_tag = soup.find("time", class_="time")
        date_posted = format_date(date_tag.get_text(strip=True) if date_tag else None)
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
        logger.error(f"Error fetching Dân trí article {article_url}: {e}")
        return None

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    clf, features = load_model_and_features()
    if not clf or not features:
        logger.error("Failed to load model or features")
        return
    with get_webdriver() as driver:
        articles = scrape_dantri_articles(limit=20, driver=driver)
        for article in articles:
            article_data = fetch_article_content(article["url"], clf, features, driver)
            if article_data:
                logger.info(f"Image URLs before saving to DB: {article_data['image_urls']}")
                save_article_to_db(article_data, cursor, conn)
    cursor.close()
    conn.close()
    logger.info("Dân trí scraping completed")

if __name__ == "__main__":
    main()