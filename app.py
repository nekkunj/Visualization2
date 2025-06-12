from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pages.dashboard


app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

sidebar = dbc.Nav(
    [
        dbc.NavLink("Accueil", href="/", active="exact"),
        dbc.NavLink("Dashboard", href="/dashboard", active="exact"),
        dbc.NavLink("Carte", href="/map", active="exact"),
    ],
    vertical=True,
    pills=True,
    style={"height": "100vh", "padding": "2rem", "background-color": "#f8f9fa"},
)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(sidebar, width=2),
        dbc.Col([
            dcc.Location(id="url"),
            html.Div(id="page-content")
        ], width=10)
    ])
], fluid=True)

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/":
        from pages.home import layout as home_layout
        return home_layout
    elif pathname == "/dashboard":
        return pages.dashboard.layout

    return dbc.Container([
        html.H1("404: Page non trouvée", className="text-danger"),
        html.Hr(),
        html.P(f"Désolé, la page {pathname} n'existe pas."),
    ])

if __name__ == "__main__":
    app.run_server(debug=True)
