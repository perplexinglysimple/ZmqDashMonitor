import dash
from dash import html, dcc
from dash.dependencies import Output, State, Input

from zmqUtils import ZmqSubscriber

from typing import Callable, List, Dict, ByteString, Tuple

class ServerTable():
    def __init__(self, serverConfig: List[Dict], zqmSubscriber: ZmqSubscriber):
        self.serverConfig = serverConfig
        self.zqmSubscriber = zqmSubscriber
        self.imageOutputList = []
        self.imageStateList = []
        self.urlClickOutputList = []
        self.urlLookup = {}

    def getImageOuputList(self) -> List[Tuple[str, str]]:
        return self.imageOutputList

    def getImageStateList(self) -> List[Tuple[str, str]]:
        return self.imageStateList
    
    def getUrlClickOutputList(self) -> List[Tuple[str, str]]:
        return [('url_redirect', 'pathname')]
    

    def getUrlLookup(self, key) -> str:
        return self.urlLookup.get(key, '/')

    def url_redirect(self, n: int, id: str):
        print(f"Redirecting to {self.getUrlLookup(id)}")
        if n is None:
            return dash.no_update
        return dcc.Location(href=self.getUrlLookup(id))

    def getPageLoadTrigger(self) -> Input:
        return Input('page-load-trigger-table', 'value')

    def update_status(self, n: int, currentState: str, id):
        status = self.zqmSubscriber.getStatus(id)
        if status == 'Unknown':
            return dash.no_update
        elif status == 'Connected':
            return '/assets/check-green.gif'
        elif status == 'Disconnected':
            return '/assets/giphy.gif'
        return dash.no_update

    def getUrlFromServerConfig(self, server_ip: str, port: str | int, topic: str, urls: List[Tuple[str, dict]]) -> str:
        for url, values in urls:
            if values['ip'] == server_ip and values['port'] == port and values['topic'] == topic:
                return url
        return None

    def addRowToTable(self, server_ip: str, port: str | int, topic: str, server_dataType: str, urls: List[Tuple[str, dict]]):
        url = self.getUrlFromServerConfig(server_ip, port, topic, urls)
        self.zqmSubscriber.addZmqServerPortTopic(server_ip, port, topic, server_dataType)
        id=self.zqmSubscriber.lookupUUID(server_ip, port, topic)
        self.imageOutputList.append((id, 'src'))
        self.imageStateList.append((id, 'src'))
        self.urlLookup[id] = url
        topic_row = html.Tr([
            html.Td(f"{server_ip}:{port}", style={'width': '33%'}),
            html.Td(topic, style={'width': '33%'}),
            html.Td(dcc.Link(html.Img(src='/assets/loading.gif', id=id, style={'height': '40px'}), href=url), style={'width': '33%'}),
        ], style={'width': '100%', 'border-bottom': '1px solid black', 'border-collapse': 'collapse', 'text-align': 'center'})
        return topic_row

    def server_table_layout(self, urls: List[Tuple[str, dict]]) -> html.Table:
        server_table = [
            html.Tr([
                dcc.Input(id=f'page-load-trigger-table', style={'display': 'none'}),
                html.Th("Server Name", style={'width': '33%'}),
                html.Th("Topic", style={'width': '33%'}),
                html.Th("Status", style={'width': '33%'})
            ], style={'width': '100%', 'background': 'lightgray', 'font-weight': 'bold', 'border': '1px solid black', 'border-collapse': 'collapse', 'text-align': 'center'})
        ]

        server_names = set()

        for serverInfo in self.serverConfig:
            server_name = serverInfo['name']
            server_ip = serverInfo['ip']
            server_port = serverInfo['port']
            server_topic = serverInfo['topic']
            server_dataType = serverInfo['dataType']
            if server_name not in server_names:
                server_row = html.Tr([
                    html.Td("", style={'width': '33%'}),
                    html.Td(server_name, style={'width': '33%'}),
                    html.Td("", style={'width': '33%'})
                ], style={'width': '100%', 'background': '#1111', 'font-weight': 'bold', 'border': '1px solid black', 'border-collapse': 'collapse', 'text-align': 'center'})

                server_table.append(server_row)
                server_names.add(server_name)

            server_table.append(self.addRowToTable(server_ip, server_port, server_topic, server_dataType, urls))

        return html.Table(server_table, style={'width': '100%', 'border-collapse': 'collapse', 'border': '1px solid black', 'margin-top': '20px'})