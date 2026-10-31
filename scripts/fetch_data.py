import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
import numpy as np
from pathlib import Path

url = "https://air-quality-api.open-meteo.com/v1/air-quality"

#top 5 US cities by population in 2025, per US Census Bureau
#decimal degrees for Open Meteo API
CITIES = [
    {"name": "New York", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Los Angeles", "latitude": 34.0522,"longitude": -118.2437},
    {"name": "Chicago", "latitude": 41.8781,"longitude": -87.6298},
    {"name": "Houston", "latitude": 29.7604,"longitude": -95.3698},
    {"name": "Phoenix", "latitude": 33.4484,"longitude": -112.0740}
]

HOURLY_VARIABLES = ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", "us_aqi"]

params = {
    "latitude": [city["latitude"] for city in CITIES],
    "longitude": [city["longitude"] for city in CITIES],
    "hourly": HOURLY_VARIABLES,
    "past_days": 1,
    "forecast_days": 2,
    "timezone": "auto"
}

def build_city_dataframe(city, response, variable_names):
    hourly = response.Hourly()
    offset = response.UtcOffsetSeconds()
    date_city = {
        "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s"),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"),
        "city": city,
        "utc_offset_seconds": offset
    }

    pollutant_data = {}
    for i, name in enumerate(variable_names):
        pollutant_data[name] = hourly.Variables(i).ValuesAsNumpy()

    hourly_data = date_city | pollutant_data
  
    return pd.DataFrame(data=hourly_data)

def main():
    #---------------------------------------------------------------------------------------
    #fetch data
    #---------------------------------------------------------------------------------------
    #Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    responses = openmeteo.weather_api(url, params = params)

    #-------------------------------------------------------------------------------
    #build dataframes
    #-------------------------------------------------------------------------------


    all_dataframes = []
    for city, response in zip(CITIES, responses, strict=True):
        df = build_city_dataframe(city["name"], response, HOURLY_VARIABLES)
        all_dataframes.append(df)

    combined_df = pd.concat(all_dataframes, ignore_index=True)

    #----------------------------------------------------------------------
    #data transformation and labeling
    #----------------------------------------------------------------------

    #create column dividing times into 'past', 'forecast_today', and 'forecast_tomorrow'
    combined_df['current_time_utc'] = pd.Timestamp.now(tz="utc")
    combined_df['utc_offset_timedelta'] = pd.to_timedelta(combined_df['utc_offset_seconds'], unit='s')
    combined_df['date'] = combined_df['date'] + combined_df['utc_offset_timedelta']
    combined_df['current_time_local'] = (combined_df['current_time_utc'] + combined_df['utc_offset_timedelta']).dt.tz_localize(None)

    conditions = [combined_df['date'] < combined_df['current_time_local'], 
                (combined_df['date'].dt.date == combined_df['current_time_local'].dt.date) & (combined_df['date'] >= combined_df['current_time_local']),
                combined_df['date'].dt.date == combined_df['current_time_local'].dt.date + pd.Timedelta(days=1)]

    label = ['past','forecast_today','forecast_tomorrow']
    combined_df['time_label'] = np.select(conditions, label, default = 'Unmapped')
    combined_df = combined_df.drop(columns=["utc_offset_timedelta"]) #drop helper column

    #---------------------------------------------------------------------
    #QA checks
    #---------------------------------------------------------------------
    unmapped_count = (combined_df['time_label'] == 'Unmapped').sum()
    if unmapped_count >0:
        raise ValueError(f"{unmapped_count} rows could not be labeled (i.e., time_label is 'Unmapped'). Check time logic.")

    expected_rows = 24 * (params["past_days"] + params["forecast_days"]) * len(CITIES)
    actual_rows = len(combined_df)
    if expected_rows != actual_rows:
        raise ValueError(f"Expected {expected_rows} rows, but got {actual_rows}.")

    #----------------------------------------------------------------------
    #write file
    #----------------------------------------------------------------------

    output_path = Path(__file__).resolve().parent.parent /"apps" / "public" / "data" / "aqi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    combined_df.to_json(output_path, orient="records", indent =2, date_format="iso", date_unit="s", double_precision=2)

if __name__ == "__main__": 
    main()