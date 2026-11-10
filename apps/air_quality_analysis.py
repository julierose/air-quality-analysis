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
    import numpy as np
    import altair as alt

    return alt, np, pd


@app.cell
def _(mo, np, pd):
    #data ingest and transformation
    aqi_path = str(mo.notebook_location()/"public"/"data"/"aqi.json")
    air_df = pd.read_json(aqi_path, precise_float=True)

    air_df['current_time_utc'] = pd.to_datetime(air_df['current_time_utc'])
    air_df['current_time_local'] = pd.to_datetime(air_df['current_time_local'])

    #create past/forecast data label
    _period_conditions = [air_df['time_label'] == 'past',
                 air_df['time_label'].isin(['forecast_today','forecast_tomorrow'])
                 ]
    _period_labels = ['past','forecast']
    air_df['time_period'] = np.select(_period_conditions, _period_labels, default = 'Unmapped')

    #create day labels to use later in AQI averages for a KPI card
    air_df['local_day'] = air_df['date'].dt.normalize()

    pollutant_cols = ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone", "us_aqi"]

    for _pollutant in pollutant_cols:
        air_df[_pollutant] = air_df[_pollutant].astype("float64")
    return (air_df,)


@app.cell
def _(air_df, mo):
    #create dropdowns for cities and pollutants
    cities = air_df['city'].unique().tolist()

    city_dropdown = mo.ui.dropdown(
        options = cities,
        value = cities[0],   #first element rather than hardcoded value in case city list changes
        label = 'Select City: '
    )

    city_multiselect = mo.ui.multiselect(
        options = cities,
        value = cities, #default to having all cities selected
        label = "Select One or More Cities: "
    )

    pollutant_dict = {
        "PM10 (μg/m³)":"pm10",
        "PM2.5 (μg/m³)":"pm2_5",
        "Carbon Monoxide (μg/m³)":"carbon_monoxide",
        "Nitrogen Dioxide (μg/m³)":"nitrogen_dioxide",
        "Sulphur Dioxide (μg/m³)":"sulphur_dioxide",
        "Ozone (μg/m³)":"ozone",
        "US AQI (0-500 index)":"us_aqi"
    }

    pollutant_dropdown = mo.ui.dropdown(
        options = pollutant_dict,
        value = list(pollutant_dict)[0], #grab first key in dict
        label = 'Select Pollutant: '
    )
    return city_dropdown, city_multiselect, pollutant_dropdown


@app.cell
def _(air_df, city_dropdown, city_multiselect):
    city_df = air_df[air_df['city'] == city_dropdown.value]

    if city_multiselect.value:
        multicity_df = air_df[air_df['city'].isin(city_multiselect.value)]
    else: #if no cities are selected, create an empty dataframe so the plot doesn't crash
        multicity_df = air_df.iloc[0:0]

    #city_df
    return city_df, multicity_df


@app.cell
def _(city_df, pd):
    #create USAQI KPI

    #local dates come from the "now" at the time of the data pull, not the viewer's clock
    _today = city_df['current_time_local'].iloc[0].normalize()
    _yesterday = _today - pd.Timedelta(days=1)

    _today_raw = city_df.loc[city_df['local_day'] == _today, 'us_aqi'].mean()
    _yesterday_raw = city_df.loc[city_df['local_day'] == _yesterday, 'us_aqi'].mean()

    #safeguard for missing values
    def _round_or_none(value):
        if pd.isna(value):
            return None
        return round(value)

    us_aqi_mean_today = _round_or_none(_today_raw)
    us_aqi_mean_yesterday = _round_or_none(_yesterday_raw)

    #run comparison only when both values exist
    if us_aqi_mean_today is None or us_aqi_mean_yesterday is None:
        kpi_direction = None
    elif us_aqi_mean_today > us_aqi_mean_yesterday:
        kpi_direction = 'increase'
    elif us_aqi_mean_today < us_aqi_mean_yesterday:
        kpi_direction = 'decrease'
    else: kpi_direction = None #equal values, no arrow

    #AQI category
    if us_aqi_mean_today < 0:
        aqi_category = ''
    elif (us_aqi_mean_today >=0) and (us_aqi_mean_today <= 50):
        aqi_category = 'Good'
    elif (us_aqi_mean_today > 50) and (us_aqi_mean_today <= 100):
        aqi_category = 'Moderate'
    elif (us_aqi_mean_today > 100) and (us_aqi_mean_today <= 150):
        aqi_category = 'Unhealthy for Sensitive Groups'
    elif (us_aqi_mean_today > 150) and (us_aqi_mean_today <= 200):
        aqi_category = 'Unhealthy'
    elif (us_aqi_mean_today > 200) and (us_aqi_mean_today <= 300):
        aqi_category = 'Very Unhealthy'
    else: aqi_category = 'Hazardous'
    return (
        aqi_category,
        kpi_direction,
        us_aqi_mean_today,
        us_aqi_mean_yesterday,
    )


