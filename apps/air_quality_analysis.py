import marimo

__generated_with = "0.24.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import pandas as pd
    import altair as alt

    return alt, pd


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
    return (air_df,)


@app.cell
def _(air_df):
    city_df = air_df[air_df['city'] == 'New York']
    city_df
    return (city_df,)


@app.cell
def _(alt, city_df):
    alt.Chart(city_df).mark_line().encode(
        x = alt.X('date:T',
                  axis = alt.Axis(
                  title='',
                titleFontSize = 12,
                  format="%b %d %I:%M %p",
                  labelAngle=20)
                 ),
        y = alt.Y('pm2_5',
                  axis = alt.Axis(
                      title = 'Particulate Matter < 2.5 um',
                  titleFontSize=12)
                 ),
        tooltip = [
            alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date'),
            alt.Tooltip('pm2_5:Q', title = 'PM < 2.5 um'),
            alt.Tooltip('time_label', title = 'Time Category')
        ]
        ).properties(
        title = alt.TitleParams(
            text = 'Test Chart',
            subtitle = 'New York City Particulate Matter < 2.5 micrometers',
            anchor = 'middle',
            fontSize = 14,
            subtitleFontSize=12,
            subtitleFontStyle='italic')
        )
    return


if __name__ == "__main__":
    app.run()
