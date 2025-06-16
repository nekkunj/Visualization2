# pages/05_Road_Severity.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px # Added for potential future use or color scales

# --- Data Loading and Cleaning (Cached for Performance) ---

@st.cache_data
def load_and_clean_data():
    """
    Loads and cleans the accident data for the Road Severity page.
    This function is cached to optimize performance, loading data only once.
    """
    st.info("Loading and cleaning data for Road Severity page...")
    try:
        df = pd.read_csv('data_fusionnee.csv')
        df.columns = df.columns.str.strip().str.replace('"', '').str.replace('\t', '')
        df = df.rename(columns=lambda x: x.strip()) # Ensure all column names are clean

        # Map GRAVITE to desired labels for consistency across the app
        if 'GRAVITE' in df.columns:
            df['GRAVITE_EN'] = df['GRAVITE'].replace({
                'Dommages matériels seulement': 'Material Damage',
                'Dommages matériels inférieurs au seuil de rapportage': 'Low Damage',
                'Léger': 'Minor',
                'Mortel ou grave': 'Severe'
            })
        else:
            st.error("Column 'GRAVITE' not found. Severity mapping skipped.")
            df['GRAVITE_EN'] = df['GRAVITE'] if 'GRAVITE' in df.columns else 'Unknown'

        # Ensure 'CD_CATEG_ROUTE' and 'CD_CONFG_ROUTE' are treated as strings
        if 'CD_CATEG_ROUTE' in df.columns:
            df['CD_CATEG_ROUTE'] = df['CD_CATEG_ROUTE'].astype(str).str.strip()
        if 'CD_CONFG_ROUTE' in df.columns:
            df['CD_CONFG_ROUTE'] = df['CD_CONFG_ROUTE'].astype(str).str.strip()

        st.success("Data loaded and cleaned successfully.")
        return df
    except FileNotFoundError:
        st.error("Error: 'assets/data_fusionnee.csv' not found. Please ensure the file is in the 'assets' directory.")
        st.stop() # Stop app execution if the data file is missing
    except Exception as e:
        st.error(f"An unexpected error occurred during data loading: {e}")
        st.exception(e) # Show full traceback for debugging
        st.stop()

# Load data when the script runs (will be cached after first run)
df = load_and_clean_data()

# --- Helper Function for Sankey Chart Generation ---