@app.cell
def _(
    aqi_category,
    kpi_direction,
    mo,
    us_aqi_mean_today,
    us_aqi_mean_yesterday,
):
    aqi_card = mo.stat(value = us_aqi_mean_today if us_aqi_mean_today is not None else "n/a",
                    label = "Today's Average US AQI",
                    caption=f"{aqi_category} | yesterday's average: {us_aqi_mean_yesterday}",
                    direction = kpi_direction,
                    target_direction = 'decrease',
                    bordered=True)
    #aqi_card
    return (aqi_card,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ------------------------------------
    #Comparing cities by pollutant
    """)
    return


@app.cell
def _(alt, city_multiselect, mo, multicity_df, pollutant_dropdown):
    #create multiselect city dropdown, reuse single pollutant dropdown
    chart2 = (
        alt.Chart(multicity_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y(pollutant_dropdown.value,
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            color = alt.Color(
                'city:N',
                title = "City",
                legend=alt.Legend(
                    title="City",
                    titleFontSize=14,
                    labelFontSize=12
                )
            ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('city:N', title = "City"),
                alt.Tooltip(pollutant_dropdown.value, title = f'{pollutant_dropdown.selected_key}')

            ])
            .properties(
            title = alt.TitleParams(
                text = f'Comparing {pollutant_dropdown.selected_key} across cities',
                subtitle = ["Local times displayed. Dashed lines represent forecast data"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 800,
            height = 400
            )
    )
    mo.vstack([city_multiselect,pollutant_dropdown,chart2], align="center")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ------------------------------------------------------------------------------------
    #City pollution profile
    """)
    return


@app.cell
def _(alt, city_df):
    #create set of charts with all pollutants and allow single select city dropdown
    chart_pm2_5 = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('pm2_5',
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('pm2_5:Q', title = 'PM2.5')
            ]
            ).properties(
            title = alt.TitleParams(
                text = 'PM2.5',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 400,
            height = 200
            )
    )
    #mo.vstack([city_dropdown,chart_pm2_5])
    return (chart_pm2_5,)


@app.cell
def _(alt, city_df):
    chart_pm10 = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('pm10',
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('pm10:Q', title = 'PM10')
            ]
            ).properties(
            title = alt.TitleParams(
                text = 'PM10',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 400,
            height = 200
            )
    )
    #mo.vstack([city_dropdown,chart_pm10])
    return (chart_pm10,)


@app.cell
def _(alt, city_df):
    chart_CO = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('carbon_monoxide',
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('carbon_monoxide:Q', title = 'Carbon Monoxide')
            ]
            ).properties(
            title = alt.TitleParams(
                text = 'Carbon Monoxide',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 400,
            height = 200
            )
    )
    #mo.vstack([city_dropdown,chart_CO])
    return (chart_CO,)


@app.cell
def _(alt, city_df):
    chart_NO2 = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('nitrogen_dioxide',
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('nitrogen_dioxide:Q', title = 'Nitrogen Dioxide')
            ]
            ).properties(
            title = alt.TitleParams(
                text = 'Nitrogen Dioxide',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 400,
            height = 200
            )
    )
    #mo.vstack([city_dropdown,chart_NO2])
    return (chart_NO2,)


