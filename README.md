# Air Quality Analysis

Automated air quality dashboard: a daily GitHub Action will pull Open-Meteo data for the 5 largest US cities. A [marimo](https://marimo.io/) data analysis and exploration notebook, hosted on GitHub Pages, will run entirely in the browser, illustrating geographic, temporal, and pollutant-based differences across the dataset.

> This repo is a work in progress. Under construction, not yet deployed. See the [project notes](docs/PROJECT_NOTES.md) for details.

## How it works

1. Data will be refreshed daily on a schedule using GitHub Actions.
2. The `fetch_data.py` script will pull data from the Open-Meteo API and write it to a JSON file.
3. The refreshed notebook will be exported and hosted publicly on GitHub Pages.

## Data notes

The 5 largest US cities were identified using 2025 US Census Bureau data, and include New York, Los Angeles, Chicago, Houston, and Phoenix.

Data will be pulled using a single latitude/longitude combination for each city. These are model-based estimates, not readings from ground monitoring stations, and represent the grid cell (tens of kilometers) containing each city’s coordinates. Data transformations will adjust for local time zone differences and create a flag separating past from future model estimates.

Hourly air quality data for yesterday, today, and tomorrow in each city’s local time will be pulled during each run of the `fetch_data.py` script.

Air quality variables include PM10, PM2.5, carbon monoxide, nitrogen dioxide, sulfur dioxide, ozone, and the US Air Quality Index.

## Status

- [x] Data fetch and transformation
- [ ] JSON output
- [ ] Notebook
- [ ] GitHub Actions
- [ ] Deployment to GitHub Pages