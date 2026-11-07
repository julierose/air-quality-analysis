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
    air_df = pd.read_json(aqi_path)

    air_df['current_time_utc'] = pd.to_datetime(air_df['current_time_utc'])
    air_df['current_time_local'] = pd.to_datetime(air_df['current_time_local'])
    _period_conditions = [air_df['time_label'] == 'past',
                 air_df['time_label'].isin(['forecast_today','forecast_tomorrow'])
                 ]
    _period_labels = ['past','forecast']
    air_df['time_period'] = np.select(_period_conditions, _period_labels, default = 'Unmapped')

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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #View individual City/Pollutant combinations
    """)
    return


@app.cell
def _(air_df, city_dropdown, city_multiselect):
    city_df = air_df[air_df['city'] == city_dropdown.value]

    if city_multiselect.value:
        multicity_df = air_df[air_df['city'].isin(city_multiselect.value)]
    else: #if no cities are selected, create an empty dataframe so the plot doesn't crash
        multicity_df = air_df.iloc[0:0]

    city_df
    return city_df, multicity_df


@app.cell
def _(alt, city_df, city_dropdown, city_multiselect, mo, pollutant_dropdown):
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
    mo.vstack([city_multiselect,pollutant_dropdown,chart])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #
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
    mo.vstack([city_multiselect,pollutant_dropdown,chart2])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #City pollution profile
    """)
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
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
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('pm2_5:Q', title = 'PM2.5')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: PM2.5',
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
    mo.vstack([city_dropdown,chart_pm2_5])
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
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
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('pm10:Q', title = 'PM10')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: PM10',
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
    mo.vstack([city_dropdown,chart_pm10])
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
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
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('carbon_monoxide:Q', title = 'Carbon Monoxide')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: Carbon Monoxide',
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
    mo.vstack([city_dropdown,chart_CO])
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
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
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('nitrogen_dioxide:Q', title = 'Nitrogen Dioxide')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: Nitrogen Dioxide',
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
    mo.vstack([city_dropdown,chart_NO2])
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
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
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('sulphur_dioxide:Q', title = 'Sulphur Dioxide')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: Sulphur Dioxide',
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
    mo.vstack([city_dropdown,chart_SO2])
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
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
                legend=alt.Legend(
                    title="Time Period",
                    titleFontSize=14,
                    labelFontSize=12
                )
                ),
            tooltip = [
                alt.Tooltip('date:T', format="%b %d, %I:%M %p", title='Date & Time'),
                alt.Tooltip('ozone:Q', title = 'Ozone')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: Ozone',
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
    mo.vstack([city_dropdown,chart_ozone])
    return


@app.cell
def _(alt, city_df, city_dropdown, mo):
    chart_usaqi = (
        alt.Chart(city_df).mark_line(point=True).encode(
            x = alt.X('date:T',
                      axis = alt.Axis(
                      title='',
                      format="%b %d %I:%M %p",
                      labelAngle=20,
                      labelFontSize = 12
                      )
                     ),
            y = alt.Y('us_aqi',
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
                alt.Tooltip('us_aqi:Q', title = 'US AQI')
            ]
            ).properties(
            title = alt.TitleParams(
                text = f'{city_dropdown.value}: US AQI',
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
    mo.vstack([city_dropdown,chart_usaqi])
    return


if __name__ == "__main__":
    app.run()
