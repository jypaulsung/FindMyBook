import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import re

# Initialize Bing Search API key and endpoint
subscription_key = 'YOUR_BING_SEARCH_API_KEY'
bing_endpoint = 'https://api.bing.microsoft.com/v7.0/search'

# Load data from CSV file and read in book titles
csv_path = 'SF_keywords.csv'
df = pd.read_csv(csv_path)

# Function to search for book information using Bing Search API
def search_book_info_bing(query):
    params = {
        'q': f"책 {query}",  # Add '책' in front of the query to get book-related results
        'mkt': 'ko-KR',
        'cc': 'KR',
        'promote': 'Webpages,News',
        'answerCount': 10,  # Return up to 10 results
        'count': 10,        # Return 10 results per request
        'setLang': 'ko',
    }
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}
    response = requests.get(bing_endpoint, headers=headers, params=params)
    response.raise_for_status()

    return response.json()

# Function to fetch page content from a URL
def fetch_page_content(url):
    try:
        page_response = requests.get(url, timeout=10)
        page_response.raise_for_status()
        return page_response.text
    except requests.exceptions.RequestException as e:
        print(f"{url}에서 페이지 콘텐츠를 가져오는 데 실패했습니다: {e}")
        return None

# Function to extract text content from HTML and filter out unwanted patterns
def extract_text_from_html(html_content, keywords):
    soup = BeautifulSoup(html_content, 'html.parser')
    text_elements = soup.find_all('p')
    text = ' '.join([element.get_text(separator=' ', strip=True) for element in text_elements])

    # Remove unwanted patterns from the text
    patterns_to_remove = [
        r'(?i)NAVER', r'공감', r'이웃추가', r'본문 바로가기', r'블로그 메뉴', r'로그인', r'카테고리 이동',
        r'블로그 검색', r'댓글 [0-9]+', r'메뉴 바로가기', r'내 블로그', r'이웃블로그', r'프롤로그',
        r'블로그 홈', r'이 블로그의 저작물은 별도 표시가 없는 한', r'댓글쓰기', r'검색', r'RSS [0-9.]+',
        r'QR/바코드 검색', r'최근 검색어', r'글 목록', r'최상단으로 이동', r'전체보기 [0-9,]+개의 글',
        r'네이버 백신', r'글 제목', r'공감한 사람 보러가기', r'닫기', r'블로그', r'URL 복사', r'공유하기',
        r'신고하기', r'메뉴', r'기능', r'이 블로그에서 공유하기', r'서재', r'가벼운 글쓰기툴 퀵에디터가 오픈했어요',
        r'주요메뉴', r'QR/바코드', r'공지 목록', r'안부', r'목록열기', r'작성일', r'전체보기 목록열기',
        r'오늘의 책 소개', r'책 소개', r'책방 문화', r'글쓰기', r'일지', r'자세한 내용을 보려면 링크를 클릭해주세요',
        r'이 포스트는 네이버 블로그에서 작성된 게시글입니다', r'공연', r'지도', r'태그', r'첫 댓글을 남겨보세요',
        r'공지글', r'MY', r'열기', r'책', r'네이버 여행 서비스 종료', r'이용제한', r'서비스 종료 안내',
        r'고객 센터', r'신고된 표현 포함', r'비밀번호 확인', r'이용 제한', r'스팸', r'알림', r'기타'
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text)

    # Check if any of the title keywords are present in the text
    if not any(keyword in text for keyword in keywords):
        return ""

    # Remove extra whitespaces and return the cleaned text
    cleaned_text = re.sub(r'\s+', ' ', text).strip()

    return cleaned_text

# Iterate through each row in the DataFrame and search for book information using Bing Search API
web_search_results = []
for index, row in df.iterrows():
    print(f"데이터 검색 중: {row['title']}")

    # Convert title to string and handle NaN values
    title = str(row['title']) # Convert to string
    if title == 'nan':
      print(f"Skipping row with missing title (index: {index})")
      continue

    search_result = search_book_info_bing(title)

    combined_content = ""
    keywords = title.split()  # Split title into keywords for text filtering
    valid_url_count = 0  # Track the number of valid URLs found

    for item in search_result.get('webPages', {}).get('value', []):
        url = item['url']

        # Filter out URLs from specific domains
        if any(domain in url for domain in ['kyobobook', 'aladin', 'yes24', 'wiki', 'ridibooks']):
            print(f"{url}의 콘텐츠는 스킵합니다.")
            continue

        print(f"\n{url}에서 콘텐츠 가져오는 중...")
        html_content = fetch_page_content(url)
        if html_content:
            page_text = extract_text_from_html(html_content, keywords)
            if page_text:
                print(f"{url}에서 파싱된 내용:\n{page_text[:1000]}...\n")
                combined_content += page_text
                valid_url_count += 1

        # Stop searching if contents from 5 valid URLs have been retrieved
        if valid_url_count >= 5:
            break

    # Store the retrieved content in the DataFrame as a new column 'web_search_data'
    df.at[index, 'web_search_data'] = combined_content

# Save the DataFrame to a CSV file
df.to_csv('SF_Bing.csv', index=False)
print("데이터가 'SF_Bing.csv'에 저장되었습니다.")