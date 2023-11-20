import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import time

from zmqUtils import ZmqSubscriber
from DashComponents.graph import ZMQGraph
from DashComponents.configUtils import readConfig, validateConfig, createHumanReadableNames, createServernamePortTopicListDict
from DashComponents.serverTable import ServerTable
from DashComponents.dataViewer import StringVeiwer, ImageVeiwer
from DashComponents.navigationBar import NavigationBars


class DashServer:
    '''
        This class implements the dash server that will display the data from the zmq subscriber.
    '''
    def __init__(self, args):
        self.app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.MATERIA, dbc.icons.FONT_AWESOME, dbc.themes.BOOTSTRAP],)
        self.output_list = []
        self.input_list = []
        self.displayedServerData = []
        self.server_table = None
        self.zqmSubscriber = ZmqSubscriber()
        self.startTime = time.time()
        self.graph = ZMQGraph(self.zqmSubscriber, 1000)
        self.serverConfig = self._readSeverConfig(args.server_config)
        self.navigationConfig = readConfig(args.navigation_config)
        self.server_table = ServerTable(self.serverConfig, self.zqmSubscriber)
        self.navBar = NavigationBars(self.navigationConfig)

    def _readSeverConfig(self, filename) -> dict:
        '''
            This function reads the server configuration file.
        '''
        # Read the configuration file
        config = createServernamePortTopicListDict(readConfig(filename))
        return config
    
    def run_server(self, debug=False, port=8050):
        '''
            This function runs the dash server.
        '''
        self.registerPages()
        self.registerCallbacks()
        self.app.run(debug=debug, port=port)

    def registerPages(self):
        '''
            This function registers the pages with the dash server.
        '''
        self.pathNames = createHumanReadableNames(self.serverConfig)
        dash.register_page("home", path="/", layout=self.setupHomeUi())
        # Creating topic viewer pages
        for pathName, rawValues in self.pathNames:
            zmqId = self.zqmSubscriber.lookupUUID(rawValues['ip'], rawValues['port'], rawValues['topic'])
            dash.register_page(zmqId, path=pathName, layout=self.setupDefaultVisUi(zmqId))
            self.registerZmqVisCallbacks(zmqId)
        # Creating custom pages
        for page in self.navBar.registerPages():
            name = page['name']
            href = page['href']
            print(name)
            if href == '/graph-view':
                dash.register_page(name, path=href, layout=self.graphLayout)
            elif href == '/server-table-view':
                dash.register_page(name, path=href, layout=self.serverTableLayout)
            elif href == '/':
                pass
            else:
                dash.register_page(name, path=href, layout=html.Div(f'{name} was configured but not implemented yet.'))
                

    def setBaseLayout(self):
        '''
            This function sets the base layout of the dash server. This is done to have a common layout across all pages for navigation.
        '''
        self.app.layout = dbc.Container([
            dcc.Interval(id='interval-component', interval=200, n_intervals=0),
            dbc.Container([self.navBar.navbar_layout(), dash.page_container], fluid=True),
        ], fluid=True)

    def setupHomeUi(self):
        '''
            This function sets up the home page of the dash server.
        '''
        self.graphLayout = self.graph.graph_layout(id='live-graph')
        self.serverTableLayout = self.server_table.server_table_layout(self.pathNames)
        return html.Div([
            dcc.Input(id='page-load-trigger', style={'display': 'none'}),
            html.H1("ZMQ Message Viewer"),
            
            self.graphLayout,

            # Display the data from the database
            html.Div([
                html.H2("Server List"),
                self.serverTableLayout,
            ]),

            # Add more components for spawning and killing servers
        ])

    def registerCallbacks(self):
        self.app.callback(
            Output('live-graph', 'figure'),
            [Input('interval-component', 'n_intervals'),
             self.graph.getPageLoadTrigger()])(self.graph.update_graph)
        
        @self.app.callback(
            [Output(output[0], output[1]) for output in self.server_table.getImageOuputList()],
            [Input('interval-component', 'n_intervals'), self.server_table.getPageLoadTrigger()],
            [State(state[0], state[1]) for state in self.server_table.getImageStateList()])
        def connectSevers(x, *args):
            #Dirty hack removing none from args
            args = [arg for arg in args if arg is not None]
            return [self.server_table.update_status(x, curState[0], id[0]) for curState, id in zip(args, self.server_table.getImageOuputList())]
        
    def registerZmqVisCallbacks(self, zmqUUid: str):
        '''
            This function registers the callbacks for the zmq visualization pages.

            TODO: Make the viewers stateful so that they can be updated with new data.
                This can easily be done by putting them in a dictionary and updating the data in the dictionary.
        '''
        @self.app.callback(
            Output(f'zmq-data-{zmqUUid}', 'children'),
            [Input(f'page-load-trigger-{zmqUUid}', 'value'),
             Input('interval-component', 'n_intervals')])
        def updateZmqData(n, *args):
            data = self.zqmSubscriber.getMostRecentData(zmqUUid)
            if self.zqmSubscriber.getDataType(zmqUUid).lower() == 'image':
                return ImageVeiwer(data).display()
            elif self.zqmSubscriber.getDataType(zmqUUid).lower() == 'string':
                return StringVeiwer(data).display()
            else:
                return html.Div([
                    html.H1("Unknown Data Type"),
                    html.Div(data.encode('utf-8')),
                ])

    def setupDefaultVisUi(self, zmqId):
        '''
            This function sets up the default visualization page for the dash server.
        '''
        return html.Div([
            dcc.Input(id=f'page-load-trigger-{zmqId}', style={'display': 'none'}),
            html.H1(f"ZMQ Message Viewer: {zmqId}"),

            # Display the zmq data received
            html.Div([
                html.H2("ZMQ Data"),
                html.Div(id=f'zmq-data-{zmqId}'),
            ]),

            dcc.Interval(id='interval-component', interval=1000 * 3, n_intervals=0),
        ])

