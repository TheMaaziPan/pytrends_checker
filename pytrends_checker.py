import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
import time
import requests
import json

# Initialize pytrends
pytrends = TrendReq(hl='en-US', tz=360)

# Streamlit app title
st.title("Google Trends Keyword Analyzer")

# API Selection and Configuration
st.sidebar.header("API Selection")
api_option = st.sidebar.radio(
    "Select API Source:",
    ["Google Trends (PyTrends)", "SERP API", "Outscraper"]
)

# API Key Management
if api_option == "SERP API":
    serp_api_key = st.sidebar.text_input("Enter SERP API Key", type="password")
    if not serp_api_key:
        st.sidebar.warning("Please enter your SERP API key to use this service.")
elif api_option == "Outscraper":
    outscraper_api_key = st.sidebar.text_input("Enter Outscraper API Key", type="password")
    if not outscraper_api_key:
        st.sidebar.warning("Please enter your Outscraper API key to use this service.")

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
timeframe = 'today 5-y'

# Function to fetch Google Trends data with retry logic (PyTrends)
def fetch_pytrends_data(keywords, region_code, retries=3, delay=2):
    for attempt in range(retries):
        try:
            pytrends.build_payload(keywords, timeframe=timeframe, geo=region_code)
            data = pytrends.interest_over_time()
            return data
        except ResponseError as e:
            if attempt < retries - 1:  # Don't wait on the last attempt
                time.sleep(delay)  # Wait before retrying
                continue
            else:
                raise e  # Re-raise the exception if all retries fail

# Function to fetch data from SERP API
def fetch_serp_api_data(keywords, region_code, api_key, retries=3, delay=2):
    # Convert region code to SERP API format if needed
    serp_region = region_code.lower() if region_code else "us"  # Default to US if worldwide
    
    results = {}
    for keyword in keywords:
        for attempt in range(retries):
            try:
                url = "https://serpapi.com/search.json"
                params = {
                    "engine": "google_trends",
                    "q": keyword,
                    "geo": serp_region,
                    "data_type": "TIMESERIES",
                    "api_key": api_key
                }
                response = requests.get(url, params=params)
                response.raise_for_status()  # Raise an exception for 4XX/5XX responses
                data = response.json()
                
                # Extract and store time series data
                if "interest_over_time" in data:
                    time_data = data["interest_over_time"]["timeline_data"]
                    for point in time_data:
                        date = point["date"]
                        value = point["values"][0]["value"]
                        if date not in results:
                            results[date] = {}
                        results[date][keyword] = value
                
                break  # Break the retry loop if successful
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise e
    
    # Convert the results to a pandas DataFrame
    df = pd.DataFrame.from_dict(results, orient='index')
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df

# Function to fetch data from Outscraper API
def fetch_outscraper_data(keywords, region_code, api_key, retries=3, delay=2):
    # Convert region code to Outscraper format if needed
    outscraper_region = region_code.lower() if region_code else "worldwide"
    
    for attempt in range(retries):
        try:
            url = "https://api.outscraper.com/api/v1/google-trends"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "keywords": keywords,
                "region": outscraper_region,
                "period": "5y"  # 5 years
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Process the Outscraper response into a pandas DataFrame
            # Note: This will need to be adjusted based on the actual response format from Outscraper
            results = {}
            for item in data.get("data", []):
                time_data = item.get("interest_over_time", [])
                keyword = item.get("keyword", "unknown")
                
                for point in time_data:
                    date = point.get("date")
                    value = point.get("value", 0)
                    
                    if date not in results:
                        results[date] = {}
                    results[date][keyword] = value
            
            df = pd.DataFrame.from_dict(results, orient='index')
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            return df
            
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                raise e

# Function to plot trends
def plot_trends(data):
    plt.figure(figsize=(10, 6))
    for keyword in keywords:
        if keyword in data.columns:
            plt.plot(data.index, data[keyword], label=keyword)
    plt.title(f"Google Trends Search Demand (5-Year View) - {selected_region}")
    plt.xlabel("Date")
    plt.ylabel("Search Interest")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

# Main app logic
if st.sidebar.button("Analyze Keywords"):
    if not keywords:
        st.warning("Please enter at least one keyword.")
    elif api_option == "SERP API" and not serp_api_key:
        st.error("Please enter your SERP API key to proceed.")
    elif api_option == "Outscraper" and not outscraper_api_key:
        st.error("Please enter your Outscraper API key to proceed.")
    else:
        st.write(f"### Analyzing Keywords using {api_option}...")
        try:
            # Fetch data based on selected API
            if api_option == "Google Trends (PyTrends)":
                trends_data = fetch_pytrends_data(keywords, region_code)
            elif api_option == "SERP API":
                trends_data = fetch_serp_api_data(keywords, region_code, serp_api_key)
            elif api_option == "Outscraper":
                trends_data = fetch_outscraper_data(keywords, region_code, outscraper_api_key)
            
            # Display weekly search volumes
            st.write("### Weekly Search Volumes")
            st.dataframe(trends_data[keywords])
            
            # Plot the trends
            st.write("### Search Demand Over Time")
            plot_trends(trends_data)
            
            # Add API source information
            st.info(f"Data source: {api_option}")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Please check your API key and try again, or try another API source.")

# Add some instructions
st.sidebar.markdown("""
**Instructions:**
1. Select an API source for Google Trends data.
2. If using SERP API or Outscraper, enter your API key.
3. Enter your keywords in the text area (one keyword per line).
4. Select a region from the dropdown menu.
5. Click the 'Analyze Keywords' button to fetch and visualize the data.
""")
