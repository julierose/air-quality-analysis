import marimo

__generated_with = "0.24.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd

    return (pd,)


@app.cell
def _(mo, pd):
    #data ingest and transformation
    aqi_path = str(mo.notebook_location()/"public"/"data"/"aqi.json")
    air_df = pd.read_json(aqi_path)

    air_df['current_time_utc'] = pd.to_datetime(air_df['current_time_utc'])
    air_df['current_time_local'] = pd.to_datetime(air_df['current_time_local'])

    pollutant_cols = ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", "us_aqi"]

    for _pollutant in pollutant_cols:
        air_df[_pollutant] = air_df[_pollutant].astype("float64")
    
    air_df.dtypes.astype(str)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
