# pages/06_Accident_Visualizations.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px # Often useful for simple charts and color scales

# --- Data Loading and Cleaning (Cached for Performance) ---

@st.cache_data
def load_and_clean_data():
    """
    Loads and cleans the accident data for the Accident Visualizations page.
    This function is cached for performance, ensuring data is loaded and
    preprocessed only once.
    """
    try:
        df = pd.read_csv('data_fusionnee.csv')
        # Clean column names by stripping whitespace and removing quotes
        df.columns = df.columns.str.strip().str.replace('"', '').str.replace('\t', '')
        df = df.rename(columns=lambda x: x.strip())

        # Map GRAVITE to desired English labels for consistency
        df['GRAVITE_EN'] = df['GRAVITE'].replace({
            'Dommages matériels seulement': 'Material Damage',
            'Dommages matériels inférieurs au seuil de rapportage': 'Low Damage',
            'Léger': 'Minor',
            'Mortel ou grave': 'Severe'
        })

        # Map JR_SEMN_ACCDN to Weekday/Weekend
        df['JR_SEMN_ACCDN_EN'] = df['JR_SEMN_ACCDN'].replace({
            'SEM': 'Weekday',
            'FDS': 'Weekend'
        })

        # Ensure MS_ACCDN (Month) is numeric
        df['MS_ACCDN'] = pd.to_numeric(df['MS_ACCDN'], errors='coerce').astype("Int64")

        # Clean REG_ADM for heatmap
        if 'REG_ADM' in df.columns:
            df['REG_ADM_CLEAN'] = df['REG_ADM'].str.replace(r"\s*\(\d+\)", "", regex=True)
        else:
            df['REG_ADM_CLEAN'] = df['REG_ADM'] # Or handle missing column as needed


        return df
    except FileNotFoundError:
        st.error("Error: 'assets/data_fusionnee.csv' not found. Please ensure the file is in the 'assets' directory.")
        st.stop() # Stop the app execution if data isn't found
    except Exception as e:
        st.error(f"An error occurred while loading or preprocessing data: {e}")
        st.stop()

# Load data once at the start of the page script
df = load_and_clean_data()

# --- Chart Generation Functions ---

def accidents_by_user_type_chart(df_data, period_type='Day'):
    """
    Creates a bar chart for accidents by user type, filtered by Day or Night.
    period_type: 'Day' or 'Night'
    """
    usager_cols = {
        'IND_AUTO_CAMION_LEGER': 'Light Vehicles',
        'IND_VEH_LOURD': 'Heavy Vehicles',
        'IND_MOTO_CYCLO': 'Motorcycles',
        'IND_VELO': 'Bicycles',
        'IND_PIETON': 'Pedestrians'
    }

    # Create a local copy to avoid modifying the cached DataFrame directly
    df_copy = df_data.copy()

    # Convert 'O'/'N' to 1/0 for user type indicators
    for col in usager_cols.keys():
        if col in df_copy.columns:
            df_copy[col] = df_copy[col].replace({'O': 1, 'N': 0})
        else:
            st.warning(f"Column '{col}' not found in data for user type analysis. Skipping.")
            df_copy[col] = 0 # Ensure column exists with default value


    # Define Day/Night based on HR_ACCDN
    def classify_period_hr(hr_str):
        if pd.isna(hr_str):
            return 'Unknown'
        try:
            # Assuming HR_ACCDN format like '08:00:00-11:59:00' or just 'HH:MM:SS'
            start_hour_str = hr_str.split('-')[0].split(':')[0]
            start_hour = int(start_hour_str)
            if 6 <= start_hour < 20: # Roughly 6 AM to 7:59 PM as Day
                return 'Day'
            else: # Roughly 8 PM to 5:59 AM as Night
                return 'Night'
        except (ValueError, IndexError):
            return 'Unknown'

    if 'HR_ACCDN' in df_copy.columns:
        df_copy['DAY_NIGHT'] = df_copy['HR_ACCDN'].apply(classify_period_hr)
    else:
        st.warning("Column 'HR_ACCDN' not found for Day/Night classification. Setting 'DAY_NIGHT' to 'Unknown'.")
        df_copy['DAY_NIGHT'] = 'Unknown'


    # Filter data for the selected period
    subset = df_copy[df_copy['DAY_NIGHT'] == period_type]

    # Check if subset is empty
    if subset.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"No data available for User Type in {period_type} period",
            xaxis_title="User Type",
            yaxis_title="Number of Accidents"
        )
        return fig

    # Calculate counts for each user type
    # Ensure all usager_cols exist before summing
    existing_usager_cols = [col for col in usager_cols.keys() if col in subset.columns]
    if not existing_usager_cols:
        fig = go.Figure()
        fig.update_layout(
            title="No relevant user type data columns found.",
            xaxis_title="User Type",
            yaxis_title="Number of Accidents"
        )
        return fig

    counts = subset[existing_usager_cols].sum()
    counts.index = [usager_cols[col] for col in counts.index] # Map column names to readable labels
    counts = counts.sort_values(ascending=False)

    fig = go.Figure(go.Bar(
        x=counts.index,
        y=counts.values,
        name=period_type,
        marker_color=px.colors.qualitative.Plotly[0] if period_type == 'Day' else px.colors.qualitative.Plotly[1]
    ))

    fig.update_layout(
        title=f"Number of Accidents by User Type - {period_type}",
        xaxis_title="User Type",
        yaxis_title="Number of Accidents",
        template="plotly_white",
        hovermode="x unified"
    )
    return fig

