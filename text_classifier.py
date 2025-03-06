import pyodbc
import pandas as pd
import pickle
import numpy as np
import string

def load_model_and_features(model_path='text_classifier.pkl', features_path='features.pkl'):
    with open(model_path, 'rb') as f:
        clf = pickle.load(f)
    with open(features_path, 'rb') as f:
        features = pickle.load(f)
    return clf, features

def fetch_new_articles():
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=ADMIN-PC;"
        "DATABASE=dataBao;"
        "Trusted_Connection=yes;"
    )
    connection = None
    try:
        connection = pyodbc.connect(conn_str)
        query = "SELECT * FROM NewArticles"  # Bảng chứa bài viết mới
        df = pd.read_sql(query, connection)
        return df
    except pyodbc.Error as e:
        print("Lỗi kết nối hoặc truy vấn:", e)
        return None
    finally:
        if connection:
            connection.close()

def transform_text_to_features(text_data, features):
    """Chuyển đổi văn bản thành features vector"""
    dataset = np.zeros((len(text_data), len(features)), dtype=np.float32)
    for i, text in enumerate(text_data):
        word_list = [word.strip(string.punctuation).lower() for word in text.split()]
        for word in word_list:
            if word in features:
                dataset[i][features.index(word)] += 1
    return dataset

def predict_and_save_results(predictions, df, output_table='NewArticles'):
    """Lưu kết quả dự đoán vào database"""
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=ADMIN-PC;"
        "DATABASE=dataBao;"
        "Trusted_Connection=yes;"
    )
    connection = None
    try:
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        # Cập nhật từng dòng với kết quả dự đoán
        for i, pred in enumerate(predictions):
            article_id = df.iloc[i]['article_id']
            update_query = f"UPDATE {output_table} SET predicted_type = ? WHERE article_id = ?"
            cursor.execute(update_query, (pred, article_id))
        
        connection.commit()
        print("Đã lưu kết quả dự đoán vào database")
    except pyodbc.Error as e:
        print("Lỗi khi lưu kết quả:", e)
    finally:
        if connection:
            connection.close()

def main():
    # Load mô hình và features đã train
    clf, features = load_model_and_features()
    
    # Lấy dữ liệu mới cần phân loại
    df = fetch_new_articles()
    if df is None:
        return
    
    # Chuyển văn bản thành features
    X = transform_text_to_features(df['content'], features)
    
    # Dự đoán
    predictions = clf.predict(X)
    
    # Lưu kết quả
    predict_and_save_results(predictions, df)
    
    # In kết quả ra màn hình để kiểm tra
    df['predicted_type'] = predictions
    print("\nKết quả dự đoán:")
    print(df[['article_id', 'content', 'predicted_type']].head())

if __name__ == "__main__":
    main()