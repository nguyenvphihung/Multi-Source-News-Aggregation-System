from utils import get_db_connection, get_webdriver, load_model_and_features, remove_duplicates_optimized, save_article_to_db
from scrape_tuoitre import scrape_tuoitre_articles, fetch_article_content as fetch_tuoitre_content
from scrape_nld import scrape_nld_articles, fetch_article_content as fetch_nld_content
from scarpe_vnexpress import scrape_vnexpress_articles, fetch_article_content as fetch_vnexpress_content
from scape_vietnamnet import scrape_vietnamnet_articles, fetch_article_content as fetch_vietnamnet_content  # Thêm mới
from scrape_vietnamplus import scrape_vietnamplus_articles, fetch_article_content as fetch_vietnamplus_content  # Thêm mới

from utils import (
    get_db_connection, get_webdriver, load_model_and_features, 
    remove_duplicates_optimized, save_article_to_db, logger
)

def main(sites=["tuoitre", "nld", "vnexpress", "vietnamnet", "vietnamplus"], article_limit=20, similarity_threshold=0.8):
    conn = get_db_connection()
    cursor = conn.cursor()
    clf, features = load_model_and_features()
    if not clf or not features:
        logger.error("Failed to load model or features")
        return

    with get_webdriver() as driver:
        all_articles = []
        
        if "nld" in sites:
            all_articles.extend(scrape_nld_articles(limit=article_limit, driver=driver))
        if "vnexpress" in sites:
            all_articles.extend(scrape_vnexpress_articles(limit=article_limit, driver=driver))
        if "vietnamnet" in sites:
            all_articles.extend(scrape_vietnamnet_articles(limit=article_limit, driver=driver))
        if "vietnamplus" in sites:
            all_articles.extend(scrape_vietnamplus_articles(limit=article_limit, driver=driver))
        if "tuoitre" in sites:
            all_articles.extend(scrape_tuoitre_articles(limit=article_limit, driver=driver)) 

        article_data_list = []
        for article in all_articles:
            if "nld.com.vn" in article["url"]:
                article_data = fetch_nld_content(article["url"], clf, features, driver)
            elif "vnexpress.net" in article["url"]:
                article_data = fetch_vnexpress_content(article["url"], clf, features, driver)
            elif "vietnamnet.vn" in article["url"]:
                article_data = fetch_vietnamnet_content(article["url"], clf, features, driver)
            elif "vietnamplus.vn" in article["url"]:
                article_data = fetch_vietnamplus_content(article["url"], clf, features, driver)
            elif "tuoitre.vn" in article["url"]:
                article_data = fetch_tuoitre_content(article["url"], clf, features, driver)
            else:
                logger.warning(f"No fetch function defined for URL: {article['url']}")
                continue

            if article_data:
                article_data_list.append(article_data)

        unique_articles = remove_duplicates_optimized(article_data_list, cursor, threshold=similarity_threshold)
        for article_data in unique_articles:
            save_article_to_db(article_data, cursor, conn)

    cursor.close()
    conn.close()
    logger.info("Scraping completed")

if __name__ == "__main__":
    main()