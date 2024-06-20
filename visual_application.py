import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime as dt
from datetime import timedelta

# parameters
# date for data
actual_data_date = "data do ustawienia"
actual_data_date_ranges = ["", ""]
# points that are chosen to be tracked by additional plots
chosen_points = []
# click blockers for plots
last_clicked = {
	"add" : None,
	"reset" : None,
	"reset_and_add" : None,
	"refresh_dates" : None,
	"next" : None
}
# first loop blocker
first_loop = True
# second inialization loop blocker
second_loop = True
# generated figs
main_simulation = {}
additional_plots = []	

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
    dcc.DatePickerRange(
            id='date-picker-range',
            start_date=dt(2020, 1, 1),
            end_date=dt(2020, 1, 31)
        ),
        dcc.DatePickerSingle(
            id='date-picker-single',
            date=dt(2020, 1, 15)
        )
    ], style={'padding': '20px'}),
    html.Div([
    html.Button('Set date and date range', id='refresh_dates'),
    html.Button('Start simulation', id='next_day')
    ]),
    dcc.Graph(
        id='main-plot',
        config={
            'modeBarButtonsToAdd': ['select2d', 'lasso2d'],
            'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
            'displaylogo': False
        },
        style={'height': '90vh'},
    ),
    
    html.Button('Add selected points', id='add'),
    html.Button('Reset selected and add new selected', id='reset_and_add'),
    html.Button('Reset selection', id='reset'),
    dcc.Graph(
        id='detail-plot-1'
    ),
    dcc.Graph(
        id='detail-plot-2'
    )
    
])

""",
dcc.Graph(
id='moving-device-plot'
)"""

df = pd.read_csv('measurements_daily.csv')

# additional functions

def is_clicked(button_name, button_value):
	global last_clicked
	verdict = last_clicked[button_name] != button_value
	if button_value != None:
		last_clicked[button_name] = button_value
	return verdict




def generate_dates(start_date, end_date):
    """
    Generate dates between start_date and end_date
    """
    dates = []
    current_date = start_date
    current_date = current_date.split("T")[0]
    end_date = end_date.split("T")[0]
    current_date = dt.strptime(current_date, '%Y-%m-%d')
    end_date = dt.strptime(end_date, '%Y-%m-%d')
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    return dates

def prepare_figs_for_date_range():
	global main_simulation, actual_data_date_ranges
	dates = generate_dates(actual_data_date_ranges[0], actual_data_date_ranges[1])
	main_simulation = {}
	
	for date in dates:
		data = df[df["Measurement Day"] == date]
		data = data[data["Status"] == "Stationary"]
		data = data[['Latitude', 'Longitude', 'Average Value', 'Device ID']]
		fig = px.scatter(data, y='Latitude', x='Longitude', hover_data=['Latitude', 'Longitude', 'Average Value', 'Device ID'], color='Average Value', range_color=[10, 40], color_continuous_scale=['blue', 'red'])
		fig.update_xaxes(range=[-180, 180])
		fig.update_yaxes(range=[-90, 90])
		
		fig.add_layout_image(
		    dict(
			source="https://www.geographyrealm.com/wp-content/uploads/2021/01/equator-world-map.jpg",
			xref="x",
			yref="y",
			x=-180,
			y=90,
			sizex=360,
			sizey=180,
			sizing="stretch",
			opacity=0.5,
			layer="below"
		    )
		)
		main_simulation[date] = fig
	prepare_figs_for_detail_plot()
		
def prepare_figs_for_detail_plot():
	global additional_plots, actual_data_date_ranges, chosen_points
	
	dates = generate_dates(actual_data_date_ranges[0], actual_data_date_ranges[1])
	additional_plots = []
	avg_values = {}
	devices = set()
	for date in dates:
		data = df[df["Measurement Day"] == date]
		data = data[data["Status"] == "Stationary"]
		avg = 0
		if len(chosen_points) > 0:
			count = 0
			selected_data = []
			for selection in chosen_points:
				subdata = data[data['Latitude'] >= selection[1][0]]
				subdata = subdata[subdata['Longitude'] >= selection[0][0]]
				subdata = subdata[subdata['Latitude'] <= selection[1][1]]
				subdata = subdata[subdata['Longitude'] <= selection[0][1]]
				devices.update(subdata["Device ID"].values)
				avg += subdata['Average Value'].mean()
				count += 1
			avg /= count
		else:
			avg = data['Average Value'].mean()
		avg_values[date] = avg
	if len(devices) > 0:
		devices = list(devices)
		data = df[df["Measurement Day"].isin(dates)]
		devices_data = data[data["Device ID"].isin(devices)]
		print(devices_data)
		fig_2 = px.line(devices_data, x='Measurement Day', y='Average Value', color='Device ID')
		
	data_1 = pd.DataFrame(list(avg_values.items()), columns=['Date', 'Value'])
	fig = px.scatter(data_1, x='Date', y='Value')
	fig.update_traces(mode='lines', line=dict(color='red', width=1))
	additional_plots.append(fig)
	
	if len(devices) == 0:
		additional_plots.append(px.scatter())
	else:
		additional_plots.append(fig_2)

def get_data_for_date():
	global main_simulation, actual_data_date
	return main_simulation[actual_data_date.split("T")[0]]

def check_date_between(start_date_str, end_date_str, date_to_check_str):
    date_format = "%Y-%m-%d"

    # Convert the date strings to datetime objects using the specified format
    start_date = dt.strptime(start_date_str.split("T")[0], date_format)
    end_date = dt.strptime(end_date_str.split("T")[0], date_format)
    date_to_check = dt.strptime(date_to_check_str.split("T")[0], date_format)

    # Check if the date_to_check is between start_date and end_date, inclusive
    return start_date <= date_to_check <= end_date
    
