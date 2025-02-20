import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import time
import concurrent.futures
from datetime import datetime
import re

# Streamlit app title
st.title("MV Google Trends Keyword Analyser")

# Input: SerpApi API Key
api_key = st.sidebar.text_input("Enter your SerpApi API Key", type="password")

# Input: List of keywords
st.sidebar.header("Input Keywords")
keywords = st.sidebar.text_area("Enter keywords (one per line)").splitlines()

# Input: Region selection
st.sidebar.header("Select Region")
region_mapping = {
    "Worldwide": "",
    "United States": "US",
    "United Kingdom": "GB",
    "Germany": "DE",
    "France": "FR",
}
selected_region = st.sidebar.selectbox("Choose a region", list(region_mapping.keys()))
region_code = region_mapping[selected_region]

# Timeframe for analysis (5 years)
timeframe = "today 5-y"

# Function to clean and parse SerpApi date format
def parse_serpapi_date(date_str):
    cleaned_date_str = re.sub(r"[\u2009\u202F]", " ", date_str)
    try:
        start_date = cleaned_date_str.split("-")[0].strip()
        year = cleaned_date_str.split(",")[-1].strip()
        full_date_str = f"{start_date}, {year}"
        return datetime.strptime(full_date_str, "%b %d, %Y")
    except Exception:
        return None

# Function to fetch Google Trends data using SerpApi with retry logic
@st.cache_data  # Cache results to prevent duplicate API calls
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
                return response.json()
            elif response.status_code == 503:
                time.sleep(delay)
            else:
                return None
        except requests.exceptions.RequestException:
            return None
    return None

# Function to process all keywords with multithreading for faster API calls
def process_all_keywords(api_key, keywords, region_code, timeframe):
    all_data = {}
    
    def fetch_and_process(keyword):
        data = fetch_trends_data(api_key, keyword, region_code, timeframe)
        if data and "interest_over_time" in data:
            timeline_data = data["interest_over_time"]["timeline_data"]
            dates = [parse_serpapi_date(entry["date"]) for entry in timeline_data]
            values = [entry["values"][0]["extracted_value"] for entry in timeline_data if "extracted_value" in entry["values"][0]]
            return keyword, pd.Series(values, index=pd.to_datetime(dates))
        return keyword, None
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_and_process, keywords)
    
    for keyword, series in results:
        if series is not None:
            all_data[keyword] = series

    return pd.DataFrame(all_data)

# Function to plot trends with Streamlit's built-in chart
def plot_trends(data):
    st.line_chart(data)

# Main app logic
if st.sidebar.button("Analyse Keywords"):
    if not api_key:
        st.warning("Please enter your SerpApi API Key.")
    elif not keywords:
        st.warning("Please enter at least one keyword.")
    else:
        with st.spinner("Fetching data... This may take a moment."):
            trends_data = process_all_keywords(api_key, keywords, region_code, timeframe)

        if not trends_data.empty:
            st.write("### Weekly Search Volumes")
            st.dataframe(trends_data)

            st.write("### Search Demand Over Time")
            plot_trends(trends_data)
        else:
            st.error("No data found. Please check your API key and keywords.")

# Instructions
st.sidebar.markdown("""
**Instructions:**
1. Enter your SerpApi API Key.
2. Enter your keywords in the text area (one per line, MAX 100 keywords).
3. Select a region from the dropdown menu.
4. Click 'Analyse Keywords' to fetch and visualize data.
""")
