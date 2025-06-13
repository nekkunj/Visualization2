from dash import dcc, html, callback, Output, Input
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# Chargement et nettoyage des données

url = "https://raw.githubusercontent.com/nekkunj/Visualization2/9806e2c16dc395657aabbea51bd1774d9eef5567/assets/data_fusionnee_original.csv"
df = pd.read_csv(url)
df.columns = df.columns.str.strip().str.replace('"', '')
df = df.rename(columns=lambda x: x.strip())

df['GRAVITE'] = df['GRAVITE'].replace({
    'Dommages matériels seulement': 'Matériels',
    'Dommages matériels inférieurs au seuil de rapportage': 'Mineurs',
    'Léger': 'Léger',
    'Mortel ou grave': 'Grave'
})

# Mappings
weather_mapping = {11: 'Clear', 12: 'Overcast', 13: 'Fog/Mist', 14: 'Rain/Drizzle', 15: 'Heavy Rain',
                   16: 'Strong Wind', 17: 'Snow/Hail', 18: 'Blowing Snow/Storm',
                   19: 'Freezing Rain', 99: 'Other'}
surface_mapping = {11: 'Dry', 12: 'Wet', 13: 'Aquaplaning', 14: 'Sand/Gravel', 15: 'Slush/Snow',
                   16: 'Snow-covered', 17: 'Hard-packed Snow', 18: 'Icy', 19: 'Muddy', 20: 'Oily', 99: 'Other'}
lighting_mapping = {1: 'Daylight - Clear Visibility', 2: 'Daylight - Low Visibility',
                    3: 'Night - Road Illuminated', 4: 'Night - Not Illuminated'}
env_mapping = {1: 'School Zone', 2: 'Residential', 3: 'Business / Commercial', 4: 'Industrial',
               5: 'Rural', 6: 'Forestry', 7: 'Recreational', 9: 'Other', 0: 'Not Specified'}

df['CD_COND_METEO'] = df['CD_COND_METEO'].map(weather_mapping)
df['CD_ETAT_SURFC'] = df['CD_ETAT_SURFC'].map(surface_mapping)
df['Lighting_Label'] = df['CD_ECLRM'].map(lighting_mapping)
df['Environment_Label'] = df['CD_ENVRN_ACCDN'].map(env_mapping)

# Dropdown options
gravite_options = [{'label': g, 'value': g} for g in df['GRAVITE'].unique()]

