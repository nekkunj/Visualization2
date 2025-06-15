import plotly.graph_objects as go
import plotly.io as pio

import pandas as pd

GRAVITE_TRANSLATION = {
    'Mortel ou grave': 'Fatal or Serious',
    'Léger': 'Minor',
    'Dommages matériels seulement': 'Property Damage Only',
    'Dommages matériels inférieurs au seuil de rapportage': 'Below Reporting Threshold'
}

def get_aggregated_counts(df, region=None, granularity='year', type_col='GRAVITE'):
    if region is not None and 'REG_ADM' in df.columns:
        df = df[df['REG_ADM'] == region]

    df[type_col] = df[type_col].map(GRAVITE_TRANSLATION)

    if granularity == 'year':
        df['time_unit'] = df['AN'].astype(str)
    elif granularity == 'month':
        df['time_unit'] = df['AN'].astype(str) + '-' + df['MS_ACCDN'].astype(str).str.zfill(2)
    elif granularity == 'daytype':
        df['time_unit'] = df['JR_SEMN_ACCDN']
    elif granularity == 'quarter_day':
        df['time_unit'] = df['HR_ACCDN']
    else:
        df['time_unit'] = df['AN'].astype(str)

    grouped = df.groupby(['time_unit', type_col]).size().reset_index(name='count')
    return grouped

def init_figure(title='Accident frequency in Quebec'):
    fig = go.Figure()
    fig.update_layout(
        template=pio.templates['simple_white'],
        dragmode=False,
        barmode='stack',
        title=title,
        xaxis_title='Time',
        yaxis_title='',
        legend_title='Accident type'
    )
    return fig

def draw(fig, data, mode, type_col='GRAVITE', granularity='year', region=None):
    COLOR_PALETTE = {
        'Fatal or Serious': "#8B0000",    # Dark Red (intense, grave)
        'Minor': "#CD5C5C",               # Indian Red (modéré)
        'Property Damage Only': "#FA8072",# Salmon (léger)
        'Below Reporting Threshold': "#F4A6A6"  # Light Red/Pink (très faible)
    }

    ordered_types = ['Fatal or Serious', 'Minor', 'Property Damage Only', 'Below Reporting Threshold']

    fig = go.Figure(fig)
    fig.data = []

    grouped = get_aggregated_counts(data, region=region, granularity=granularity, type_col=type_col)

    if mode == 'percent':
        total_per_time = grouped.groupby('time_unit')['count'].transform('sum')
        grouped['value'] = 100 * grouped['count'] / total_per_time
    else:
        grouped['value'] = grouped['count']

    for t in ordered_types:
        subset = grouped[grouped[type_col] == t]
        if not subset.empty:
            fig.add_bar(
                x=subset['time_unit'],
                y=subset['value'],
                name=t,
                marker_color=COLOR_PALETTE.get(t, '#999999')
            )

    fig.update_layout(
        barmode='stack',
        xaxis_title='Time',
        yaxis_title='Accident Frequency' if mode == 'count' else 'Accidents (%)',
        legend_title='Accident Type'
    )

    return fig