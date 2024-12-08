import requests
from bs4 import BeautifulSoup
import csv
import re

# Extracting book urls and page numbers of the genre from the main url
main_url = "https://www.yes24.com/Product/Category/SteadySeller?pageNumber=1&pageSize=24&categoryNumber=001001046011005" # SF genre
response = requests.get(main_url)

if response.status_code == 200:
  html = response.text
  soup = BeautifulSoup(html, 'html.parser')
  genre = soup.select_one('#divTitle > h3 > em > u').text
  print(f"Extracting book urls and page numbers of {genre} genre from {main_url}")
else:
  print(response.status_code)
  print("Please try again.")

num_pages = soup.select_one('#bestContentsWrap > div.bSGoodsPagen > div > div > div > a.bgYUI.end').get('title')
titles = {}
book_urls = {}

# Function to get book titles and urls from each page
def get_book_urls(page_num):
  url = f"https://www.yes24.com/Product/Category/SteadySeller?pageNumber={page_num}&pageSize=24&categoryNumber=001001046011005"
  response = requests.get(url)
  if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    print(f"Successfully accessed page {page_num} of {genre} genre.")
  else:
    print(response.status_code)
    print("Please try again.")
  titles[f"title_{page_num}"] = []
  book_urls[f"book_url_{page_num}"] = {}
  for i in range(1, 25):
    if not soup.select_one(f'#yesBestList > li:nth-child({i}) > div > div.item_info > div.info_row.info_name > a.gd_name'):
      continue
    title = soup.select_one(f'#yesBestList > li:nth-child({i}) > div > div.item_info > div.info_row.info_name > a.gd_name')
    title = re.sub(r'\[예스리커버\]|\(리커버\)','', title.text).strip()
    titles[f"title_{page_num}"].append(title)
    book_url = "https://www.yes24.com"+soup.select_one(f'#yesBestList > li:nth-child({i}) > div > div.item_info > div.info_row.info_name > a.gd_name').get('href')
    book_urls[f"book_url_{page_num}"].update({title: book_url})

# Iterate through the pages to get all the book urls
for i in range(1, int(num_pages)+1):
  get_book_urls(i)

# Initialize the data_list dictionary to store the extracted data
data_list = {}

# Function to get book information from each book url
def get_book_info(data_list, data_index, title, url):
  response = requests.get(url)
  if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    print("Successfully accessed the web page.")
  else:
    print(response.status_code)
    print("Please try again.")

  item_info = ""
  for i in range(1, 5):
    if not soup.select_one(f"#infoset_specific > div.infoSetCont_wrap > div > table > tbody > tr:nth-child({i}) > th"):
      continue
    else:
      item_info += soup.select_one(f"#infoset_specific > div.infoSetCont_wrap > div > table > tbody > tr:nth-child({i}) > th").text
      item_info += " "
      item_info += soup.select_one(f"#infoset_specific > div.infoSetCont_wrap > div > table > tbody > tr:nth-child({i}) > td").text
      if i != 4:
        item_info += " "

  related_category = ""
  for cat in soup.select("#infoset_goodsCate > div.infoSetCont_wrap > dl > dd > ul > li"):
    related_category += cat.text.replace("\n", "")

  book_intro = ""
  foundBookIntro = False
  if not soup.select("#infoset_introduce > div.infoSetCont_wrap > table > tbody > tr > td > div > div"):
    pass
  else:
    foundBookIntro = True
    for intro in soup.select("#infoset_introduce > div.infoSetCont_wrap > table > tbody > tr > td > div > div"):
      book_intro += intro.text.strip()
      book_intro += " "
  if not soup.select("#infoset_introduce > div.infoSetCont_wrap > table > tbody > tr > td > div.infoWrap_mdBox > dl > dd"):
    pass
  else:
    foundBookIntro = True
    for intro in soup.select("#infoset_introduce > div.infoSetCont_wrap > table > tbody > tr > td > div.infoWrap_mdBox > dl > dd"):
      book_intro += intro.text.strip()
      book_intro += " "
  if not soup.select_one("#infoset_introduce > div.infoSetCont_wrap > div.infoWrap_txt > div > textarea"):
    pass
  else:
    foundBookIntro = True
    for intro in soup.select("#infoset_introduce > div.infoSetCont_wrap > div.infoWrap_txt > div > textarea"):
      book_intro += intro.text.strip()
      book_intro += " "
  if not soup.select_one("#infoset_introduce > div.infoSetCont_wrap > div.infoWrap_mdBox > dl > dd"):
    pass
  else:
    foundBookIntro = True
    for intro in soup.select("#infoset_introduce > div.infoSetCont_wrap > div.infoWrap_mdBox > dl > dd"):
      book_intro += intro.text.strip()
      book_intro += " "
  if not soup.select("#infoset_introduce > div.infoSetCont_wrap > div.infoWrap_txt"):
    pass
  else:
    for intro in soup.select("#infoset_introduce > div.infoSetCont_wrap > div.infoWrap_txt"):
      book_intro += intro.text.strip()
      book_intro += " "
  if not foundBookIntro:
    book_intro = "Can't find the book introduction."

  summary = soup.select_one("#infoset_summary > div.infoSetCont_wrap > div.infoWrap_txt")
  if not summary:
    summary = "Can't find the summary."
  else:
    summary = summary.text.strip()

  publisher_review = soup.select("#infoset_pubReivew > div.infoSetCont_wrap > div.infoWrap_txt")
  if not publisher_review:
    publisher_review = "Can't find the publisher review."
  else:
    publisher_review = ""
    for pub in soup.select("#infoset_pubReivew > div.infoSetCont_wrap > div.infoWrap_txt"):
      publisher_review += pub.text.strip()

  data_list[f"data_list_{data_index}"][title] = {
      "title": title,
      "item_info": item_info,
      "related_category": related_category,
      "book_intro": book_intro,
      "summary": summary,
      "publisher_review": publisher_review
  }

