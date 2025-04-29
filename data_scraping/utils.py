import logging
import numpy as np
import psycopg2
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dateutil.parser import parse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Chrome options config
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--enable-unsafe-swiftshader")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-webgl")

@contextmanager
def get_webdriver():
    driver = webdriver.Chrome(options=chrome_options)
    try:
        yield driver
    finally:
        driver.quit()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            connect_timeout=5,
            sslmode="require"
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}", exc_info=True)
        raise

def load_model_and_features(model_path='text_classifier.pkl', features_path='features.pkl'):
    try:
        clf = joblib.load(model_path)
        features = joblib.load(features_path)
        logger.info("Loaded model and features")
        return clf, features
    except Exception as e:
        logger.error(f"Error loading model/features: {e}", exc_info=True)
        return None, None

def transform_text_to_features(text_data, features):
    try:
        vectorizer = CountVectorizer(vocabulary=features, lowercase=True)
        dataset = vectorizer.transform(text_data).toarray()
        return dataset
    except Exception as e:
        logger.error(f"Error transforming text: {e}", exc_info=True)
        return np.zeros((len(text_data), len(features)), dtype=np.float32)

def fetch_existing_articles_content(cursor, limit=None):
    query = "SELECT content FROM articles"
    if limit:
        query += f" ORDER BY date_posted DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]

def remove_duplicates_optimized(articles, cursor, threshold=0.8, batch_size=1000):
    existing_contents = fetch_existing_articles_content(cursor, limit=batch_size)
    if not articles or not existing_contents:
        return articles
    new_contents = [article["content"] for article in articles]
    vectorizer = CountVectorizer()
    tfidf_existing = vectorizer.fit_transform(existing_contents)
    tfidf_new = vectorizer.transform(new_contents)
    similarity_matrix = cosine_similarity(tfidf_new, tfidf_existing)
    unique_articles = [
        article for i, article in enumerate(articles)
        if not np.any(similarity_matrix[i] >= threshold)
    ]
    logger.info(f"Kept {len(unique_articles)} unique articles out of {len(articles)}")
    return unique_articles

def generate_article_id(cursor):
    cursor.execute("""
        SELECT MAX(CAST(SUBSTRING(article_id, 4, LENGTH(article_id)) AS INT))
        FROM articles WHERE article_id LIKE 'BB-%'
    """)
    last_num = cursor.fetchone()[0] or 0
    return f"BB-{last_num + 1}"

def save_article_to_db(article_data, cursor, conn):
    try:
        article_id = generate_article_id(cursor)
        cursor.execute("SELECT COUNT(*) FROM articles WHERE title = %s", (article_data['title'],))
        if cursor.fetchone()[0] > 0:
            logger.info(f"Article '{article_data['title']}' already exists. Skipping.")
            return
        
        max_lengths = {
            'author': 255, 'title': 500, 'description': 1000, 'content': 8000,
            'source_url': 1000, 'image_urls': 2000, 'video_urls': 2000
        }
        safe_data = {
            key: (value[:max_lengths.get(key, 8000)] if isinstance(value, str) else value)
            for key, value in article_data.items()
        }
        safe_image_urls = ','.join(safe_data['image_urls']) if safe_data['image_urls'] else ''
        safe_video_urls = ','.join(safe_data['video_urls']) if safe_data['video_urls'] else ''

        with conn:
            cursor.execute("""
                INSERT INTO articles (
                    article_id, title, description, content, date_posted, 
                    author, source_url, status, type, image_urls, video_urls
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                article_id, safe_data['title'], safe_data['description'], safe_data['content'],
                safe_data['date_posted'], safe_data['author'], safe_data['source_url'],
                safe_data['status'], safe_data['predicted_type'], safe_image_urls, safe_video_urls
            ))
            conn.commit()
        logger.info(f"Saved article: {safe_data['title']} with ID {article_id}")
    except Exception as e:
        logger.error(f"Failed to save article '{article_data.get('title', 'Unknown')}': {e}")
        conn.rollback()
