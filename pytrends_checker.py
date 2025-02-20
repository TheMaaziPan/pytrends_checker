import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import time
from datetime import datetime
import re

# Streamlit app title
st.title("MV Google Trends Keyword Analyser")

# Input: SerpApi API Key
api_key = st.sidebar.text_input("Enter your SerpApi API Key", type="password")

# Input: List of keywords
st.sidebar.header("Input Keywords")
keywords = st.sidebar.text_area("Enter keywords (one per line)", "").splitlines()

# Input: Region selection
st.sidebar.header("Select Region")
region_mapping = {
    "Worldwide": "",
    "United States": "US",
    "United Kingdom": "GB",
    "Germany": "DE",
    "France": "FR",
    # Add more regions as needed
}
selected_region = st.sidebar.selectbox("Choose a region", list(region_mapping.keys()))
region_code = region_mapping[selected_region]

# Timeframe for analysis (5 years)
timeframe = "today 5-y"

# Function to clean and parse SerpApi date format
def parse_serpapi_date(date_str):
    # Remove non-standard characters (e.g., thin spaces \u2009)
    cleaned_date_str = re.sub(r"[\u2009\u202F]", " ", date_str)
    
    # Extract the start date from the range (e.g., "Feb 16 - 22, 2020" -> "Feb 16, 2020")
    start_date = cleaned_date_str.split("-")[0].strip()
    year = cleaned_date_str.split(",")[-1].strip()
    full_date_str = f"{start_date}, {year}"
    
    # Parse the cleaned date string
    return datetime.strptime(full_date_str, "%b %d, %Y")

# Function to fetch Google Trends data using SerpApi with retry logic
def fetch_trends_data(api_key, keyword, region_code, timeframe, retries=3, delay=2):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": keyword,
        "geo": region_code,
        "date": timeframe,
        "api_key": api_key,
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 503:
                st.warning(f"Server overloaded (503). Retrying {attempt + 1}/{retries}...")
                time.sleep(delay)  # Wait before retrying
            else:
                st.error(f"Failed to fetch data for {keyword}. Status code: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error fetching data for {keyword}: {e}")
            return None
    st.error(f"Max retries reached for {keyword}. Skipping.")
    return None

# Function to process all keywords
def process_all_keywords(api_key, keywords, region_code, timeframe):
    all_data = {}
    for keyword in keywords:
        st.write(f"Fetching data for: {keyword}")
        data = fetch_trends_data(api_key, keyword, region_code, timeframe)
        if data and "interest_over_time" in data:
            timeline_data = data["interest_over_time"]["timeline_data"]
            dates = [parse_serpapi_date(entry["date"]) for entry in timeline_data]
            values = [entry["values"][0]["extracted_value"] for entry in timeline_data]
            all_data[keyword] = pd.Series(values, index=pd.to_datetime(dates))
        time.sleep(1)  # Add a delay to avoid rate limits
    return pd.DataFrame(all_data)

# Function to plot trends
def plot_trends(data):
    plt.figure(figsize=(12, 6))
    for keyword in data.columns:
        plt.plot(data.index, data[keyword], label=keyword)
    plt.title(f"Google Trends Search Demand (5-Year View) - {selected_region}")
    plt.xlabel("Date")
    plt.ylabel("Search Interest")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True)
    st.pyplot(plt)

# Main app logic
if st.sidebar.button("Analyse Keywords"):
    if not api_key:
        st.warning("Please enter your SerpApi API Key.")
    elif not keywords:
        st.warning("Please enter at least one keyword.")
    else:
        st.write("### Analysing Keywords...")
        try:
            # Fetch and process data for all keywords
            trends_data = process_all_keywords(api_key, keywords, region_code, timeframe)
            
            # Display weekly search volumes
            st.write("### Weekly Search Volumes")
            st.dataframe(trends_data)
            
            # Plot the trends
            st.write("### Search Demand Over Time")
            plot_trends(trends_data)
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Add some instructions
st.sidebar.markdown("""
**Instructions:**
1. Enter your SerpApi API Key.
2. Enter your keywords in the text area (one keyword per line).
3. Select a region from the dropdown menu.
4. Click the 'Analyse Keywords' button to fetch and visualise the data.
""")
