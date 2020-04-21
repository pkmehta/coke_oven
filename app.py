# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 17:41:47 2020

@author: 1048168
"""


import sqlite3
import pandas as pd
import data_cleaning  as cl
import numpy as np
import json
import base64
import datetime
import io

# importing dash Modules
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State



# Importing Plotly for the graphs
import plotly.graph_objs as go

#importing the logging Module
import logging

# basic configuration for root Log File
logging.basicConfig(filename='coke_oven_root.log',level=logging.DEBUG, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%d-%m-%y %H:%M:%S')

# Customized log file handler
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('coke_oven_custom.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


#Creating Dash app
app= dash.Dash(__name__)

server = app.server # the Flask app

app.title = 'JSW Coke Oven'

app.layout= html.Div([

    #First Div Element for Header
    html.Div(
    [

    # First row element of the Frist Div element
        html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '45px',
                    'lineHeight': '45px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '5px'
                },
        # Allow multiple files to be uploaded
                multiple=True
                )
                ],
        style={
                'width': '12%','display': 'inline-block'}
                ),
        # End of First row element of the Frist Div element

        #Second Div Element for Graph
        html.Div([
        dcc.Loading(id="loading-1", type="default")
        ],
            style={'width': '5%','display': 'inline-block','margin': 'auto'}
            ),

        # Second row element of the Frist Div element
        html.Div([
            html.Div(id='output-data-upload')
            ],
        style={'width': '13%','display': 'inline-block'}
        ),


        # Third row element of the Frist Div element
        html.Div([
             html.H1(
                    "Coke Oven4: Battery #6 Amperage DashBoard",
                    style={"margin-bottom": "0px",'textAlign': 'center'},
                        )
         ],style={'width': '50%',"margin-bottom": "0px",'textAlign': 'center','display': 'inline-block'}
         ),

    # Fourth row element of the Frist Div element
         html.Div([
            html.Button(
            id='refresh-button',
            n_clicks=0,
            children='Refresh',
            style={'fontSize':22}
            )
        ],
         style={ 'width': '10%','display': 'inline-block'}
        ),
         # Fifth row element of the Frist Div element
     html.Div([
        html.Button(
        id='email-button',
        n_clicks=0,
        children='Send Email',
        style={'fontSize':22}
        )
    ],
     style={ 'width': '10%','display': 'inline-block'}
    )

    ]
    ),


   #Third Div Element for Graph
    html.Div([
        dcc.Graph(
            id='bar-graph'

        ),

    html.Hr(),  # horizontal line
    ]

        ),
    html.Div([
    dcc.Graph(
        id='trend-graph'

    )]
        ),
    html.Div(id='email_confirmation')

],

  style={'backgroundColor':'#f9f9f9'}
)



  # First Callback function to return the bar chart
@app.callback(Output('bar-graph', 'figure'),
              [Input('refresh-button', 'n_clicks')])
def callback_bar(n_clicks):
    #Making a connection with our SQLite DB
    conn = sqlite3.connect('coke_oven.db')
    # df2=cl.clean_data("bat_6_amperage_sheet.xlsx")
    # df2.to_sql(name='bat6_amperage', con=conn, if_exists = 'append')

# =============================================================================
#     try:
#         df_bat6 = pd.read_sql_query('select * from bat6_amperage order by record_date desc;', conn)
#
#     except:
#         logger.exception("Table Doesn't Exist")
#         cl.win_notification()
# =============================================================================

    df_bat6 = pd.read_sql_query('select * from bat6_amperage order by record_date desc;', conn)
    conn.close()
    if df_bat6.empty:
#       cl.win_notification()
       return
    else:
       df_bat6['record_date'] = pd.to_datetime(df_bat6['record_date'], format='%Y-%m-%d %H:%M:%S').dt.strftime("%d-%m-%Y")
       df_oven_list = (df_bat6.iloc[0]).tolist()
       latest_date =df_oven_list[0]
       oven_list = df_oven_list[1:]

       oven_values = df_bat6.iloc[:3].T

        # Getting the color of the bar based on the value
       color =cl.bar_color(oven_values)

       col_list = (df_bat6.columns).tolist()[1:]
       data =[]
       trace=go.Bar(
                    x = col_list,
                    y = oven_list,
                    #mode = 'lines+markers',
                    #line=dict(shape="spline", width=1, color="#92d8d8"),
                    marker=dict(color=color.tolist())
                )

       data.append(trace)
       layout=  go.Layout(
                title = f'Amperage Value of {latest_date}',
                xaxis = {'title': 'Days'},
                yaxis = {'title': 'Amperage Values'},
                height=350,
                hovermode='closest',
                plot_bgcolor='#f9f9f9'

            )

       figure = dict(data=data, layout=layout)

#       fig1 = go.Figure(data=data,layout=layout)

#      fig1.write_image("images/bar.png")
       return figure



  # First Callback function to return the trend chart
@app.callback(Output('trend-graph', 'figure'),
              [Input('bar-graph', 'hoverData')])
def callback_trend(hoverData):
    data =[]
    selected_oven = hoverData['points'][0]['x']
    conn = sqlite3.connect('coke_oven.db')
    df_hover = pd.read_sql(f'select * from (select {selected_oven}, record_date from bat6_amperage order by record_date desc limit 20) order by record_date asc;', con=conn)
    conn.close()
    df_hover['threshold']=160
    df_hover['record_date'] = pd.to_datetime(df_hover['record_date'], format='%Y-%m-%d %H:%M:%S').dt.strftime("%d-%m-%Y")
    trace=go.Scatter(
        y= df_hover[f"{selected_oven}"],
        x= df_hover["record_date"],
        mode = 'lines+markers',
        name= selected_oven
        )
    data.append(trace)
    trace=go.Scatter(
        y= df_hover['threshold'],
        x= df_hover["record_date"],
        mode = 'lines',
        name= 'Threshold Value'
        )
    data.append(trace)

    layout = go.Layout(
            title = f'Amperage Trend Chart of {selected_oven}',
            xaxis = {'title': 'Time Series Axis'},
            yaxis = {'title': 'Amperage Value','range':[75,200]},
            height=350,
            hovermode='closest',
            plot_bgcolor='#f9f9f9'
        )
    figure = dict(data=data, layout=layout)    
    return figure


@app.callback([Output('output-data-upload', 'children'),Output('loading-1', 'children')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])

def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            cl.parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        children2 = ' '
        return children, children2


@app.callback(Output('email_confirmation','children'),
    [Input('email-button', 'n_clicks')])

def email_output(n_clicks):
    cl.status_email()

    return


#Running the Dash Server
if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
#    app.run_server()
