import pandas as pd
import plotly.express as px

REGION_COORDS = {
    "Bas-Saint-Laurent (01)": (48.5, -68.5),
    "Saguenay―Lac-Saint-Jean (02)": (48.3, -71.1),
    "Capitale-Nationale (03)": (47.0, -71.5),
    "Mauricie (04)": (46.6, -72.7),
    "Estrie (05)": (45.5, -71.9),
    "Montréal (06)": (45.5, -73.6),
    "Outaouais (07)": (45.5, -76.0),
    "Abitibi-Témiscamingue (08)": (48.0, -78.5),
    "Côte-Nord (09)": (50.2, -63.0),
    "Nord-du-Québec (10)": (53.0, -76.0),
    "Gaspésie―Îles-de-la-Madeleine (11)": (49.0, -64.3),
    "Chaudière-Appalaches (12)": (46.5, -70.9),
    "Laval (13)": (45.6, -73.8),
    "Lanaudière (14)": (46.0, -73.4),
    "Laurentides (15)": (46.3, -74.0),
    "Montérégie (16)": (45.3, -73.0),
    "Centre-du-Québec (17)": (46.4, -72.0)
}


def prepare_region_data(filepath='./assets/data_fusionnee.csv'):
    '''
    Prépare les données agrégées par région pour la carte.

    Args:
        filepath (str): chemin vers le fichier CSV

    Returns:
        pd.DataFrame: données prêtes avec lat/lon/nb_accidents
    '''
    df = pd.read_csv(filepath)

    # Nettoyage des noms de colonnes
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", '').str.replace('\t', '')

    # Vérifier et renommer si nécessaire
    if 'REG_ADM' not in df.columns:
        for col in df.columns:
            if 'REG_ADM' in col:
                df.rename(columns={col: 'REG_ADM'}, inplace=True)
                break

    # Extraire le nom de région
    df['region'] = df['REG_ADM']

    # Compter le nombre d'accidents par région
    df_counts = df['region'].value_counts().reset_index()
    df_counts.columns = ['region', 'nb_accidents']

    # Ajouter les coordonnées
    df_counts['latitude'] = df_counts['region'].map(lambda r: REGION_COORDS.get(r, (None, None))[0])
    df_counts['longitude'] = df_counts['region'].map(lambda r: REGION_COORDS.get(r, (None, None))[1])
    return df_counts
# def draw_geo_map(df_counts, center_lat=47.5, center_lon=-71.5, zoom=4.5):
#     # Nettoyer les noms de région pour la légende
#     df_counts['clean_region'] = df_counts['region'].str.replace(r'\s*\(\d+\)', '', regex=True)

#     # Définir le texte de survol en anglais
#     df_counts['hover_text'] = df_counts.apply(
#         lambda row: f"<b>{row['clean_region']}</b><br>Number of accidents: {row['nb_accidents']:,}", axis=1
#     )

#     fig = px.scatter_geo(
#         df_counts,
#         lat='latitude',
#         lon='longitude',
#         size='nb_accidents',
#         color='clean_region',
#         hover_name='clean_region',
#         custom_data=['hover_text', 'region'],  # pour le survol et les callbacks
#         projection='natural earth',
#         title='Click on a region on the map to explore accident trends over time in the panel on the right'
#     )

#     # Personnaliser le contenu du survol
#     fig.update_traces(
#         hovertemplate='%{customdata[0]}<extra></extra>'
#     )

#     fig.update_layout(
#         geo=dict(
#             scope='north america',
#             showland=True,
#             landcolor='lightgray',
#             center=dict(lat=center_lat, lon=center_lon),
#             projection_scale=zoom
#         ),
#         legend_title='Region'
#     )

#     return fig

import plotly.express as px
import plotly.graph_objects as go

def draw_geo_map(df_counts, center_lat=47.5, center_lon=-71.5, zoom=4.5):
    fig = px.scatter_geo(
        df_counts,
        lat='latitude',
        lon='longitude',
        size='nb_accidents',
        color='region',
        hover_name='region',
        hover_data={'nb_accidents': True, 'latitude': False, 'longitude': False},
        projection='natural earth',
        title='Click on a region on the map to explore accident trends over time in the panel on the right',
        custom_data=['region']
    )

    fig.update_layout(
        legend_title=dict(text='Region'),
        template='plotly_white',  # Assure l'application du style
        font=dict(
            family='Open Sans, sans-serif',
            size=14,
            color='#333333'
        ),
        title_font=dict(
            family='Open Sans, sans-serif',
            size=14,
            color='#333333'
        ),
        legend=dict(
            font=dict(
                family='Open Sans, sans-serif',
                size=12,
                color='#333333'
            )
        ),
        geo=dict(
            scope='north america',
            showland=True,
            landcolor='lightgray',
            center=dict(lat=center_lat, lon=center_lon),
            projection_scale=zoom
        )
    )

    return fig
