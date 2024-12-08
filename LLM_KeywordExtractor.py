import os
import time
from groq import Groq
import pandas as pd
import tiktoken
import csv


# Initialize the Groq API key
GROQ_API_KEY = "YOUR_GROQ_API"

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

# Function to count tokens
def num_tokens_from_string(string: str, encoding_name: str) -> int:
  """ Return the number of tokens in a text string."""
  encoding = tiktoken.get_encoding(encoding_name)
  num_tokens = len(encoding.encode(string))
  return num_tokens

# Function to use LLAMA3 model to extract keywords based on the book's data
def extract_keywords_from_data(book_title, data):
  # Maximum token limit for the input
  max_tokens = 5000

  # Count the number of tokens in the input data
  input_tokens = num_tokens_from_string(data, "cl100k_base")

  # Truncate the input data if it exceeds the token limit
  if input_tokens > max_tokens:
    encoding = tiktoken.get_encoding("cl100k_base")
    truncated_data = encoding.decode(encoding.encode(data)[:max_tokens])
    print(f"Input data truncated from {input_tokens} tokens to {max_tokens} tokens.")
    data = truncated_data
  prompt = (
      f"book_title: '{book_title}'\n"
      f"input_data: '{data}'\n\n"
      "Analyze and return the results under the following conditions. Follow the conditions strictly."
      "1. Analyze the book_title and input_data to extract 10 relevant keywords that represent the book.\n"
      "2. Keywords should all be in Korean and delineated with commas like '우주선, 지구, 인류, SF' format.\n"
      "3. Do not select the book_title itself or genre 'SF' as a keyword.\n"
      "4. Do not select the author's name as a keyword."
      "5. Do not select names of awards as keywords."
      "6. Return only the keywords. Do not include any explanation or additional sentences.\n"
      "7. Do not add 'Here are the relevant keywords representing the book, based on the analysis of the input data:' in the result.\n"
  )

  response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are an assistant that helps to identify book titles, characters, and relevant keywords."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.2,
    )
  # Only extract words split by commas
  result_text = response.choices[0].message.content.strip()
  return result_text

# Load the data from the CSV file
df_llm = pd.read_csv('SF_LLM.csv')
df_keywords = pd.read_csv('SF_LLM_keywords.csv')

# Get the list of book titles in SF_LLM_keywords.csv
existing_titles = df_keywords['title'].tolist()

# Iterate through SF_LLM.csv and check for missing titles
for index, row in df_llm.iterrows():
    book_title = row['title']
    web_search_text = row['web_search_data']  # Assuming this column exists in SF_LLM.csv

    # Check if web_search_data is available
    if pd.isna(web_search_text) or not web_search_text.strip():
      print(f"Book with empty 'web_search_data': {book_title}")
      continue

    if book_title not in existing_titles:
      try:
        print(f"Processing missing book {index+1}: {book_title}")
        result_text = extract_keywords_from_data(book_title, web_search_text)
        print(f"Extracted keywords: {result_text}")

        # Append the new data to SF_LLM_keywords.csv
        new_row = {'title': book_title, 'web_search_data_keywords': result_text}
        df_keywords = pd.concat([df_keywords, pd.DataFrame([new_row])], ignore_index=True)
        df_keywords.to_csv('SF_LLM_keywords.csv', index=False)

        # Add the book title to existing_titles to avoid re-processing
        existing_titles.append(book_title)
      except Exception as e:
        print(f"Error processing book {index+1} - '{book_title}': {e}")

print("Missing book titles processed and keywords added to SF_LLM_keywords.csv")

# Read 'book_intro', 'summary', 'publisher_review', and 'purchase_review' columns
# Merge them into one column and use it to extract keywords with LLM
# Function to merge specified columns
def merge_columns(row, columns):
  return ' '.join([row[col] for col in columns if col in row and row[col]])

# Function to extract titles from temp_file.csv
def get_processed_titles(temp_file_path):
  processed_titles = set()
  if os.path.exists(temp_file_path):
    with open(temp_file_path, mode='r', encoding='utf-8') as temp_file:
      reader = csv.DictReader(temp_file)
      for row in reader:
        processed_titles.add(row['title'])
  return processed_titles

