from dash import html
import pickle

class DataViewer:
    def __init__(self, zmqId: str):
        self.zmqId = zmqId
        self.data = None

    def update(self, data):
        '''
            Do not do long computations or block in this function. You should only update the data in this function and do any long computations in the in a thread.
        '''
        self.data = data

    def display(self) -> html.Div:
        '''
            Do not do long computations or block in this function. You should only update the data in this function and do any long computations in the in a thread.
        '''
        return html.Div([
            html.H1(f"Raw Data"),
            html.H3(f"Time Received: {self.data.get('time', 'Unknown')}"),
            html.Div(self.data.get('message', 'Unknown')),
        ])

class StringVeiwer(DataViewer):
    def display(self) -> html.Div:
        return html.Div([
            html.H1("Raw String Data"),
            html.H3(f"Time Received: {self.data.get('time', 'Unknown')}"),
            html.Div(self.data.get('message', 'Unknown')),
        ])

class ImageVeiwer(DataViewer):
    def display(self) -> html.Div:
        decodedData = pickle.loads(self.data)
        return html.Div([
            html.H1("Image Data"),
            html.Img(src=decodedData['image']),
        ])