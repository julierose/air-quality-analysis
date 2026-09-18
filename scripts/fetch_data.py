import openmeteo_requests
import requests_cache
from retry_requests import retry

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

params = {
    "latitude": [city["latitude"] for city in CITIES],
    "longitude": [city["longitude"] for city in CITIES],
    "hourly": ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", "us_aqi"],
    "past_days": 1,
    "forecast_days": 2
}

responses = openmeteo.weather_api(url, params = params)

for i, response in enumerate(responses):
    print(CITIES[i]["name"], response.Latitude(), response.Longitude())