# Function to read the CSV file and process each row
# Merge columns, extract keywords from the merged column, and update the keywords to the CSV file
def append_keywords_to_csv(file_path, temp_file_path):
  processed_titles = get_processed_titles(temp_file_path)
  with open(file_path, mode='r', encoding='utf-8') as input_file, open(temp_file_path, mode='a', encoding='utf-8') as output_file:
    reader = csv.DictReader(input_file)
    fieldnames = reader.fieldnames + ['basic_LLM_keywords']
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)

    # Check if the temp_file is empty
    if os.stat(temp_file_path).st_size == 0:
      writer.writeheader()

    for row in reader:
      if row['title'] not in processed_titles:
        merged_text = merge_columns(row, ['book_intro', 'summary', 'publisher_review', 'purchase_review'])
        keywords = extract_keywords_from_data(row['title'], merged_text)
        # Add the keywords to 'basic_LLM_keywords' column
        print(f"Keywords extracted from the book {row['title']}: {keywords}")
        row['basic_LLM_keywords'] = keywords
        # Update the csv file
        writer.writerow(row)

file_path = 'SF_data.csv'
temp_file_path = 'temp_file.csv'
append_keywords_to_csv(file_path, temp_file_path)

print(f"Keywords have been updated to {temp_file_path}")

# Merge keywords from temp_file.csv and SF_LLM_keywords.csv to create 'extended_keywords' column
# Save the 'extended_keywords' column with 'title' column in SF_extended_keywords.csv
# Read rows from temp_file.csv and SF_LLM_keywords.csv
temp_df = pd.read_csv('temp_file.csv')
sf_llm_df = pd.read_csv('SF_LLM_keywords.csv')

# Initialize a list to store the results
results = []

# Iterate through each row in temp_file.csv
for _, temp_row in temp_df.iterrows():
  title = temp_row['title']
  basic_llm_keywords = temp_row['basic_LLM_keywords']

  # Check if the title exists in SF_LLM_keywords.csv
  sf_llm_row = sf_llm_df[sf_llm_df['title'] == title]

  if not sf_llm_row.empty:
    # Merge the keywords if the title exists
    web_search_data_character_keywords = sf_llm_row['web_search_data_character_keywords'].values[0]
    extended_keywords = f"{basic_llm_keywords}, {web_search_data_character_keywords}"
  else:
    # Use the basic_llm_keywords if the title does not exist
    extended_keywords = basic_llm_keywords

  # Append the result to the list
  results.append({'title': title, 'extended_keywords': extended_keywords})

# Create a DataFrame from the results and save it to a new CSV file
extended_keywords_df = pd.DataFrame(results)
extended_keywords_df.to_csv('SF_extended_keywords.csv', index=False)

print("SF_extended_keywords.csv file has been created successfully.")

# Filtering out keywords from SF_extended_keywords.csv
# List of keywords to filter out
keyword_filter = ['SF', '과학', '소설', '판타지', '예스24', '북클럽', '리뷰', '문장', '인물', '스토리', '상상력', 'SF 소설', '과학 소설', 'SF소설',
                  '한국형 SF', '과학기술', '과학소설', '공상 과학 소설', '_SF 문학', '과학 기술', '모험 소설', '공상 과학', 'SF 장르', '장르문학', '네이버',
                  'eBook', '오디오북', '애플TV+', 'SF액션영화', 'sf소설', '_SF', '장르', 'sf', 'PC', '앱', '기기', '콘텐츠', '사이언스 픽션', 'iPad', '예약판매',
                  '출간기념','스페셜 박스세트','안락할 독서','완전판','이벤트', 'SF 문학', 'SF시리즈', '_SF_영화','마이클_베이', '출판', '도서', '읽기',
                  'PC 모바일', '네이버 eBook리더', '시리즈 앱', '기기 변경', '전권 구매', '저작권법', '통신판매업', '코넬대학교', '스탠퍼드대학교',
                  '소설가', ]
# Function to remove duplicate keywords and filter based on keyword_filter
def process_keywords(keywords):
  # Split the keywords by commas and remove leading/trailing spaces
  keywords_list = [keyword.strip() for keyword in keywords.split(',')]

  # Remove duplicate keywords
  unique_keywords = list(dict.fromkeys(keywords_list)) # Preserve order using dict.fromkeys

  # Filter out keywords in keyword_filter
  filtered_keywords = [keyword for keyword in unique_keywords if keyword not in keyword_filter]

  # Join the filtered keywords back into a comma-separated string
  return ', '.join(filtered_keywords)

# Read the CSV file
df = pd.read_csv('SF_extended_keywords.csv')

# Apply the process_keywords function to the 'extended_keywords' column
df['extended_keywords'] = df['extended_keywords'].apply(process_keywords)

# Save the updated DataFrame to a CSV file
df.to_csv('SF_extended_keywords_filtered.csv', index=False)

print("Duplicate keywords removed and keywords filtered. Results saved to SF_extended_keywords_filtered.csv.")