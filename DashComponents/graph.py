import dash
import time
from collections import deque

from dash import dcc, Input, html
from typing import List
from src.zmqUtils import ZmqSubscriber


class ZMQGraph:
    '''
        This class implements a graph that displays the data throughput of the zmq messages.
    '''
    def __init__(self, zqmSubscriber: ZmqSubscriber, historyPoints: int = 100, filterIds: List[str] | None = None):
        self.zqmSubscriber = zqmSubscriber
        self.startTime = time.time()
        self.historyPoints = historyPoints
        self.history = deque(maxlen=self.historyPoints)
        self.filterIds = filterIds

    def graph_layout(self, id: str) -> dcc.Graph:
        return html.Div([
                dcc.Input(id=f'page-load-trigger-graph', style={'display': 'none'}),
                dcc.Graph(id=id, animate=True)
            ])

    def getPageLoadTrigger(self) -> Input:
        return Input('page-load-trigger-graph', 'value')

    def update_graph(self, n: int, *args) -> dict:
        # Get the metrics from the zmq subscriber
        try:
            metrics = self.zqmSubscriber.getMetrics(self.filterIds)
        except KeyError as e:
            print(f'KeyError: {e}')
            return dash.no_update
        if len(metrics) == 0:
            print('No metrics found')
            return dash.no_update
        graph_data = []

        for uuid, metric in metrics.items():
            # Time is the x axis in seconds
            x_values = (time.time() - self.startTime, )
            message_rates = (metric['message_rate'], )
            payload_rates = (metric['payload_rate'], )

            graph_data.append(
                {'x': x_values, 'y': message_rates, 'mode': 'lines+markers', 'name': f'{uuid}-Message Rate'}
            )
            graph_data.append(
                {'x': x_values, 'yaxis': 'y2', 'y': payload_rates, 'mode': 'lines+markers', 'name': f'{uuid}-Payload Rate (KB/s)'}
            )

        graph_layout = {
            'title': 'Data Throughput Metrics',
            'xaxis': {'title': 'Time (s)'},
            'yaxis': {'title': 'Rate (Hz) and KB', 'side': 'left'},
            'yaxis2': {'title': 'Payload Rate (KB/s)', 'side': 'right', 'overlaying': 'y'},
            'autosize': True,
        }

        if not len(graph_data):
            return dash.no_update
        self.history.append(graph_data)

        # Merge the data from the history to a single dictionary.
        # Only merge the same names together
        rolling_history = {}
        for gData in self.history:
            for data in gData:
                if data['name'] not in rolling_history:
                    rolling_history[data['name']] = {'x': list(data['x']), 'y': list(data['y']), 'mode': data['mode'], 'name': data['name'], 'yaxis': data.get('yaxis', 'y')}
                else:
                    rolling_history[data['name']]['x'].extend(data['x'])
                    rolling_history[data['name']]['y'].extend(data['y'])
        
        # Strip the keys from the dictionary
        rolling_history = list(rolling_history.values())

        # Find the min and max x values
        minX = rolling_history[0]['x'][0]
        maxX = rolling_history[0]['x'][0]
        for data in rolling_history:
            if data['x'][0] < minX:
                minX = data['x'][0]
            if data['x'][-1] > maxX:
                maxX = data['x'][-1]

        graph_layout['xaxis']['range'] = [minX, maxX]

        return {'data': rolling_history, 'layout': graph_layout}