def accident_severity_month_chart(df_data, period_type='Day'):
    """
    Creates a stacked bar chart for accident severity by month, filtered by Day or Night.
    period_type: 'Day' or 'Night'
    """
    # gravite_map and month_labels are defined globally in load_and_clean_data now
    # Access mapped gravity column 'GRAVITE_EN'

    df_clean = df_data.copy()
    # Ensure 'MS_ACCDN' is numeric (already done in load_and_clean_data, but defensive)
    df_clean['MS_ACCDN'] = pd.to_numeric(df_clean['MS_ACCDN'], errors='coerce').astype("Int64")

    # Define DAY/NIGHT based on HR_ACCDN if not already done.
    # Re-using the logic from the user type chart for consistency.
    def classify_period_severity_hr(hr_str):
        if pd.isna(hr_str):
            return 'Unknown'
        try:
            start_hour_prefix = hr_str.split(':')[0]
            start_hour = int(start_hour_prefix)
            if 6 <= start_hour < 20:
                return 'Day'
            else:
                return 'Night'
        except (ValueError, IndexError):
            return 'Unknown'

    if 'HR_ACCDN' in df_clean.columns:
        df_clean['DAY_NIGHT'] = df_clean['HR_ACCDN'].apply(classify_period_severity_hr)
    else:
        df_clean['DAY_NIGHT'] = 'Unknown' # Fallback if HR_ACCDN is missing

    # Drop rows with NaN in critical columns before grouping
    df_clean = df_clean.dropna(subset=['GRAVITE_EN', 'MS_ACCDN', 'DAY_NIGHT'])

    # Filter data for the selected period
    grouped = df_clean[df_clean['DAY_NIGHT'] == period_type]
    grouped = grouped.groupby(['MS_ACCDN', 'GRAVITE_EN']).size().reset_index(name='Count')

    if grouped.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"No data available for Monthly Severity in {period_type} period",
            xaxis_title="Month",
            yaxis_title="Number of Accidents"
        )
        return fig

    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    severity_order = ["Severe", "Minor", "Material Damage", "Low Damage"] # Use English labels
    color_map = {
        "Severe": "darkred",
        "Minor": "lightgreen",
        "Material Damage": "steelblue",
        "Low Damage": "lightgrey"
    }

    fig = go.Figure()
    for grav in severity_order:
        df_grav = grouped[grouped['GRAVITE_EN'] == grav]
        # Ensure all months are present, fill missing with 0
        # Reindex to get a complete month range (1-12)
        counts = df_grav.set_index('MS_ACCDN').reindex(range(1, 13), fill_value=0)['Count']
        fig.add_trace(go.Bar(
            x=month_labels, # Use month names for x-axis
            y=counts,
            name=grav,
            marker_color=color_map.get(grav, 'gray')
        ))

    fig.update_layout(
        title=f"Monthly Accident Severity ({period_type}time)",
        xaxis_title="Month",
        yaxis_title="Number of Accidents",
        barmode='stack',
        template="plotly_white",
        hoverlabel=dict(
            bgcolor="white",
            font=dict(color="black")
        )
    )
    return fig

