import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from pyngrok import ngrok

ngrok.set_auth_token("ngrok_auth_token")

# Start ngrok tunnel - Connect it to port 8502
public_url = ngrok.connect(8502)
print("Public URL:", public_url)

# Initialize OpenAI API Client
client = OpenAI(
    api_key = "OpenAI_API_Key",
    base_url = "https://api.upstage.ai/v1/solar",
)

# Authentication for the Naver API
NAVER_CLIENT_ID = "NAVER_Client_ID"
NAVER_CLIENT_SECRET = "NAVER_Client_Password"

# Page layout configuration for Streamlit
st.set_page_config(
    page_title="📚 책 추천 시스템",
    page_icon="📖",
    layout="wide"
)

# Load data
file_path = "books_with_solar_embeddings.csv"
data = pd.read_csv(file_path)

# Convert 'embedding' column back to numpy array
data["embedding"] = data["embedding"].apply(lambda x: np.array(list(map(float, x.split(',')))))

# Function to preprocess keywords: remove punctuation and duplicate words
def preprocess_text(text):
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

# Function to search for a book using the Naver API
def search_book_on_naver(book_title):
    url = "https://openapi.naver.com/v1/search/book.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": book_title, "display": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result["items"]:
            item = result["items"][0]
            return {
                "title": item["title"],
                "description": item["description"],
                "image": item["image"],
                "link": item["link"],
            }
    return None

# Function to generate a user embedding using Solar API
def get_weighted_user_embedding(user_input, client):
    processed_input = preprocess_text(user_input)
    keywords = processed_input.split(",")  # Split user input by comma
    embeddings = []

    for keyword in keywords:
        if keyword.strip():
            try:
                response = client.embeddings.create(
                    input=keyword.strip(),
                    model="embedding-passage"
                )
                embedding = np.array(response.data[0].embedding)
                embeddings.append(embedding)
            except Exception as e:
                st.error(f"키워드 임베딩 생성 중 오류 발생: {keyword}, {e}")
                embeddings.append(np.zeros(768))

    if embeddings:
        return np.average(embeddings, axis=0)
    return np.zeros(768)

# Function to recommend books based on keyword embeddings
def recommend_books_with_weighted_keywords(user_input, data, client, top_n=5):
    user_embedding = get_weighted_user_embedding(user_input, client)
    data["similarity"] = data["embedding"].apply(
        lambda book_emb: cosine_similarity(user_embedding.reshape(1, -1), book_emb.reshape(1, -1))[0][0]
    )
    recommendations = data.sort_values(by="similarity", ascending=False).head(top_n)
    # Return a list of dictionaries with title and similarity
    print(recommendations[["title", "similarity"]].to_dict(orient="records"))
    return recommendations[["title", "similarity"]].to_dict(orient="records")

# Function to fetch book details from Naver API
def fetch_recommendations_with_details(recommended_books, exclude_title=None):
    results = []
    for book in recommended_books:
        title = book["title"]
        similarity = book["similarity"]
        if exclude_title and title == exclude_title: # Skip the input book
            print(f"Skipping {title} as it is the same as the input book.") 
            continue
        book_info = search_book_on_naver(title)
        if book_info:
            book_info["similarity"] = similarity  # Add 'similarity' column to book_info
            results.append(book_info)
    return results

# Streamlit UI
st.title("📚 책 추천 시스템")
st.sidebar.title("검색 옵션")
st.sidebar.markdown("**책 제목을 입력하세요.**")
book_title_input = st.sidebar.text_input("🔍 책 제목 입력:", "예: 프로젝트 헤일메리")
top_n = st.sidebar.slider("추천 받을 책 수:", min_value=1, max_value=10, value=5)

# Show recommendations when the button is clicked
if st.sidebar.button("추천 받기"):
    st.markdown("## 추천 결과:")

    # Call the Naver API to search for the book
    book_info = search_book_on_naver(book_title_input)
    if book_info:
        st.image(book_info["image"], width=120)
        st.markdown(f"**책 제목:** {book_info['title']}")
        st.markdown(f"**책 설명:** {book_info['description']}")
        st.markdown(f"**[🔗 네이버 책 링크]({book_info['link']})**")

        # Use the Solar API to find similar books
        recommended_books = recommend_books_with_weighted_keywords(
            book_info["description"], data, client, top_n=top_n
        )

        # Retrieve details for the recommended books from the Naver API
        recommendations = fetch_recommendations_with_details(recommended_books, exclude_title=book_info["title"])

        # Display the recommended books
        if recommendations:
            for book in recommendations:
                st.markdown(f"### 📖 {book['title']}")
                st.image(book["image"], width=120)
                st.markdown(f"**줄거리:** {book['description']}")
                st.markdown(f"**유사도:** {book['similarity']:.4f}") # Show Cosine Similarity to the 4th decimal point
                st.markdown(f"**[🔗 네이버 책 링크]({book['link']})**")
                st.markdown("---")
        else:
            st.warning("추천 결과가 없습니다.")