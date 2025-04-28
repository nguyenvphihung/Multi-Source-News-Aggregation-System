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

def scrape_vietnamnet_articles(limit=20, driver=None):
    url = "https://vietnamnet.vn/tin-tuc-24h"
    articles = []
    seen_urls = set()
    try:
        logger.info(f"Scraping Vietnamnet articles from {url}")
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "container__left"))
        )
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "horizontalPost"))
        )
        time.sleep(2)  # Chờ render

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Tìm tất cả container__left
        all_containers = soup.find_all("div", class_="container__left")
        # Chọn container chứa horizontalPost
        news_list = None
        for container in all_containers:
            if container.find("div", class_="horizontalPost"):
                news_list = container
                break
        
        if not news_list:
            logger.warning("Không tìm thấy khối chứa horizontalPost")
            return articles

        article_items = news_list.find_all("div", class_="horizontalPost")
        logger.info(f"Found {len(article_items)} article items")
        
        for article in article_items[:limit]:
            try:
                main_section = article.find("div", class_="horizontalPost__main")
                if not main_section:
                    continue
                
                title_tag = main_section.find("h2", class_="horizontalPost__main-title") or main_section.find("h3", class_="horizontalPost__main-title")
                if not title_tag or not title_tag.find("a"):
                    continue
                
                link_tag = title_tag.find("a")
                article_url = link_tag["href"]
                if not article_url.startswith("https://vietnamnet.vn/"):
                    article_url = "https://vietnamnet.vn/" + article_url
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)

                title = link_tag.text.strip() if link_tag else "No title"
                
                articles.append({
                    "title": title,
                    "url": article_url,
                })
            
            except Exception as e:
                logger.error(f"Error parsing Vietnamnet article: {e}")
                continue
        
        logger.info(f"Scraped {len(articles)} articles from Vietnamnet")
        return articles
    
    except Exception as e:
        logger.error(f"Error scraping Vietnamnet {url}: {e}")
        return articles

def fetch_article_content(article_url, clf, features, driver):
    try:
        logger.info(f"Fetching Vietnamnet article: {article_url}")
        driver.get(article_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Cuộn trang để kích hoạt lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Chờ 5 giây để ảnh tải
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Lấy tiêu đề
        title_tag = soup.find("h1", class_="content-detail-title")
        title = title_tag.text.strip() if title_tag else "No title"

        # Lấy mô tả
        description_tag = soup.find("h2", class_="content-detail-sapo")
        description = description_tag.text.strip() if description_tag else "No description"

        # Lấy nội dung bài viết
        content_div = soup.select_one("div.maincontent.main-content")
        if not content_div:
            logger.warning(f"No content found at {article_url}")
            return None
        
        # Loại bỏ phần không mong muốn
        for unwanted in content_div.find_all("div", class_="ck-cms-insert-neww-group"):
            unwanted.decompose()

        plain_content = ""
        image_urls_list = []
        html_content = '<div class="article-contents">\n'

        for elem in content_div.find_all(["p", "h2", "h3", "figure"]):
            if elem.name in ["h2", "h3"]:
                plain_content += f"{elem.get_text(strip=True)}\n"
                html_content += f'<{elem.name} class="article-subheading">{elem.get_text(strip=True)}</{elem.name}>\n'
            elif elem.name == "figure":
                picture_tag = elem.find("picture")
                caption_tag = elem.find("figcaption")
                image_url = None
                if picture_tag:
                    source_tag = picture_tag.find("source")
                    if source_tag and "data-srcset" in source_tag.attrs:
                        image_url = source_tag["data-srcset"].strip().split(' ')[0]
                        if image_url.endswith(('.jpg', '.jpeg', '.png')) and image_url not in image_urls_list:
                            image_urls_list.append(image_url)
                            logger.info(f"Found image from source data-srcset in figure: {image_url}")
                
                # Lấy alt từ <img> nếu có
                img_tag = elem.find("img")
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

        X = transform_text_to_features([plain_content], features)
        predicted_type = clf.predict(X)[0]

        # Lấy tác giả
        author_div = soup.find("div", class_="article-detail-author author-single")
        if author_div:
            name_tag = author_div.find("span", class_="name")
            author = name_tag.get_text(strip=True) if name_tag else "Unknown author"
        else:
            author = "Unknown author"

        # Lấy ngày đăng
        date_tag = soup.find("time")
        date_posted = format_date(date_tag.get_text(strip=True) if date_tag else None)

        html_soup = BeautifulSoup(html_content, 'html.parser')
        image_urls = [img["src"] for img in html_soup.find_all("img") if "src" in img.attrs]
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
        logger.error(f"Error fetching Vietnamnet article {article_url}: {e}")
        return None

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    clf, features = load_model_and_features()
    if not clf or not features:
        logger.error("Failed to load model or features")
        return

    with get_webdriver() as driver:
        articles = scrape_vietnamnet_articles(limit=20, driver=driver)
        for article in articles:
            article_data = fetch_article_content(article["url"], clf, features, driver)
            if article_data:
                logger.info(f"Image URLs before saving to DB: {article_data['image_urls']}")
                save_article_to_db(article_data, cursor, conn)
    
    cursor.close()
    conn.close()
    logger.info("Vietnamnet scraping completed")

if __name__ == "__main__":
    main()