def generate_severe_accidents_heatmap_chart(df_data):
    """
    Generates a heatmap of severe accidents by region and month.
    """
    month_map = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    # Filter for severe accidents using the mapped English severity
    # Use REG_ADM_CLEAN for region name
    df_grave = df_data[df_data['GRAVITE_EN'] == 'Severe'].dropna(subset=['REG_ADM_CLEAN', 'MS_ACCDN']).copy()

    # Convert month to numeric and filter valid range
    df_grave['MS_ACCDN'] = pd.to_numeric(df_grave['MS_ACCDN'], errors='coerce').astype('Int64')
    df_grave = df_grave[df_grave['MS_ACCDN'].between(1, 12)]

    if df_grave.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No severe accident data to display for heatmap.",
            xaxis={"visible": False},
            yaxis={"visible": False}
        )
        return fig

    # Pivot table: rows are regions, columns are months
    pivot = df_grave.pivot_table(
        index='REG_ADM_CLEAN',
        columns='MS_ACCDN',
        aggfunc='size',
        fill_value=0
    )

    # Ensure all 12 months (1-12) are present in columns, fill missing with 0
    for m in range(1, 13):
        if m not in pivot.columns:
            pivot[m] = 0
    pivot = pivot[sorted(pivot.columns)] # Reorder months numerically

    x_labels = [month_map[m] for m in pivot.columns] # Month abbreviations for x-axis
    y_labels = pivot.index.tolist() # Region names for y-axis
    z_values = pivot.values # Accident counts

    # Construction of hover text for rich tooltips
    hover_text = [[f"{val} severe accidents in {y_labels[i]} during {x_labels[j]}"
                   for j, val in enumerate(row)] for i, row in enumerate(z_values)]

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        text=hover_text,
        hoverinfo="text", # Show custom hover text
        colorscale='Reds', # Red color scale for severity
        colorbar=dict(title="Accidents")
    ))

    fig.update_layout(
        title="Severe Accidents by Region and Month (Hover for Details)",
        xaxis_title="Month",
        yaxis_title="Administrative Region",
        template="plotly_white",
        height=800 # Set a reasonable height
    )
    return fig

def generate_accident_severity_bar_chart_by_time(df_data, granularity_type='Month'):
    """
    Generates a stacked bar chart for accident severity by month, week type, or hour range.
    granularity_type: 'Month', 'Week Type', or 'Hour Range'
    """
    df_clean = df_data.copy()

    # Drop rows with NaN in critical columns
    df_clean = df_clean.dropna(subset=['GRAVITE_EN', 'MS_ACCDN', 'JR_SEMN_ACCDN_EN', 'HR_ACCDN'])

    # Labels and order for display
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    weektype_order = ['Weekday', 'Weekend']
    hour_order = [
        '00:00:00-03:59:00', '04:00:00-07:59:00',
        '08:00:00-11:59:00', '12:00:00-15:59:00',
        '16:00:00-19:59:00', '20:00:00-23:59:00'
    ]

    severity_order = ["Severe", "Minor", "Material Damage", "Low Damage"]
    color_map = {
        "Severe": "darkred",
        "Minor": "lightgreen",
        "Material Damage": "steelblue",
        "Low Damage": "lightgrey"
    }

    fig = go.Figure()
    title = ""
    x_axis_title = ""
    plot_data = pd.DataFrame()
    x_labels = []
    granularity_col_name = ""

    if granularity_type == 'Month':
        title = "Accident Severity by Month"
        x_axis_title = "Month"
        granularity_col_name = 'MS_ACCDN'
        grouped = df_clean.groupby([granularity_col_name, 'GRAVITE_EN']).size().reset_index(name='Count')
        plot_data = grouped.pivot(index=granularity_col_name, columns='GRAVITE_EN', values='Count').fillna(0)
        plot_data = plot_data.reindex(range(1, 13), fill_value=0) # Ensure all months are present
        x_labels = month_labels
    elif granularity_type == 'Week Type':
        title = "Accident Severity by Week Type"
        x_axis_title = "Day Type"
        granularity_col_name = 'JR_SEMN_ACCDN_EN'
        grouped = df_clean.groupby([granularity_col_name, 'GRAVITE_EN']).size().reset_index(name='Count')
        plot_data = grouped.pivot(index=granularity_col_name, columns='GRAVITE_EN', values='Count').fillna(0)
        plot_data = plot_data.reindex(weektype_order, fill_value=0) # Ensure order
        x_labels = weektype_order
    elif granularity_type == 'Hour Range':
        title = "Accident Severity by Time of Day"
        x_axis_title = "Hour Range"
        granularity_col_name = 'HR_ACCDN' # Use original HR_ACCDN string column
        grouped = df_clean.groupby([granularity_col_name, 'GRAVITE_EN']).size().reset_index(name='Count')
        plot_data = grouped.pivot(index=granularity_col_name, columns='GRAVITE_EN', values='Count').fillna(0)
        plot_data = plot_data.reindex(hour_order, fill_value=0) # Ensure order
        x_labels = hour_order

    if plot_data.empty:
        fig = go.Figure()
        fig.update_layout(title=f"No data for {granularity_type}", xaxis_title=x_axis_title, yaxis_title="Number of Accidents")
        return fig

    # Add traces for all severities based on the selected granularity
    for grav in severity_order:
        y_values = plot_data[grav] if grav in plot_data.columns else [0] * len(x_labels)
        fig.add_trace(go.Bar(
            x=x_labels,
            y=y_values,
            name=grav,
            marker_color=color_map.get(grav, 'gray')
        ))

    fig.update_layout(
        title=title,
        xaxis_title=x_axis_title,
        yaxis_title="Number of Accidents",
        barmode='stack',
        template="plotly_white",
        hoverlabel=dict(
            bgcolor="white",
            font=dict(color="black")
        )
    )
    return fig


