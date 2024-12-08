import pandas as pd
import numpy as np
import re
from openai import OpenAI
import os

# Initialize OpenAI API Client
client = OpenAI(
    api_key = "OpenAI_API_Key",
    base_url = "https://api.upstage.ai/v1/solar",
)

# Load data
file_path = "SF_extended_keywords_filtered.csv"
data = pd.read_csv(file_path)

# Function to preprocess keywords: remove punctuation and duplicate words
def preprocess_text(text):
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    tokens = text.split()  # Tokenize by whitespace
    unique_tokens = list(dict.fromkeys(tokens))  # Remove duplicates
    return ' '.join(unique_tokens)  # Return as a single string

# Preprocess extended_keywords column
data["processed_keywords"] = data["extended_keywords"].dropna().apply(preprocess_text)

# Generate embeddings using Solar API
def get_solar_embedding(text):
    try:
      response = client.embeddings.create(
          input = text,
          model = "embedding-passage",
      )
      return response.data[0].embedding
    except Exception as e:
        print(f"Error processing text: {text}, Error: {e}")
        return np.zeros(768)  # Default embedding size

# Apply embedding generation to each book
data["embedding"] = data["processed_keywords"].apply(lambda text: get_solar_embedding(text))

# Convert embedding data to string (for CSV saving)
data["embedding"] = data["embedding"].apply(lambda x: ','.join(map(str, x)))

# Save results to a new CSV file
output_file_path = "books_with_solar_embeddings.csv"
data.to_csv(output_file_path, index=False)

print(f"New file saved: {output_file_path}")