for i in range(1, int(num_pages)+1):
  data_list[f"data_list_{i}"]={}
  for title, url in book_urls[f"book_url_{i}"].items():
    get_book_info(data_list, i, title, url)
    print(f"Successfully crawled a book from page {i}.")

import logging
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import csv
from concurrent.futures import ThreadPoolExecutor

# Dynamically retrieve customer reviews from the URL with Selenium's WebDriver
def get_purchase_review(url_data, book_data, data_index):
  try:
    service = Service()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument(f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36')

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(600)
    for title, url in url_data.items():
      driver.get(url)

      purchase_review = []
      cropped_reviews = driver.find_elements(By.CSS_SELECTOR, "#infoset_reviewContentList > div")
      for i, rev in enumerate(cropped_reviews, start=1):
        more_button = rev.find_elements(By.CSS_SELECTOR, "div.reviewInfoBot.crop > a > div > span")
        if more_button:
          try:
            more_button[0].click()
            # Wait until the more button is clicked and the full review is loaded
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.reviewInfoBot.origin > div.review_cont")))
          except Exception as e:
            logging.error(f"Couldn't click the more button. {str(e)}")
        original_reviews = rev.find_elements(By.CSS_SELECTOR, "div.reviewInfoBot.origin > div.review_cont")
        for j, or_rev in enumerate(original_reviews):
          purchase_review.append(f"{i-2}. {or_rev.text.strip()}\n")
      if title in book_data:
        book_data[title].update({"purchase_review": purchase_review if purchase_review else "Can't find the purchase reviews."})
  except Exception as e:
    logging.error(f"Error while crawling: {str(e)}")
  finally:
    if driver is not None:
      try:
        driver.quit()
        logging.info("Terminating the web driver.")
      except Exception as e:
        logging.error(f"Error while terminating the web driver: {str(e)}")

# Function to save the extracted data to a CSV file
def save_to_csv(data_list, genre, file_index):
  file_exists = os.path.isfile(f'{genre}_{file_index}.csv')
  # Get the fieldnames from the first book's data (assuming all books have the same fields)
  # If data_list is empty, provide default fieldnames to prevent error
  fieldnames = list(data_list.values())[0].keys() if data_list else ['title','item_info', 'related_category', 'book_intro', 'summary', 'publisher_review', 'purchase_review']
  with open(f'{genre}_{file_index}.csv', 'a', newline='', encoding='utf-8') as output_file:
    dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    if not file_exists:
      dict_writer.writeheader() # Write header only if the file doesn't exist
    dict_writer.writerows(data_list.values())

# Divide the data_list into chunks for parallel processing
max = int(num_pages)
chunks = []
chunk_size = 3 # Number of threads executing in parallel
for i in range(1, max+1, chunk_size):
  end = min(i+chunk_size-1, max)
  chunks.append([i, end])

import threading
threads = []

for i in range(0, len(chunks)):
  for j in range(chunks[i][0], chunks[i][1]+1):
    thread = threading.Thread(target=get_purchase_review, args=(book_urls[f"book_url_{j}"], data_list[f"data_list_{j}"], j))
    threads.append(thread)
    thread.start()
    time.sleep(60) # Wait for 60 seconds before starting the next thread to prevent getting blocked by the website
    # However, this is not a perfect solution as the website may still block the IP address
    # Therefore, if a "Read timed out" error occurs, that page should be manually crawled again to ensure no data is missing
  for thread in threads:
    thread.join()
  threads.clear()

print("All threads have finished.")

# Save the extracted data to CSV files
for i in range(1, int(num_pages)+1):
  save_to_csv(data_list[f"data_list_{i}"], genre, i)

# Function to merge multiple CSV files into one
def merge_csv_files(input_files, output_file):
    # Check if the output file already exists
    file_exists = os.path.isfile(output_file)

    with open(output_file, 'a', newline='', encoding='utf-8') as outfile:
        writer = None
        for file in input_files:
            with open(file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                if writer is None:
                    # Initialize the writer with fieldnames from the first file
                    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                    if not file_exists:
                        writer.writeheader()  # Write header only once
                for row in reader:
                    writer.writerow(row)

input_files = [f'SF_{i}.csv' for i in range(1, 18)]
merge_csv_files(input_files, 'SF_data.csv')

print("Successfully merged all the csv files into SF_data.csv.")
