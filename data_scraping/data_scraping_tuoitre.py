import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import pyodbc
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import numpy as np
import string


# Kết nối đến cơ sở dữ liệu SQL Server
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=MSI\\SQLEXPRESS;"  # Lưu ý dấu \\ khi sử dụng Python
    "DATABASE=dataBao;"
    "Trusted_Connection=yes;"
)

cursor = conn.cursor()

# Khởi động trình duyệt không có giao diện người dùng
chrome_options = Options()
chrome_options.add_argument("--headless")  # Chạy ẩn trình duyệt
chrome_options.add_argument("--disable-gpu")  # Tắt GPU (khắc phục lỗi GLES3)
chrome_options.add_argument("--disable-software-rasterizer")  # Tắt GPU xử lý phần mềm
chrome_options.add_argument("--disable-dev-shm-usage")  # Giảm tải bộ nhớ
chrome_options.add_argument("--no-sandbox")  # Cho phép chạy trong môi trường sandbox
chrome_options.add_argument("--log-level=3")  # Giảm mức log lỗi
chrome_options.add_argument("--disable-web-security")  # Vô hiệu hóa kiểm tra bảo mật
chrome_options.add_argument("--allow-running-insecure-content")  # Cho phép nội dung không an toàn


driver = webdriver.Chrome(options=chrome_options)

def scrape_articles(category_url, category):
    try:
        driver.get(category_url)
        time.sleep(3)

        # Tạo soup từ nội dung trang đã tải về
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = []

        # Tìm tất cả các bài báo trong phần 'box-category-middle'
        article_elements = soup.select('#load-list-news .box-category-item')

        for article in article_elements:
            # Lấy link bài viết và tiêu đề
            link = article.select_one('a.box-category-link-title')
            if link:
                url = link['href']
                title = link['title']
                if url.startswith('/'):
                    url = 'https://tuoitre.vn' + url
                elif url.startswith('//'):
                    url = 'https:' + url

                summary_tag = article.select_one('p.box-category-sapo')
                description = summary_tag.text.strip() if summary_tag else "Không tìm thấy tóm tắt"

                try:
                    article_data = get_article_data(url, category)
                    if article_data:
                        article_data['title'] = title
                        article_data['description'] = description
                        articles.append(article_data)
                except Exception as e:
                    print(f"Error processing article {url}: {e}")
                    continue

        return articles
    except Exception as e:
        print(f"Error scraping category: {e}")
        return []

def get_article_data(article_url, category):
    try:
        driver.get(article_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "No Title Found"

        description_tag = soup.find('h2')
        description = description_tag.text.strip() if description_tag else "No Description Found"

        content_div = soup.select_one('div.detail-content.afcbc-body')

        if content_div:
            for figcaption in content_div.find_all('figcaption'):
                figcaption.decompose() 
            
            for paragraph in content_div.find_all('p', class_='VCObjectBoxRelatedNewsItemSapo'):
                paragraph.decompose()  

            paragraphs = content_div.find_all(['p', 'h2', 'h3'])
            text_parts = []
            for elem in paragraphs:
                if elem.name in ['h2', 'h3']:
                    text_parts.append(f"{elem.get_text(strip=True)}\n")
                else:
                    for child in elem.children:
                        if child.name == 'a':
                            text_parts.append(child.get_text(strip=True))
                        elif isinstance(child, str):
                            text_parts.append(child.strip())
                    text_parts.append('\n')

            content = ' '.join(part for part in text_parts if part)
        else:
            content = "Không tìm thấy nội dung!"

        date_tag = soup.find('time')
        date_posted = date_tag['datetime'] if date_tag else datetime.now().isoformat()
        try:
            date_posted = datetime.fromisoformat(date_posted).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            date_posted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        author_div = soup.find('div', class_='detail-info')
        if author_div:
            author_info = author_div.find('div', class_='detail-author oneauthor')
            author_tag = author_info.find('div', class_='author-info') if author_info else None
            author = author_tag.text.strip() if author_tag else "Unknown"
        else:
            author = "Unknown"

        source_url = article_url
        status = "published"
        type_ = category

        image_tags = soup.find_all('img')
        image_urls = [img['src'] for img in image_tags if 'src' in img.attrs]

        video_tags = soup.find_all('video')
        video_urls = [video['src'] for video in video_tags if 'src' in video.attrs]

        return {
            'title': title,
            'description': description,
            'content': content,
            'date_posted': date_posted,
            'author': author,
            'source_url': source_url,
            'status': status,
            'type': type_,
            'image_urls': image_urls,
            'video_urls': video_urls
        }
    except Exception as e:
        print(f"Error getting article data from {article_url}: {e}")
        return None

def scrape_articles_from_categories(categories):
    all_articles = []
    for category in categories:
        category_url = f'https://tuoitre.vn/{category}.htm'
        print(f"Scraping category: {category}")
        articles = scrape_articles(category_url, category)
        all_articles.extend(articles)
    return all_articles

def fetch_existing_articles_content():
    cursor.execute("SELECT content FROM Articles")  # Lấy nội dung từ bảng Articles
    return cursor.fetchall()  # Trả về danh sách các hàng nội dung

def remove_duplicates_optimized(articles, threshold=0.8):
    existing_contents = [content[0] for content in fetch_existing_articles_content()]
    all_contents = existing_contents + [article["content"] for article in articles]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_contents)

    similarity_matrix = cosine_similarity(tfidf_matrix)

    unique_articles = []
    for i, new_article in enumerate(articles):
        new_index = len(existing_contents) + i  # Vị trí của bài báo mới trong ma trận
        is_duplicate = any(similarity_matrix[new_index, j] >= threshold for j in range(len(existing_contents)))

        if not is_duplicate:
            unique_articles.append(new_article)

    return unique_articles

