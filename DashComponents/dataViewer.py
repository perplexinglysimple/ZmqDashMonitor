from dash import html
import pickle

class DataViewer:
    def __init__(self, data):
        self.data = data

    def update(self, data):
        self.data = data

    def display(self):
        raise NotImplementedError("Subclasses should implement this!")

class StringVeiwer(DataViewer):
    def display(self):
        return html.Div([
            html.H1("Raw String Data"),
            html.H3(f"Time Received: {self.data.get('time', 'Unknown')}"),
            html.Div(self.data.get('message', 'Unknown')),
        ])

class ImageVeiwer(DataViewer):
    def display(self):
        decodedData = pickle.loads(self.data)
        return html.Div([
            html.H1("Image Data"),
            html.Img(src=decodedData['image']),
        ])