
import streamlit as st
import pandas as pd
import requests
import time
import concurrent.futures
from datetime import datetime
import re
import matplotlib.pyplot as plt

# Custom CSS for styling
st.markdown(
    """
    <style>
    /* Main title styling */
    h1 {
        color: #1A73E8;
        text-align: center;
        font-family: 'Roboto', sans-serif;
        font-size: 2.5rem;
        margin-bottom: 20px;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    /* Button styling */
    .stButton>button {
        background-color: #1A73E8;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 1rem;
        border: none;
        font-family: 'Roboto', sans-serif;
    }

    .stButton>button:hover {
        background-color: #1557B0;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    /* Graph styling */
    .stPlotlyChart, .stPyplot {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    /* Footer styling */
    .footer {
        text-align: center;
        padding: 20px;
        font-size: 0.9rem;
        color: #666;
        background-color: #F8F9FA;
        margin-top: 20px;
        border-radius: 10px;
    }

    /* General body styling */
    body {
        background-color: #F8F9FA;
        font-family: 'Roboto', sans-serif;
        color: #333333;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Streamlit app title
st.title("MV Google Trends Analyser")

# Input: SerpApi API Key
api_key = st.sidebar.text_input("Enter your MV API Key", type="password")

# Input: List of keywords
st.sidebar.header("Input Keywords")
keywords = st.sidebar.text_area("Enter keywords (one per line, MAX 100 keywords)").splitlines()

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
    """
    Clean and parse the date string returned by SerpApi.
    """
    cleaned_date_str = re.sub(r"[\u2009\u202F]", " ", date_str)  # Remove non-standard spaces
    try:
        start_date = cleaned_date_str.split("-")[0].strip()  # Extract start date
        year = cleaned_date_str.split(",")[-1].strip()  # Extract year
        full_date_str = f"{start_date}, {year}"  # Combine into a standard format
        return datetime.strptime(full_date_str, "%b %d, %Y")  # Parse the date
    except Exception as e:
        st.warning(f"Failed to parse date: {date_str}. Error: {e}")
        return None

# Function to fetch Google Trends data using SerpApi with retry logic
@st.cache_data  # Cache results to prevent duplicate API calls
def fetch_trends_data(api_key, keyword, region_code, timeframe, retries=3, delay=2):
    """
    Fetch Google Trends data for a single keyword using SerpApi.
    """
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
                time.sleep(delay)  # Wait before retrying
            else:
                st.error(f"Failed to fetch data for {keyword}. Status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data for {keyword}: {e}")
            return None
    st.error(f"Max retries reached for {keyword}. Skipping.")
    return None

# Function to process all keywords with multithreading for faster API calls
def process_all_keywords(api_key, keywords, region_code, timeframe):
    """
    Process all keywords using multithreading for faster API calls.
    """
    all_data = {}
    
    def fetch_and_process(keyword):
        """
        Fetch and process data for a single keyword.
        """
        data = fetch_trends_data(api_key, keyword, region_code, timeframe)
        if data and "interest_over_time" in data:
            timeline_data = data["interest_over_time"]["timeline_data"]
            dates = [datetime.fromtimestamp(eval(entry.get('timestamp'))).date() for entry in timeline_data]
            values = [entry["values"][0].get("extracted_value", 0) for entry in timeline_data]
            return keyword, pd.Series(values, index=pd.to_datetime(dates))
        return keyword, None
    
    # Use ThreadPoolExecutor for concurrent API calls
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_and_process, keywords))
    
    # Combine results into a DataFrame
    for keyword, series in results:
        if series is not None:
            all_data[keyword] = series

    return pd.DataFrame(all_data)

# Function to plot trends with Matplotlib for better control
def plot_trends(data):
    """
    Plot trends using Matplotlib for better control over the graph.
    """
    plt.figure(figsize=(12, 6))
    for column in data.columns:
        plt.plot(data.index, data[column], label=column)
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
        with st.spinner("Fetching data... This may take a moment."):
            trends_data = process_all_keywords(api_key, keywords, region_code, timeframe)

        if not trends_data.empty:
            # Replace NaN values with 0 for better display
            trends_data = trends_data.fillna(0)

            # Display weekly search volumes with dates
            st.write("### Weekly Search Volumes")
            st.dataframe(trends_data)

            # Plot the trends
            st.write("### Search Demand Over Time")
            plot_trends(trends_data)
        else:
            st.error("No data found. Please check your API key and keywords.")
# Footer
st.markdown(
    '<div class="footer">Made with ❤️ by MV</div>',
    unsafe_allow_html=True,
)

# Instructions
st.sidebar.markdown("""
**Instructions:**
1. Enter your MV API Key.
2. Enter your keywords in the text area (one per line, MAX 100 keywords).
3. Select a region from the dropdown menu.
4. Click 'Analyse Keywords' to fetch and visualise data.
""")