def generate_article_id():
    cursor.execute("""
        SELECT TOP 1 CAST(RIGHT(article_id, LEN(article_id) - 3) AS INT) 
        FROM Articles 
        WHERE article_id LIKE 'BB-%' 
        ORDER BY CAST(RIGHT(article_id, LEN(article_id) - 3) AS INT) DESC
    """)
    
    last_record = cursor.fetchone()
    last_num = last_record[0] if last_record and last_record[0] is not None else 0  
    new_id_num = last_num + 1
    new_id = f"BB-{new_id_num}"
    
    return new_id

def save_article_to_db(article_data):
    try:
        article_id = generate_article_id()  

        cursor.execute("SELECT COUNT(*) FROM Articles WHERE title = ?", article_data['title'])
        if cursor.fetchone()[0] > 0:
            print(f"Article '{article_data['title']}' already exists. Skipping insertion.")
            return  

        cursor.execute("""
            INSERT INTO Articles (article_id, title, description, content, date_posted, author, source_url, status, type, image_urls, video_urls) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        article_id,
        article_data['title'], 
        article_data['description'], 
        article_data['content'],
        article_data['date_posted'], 
        article_data['author'], 
        article_data['source_url'],
        article_data['status'], 
        article_data['predicted_type'], 
        ', '.join(article_data['image_urls']),  
        ', '.join(article_data['video_urls'])  
        )
        conn.commit()
        print(f"Saved article: {article_data['title']}")
    except Exception as e:
        print(f"Failed to insert article into SQL database: {e}")

categories = ['thoi-su']

# Load mô hình phân loại bài báo
def load_model_and_features(model_path='text_classifier.pkl', features_path='features.pkl'):
    with open(model_path, 'rb') as f:
        clf = pickle.load(f)  # Load model
    with open(features_path, 'rb') as f:
        features = pickle.load(f)  # Load danh sách từ đặc trưng
    return clf, features

# Chuyển đổi văn bản thành vector đặc trưng
def transform_text_to_features(text_data, features):
    dataset = np.zeros((len(text_data), len(features)), dtype=np.float32)
    for i, text in enumerate(text_data):
        word_list = [word.strip(string.punctuation).lower() for word in text.split()]
        for word in word_list:
            if word in features:
                dataset[i][features.index(word)] += 1
    return dataset

# Cào danh sách 20 bài báo mới nhất
def scrape_latest_articles(limit=20):
    url = "https://tuoitre.vn/tin-moi-nhat.htm"

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    articles = []
    news_list = soup.find("div", id="load-list-news")
    if news_list:
        article_items = news_list.find_all("div", class_="box-category-item")[:limit]

        for article in article_items:
            try:
                time_tag = article.find("span", class_="time-ago-last-news")
                date_posted = time_tag["title"] if time_tag else "Không rõ ngày"

                link_tag = article.find("a", class_="box-category-link-with-avatar")
                if not link_tag:
                    continue
                article_url = "https://tuoitre.vn" + link_tag["href"]
                title = link_tag["title"]

                img_tag = link_tag.find("img")
                image_url = img_tag["src"] if img_tag else None

                articles.append({
                    "title": title,
                    "url": article_url,
                    "date_posted": date_posted,
                    "image_url": image_url
                })

                if len(articles) >= limit:
                    break

            except Exception as e:
                print(f"Lỗi khi lấy dữ liệu bài báo: {e}")
                continue

    return articles

def format_date(date_string):
    if not date_string:  # Nếu `None` hoặc rỗng, dùng ngày hiện tại
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Loại bỏ "GMT+7" nếu có
        date_string = date_string.replace(" GMT+7", "").strip()

        # Xử lý ngày theo định dạng chuẩn SQL Server
        return datetime.strptime(date_string, "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Nếu lỗi, dùng ngày hiện tại

# Cào nội dung từng bài báo & phân loại
def get_article_content(article_url, clf, features):
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(article_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.find("h1")
        title = title_tag.text.strip() if title_tag else "Không tìm thấy tiêu đề"

        description_tag = soup.find("h2")
        description = description_tag.text.strip() if description_tag else "Không tìm thấy mô tả"

        content_div = soup.select_one("div.detail-content.afcbc-body")
        if not content_div:
            print(f"Không tìm thấy nội dung bài báo: {article_url}")
            return None

        # Xóa các phần không cần thiết
        for unwanted in content_div.find_all("div", class_=["VCSortableInPreviewMode"], type="RelatedNewsBox"):
            unwanted.decompose()

        # Xử lý nội dung
        content = ""
        for elem in content_div.find_all(["p", "h2", "h3", "figure"]):
            if elem.name in ["h2", "h3"]:
                content += f"<{elem.name}>{elem.get_text(strip=True)}</{elem.name}>\n"
            elif elem.name == "figure":
                img_tag = elem.find("img")
                caption_tag = elem.find("figcaption")
                if img_tag:
                    content += f'<figure><img src="{img_tag["src"]}" alt="{img_tag.get("alt", "")}" /></figure>'
                if caption_tag:
                    content += f'<figcaption>{caption_tag.get_text(strip=True)}</figcaption>'
            else:
                content += f"<p>{elem.get_text(strip=True)}</p>\n"

        # Dự đoán loại bài báo
        X = transform_text_to_features([content], features)
        predicted_type = clf.predict(X)[0]

        # Lấy tác giả
        author_div = soup.find("div", class_="detail-author")
        author = author_div.text.strip() if author_div else "Không rõ tác giả"

        # Lấy ngày đăng bài
        date_tag = soup.select_one('div.detail-time [data-role="publishdate"]')
        date_posted = format_date(date_tag.get_text(strip=True) if date_tag else None)

        # Lấy danh sách ảnh & video
        image_urls = [img["src"] for img in content_div.find_all("img") if "src" in img.attrs]
        video_urls = [video["src"] for video in soup.find_all('video') if 'src' in video.attrs]

        return {
            "title": title,
            "description": description,
            "content": content,
            "date_posted": date_posted,
            "author": author,
            "source_url": article_url,
            "status": "published",
            "predicted_type": predicted_type,
            "image_urls": image_urls,
            "video_urls": video_urls,
        }

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ {article_url}: {e}")
        return None
    finally:
        driver.quit()

# Chạy chương trình
clf, features = load_model_and_features()
latest_articles = scrape_latest_articles(limit=20)

for article in latest_articles:
    article_data = get_article_content(article["url"], clf, features)
    if article_data:
        save_article_to_db(article_data)


# Cào bài viết mới nhất & phân loại
# article_url = "https://nld.com.vn/deepseek-thuc-day-chay-dua-ai-giua-my-va-trung-quoc-196250217211123744.htm"
# article_data = get_article_content(article_url, clf, features)

# # Hiển thị kết quả
# if article_data:
#     print("\nKết quả cào dữ liệu & phân loại bài báo:")
#     print(f"Tiêu đề: {article_data['title']}")
#     print(f"Mô tả: {article_data['description']}")
#     print(f"Loại bài báo dự đoán: {article_data['type']}")


# # Cào tất cả các bài báo từ các danh mục
# all_articles = scrape_articles_from_categories(categories)

# # Loại bỏ các bài báo trùng lặp dựa trên nội dung đã có trong cơ sở dữ liệu
# unique_articles = remove_duplicates_optimized(all_articles)

# # Lưu dữ liệu bài viết vào file JSON
# with open('all_articles.json', 'w', encoding='utf-8') as json_file:
#     json.dump(unique_articles, json_file, ensure_ascii=False, indent=4)

# print("Data saved to 'all_articles.json'")

# Đóng trình duyệt sau khi hoàn tất
driver.quit()
cursor.close()
conn.close()