@app.cell
def _(alt, city_df):
    chart_SO2 = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('sulphur_dioxide',
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('sulphur_dioxide:Q', title = 'Sulphur Dioxide')
            ]
            ).properties(
            title = alt.TitleParams(
                text = 'Sulphur Dioxide',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 400,
            height = 200
            )
    )
    #mo.vstack([city_dropdown,chart_SO2])
    return (chart_SO2,)


@app.cell
def _(alt, city_df):
    chart_ozone = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('ozone',
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=None
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('ozone:Q', title = 'Ozone')
            ]
            ).properties(
            title = alt.TitleParams(
                text = 'Ozone',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 400,
            height = 200
            )
    )
    #mo.vstack([city_dropdown,chart_ozone])
    return (chart_ozone,)


@app.cell
def _(
    aqi_card,
    chart_CO,
    chart_NO2,
    chart_SO2,
    chart_ozone,
    chart_pm10,
    chart_pm2_5,
    city_dropdown,
    mo,
):
    mo.vstack(
        [mo.md(f"## Air Quality Snapshot: {city_dropdown.value}").style({"text-align": "center"}),
         mo.md("Local times displayed. Dashed lines represent forecast data").style({"text-align": "center","font_size":"0.9em","font-style":"italic"}),
        mo.hstack([city_dropdown,aqi_card], justify="center"),
        mo.hstack([chart_pm2_5,chart_pm10,chart_CO]),
        mo.hstack([chart_NO2,chart_SO2,chart_ozone])]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    -----------------------
    #Data in depth: explore individual city/pollutant combinations
    """)
    return


@app.cell
def _(alt, city_df, city_dropdown, mo, pollutant_dropdown):
    chart = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y(pollutant_dropdown.value,
                      axis = alt.Axis(
                          title = '',
                      titleFontSize=14,
                      titleFontWeight="normal",
                      labelFontSize=12)
                     ),
            strokeDash=alt.StrokeDash(
                'time_period:N',
                scale=alt.Scale(
                    domain=['past','forecast'],
                    range=[[1,0],[5,3]]   #set dash to solid for past, forecast has dash 5, gap 3   
                ),
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip(pollutant_dropdown.value, title = f'{pollutant_dropdown.selected_key}')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: {pollutant_dropdown.selected_key}',
                # subtitle = ["Particulate matter with a diameter of 2.5 microns or smaller.",
                #             "Measured in micrograms per cubic meter"],
                anchor = 'middle',
                fontSize = 14,
                subtitleFontSize=12,
                subtitleFontStyle='italic'),
            width = 800,
            height = 400
            )
    )
    mo.vstack([city_dropdown,pollutant_dropdown,chart], align = 'center')
    return


@app.cell
def _(city_df):
    display_cols = ['city','date','pm2_5','pm10','carbon_monoxide','nitrogen_dioxide','sulphur_dioxide','ozone','us_aqi']
    display_names = ['City','Date and Time','PM2.5 (μg/m³)','PM10 (μg/m³)','Carbon Monoxide (μg/m³)','Nitrogen Dioxide (μg/m³)','Sulphur Dioxide (μg/m³)','Ozone (μg/m³)','US AQI (0-500 index)']
    city_df_table = city_df[display_cols]
    city_df_table.columns = display_names
    return (city_df_table,)


@app.cell
def _(city_df_table, mo):
    mo.ui.table(data = city_df_table, page_size=24, selection=None, format_mapping={"Date and Time": lambda x: x.strftime("%b %d, %I:%M %p")})
    return


@app.cell
def _(mo):
    mo.md("""
    Data: air quality data by [Open-Meteo.com](https://open-meteo.com/), used under the
    [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license
    ([Open-Meteo licence terms](https://open-meteo.com/en/licence)). The values are model-based
    estimates from the Copernicus Atmosphere Monitoring Service (CAMS), not readings from ground
    monitoring stations.

    Changes made to the data: times shifted to each city's local time, hours flagged as past or
    forecast, and values rounded to two decimal places.

    Contains modified Copernicus Atmosphere Monitoring Service information 2026. Neither the
    European Commission nor ECMWF is responsible for any use that may be made of the Copernicus
    information or data it contains.

    Full citations are in the [project README](https://github.com/julierose/air-quality-analysis#data-sources-and-attribution).
    """)
    return


if __name__ == "__main__":
    app.run()
