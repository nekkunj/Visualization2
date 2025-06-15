import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import duckdb

@st.cache_data(ttl=600)
def load_data():
    url = "https://raw.githubusercontent.com/nekkunj/Visualization2/9806e2c16dc395657aabbea51bd1774d9eef5567/assets/data_fusionnee_original.csv"
    query = f"SELECT * FROM read_csv_auto('{url}')"
    df = duckdb.query(query).to_df()
    
    df.columns = df.columns.str.strip().str.replace('"', '')
    df = df.rename(columns=lambda x: x.strip())
    
    df['GRAVITE'] = df['GRAVITE'].replace({
        'Dommages matériels seulement': 'Matériels',
        'Dommages matériels inférieurs au seuil de rapportage': 'Mineurs',
        'Léger': 'Léger',
        'Mortel ou grave': 'Grave'
    })

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
    
    return df

def show_dashboard():
    st.title("Road Accident Dashboard – Québec")

    df = load_data()

    dashboard_option = st.selectbox("Choisir une vue", [
        'Weather', 'Road Surface', 'Lighting', 'Environment',
        'Road Defects', 'Construction Zones', 'Weather vs Surface Heatmap', 'Before / After COVID-19'
    ])

    gravite_filter = st.selectbox("Gravité", options=[""] + list(df['GRAVITE'].dropna().unique()))
    year_range = st.slider("Filtrer par année", int(df['AN'].min()), int(df['AN'].max()), (int(df['AN'].min()), int(df['AN'].max())))

    filtered_df = df[(df['AN'] >= year_range[0]) & (df['AN'] <= year_range[1])]
    if gravite_filter:
        filtered_df = filtered_df[filtered_df['GRAVITE'] == gravite_filter]

    if dashboard_option in ['Weather', 'Weather vs Surface Heatmap']:
        meteo_filter = st.selectbox("Météo", options=[""] + list(filtered_df['CD_COND_METEO'].dropna().unique()))
        if meteo_filter:
            filtered_df = filtered_df[filtered_df['CD_COND_METEO'] == meteo_filter]

    if dashboard_option in ['Road Surface', 'Weather vs Surface Heatmap']:
        surface_filter = st.selectbox("Surface", options=[""] + list(filtered_df['CD_ETAT_SURFC'].dropna().unique()))
        if surface_filter:
            filtered_df = filtered_df[filtered_df['CD_ETAT_SURFC'] == surface_filter]

    if dashboard_option == 'Environment':
        env_filter = st.selectbox("Environment", options=[""] + list(filtered_df['Environment_Label'].dropna().unique()))
        if env_filter:
            filtered_df = filtered_df[filtered_df['Environment_Label'] == env_filter]

    if dashboard_option == 'Road Defects':
        road_filter = st.selectbox("Road Defect", options=[""] + list(filtered_df['CD_ASPCT_ROUTE'].dropna().unique()))
        if road_filter:
            filtered_df = filtered_df[filtered_df['CD_ASPCT_ROUTE'] == road_filter]

    if dashboard_option == 'Construction Zones':
        const_filter = st.selectbox("Construction Zone", options=[""] + list(filtered_df['CD_ZON_TRAVX_ROUTR'].dropna().unique()))
        if const_filter:
            filtered_df = filtered_df[filtered_df['CD_ZON_TRAVX_ROUTR'] == const_filter]

    # --- Visualization ---
    if dashboard_option == 'Weather':
        fig = px.histogram(filtered_df, x='CD_COND_METEO', color='GRAVITE', barmode='group', title="Accidents by Weather")
        st.plotly_chart(fig)

    elif dashboard_option == 'Road Surface':
        fig = px.histogram(filtered_df, x='CD_ETAT_SURFC', color='GRAVITE', barmode='group', title="Accidents by Road Surface")
        st.plotly_chart(fig)

    elif dashboard_option == 'Lighting':
        fig = px.histogram(filtered_df, x='Lighting_Label', color='GRAVITE', barmode='group', title="Accidents by Lighting")
        st.plotly_chart(fig)

    elif dashboard_option == 'Environment':
        fig = px.histogram(filtered_df, x='Environment_Label', title="Accidents by Environment")
        st.plotly_chart(fig)

    elif dashboard_option == 'Road Defects':
        fig = px.histogram(filtered_df, x='CD_ASPCT_ROUTE', color='GRAVITE', barmode='group', title="Accidents by Road Defects")
        st.plotly_chart(fig)

    elif dashboard_option == 'Construction Zones':
        fig = px.histogram(filtered_df, x='CD_ZON_TRAVX_ROUTR', color='GRAVITE', barmode='group', title="Construction Zone Accidents")
        st.plotly_chart(fig)

    elif dashboard_option == 'Weather vs Surface Heatmap':
        heat_df = filtered_df[filtered_df['GRAVITE'] == 'Grave']
        fig = px.density_heatmap(heat_df, x='CD_COND_METEO', y='CD_ETAT_SURFC',
                                 title="Severe Accidents Heatmap", color_continuous_scale='Reds')
        st.plotly_chart(fig)

    elif dashboard_option == 'Before / After COVID-19':
        total_by_year = df.groupby('AN').size()
        grave_by_year = df[df['GRAVITE'] == 'Grave'].groupby('AN').size()
        fig = go.Figure([
            go.Scatter(x=total_by_year.index, y=total_by_year.values,
                       mode='lines+markers', name='Total'),
            go.Scatter(x=grave_by_year.index, y=grave_by_year.values,
                       mode='lines+markers', name='Graves', line=dict(color='red'))
        ])
        fig.update_layout(title="COVID Impact on Accidents", xaxis_title="Year", yaxis_title="Number of Accidents")
        st.plotly_chart(fig)
