# Air Quality Analysis

Automated air quality dashboard: a daily GitHub Action pulls Open-Meteo data for the 5 largest US cities. A [marimo](https://marimo.io/) data analysis and exploration notebook, hosted on GitHub Pages, runs entirely in the browser, illustrating geographic, temporal, and pollutant-based differences across the dataset. [View live notebook](https://julierose.github.io/air-quality-analysis/). Note: the first load takes ~15 seconds while Python starts in your browser.

## How it works

1. Data are refreshed daily on a schedule using GitHub Actions.
2. The `fetch_data.py` script pulls data from the Open-Meteo API and writes it to a JSON file.
3. The refreshed notebook is exported and hosted publicly on GitHub Pages.

## Data notes

The 5 largest US cities were identified using 2025 US Census Bureau data, and include New York, Los Angeles, Chicago, Houston, and Phoenix.

Data are pulled using a single latitude/longitude combination for each city. The values are model-based estimates, not readings from ground monitoring stations, and represent the grid cell (tens of kilometers) containing each city’s coordinates. Data transformations adjust for local time zone differences, create a flag separating past from future model estimates, and apply two-decimal rounding.

Hourly air quality data for yesterday, today, and tomorrow in each city’s local time are pulled during each run of the `fetch_data.py` script.

Air quality variables include PM10, PM2.5, carbon monoxide, nitrogen dioxide, sulphur dioxide, ozone, and the US Air Quality Index.

## Status

- [x] Data fetch and transformation
- [x] JSON output
- [x] Notebook
- [x] GitHub Actions
- [x] Deployment to GitHub Pages
- [x] Scheduled daily refresh

## Local setup

These steps were tested on Windows with PowerShell and Python 3.14.

1. Clone the repo and move into the folder:

```powershell
git clone https://github.com/julierose/air-quality-analysis.git
cd air-quality-analysis
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

   On macOS or Linux, activate with `source .venv/bin/activate` instead.

   If PowerShell blocks `Activate.ps1` with an error saying running scripts is disabled on this system, see Microsoft's documentation on [execution policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies).

3. Install the dependencies:

```powershell
pip install -r requirements.txt
```

4. Run:
```python
 scripts/fetch_data.py
```

5. Open the notebook in marimo's editor:

```powershell
python -m marimo edit apps/air_quality_analysis.py
```

## Data sources and attribution

Air quality data by [Open-Meteo.com](https://open-meteo.com/), used under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license (see [Open-Meteo's license terms](https://open-meteo.com/en/license)). Changes made to the data: adjusted for local time zones, flagged as past or forecast, and converted to JSON.

Open-Meteo's air quality data is based on forecasts from the Copernicus Atmosphere Monitoring Service (CAMS). For locations outside of Europe it draws on the [CAMS global atmospheric composition forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts) (about 40 km resolution, CC BY license).

**Citations**

- Copernicus Atmosphere Monitoring Service (2021): CAMS global atmospheric composition forecasts. Atmosphere Data Store, DOI: [10.24381/04a0b097](https://doi.org/10.24381/04a0b097). Accessed via Open-Meteo.
- Citation requested by Open-Meteo (CAMS European ensemble): METEO FRANCE, Institut national de l'environnement industriel et des risques (Ineris), Aarhus University, Norwegian Meteorological Institute (MET Norway), Jülich Institut für Energie- und Klimaforschung (IEK), Institute of Environmental Protection – National Research Institute (IEP-NRI), Koninklijk Nederlands Meteorologisch Instituut (KNMI), Nederlandse Organisatie voor toegepast-natuurwetenschappelijk onderzoek (TNO), Swedish Meteorological and Hydrological Institute (SMHI), Finnish Meteorological Institute (FMI), Italian National Agency for New Technologies, Energy and Sustainable Economic Development (ENEA) and Barcelona Supercomputing Center (BSC) (2022): CAMS European air quality forecasts, ENSEMBLE data. Copernicus Atmosphere Monitoring Service (CAMS) Atmosphere Data Store (ADS). (Updated twice daily).

**Copernicus attribution**

Contains modified Copernicus Atmosphere Monitoring Service information 2026. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.

City selection based on [Census Bureau Vintage 2025 population estimates](https://www.census.gov/newsroom/press-kits/2026/vintage-2025-city-town-pop-estimates.html).

## License

The code in this repository is released under the [MIT License](LICENSE). The data it uses is not covered by that license; see [Data sources and attribution](#data-sources-and-attribution) for the terms that apply to it.