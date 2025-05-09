# Function to fetch data from Outscraper API with async support
def fetch_outscraper_data(keywords, region_code, api_key, retries=3, delay=2, max_polls=10, poll_interval=5):
    # Convert region code to Outscraper format if needed
    outscraper_region = region_code.lower() if region_code else "worldwide"
    
    # Create a dictionary to store results for all keywords
    all_data = {}
    
    for keyword in keywords:
        st.write(f"Fetching data for keyword: {keyword}")
        
        try:
            # Step 1: Initiate the request in async mode
            url = "https://api.outscraper.cloud/google-trends"
            params = {
                "query": keyword,
                "region": outscraper_region,
                "period": "5y",  # 5 years
                "async": "true"  # Asynchronous request
            }
            
            headers = {
                "X-API-KEY": api_key
            }
            
            # Make the initial request
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            initial_data = response.json()
            
            # Check if we have a request_id for polling
            if not isinstance(initial_data, dict) or 'id' not in initial_data:
                st.warning(f"No request ID returned for keyword '{keyword}'. Response: {initial_data}")
                continue
                
            request_id = initial_data['id']
            st.write(f"Request initiated, polling for results (ID: {request_id})...")
            
            # Step 2: Poll for results
            result_url = f"https://api.outscraper.cloud/requests/{request_id}"
            
            # Poll until we get a result or reach max attempts
            for poll_attempt in range(max_polls):
                time.sleep(poll_interval)  # Wait between polls
                
                st.write(f"Polling for results... (Attempt {poll_attempt + 1}/{max_polls})")
                poll_response = requests.get(result_url, headers=headers, timeout=30)
                
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    
                    # Check if job is completed
                    if poll_data.get('status') == 'Finished':
                        # Extract and process the results
                        results = poll_data.get('data', [])
                        
                        if results and isinstance(results, list) and len(results) > 0:
                            trend_data = results[0].get('interest_over_time', [])
                            
                            # Process each data point
                            for point in trend_data:
                                date = point.get('date')
                                value = point.get('value', 0)
                                
                                # Initialize the date in the results dictionary if not present
                                if date not in all_data:
                                    all_data[date] = {}
                                    
                                # Add the value for this keyword on this date
                                all_data[date][keyword] = value
                            
                            st.success(f"Successfully retrieved data for '{keyword}'")
                            break
                        else:
                            st.warning(f"No trend data found for keyword '{keyword}'")
                            break
                    
                    elif poll_data.get('status') == 'Failed':
                        st.error(f"The request for '{keyword}' failed: {poll_data.get('error', 'Unknown error')}")
                        break
                        
                    # If not complete, continue polling
                    if poll_attempt == max_polls - 1:
                        st.warning(f"Max polling attempts reached for '{keyword}'. The request may still be processing.")
                
                else:
                    st.error(f"Failed to poll for results: {poll_response.status_code}")
                    break
                    
        except Exception as e:
            st.error(f"Error processing keyword '{keyword}': {str(e)}")
            # Continue with next keyword rather than failing completely
            continue
    
    # Convert the dictionary to a DataFrame if we have data
    if not all_data:
        raise Exception("No data was returned from the Outscraper API for any keywords")
    
    df = pd.DataFrame.from_dict(all_data, orient='index')
    
    # Fill NaN values with 0 for keywords that don't have data for all dates
    df = df.fillna(0)
    
    # Convert index to datetime and sort
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    
    return df
