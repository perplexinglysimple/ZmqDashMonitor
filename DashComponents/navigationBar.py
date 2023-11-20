import dash
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output



class NavigationBars:
    def __init__(self, navigationConfig: dict):
        self.sidebarLinks = []
        self.topbarLinks = []
        self.pageToRegister = []
        self.navigationConfig = navigationConfig
        self.setupNavigation()

    def setupNavigation(self):
        print(self.navigationConfig)
        self.displayName = self.navigationConfig['Title']
        self.description = self.navigationConfig['Description']
        self.sideBarTitle = self.navigationConfig['Sidebar']['Title']
        for links in self.navigationConfig['Sidebar']['Links']:
            name = links['text']
            href = links['href']
            icon = links.get('icon', None)
            self.addLinkToSidebar(name, href, icon)
            self.pageToRegister.append({'name': name, 'href': href, 'icon': icon})
        for links in self.navigationConfig['Topbar']['Links']:
            name = links['text']
            href = links['href']
            self.topbarLinks.append((name, href))
            self.pageToRegister.append({'name': name, 'href': href, 'icon': icon})

    def registerPages(self):
        return self.pageToRegister

    def navbar_layout(self):
        return html.Div([
            self.create_topbar(),
            #self.create_sidebar(),
        ])

    def addLinkToSidebar(self, name: str, href: str, icon: str = None):
        className = f"fas {icon} me-2" if icon else "fas me-2"
        self.sidebarLinks.append( 
                        dbc.NavLink(
                            [html.I(className=className), html.Span(name)],
                            href=href,
                            active="exact")
                        )

    def create_topbar(self):
        return dbc.NavbarSimple(
            dbc.Nav(
                # Place the links in a list and display them horizontally
                [
                    dbc.NavLink([dbc.NavLink(item[0], href=item[1]) for item in self.topbarLinks]),
                ]
            ),
            brand=self.displayName,
            color="primary",
            dark=True,
            className="mb-2",
        )
        # return html.Div(
        #     className='topbar',
        #     children=[
        #         html.H1(self.displayName, className='app-title')
        #     ]
        # )
    

    def create_sidebar(self):
        return html.Div([
                html.Div([
                    html.H2(self.sideBarTitle, style={"color": "white"}),
                ], className="sidebar-header"),
                html.Hr(),
                dbc.Nav(
                    self.sidebarLinks,
                    vertical=True,
                    pills=True,
                ),
            ], className="sidebar")