import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq

# Initialize pytrends
pytrends = TrendReq(hl='en-US', tz=360)

# Streamlit app title
st.title("Google Trends Keyword Analyzer")

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

# Function to fetch Google Trends data
def fetch_trends_data(keywords, region_code):
    pytrends.build_payload(keywords, timeframe=timeframe, geo=region_code)
    data = pytrends.interest_over_time()
    return data

# Function to plot trends
def plot_trends(data):
    plt.figure(figsize=(10, 6))
    for keyword in keywords:
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
    else:
        st.write("### Analyzing Keywords...")
        try:
            # Fetch Google Trends data
            trends_data = fetch_trends_data(keywords, region_code)
            
            # Display weekly search volumes
            st.write("### Weekly Search Volumes")
            st.dataframe(trends_data[keywords])
            
            # Plot the trends
            st.write("### Search Demand Over Time")
            plot_trends(trends_data)
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Add some instructions
st.sidebar.markdown("""
**Instructions:**
1. Enter your keywords in the text area (one keyword per line).
2. Select a region from the dropdown menu.
3. Click the 'Analyze Keywords' button to fetch and visualize the data.
""")