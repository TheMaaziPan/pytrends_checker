import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError
import time

# Initialize pytrends
pytrends = TrendReq(hl='en-US', tz=360)

# Streamlit app title
st.title("Google Trends Keyword Analyzer")

# Input: List of keywords
st.sidebar.header("Input Keywords")
keywords_input = st.sidebar.text_area("Enter keywords (one per line)", "")
keywords = [kw.strip() for kw in keywords_input.splitlines() if kw.strip()]

# Input: Region selection
st.sidebar.header("Select Region")
region_mapping = {
    "Worldwide": "",
    "United States": "US",
    "United Kingdom": "GB",
    "Germany": "DE",
    "France": "FR",
    "Japan": "JP",
    "India": "IN",
    "Brazil": "BR",
    "Canada": "CA",
    "Australia": "AU"
}
selected_region = st.sidebar.selectbox("Choose a region", list(region_mapping.keys()))
region_code = region_mapping[selected_region]

# Timeframe for analysis (5 years)
timeframe = 'today 5-y'

# Function to fetch Google Trends data with retry logic
def fetch_trends_data(keywords, region_code, retries=3, delay=2):
    for attempt in range(retries):
        try:
            pytrends.build_payload(keywords, timeframe=timeframe, geo=region_code)
            data = pytrends.interest_over_time()
            if not data.empty:
                return data
            raise ResponseError("Empty data returned from Google Trends")
        except ResponseError as e:
            if attempt < retries - 1:  # Don't wait on the last attempt
                time.sleep(delay)  # Wait before retrying
                continue
            raise  # Re-raise the exception if all retries fail

# Function to plot trends
def plot_trends(data, keywords, selected_region):
    plt.figure(figsize=(10, 6))
    for keyword in keywords:
        if keyword in data.columns:
            plt.plot(data.index, data[keyword], label=keyword)
    plt.title(f"Google Trends Search Demand (5-Year View) - {selected_region}")
    plt.xlabel("Date")
    plt.ylabel("Search Interest (Relative)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()  # Prevent label cutoff
    st.pyplot(plt)
    plt.close()  # Close the figure to prevent memory leaks

# Main app logic
if st.sidebar.button("Analyze Keywords"):
    if not keywords:
        st.warning("Please enter at least one keyword.")
    else:
        st.write("### Analyzing Keywords...")
        with st.spinner("Fetching data from Google Trends..."):
            try:
                # Fetch Google Trends data with retry logic
                trends_data = fetch_trends_data(keywords, region_code)
                
                # Display weekly search volumes
                st.write("### Weekly Search Volumes (Relative Interest)")
                st.dataframe(trends_data[keywords].style.highlight_max(axis=0))
                
                # Plot the trends
                st.write("### Search Demand Over Time")
                plot_trends(trends_data, keywords, selected_region)
                
                # Show some statistics
                st.write("### Key Statistics")
                st.write(trends_data[keywords].describe())
                
            except ResponseError as e:
                st.error(f"Google Trends API error: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

# Add some instructions
st.sidebar.markdown("""
**Instructions:**
1. Enter your keywords in the text area (one keyword per line)
2. Select a region from the dropdown menu
3. Click the 'Analyze Keywords' button to fetch and visualize the data

**Note:** 
- Data shows relative search interest (0-100 scale)
- Results are normalized against total search volume
- Limited to 5 keywords at a time (Google Trends limitation)
""")

# Add a footer
st.markdown("---")
st.markdown("*Data provided by Google Trends*")
