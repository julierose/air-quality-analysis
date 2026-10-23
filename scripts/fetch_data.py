import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
import numpy as np
from pathlib import Path

#Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

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

responses = openmeteo.weather_api(url, params = params)

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

all_dataframes = []
for city, response in zip(CITIES, responses):
    df = build_city_dataframe(city["name"], response, HOURLY_VARIABLES)
    all_dataframes.append(df)

combined_df = pd.concat(all_dataframes, ignore_index=True)

#create column dividing times into 'observed', 'forecast_today', and 'forecast_tomorrow'
combined_df['current_time_utc'] = pd.Timestamp.now(tz="utc")
combined_df['utc_offset_timedelta'] = pd.to_timedelta(combined_df['utc_offset_seconds'], unit='s')
combined_df['date'] = combined_df['date'] + combined_df['utc_offset_timedelta']
combined_df['current_time_local'] = (combined_df['current_time_utc'] + combined_df['utc_offset_timedelta']).dt.tz_localize(None)

conditions = [combined_df['date'] < combined_df['current_time_local'], 
              (combined_df['date'].dt.date == combined_df['current_time_local'].dt.date) & (combined_df['date'] >= combined_df['current_time_local']),
              combined_df['date'].dt.date == combined_df['current_time_local'].dt.date + pd.Timedelta(days=1)]

label = ['observed','forecast_today','forecast_tomorrow']
combined_df['time_label'] = np.select(conditions, label, default = 'Unmapped')
combined_df = combined_df.drop(columns=["utc_offset_timedelta"]) #drop helper column

output_path = Path(__file__).resolve().parent.parent /"apps" / "public" / "data" / "aqi.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

combined_df.to_json(output_path, orient="records", indent =2, date_format="iso", date_unit="s", double_precision=2)