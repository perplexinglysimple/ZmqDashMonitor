import dash
from dash import html, dcc, callback
from dash.dependencies import Output, State, Input

from src.zmqUtils import ZmqSubscriber
from DashComponents.configUtils import createHumanReadableNames, createServernamePortTopicListDict
from DashComponents.dataViewer import StringVeiwer, ImageVeiwer, DataViewer

from typing import Callable, List, Dict, ByteString, Tuple

def setupDefaultVisUi(zmqId: str, interval: int = 1000 * 3):
    return html.Div([
        dcc.Input(id=f'page-load-trigger-{zmqId}', style={'display': 'none'}),
        html.H1(f"ZMQ Message Viewer: {zmqId}"),

        # Display the zmq data received
        html.Div([
            html.H2("ZMQ Data"),
            html.Div(id=f'zmq-data-{zmqId}'),
        ]),

        dcc.Interval(id=f'{zmqId}-interval-component', interval=interval, n_intervals=0),
    ])

def registerZmqVisCallbacks(zmqId: str, zqmSubscriber: ZmqSubscriber):
    dataType = zqmSubscriber.getDataType(zmqId).lower()
    dataObject = ImageVeiwer(zmqId=zmqId) if dataType == 'image' else StringVeiwer(zmqId=zmqId) if dataType == 'string' else DataViewer(zmqId=zmqId)
    @callback(
        Output(f'zmq-data-{zmqId}', 'children'),
        [Input(f'page-load-trigger-{zmqId}', 'value'),
            Input(f'{zmqId}-interval-component', 'n_intervals')])
    def updateZmqData(n, *args):
        dataObject.update(zqmSubscriber.getMostRecentData(zmqId))
        return dataObject.display()

def dynamicallyCreateVis(serverConfig: List[Dict], zqmSubscriber: ZmqSubscriber):
    pathNames = createHumanReadableNames(serverConfig)
    # Creating topic viewer pages
    for pathName, rawValues in pathNames:
        zmqId = zqmSubscriber.lookupUUID(rawValues['ip'], rawValues['port'], rawValues['topic'])
        updateRate = rawValues.get('UpdateRate', 3) * 1000
        dash.register_page(zmqId, path=pathName, layout=setupDefaultVisUi(zmqId, updateRate))
        registerZmqVisCallbacks(zmqId, zqmSubscriber)