# --- Streamlit Layout for Accident Visualizations Page ---

st.title("Accident Visualizations Dashboard")

st.write(
    """
    Explore various visualizations related to road accidents, including user type involvement,
    monthly severity trends, regional heatmaps, and severity breakdown by time.
    """
)

st.markdown("---")

# Use st.tabs to create separate sections for each visualization
tab1, tab2, tab3, tab4 = st.tabs([
    "Accidents by User Type (Day/Night)",
    "Severity by Month (Day/Night)",
    "Severe Accidents Heatmap",
    "Severity by Time Breakdown"
])

with tab1:
    st.subheader("Comparison of User Type Involvement in Day vs Night")
    # Streamlit radio button replaces Plotly updatemenus for interactivity
    period_type_user = st.radio(
        "Select Time Period for User Type Analysis:",
        ('Day', 'Night'),
        key='user_type_period_selector' # Unique key for the widget
    )
    # Generate the figure based on the selected period
    fig_user_type = accidents_by_user_type_chart(df, period_type_user)
    st.plotly_chart(fig_user_type, use_container_width=True)

with tab2:
    st.subheader("Monthly Severity Distribution: Day vs Night")
    # Streamlit radio button replaces Plotly updatemenus for interactivity
    period_type_severity = st.radio(
        "Select Time Period for Monthly Severity Analysis:",
        ('Day', 'Night'),
        key='severity_month_period_selector' # Unique key for the widget
    )
    # Generate the figure based on the selected period
    fig_severity_month = accident_severity_month_chart(df, period_type_severity)
    st.plotly_chart(fig_severity_month, use_container_width=True)

with tab3:
    st.subheader("Severe Accidents by Region and Month")
    # Heatmap is static in terms of its interactivity choices, so no radio button needed here
    fig_heatmap = generate_severe_accidents_heatmap_chart(df)
    st.plotly_chart(fig_heatmap, use_container_width=True)

with tab4:
    st.subheader("Severity Breakdown: Monthly, Weekly, and Hourly Views")
    # Streamlit radio button replaces Plotly updatemenus for interactivity
    granularity_type_bar = st.radio(
        "Select Granularity for Severity Breakdown:",
        ('Month', 'Week Type', 'Hour Range'),
        key='severity_breakdown_granularity_selector' # Unique key for the widget
    )
    # Generate the figure based on the selected granularity
    fig_severity_breakdown = generate_accident_severity_bar_chart_by_time(df, granularity_type_bar)
    st.plotly_chart(fig_severity_breakdown, use_container_width=True)

