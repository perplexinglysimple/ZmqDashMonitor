import dash
from dash import html, dcc, callback, Input, Output, State

from typing import List

from DashComponents.serverTable import ServerTable
from DashComponents.configUtils import readConfig
from src.zmqUtils import ZmqSubscriber
from DashComponents.configUtils import createHumanReadableNames, createServernamePortTopicListDict

dash.register_page(__name__)

# ZMQ Subscriber is a singleton
zmqSub = ZmqSubscriber()

# Read the configuration file
config = readConfig('configs/tableConfig.yaml')
processedConfig = createServernamePortTopicListDict(config)
server_table = ServerTable(processedConfig, zmqSub)
humanReadableNames = createHumanReadableNames(processedConfig)
serverTableLayout = server_table.server_table_layout(humanReadableNames)

layout = html.Div([
    html.H1("Server List"),
    serverTableLayout
])

@callback(
    [Output(output[0], output[1]) for output in server_table.getImageOuputList()],
    [Input('interval-component', 'n_intervals'), server_table.getPageLoadTrigger()],
    [State(state[0], state[1]) for state in server_table.getImageStateList()])
def connectSevers(x, *args):
    #Dirty hack removing none from args
    args = [arg for arg in args if arg is not None]
    return [server_table.update_status(x, curState[0], id[0]) 
                for curState, id in zip(args, server_table.getImageOuputList())]