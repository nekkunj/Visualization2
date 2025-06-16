# pages/03_Polar_Grave_Surface.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np # Import numpy for np.nan

# --- Data Loading and Preprocessing (Cached for Performance) ---

@st.cache_data
def load_data():
    """
    Loads and preprocesses the accident data for the polar chart.
    This function is cached to prevent re-loading data on every rerun.
    """
    try:
        df = pd.read_csv('assets/data_fusionnee.csv')
        df['MS_ACCDN'] = pd.to_numeric(df['MS_ACCDN'], errors='coerce').astype(int) # Ensure integer type

        def month_to_season(month):
            if month in [1, 2, 3]: return 'Winter'
            elif month in [4, 5, 6]: return 'Spring'
            elif month in [7, 8, 9]: return 'Summer'
            else: return 'Autumn'

        df['SEASON'] = df['MS_ACCDN'].apply(month_to_season)
        # Ensure 'GRAVITE' column exists before applying replace
        if 'GRAVITE' in df.columns:
            df['Severity'] = df['GRAVITE'].apply(lambda x: 'Severe' if x == 'Mortel ou grave' else 'Other')
        else:
            st.error("Column 'GRAVITE' not found in data. Severity classification will be skipped.")
            df['Severity'] = 'Unknown' # Assign a default or handle as needed

        return df
    except FileNotFoundError:
        st.error("Error: 'assets/data_fusionnee.csv' not found. Please ensure the file is in the 'assets' directory.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading data: {e}")
        st.stop()

df = load_data()

# --- Mappings and Constants ---

surface_state_labels = ["Dry", "Wet", "Hydroplaning", "Sand/Gravel", "Melting snow",
                        "Snow", "Compacted snow", "Icy", "Muddy", "Other"]
surface_state_codes = [11, 12, 13, 14, 15, 16, 17, 18, 19, 99]

# Calculate theta values based on the number of surface states for even distribution
theta = [i * (360 / len(surface_state_codes)) for i in range(len(surface_state_codes))]

lighting_colors = {
    1: "#FFD700",  # Gold
    2: "#FFA500",  # Orange
    3: "#1E90FF",  # Dodger Blue
    4: "#2F4F4F"   # Dark Slate Gray
}
lighting_labels = {
    1: "Daylight and clear",
    2: "Daylight and twilight",
    3: "Night and lit road",
    4: "Night and unlit road"
}

# Get unique seasons for the dropdown
seasons = sorted(df['SEASON'].dropna().unique().tolist())

# --- Streamlit Layout ---

st.title("Severe Accidents by Surface Type and Season")
st.subheader("Barpolar Chart")

# Dropdown for season selection (replaces dcc.Dropdown)
selected_season = st.selectbox(
    "Select a Season:",
    options=seasons,
    index=0, # Default to the first season in the list
    key='season-dropdown'
)

# Filter data based on selected season and severe accidents (logic from Dash callback)
# Ensure to use .copy() to prevent SettingWithCopyWarning if further modifications were made
season_df = df[(df['SEASON'] == selected_season) & (df['Severity'] == 'Severe')].copy()

# Create the polar chart
if not season_df.empty:
    fig = go.Figure()
    max_val = 0

    # Group by lighting and surface, then unstack to ensure all combinations are considered
    # and fill NaNs with 0 for consistent plotting.
    # Ensure CD_ECLRM and CD_ETAT_SURFC columns exist before grouping
    if 'CD_ECLRM' in season_df.columns and 'CD_ETAT_SURFC' in season_df.columns:
        grouped_counts = season_df.groupby(['CD_ECLRM', 'CD_ETAT_SURFC']).size().unstack(fill_value=0)
    else:
        st.warning("Missing 'CD_ECLRM' or 'CD_ETAT_SURFC' columns. Cannot generate detailed polar chart.")
        grouped_counts = pd.DataFrame() # Create empty DataFrame to skip loop

    if not grouped_counts.empty:
        for lighting_code, lighting_name in lighting_labels.items():
            if lighting_code in grouped_counts.index: # Check if this lighting type exists in the filtered data
                # Extract counts for the current lighting type, ensuring all surface codes are present
                # and filling missing ones with 0
                counts_for_lighting = grouped_counts.loc[lighting_code].reindex(surface_state_codes, fill_value=0)
                r_vals = counts_for_lighting.values.tolist()
                max_val = max(max_val, max(r_vals))

                hover_texts = []
                for i, (code, label) in enumerate(zip(surface_state_codes, surface_state_labels)):
                    n = r_vals[i]
                    hover_texts.append(
                        f"Season: {selected_season}<br>Surface: {label}<br>Lighting: {lighting_name}<br>Severe accidents: {n}"
                    )

                fig.add_trace(go.Barpolar(
                    r=r_vals,
                    theta=theta,
                    name=lighting_name,
                    marker_color=lighting_colors.get(lighting_code, "#808080"), # Fallback color
                    hoverinfo='text',
                    hovertext=hover_texts
                ))
            else:
                # If a lighting type has no data for the selected season/severity, add a dummy trace
                # so it still appears in the legend but with no visible bars.
                fig.add_trace(go.Barpolar(
                    r=[0] * len(surface_state_codes),
                    theta=theta,
                    name=lighting_name,
                    marker_color=lighting_colors.get(lighting_code, "#808080"),
                    hoverinfo='text',
                    hovertext=[f"No data for {lighting_name} in {selected_season}"] * len(surface_state_codes)
                ))

        fig.update_layout(
            title=f"Polar Bar Chart – Number of Severe Accidents ({selected_season})",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, max_val * 1.05]), # Adjust range based on max value
                angularaxis=dict(
                    tickvals=theta,
                    ticktext=surface_state_labels,
                    rotation=90,
                    direction="clockwise",
                    linecolor="gray",
                    gridcolor="lightgray"
                )
            ),
            template="plotly_white",
            height=800, # Set a fixed height as per original Dash layout
            width=900,  # Set a fixed width as per original Dash layout, adjust for responsiveness with use_container_width
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig, use_container_width=True) # Renders the Plotly figure
    else:
        st.info("No data available to create the polar chart for the selected season and filters.")
else:
    st.info("No severe accident data available for the selected season.")

