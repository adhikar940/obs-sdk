import requests
import pandas as pd
import time

def fetch_data():
    response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
    return response.json()

def process_data():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    return df.groupby("a").sum()

def main():
    print("Fetching data...")
    data = fetch_data()
    print("Data fetched:", data)
    print("Processing data...")
    result = process_data()
    print("Processed data:\n", result)
    time.sleep(1)

if __name__ == "__main__":
    main()