# Layout
layout = html.Div([
    html.H1("Road Accident Dashboard – Quebec", style={'textAlign': 'center'}),

    html.Div([
        dcc.Dropdown(
            id='dashboard-dropdown',
            options=[
                {'label': '1. Weather', 'value': 'weather'},
                {'label': '2. Road Surface', 'value': 'surface'},
                {'label': '3. Lighting', 'value': 'lighting'},
                {'label': '4. Environment', 'value': 'environment'},
                {'label': '5. Road Defects', 'value': 'defects'},
                {'label': '6. Construction Zones', 'value': 'construction'},
                {'label': '7. Weather vs Surface Heatmap', 'value': 'heatmap'},
                {'label': '8. Before / After COVID-19', 'value': 'covid'},
            ],
            value='weather',
            style={'width': '50%'}
        )
    ], style={'marginBottom': '20px'}),

    html.Div([
        dcc.Dropdown(id='filter-gravite', options=gravite_options, placeholder="Gravité"),
        dcc.Dropdown(id='filter-meteo', placeholder="Météo"),
        dcc.Dropdown(id='filter-surface', placeholder="Surface"),
        dcc.Dropdown(id='filter-env', placeholder="Environment"),
        dcc.Dropdown(id='filter-road', placeholder="Road Defect"),
        dcc.Dropdown(id='filter-const', placeholder="Construction Zone"),
    ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '20px'}),

    html.Div(id='graph-output'),

    html.Div([
        html.Label("Filtrer par année"),
        dcc.RangeSlider(
            id='filter-annee',
            min=df['AN'].min(),
            max=df['AN'].max(),
            value=[df['AN'].min(), df['AN'].max()],
            marks={int(year): str(int(year)) for year in sorted(df['AN'].unique())},
            step=1,
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'marginTop': '40px'})
])

# Activer ou désactiver certains filtres selon la sélection
@callback(
    Output('filter-gravite', 'disabled'),
    Output('filter-meteo', 'disabled'),
    Output('filter-surface', 'disabled'),
    Output('filter-env', 'disabled'),
    Output('filter-road', 'disabled'),
    Output('filter-const', 'disabled'),
    Input('dashboard-dropdown', 'value')
)
def toggle_filters(selected):
    return (
        selected != 'covid',
        selected in ['weather', 'heatmap'],
        selected in ['surface', 'heatmap'],
        selected == 'environment',
        selected == 'defects',
        selected == 'construction'
    )

# Mise à jour dynamique des options de filtres
@callback(
    Output('filter-meteo', 'options'),
    Output('filter-surface', 'options'),
    Output('filter-env', 'options'),
    Output('filter-road', 'options'),
    Output('filter-const', 'options'),
    Input('filter-annee', 'value'),
    Input('filter-gravite', 'value')
)
def update_filter_options(annee_range, gravite):
    filtered_df = df[(df['AN'] >= annee_range[0]) & (df['AN'] <= annee_range[1])]
    if gravite:
        filtered_df = filtered_df[filtered_df['GRAVITE'] == gravite]

    return [
        [{'label': v, 'value': v} for v in filtered_df['CD_COND_METEO'].dropna().unique()],
        [{'label': v, 'value': v} for v in filtered_df['CD_ETAT_SURFC'].dropna().unique()],
        [{'label': v, 'value': v} for v in filtered_df['Environment_Label'].dropna().unique()],
        [{'label': v, 'value': v} for v in filtered_df['CD_ASPCT_ROUTE'].dropna().unique()],
        [{'label': v, 'value': v} for v in filtered_df['CD_ZON_TRAVX_ROUTR'].dropna().unique()]
    ]

# Callback principal pour les graphiques
@callback(
    Output('graph-output', 'children'),
    Input('dashboard-dropdown', 'value'),
    Input('filter-annee', 'value'),
    Input('filter-gravite', 'value'),
    Input('filter-meteo', 'value'),
    Input('filter-surface', 'value'),
    Input('filter-env', 'value'),
    Input('filter-road', 'value'),
    Input('filter-const', 'value')
)
def update_graph(selected, annee_range, gravite, meteo, surface, env, road, const):
    dff = df[(df['AN'] >= annee_range[0]) & (df['AN'] <= annee_range[1])]
    if gravite: dff = dff[dff['GRAVITE'] == gravite]
    if meteo: dff = dff[dff['CD_COND_METEO'] == meteo]
    if surface: dff = dff[dff['CD_ETAT_SURFC'] == surface]
    if env: dff = dff[dff['Environment_Label'] == env]
    if road: dff = dff[dff['CD_ASPCT_ROUTE'] == road]
    if const: dff = dff[dff['CD_ZON_TRAVX_ROUTR'] == const]

    if selected == 'weather':
        fig = px.histogram(dff, x='CD_COND_METEO', color='GRAVITE', barmode='group', title="Accidents by Weather")
    elif selected == 'surface':
        fig = px.histogram(dff, x='CD_ETAT_SURFC', color='GRAVITE', barmode='group', title="Accidents by Road Surface")
    elif selected == 'lighting':
        fig = px.histogram(dff, x='Lighting_Label', color='GRAVITE', barmode='group', title="Accidents by Lighting")
    elif selected == 'environment':
        fig = px.histogram(dff, x='Environment_Label', title="Accidents by Environment")
    elif selected == 'defects':
        fig = px.histogram(dff, x='CD_ASPCT_ROUTE', color='GRAVITE', barmode='group', title="Accidents by Road Defects")
    elif selected == 'construction':
        fig = px.histogram(dff, x='CD_ZON_TRAVX_ROUTR', color='GRAVITE', barmode='group', title="Construction Zone Accidents")
    elif selected == 'heatmap':
        fig = px.density_heatmap(dff[dff['GRAVITE'] == 'Grave'], x='CD_COND_METEO', y='CD_ETAT_SURFC',
                                 title="Severe Accidents Heatmap", color_continuous_scale='Reds')
    elif selected == 'covid':
        fig = go.Figure([
            go.Scatter(x=df.groupby('AN').size().index, y=df.groupby('AN').size().values,
                       mode='lines+markers', name='Total'),
            go.Scatter(x=df[df['GRAVITE'] == 'Grave'].groupby('AN').size().index,
                       y=df[df['GRAVITE'] == 'Grave'].groupby('AN').size().values,
                       mode='lines+markers', name='Graves', line=dict(color='red'))
        ])
        fig.update_layout(title="COVID Impact on Accidents", xaxis_title="Year", yaxis_title="Number of Accidents")
    else:
        return html.P("Aucune option valide sélectionnée.")

    return dcc.Graph(figure=fig)
