import dash
from dash import html, dcc, callback, Input, Output, State

from typing import List, Dict

from DashComponents.graph import ZMQGraph
from DashComponents.configUtils import readConfig
from src.zmqUtils import ZmqSubscriber

dash.register_page(__name__)

# ZMQ Subscriber is a singleton
zmqSub = ZmqSubscriber()

# Read the configuration file
config = readConfig('configs/graphConfig.yaml')
graphIds: Dict[str, ZMQGraph] = {}
graphs: List[html.Div] = []
for graph in config['graphs']:
    id = graph['id']
    g = ZMQGraph(zmqSub, graph['historyPoints'], graph.get('filter_ids', None))

    graphLayout = html.Div([
        html.H1(graph['title']),
        html.H4(graph['description']),
        g.graph_layout(id=id),
        html.Br()
    ])

    graphIds[id] = g

    @callback(
        Output(id, 'figure'),
        [Input('interval-component', 'n_intervals'),
            g.getPageLoadTrigger()])
    def updateGraph(n, *args):
        id = dash.callback_context.outputs_list['id']
        return graphIds[id].update_graph(n, *args)

    graphs.append(graphLayout)

layout = html.Div([
    html.H1('Graph View'),
    html.Div(graphs),
])