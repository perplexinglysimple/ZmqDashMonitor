import dash
from dash import html
from dash import dcc

dash.register_page(__name__, path='/')

layout = html.Div([
    dcc.Input(id='page-load-trigger', style={'display': 'none'}),
    html.H1("ZMQ Message Viewer"),
])