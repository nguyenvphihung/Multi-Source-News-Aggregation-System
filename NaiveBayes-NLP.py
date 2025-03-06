import pyodbc
import pandas as pd
import string
import numpy as np
from sklearn import model_selection
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_score
import pickle

def fetch_data_from_db():
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=ADMIN-PC;"
        "DATABASE=dataBao;"
        "Trusted_Connection=yes;"
    )
    connection = None
    try:
        connection = pyodbc.connect(conn_str)
        query = "SELECT * FROM Articles"
        df = pd.read_sql(query, connection)
        return df
    except pyodbc.Error as e:
        print("Lỗi kết nối hoặc truy vấn:", e)
    finally:
        if connection:
            connection.close()

def build_vocabulary(text_data, stopwords, cutoff_freq=1):
    vocab = {}
    for text in text_data:
        for word in text.split():
            word_new = word.strip(string.punctuation).lower()
            if len(word_new) > 2 and word_new not in stopwords:
                vocab[word_new] = vocab.get(word_new, 0) + 1
    features = [word for word, freq in vocab.items() if freq >= cutoff_freq]
    return features

def transform_text_to_features(text_data, features):
    dataset = np.zeros((len(text_data), len(features)), dtype=np.float32)
    for i, text in enumerate(text_data):
        word_list = [word.strip(string.punctuation).lower() for word in text.split()]
        for word in word_list:
            if word in features:
                dataset[i][features.index(word)] += 1
    return dataset

def train_model(X_train, Y_train):
    clf = MultinomialNB()
    clf.fit(X_train, Y_train)
    return clf

def evaluate_model(clf, X_train, Y_train, X_test, Y_test):
    Y_test_pred = clf.predict(X_test)
    train_score = clf.score(X_train, Y_train)
    test_score = clf.score(X_test, Y_test)
    report = classification_report(Y_test, Y_test_pred)
    return train_score, test_score, report

def cross_validation(clf, X_train, Y_train, k=5):
    scores = cross_val_score(clf, X_train, Y_train, cv=k)
    return scores

stopwords = [
    'và', 'nhưng', 'có', 'không', 'cũng', 'rất', 'vì', 'đã', 'đang', 'được', 
    'trên', 'dưới', 'cho', 'từ', 'là', 'với', 'như', 'của', 'ở', 'để', 
    'thì', 'bị', 'bởi', 'này', 'nọ', 'nào', 'tại', 'ra', 'đó', 'vậy',
    'gì', 'khi', 'lúc', 'nên', 'mà', 'vẫn', 'đâu', 'đây', 'điều', 
    'sao', 'đôi', 'tuy', 'mỗi', 'một', 'các', 'nhiều', 'hơn', 'đều', 
    'cần', 'trước', 'sau', 'nữa', 'phải', 'hoặc', 'ai', 'gì', 
    'thế', 'vậy', 'nhỉ', 'vừa', 'mới', 'được', 'phía', 'trong', 
    'ngoài', 'khác', 'nếu', 'thì', 'làm', 'hết', 'vì', 'qua', 
    'dù', 'rằng', 'suốt', 'không', 'thành', 'đến', 'chỉ', 
    'một', 'đã', 'có', 'thể', 'thật', 'biết', 'bằng', 'cái', 
    'bao', 'rồi', 'luôn', 'chưa', 'nào', 'cái', 'trong', 
    'khi', 'cùng', 'theo', 'nơi', 'này', 'đi', 'dùng', 
    'gì', 'phía', 'do', 'lại', 'hay', 'được', 'với', 'bao', 
    'bao', 'một', 'lúc', 'chỉ', 'không', 'cũng', 'gì', 
    'mình', 'bạn', 'nào', 'đã', 'để', 'có', 'cho', 'của', 
    'và', 'nhưng', 'thì', 'chỉ', 'là', 'cái', 'tại', 
    'vì', 'mà', 'bởi', 'ai', 'lại', 'gì', 'này', 
    'này', 'đó', 'vì', 'được', 'lúc', 'khi',
    'com', 'net', 'org', 'http', 'https', 'www', 
    'tin', 'bài', 'theo', 'về', 'tại', 'từ', 'người',
    'cho', 'các', 'những', 'này', 'được', 'đang', 'cũng',
    'khi', 'đến', 'để', 'có thể', 'theo', 'tại', 'nơi'
]

if __name__ == "__main__":
    # Lấy dữ liệu từ database
    df = fetch_data_from_db()
    
    # Chuẩn bị dữ liệu
    X = np.array(df['content'])
    Y = np.array(df['type'])
    
    # Chia dữ liệu
    X_train, X_test, Y_train, Y_test = model_selection.train_test_split(X, Y, test_size=0.2, random_state=0)
    
    # Xây dựng từ vựng
    features = build_vocabulary(X_train, stopwords)
    
    # Tạo ma trận đặc trưng cho tập train và test
    X_train_dataset = transform_text_to_features(X_train, features)
    X_test_dataset = transform_text_to_features(X_test, features)
    
    # Huấn luyện mô hình
    clf = train_model(X_train_dataset, Y_train)
    
    # Đánh giá mô hình
    train_score, test_score, report = evaluate_model(clf, X_train_dataset, Y_train, X_test_dataset, Y_test)
    print("Sklearn's score on training data:", train_score)
    print("Sklearn's score on testing data:", test_score)
    print("Classification report for testing data:\n", report)
    
    # Cross-validation
    scores = cross_validation(clf, X_train_dataset, Y_train)
    print("Cross-validation scores:", scores)
    print("Mean accuracy across folds:", scores.mean())


with open('text_classifier.pkl', 'wb') as f:
    pickle.dump(clf, f)
with open('features.pkl', 'wb') as f:
    pickle.dump(features, f)