def create_sankey_chart(data_frame, chart_type='Road Category'):
    """
    Creates a Sankey diagram to visualize accident flows from
    road categories/configurations to severity, with color coding.
    chart_type: 'Road Category' or 'Road Configuration'
    """
    st.info(f"Generating Sankey chart for: {chart_type}")

    if data_frame.empty:
        fig = go.Figure()
        fig.update_layout(title="No data to display for this chart.")
        st.warning("Input DataFrame is empty for Sankey chart generation.")
        return fig

    # Define color map for severities
    severity_color_map = {
        "Severe": "darkred",
        "Minor": "lightgreen",
        "Material Damage": "steelblue",
        "Low Damage": "lightgrey",
        "Other": "gray" # Fallback color
    }

    # Define a consistent order for severity labels for visualization consistency
    severity_order = ['Severe', 'Minor', 'Material Damage', 'Low Damage']

    # Get unique labels for nodes, ensuring they exist in the dataframe
    road_categories = sorted(data_frame['CD_CATEG_ROUTE'].dropna().unique().tolist()) if 'CD_CATEG_ROUTE' in data_frame.columns else []
    road_configs = sorted(data_frame['CD_CONFG_ROUTE'].dropna().unique().tolist()) if 'CD_CONFG_ROUTE' in data_frame.columns else []
    severities_in_data = sorted(data_frame['GRAVITE_EN'].dropna().unique().tolist()) if 'GRAVITE_EN' in data_frame.columns else []

    # Filter 'severities_in_data' to only include those in our defined order, maintaining desired order
    present_severities_ordered = [s for s in severity_order if s in severities_in_data]

    source = []
    target = []
    value = []
    nodes_labels = []
    nodes_colors = []
    links_colors = [] # New list for link colors

    # Determine nodes and flows based on chart_type
    if chart_type == 'Road Category':
        if not road_categories or not present_severities_ordered:
            st.warning("Missing required data for Road Category Sankey chart (categories or severities).")
            return go.Figure().update_layout(title="Missing data for Road Category chart.")
        
        nodes_labels = road_categories + present_severities_ordered
        label_to_index = {label: i for i, label in enumerate(nodes_labels)}

        # Assign colors to nodes: default for categories, specific for severities
        for label in nodes_labels:
            if label in severity_color_map:
                nodes_colors.append(severity_color_map[label])
            else:
                nodes_colors.append("lightgray") # Default color for road categories

        # Aggregate flows: from road category to severity
        if 'CD_CATEG_ROUTE' in data_frame.columns and 'GRAVITE_EN' in data_frame.columns:
            flows_data = data_frame.groupby(['CD_CATEG_ROUTE', 'GRAVITE_EN']).size().reset_index(name='count')
            for _, row in flows_data.iterrows():
                cat_label = row['CD_CATEG_ROUTE']
                grav_label = row['GRAVITE_EN']
                # Ensure labels exist in the current nodes_labels and are valid
                if cat_label in label_to_index and grav_label in label_to_index:
                    source.append(label_to_index[cat_label])
                    target.append(label_to_index[grav_label])
                    value.append(row['count'])
                    links_colors.append(severity_color_map.get(grav_label, "gray")) # Color links by target severity
        else:
            st.warning("Required columns 'CD_CATEG_ROUTE' or 'GRAVITE_EN' not found for Road Category Sankey.")

    else: # chart_type == 'Road Configuration'
        if not road_configs or not present_severities_ordered:
            st.warning("Missing required data for Road Configuration Sankey chart (configs or severities).")
            return go.Figure().update_layout(title="Missing data for Road Configuration chart.")

        nodes_labels = road_configs + present_severities_ordered
        label_to_index = {label: i for i, label in enumerate(nodes_labels)}

        # Assign colors to nodes: default for configs, specific for severities
        for label in nodes_labels:
            if label in severity_color_map:
                nodes_colors.append(severity_color_map[label])
            else:
                nodes_colors.append("lightgray") # Default color for road configurations

        # Aggregate flows: from road config to severity
        if 'CD_CONFG_ROUTE' in data_frame.columns and 'GRAVITE_EN' in data_frame.columns:
            flows_data = data_frame.groupby(['CD_CONFG_ROUTE', 'GRAVITE_EN']).size().reset_index(name='count')
            for _, row in flows_data.iterrows():
                conf_label = row['CD_CONFG_ROUTE']
                grav_label = row['GRAVITE_EN']
                # Ensure labels exist in the current nodes_labels and are valid
                if conf_label in label_to_index and grav_label in label_to_index:
                    source.append(label_to_index[conf_label])
                    target.append(label_to_index[grav_label])
                    value.append(row['count'])
                    links_colors.append(severity_color_map.get(grav_label, "gray")) # Color links by target severity
        else:
            st.warning("Required columns 'CD_CONFG_ROUTE' or 'GRAVITE_EN' not found for Road Configuration Sankey.")

    if not source: # Check if no valid links were generated
        fig_sankey = go.Figure()
        fig_sankey.update_layout(title=f"No valid links generated for {chart_type} Sankey diagram.")
        st.warning(f"No links created for {chart_type} Sankey chart. Check data and mappings.")
        return fig_sankey

    # Create Sankey diagram figure
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes_labels,
            color=nodes_colors, # Apply specific colors to nodes
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=links_colors, # Apply specific colors to links
            line=dict(color="lightgray", width=0.5) # Optional: outline for links
        )
    )])

    title_text = f"Accident Severity: {chart_type} → Severity"
    fig_sankey.update_layout(
        title_text=title_text,
        font_size=10,
        height=600,
        width=900,
        template="plotly_white"
    )
    st.success(f"Sankey chart '{chart_type}' figure created successfully with custom colors.")
    return fig_sankey

# --- Streamlit Layout ---

st.title("Road Accident Severity Analysis")

st.write(
    """
    This page visualizes the flow of road accidents from different road characteristics
    to their resulting severity. Use the selection below to switch between
    **Road Category** and **Road Configuration** as the starting point of the flow.
    """
)

st.markdown("---")

# Streamlit radio button to select chart type (replaces Plotly updatemenus buttons)
chart_selection = st.radio(
    "Select the type of flow to visualize:",
    ('Road Category', 'Road Configuration'),
    key='sankey_chart_type_selector', # Unique key for the widget
    horizontal=True # Display radio buttons horizontally
)

# Generate and display the Sankey chart based on selection
sankey_fig = create_sankey_chart(df, chart_selection)
st.plotly_chart(sankey_fig, use_container_width=True) # Render the Plotly figure