def get_next_possible_day():
	global actual_data_date, actual_data_date_ranges
	date = dt.strptime(actual_data_date.split("T")[0], "%Y-%m-%d")
	date += timedelta(days=1)
	date = date.strftime('%Y-%m-%d')
	if not check_date_between(actual_data_date_ranges[0], actual_data_date_ranges[1], date):
		date = actual_data_date_ranges[0]
	actual_data_date = date

@app.callback(
	[
		Output('main-plot', 'figure'),
		Output('date-picker-single', 'date'),
		Output('detail-plot-1', 'figure'),
		Output('detail-plot-2', 'figure')
	],
	[
		Input('refresh_dates', 'n_clicks'),
		Input('add', 'n_clicks'),
		Input('reset_and_add', 'n_clicks'),
		Input('reset', 'n_clicks'),
		Input('next_day', 'n_clicks')
	],
	[
	dash.dependencies.State('main-plot', 'figure'),
	dash.dependencies.State('detail-plot-1', 'figure'),
	dash.dependencies.State('detail-plot-2', 'figure'),
	dash.dependencies.State('date-picker-single', 'date'),
	dash.dependencies.State('date-picker-range', 'start_date'),
	dash.dependencies.State('date-picker-range', 'end_date')
	]
)
def main_function(
		refresh_button,
		add_button,
		reset_and_add_button,
		reset_button,
		next_button,
		existing_main_plot,
		existing_detail_plot,
		existing_detail_plot_2,
		chosen_date,
		start_date,
		end_date
):
	global chosen_points, first_loop, second_loop, actual_data_date, actual_data_date_ranges, additional_plots
	buttons = {
		"refresh_dates" : refresh_button,
		"add" : add_button,
		"reset_and_add" : reset_and_add_button,
		"reset" : reset_button,
		"next" : next_button
	}
	print("!")
	
	
	for (button_name, button_value) in buttons.items():
		if is_clicked(button_name, button_value):
			if button_name == "refresh_dates":
				if actual_data_date_ranges[0] != start_date or actual_data_date_ranges[1] != end_date:
					actual_data_date_ranges = [start_date, end_date]
					prepare_figs_for_date_range()
				if check_date_between(chosen_date, start_date, end_date):
					actual_data_date = chosen_date
				else:
					actual_data_date = start_date
			result_plot = None
			if button_name == "next":
				get_next_possible_day()
			result_plot = get_data_for_date()
			if button_name == "reset" or button_name == "reset_and_add":
				chosen_points = []
				prepare_figs_for_detail_plot()
			if button_name == "add" or button_name == "reset_and_add" or button_name == "next":
				if not(existing_main_plot == None or "selections" not in existing_main_plot["layout"]):
					for selection in existing_main_plot["layout"]["selections"]:
						chosen_points.append([
						[
							min(selection["x0"], selection["x1"]),
							max(selection["x1"], selection["x0"])
						],
						[
							min(selection["y0"], selection["y1"]),
							max(selection["y0"], selection["y1"])
						]
						])
				if len(chosen_points) > 0:
					for selection in chosen_points:
						result_plot.add_shape(
							type="rect",
							x0=selection[0][0], y0=selection[1][0], x1=selection[0][1], y1=selection[1][1],
							line=dict(color="RoyalBlue", width=3),
							fillcolor="LightSkyBlue",
							opacity=0.3
						)
				if button_name in ["add", "reset_and_add"]:
					prepare_figs_for_detail_plot()
					
			return result_plot, dt.strptime(actual_data_date.split("T")[0], "%Y-%m-%d"), additional_plots[0], additional_plots[1]
	if existing_detail_plot == None:
		existing_detail_plot = px.scatter()
	if existing_detail_plot_2 == None:
		existing_detail_plot_2 = px.scatter()
	return px.scatter(), dt(2020, 1, 15), existing_detail_plot, existing_detail_plot_2

"""
@app.callback(
	[
		Output('moving-device-plot', 'figure')
	],
	[
		Input('refresh_dates', 'n_clicks')
	]
)	
def step_up_moving_plot(n_click):
	dates = ["2018-02","2018-03","2018-04","2018-05","2018-06","2018-07","2018-08","2018-09","2018-10","2018-11"]
	df_data = df[df['Status'] == "Moving"]
	df_data = df_data[df_data['Device ID'] == 0]
	
	df_data['month'] = df_data['Measurement Day'].astype(str).str.slice(0, 7)

	df_summed = df_data.groupby('month').agg({'Longitude': 'mean', 'Latitude': 'mean', 'Average Value': 'sum'}).reset_index()
	data = df_summed[df_summed["month"].isin(dates)]
	fig = px.scatter(data, y='Latitude', x='Longitude', hover_data=['Latitude', 'Longitude', 'Average Value', 'month'])
	fig.update_xaxes(range=[-180, 180])
	fig.update_yaxes(range=[-90, 90])
	
	fig.add_layout_image(
	    dict(
		source="https://www.geographyrealm.com/wp-content/uploads/2021/01/equator-world-map.jpg",
		xref="x",
		yref="y",
		x=-180,
		y=90,
		sizex=360,
		sizey=180,
		sizing="stretch",
		opacity=0.5,
		layer="below"
	    )
	)
	print(n_click)
	if n_click == None:
		return px.scatter()
	else:
		return px.scatter()
"""
	
	
	
	
	
	
	
	
	
	
	
app.run_server(debug=True)	
	
	
	
	
	
	
	
	
	
	
