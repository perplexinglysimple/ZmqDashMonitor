'''
    Implements a dash web app that displays zmq messages going through the system.
'''

# Imports
import dash
import dash_bootstrap_components as dbc

from dash import dcc

from DashComponents.configUtils import readConfig, validateConfig, createHumanReadableNames, createServernamePortTopicListDict
from DashComponents.navigationBar import NavigationBars
from DashComponents.visUtils import dynamicallyCreateVis

from src.zmqUtils import ZmqSubscriber

def argParse():
    import argparse
    parser = argparse.ArgumentParser(description='Run the ZMQ Message Viewer')
    parser.add_argument('--debug', action='store_true', help='Run the server in debug mode')
    parser.add_argument('--port', type=int, default=8050, help='Port to run the server on')
    parser.add_argument('--server_config', type=str, default='configs/monitorConfig.yaml', help='Path to the server configuration file')
    parser.add_argument('--navigation_config', type=str, default='configs/navigationConfig.yaml', help='Path to the navigation configuration file')
    return parser.parse_args()

if __name__ == '__main__':
    args = argParse()
    config = createServernamePortTopicListDict(readConfig(args.server_config))
    zqmSubscriber = ZmqSubscriber()
    navBar = NavigationBars(readConfig(args.navigation_config))
    app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.MATERIA, dbc.icons.FONT_AWESOME, dbc.themes.BOOTSTRAP])
    app.layout = dbc.Container([
            dcc.Input(id='page-load-trigger', style={'display': 'none'}),
            dcc.Interval(id='interval-component', interval=200, n_intervals=0),
            dbc.Container([navBar.navbar_layout(), dash.page_container], fluid=True),
        ], fluid=True)
    dynamicallyCreateVis(config, zqmSubscriber)
    app.run(debug=args.debug, port=args.port)
