import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import pandas as pd
import numpy as np
import re

from scipy.io.arff import loadarff
import matplotlib.pyplot as plt
import pydeck as pdk
import wikipedia


@st.cache()
def load_mammals():
    path_with_files = Path(r"C:\Users\zbenm\Mammals")
    file = "mammals.arff"
    #file = "commonmammals.arff"

    data, _ = loadarff(path_with_files / file)

    df = pd.DataFrame(data)

    columns = df.columns
    r = re.compile('^bio')
    bio_columns = [col for col in columns if r.match(col)]
    r = re.compile('^[A-Z]')
    mammal_columns = [col for col in columns if r.match(col)]
    location_columns = ['latitude', 'longitude']
    monthly_columns = [col for col in columns if
                       col not in set(mammal_columns) | set(bio_columns) | set(location_columns)]

    df['cell_id'] = df.index

    df_grid_cell = df[['cell_id'] + location_columns + bio_columns]

    df_monthly_v1 = df[['cell_id'] + monthly_columns]
    df_monthly_v2 = df_monthly_v1.melt(id_vars=['cell_id'])
    df_monthly_v2[['statistics', 'month']] = pd.DataFrame.from_records(
        df_monthly_v2['variable'].str.split('_').apply(lambda l: ('_'.join(l[:-2]), '_'.join(l[-2:])))
    )
    df_monthly_v3 = df_monthly_v2.pivot(values='value',
                                        index=['cell_id', 'month'],
                                        columns=['statistics']).reset_index()
    
    df_mammals_v1 = df[['cell_id'] + mammal_columns]
    df_mammals_v2 = df_mammals_v1.melt(id_vars='cell_id', var_name='Mammal')
    df_mammals_v2['value'] = df_mammals_v2['value'] == b'1'

    return df_grid_cell, df_monthly_v3, df_mammals_v2


df_grid_cell, df_monthly, df_mammals = load_mammals()


def heatmap_of_varieties():
    how_many_mammals = (
        df_mammals
        .groupby('cell_id')
        .agg(count_animals=('value', 'sum'))
    )
    merged_df = how_many_mammals.merge(df_grid_cell, on='cell_id')[["longitude", "latitude", "count_animals"]]

    view = pdk.data_utils.compute_view(df_grid_cell[["longitude", "latitude"]])
    view.zoom = 3

    COLOR_BREWER_BLUE_SCALE = [
        [240, 249, 232],
        [204, 235, 197],
        [168, 221, 181],
        [123, 204, 196],
        [67, 162, 202],
        [8, 104, 172],
    ]

    mammals_kinds = pdk.Layer(
        "HeatmapLayer",
        data=merged_df,
        opacity=0.9,
        get_position=["longitude", "latitude"],
        aggregation="MEAN",
        color_range=COLOR_BREWER_BLUE_SCALE,
        threshold=1,
        get_weight='count_animals',
        pickable=True,
    )

    r = pdk.Deck(
        layers=[mammals_kinds],
        initial_view_state=view,
        map_provider="mapbox",
    )

    st.write('Heatmap of number of mammal kinds')
    st.write(r, allow_unsafe=True)


heatmap_of_varieties()

selected_mammal = st.selectbox(
    'Select a mammal',
    df_mammals['Mammal'].unique()
)

url = wikipedia.page(selected_mammal).url
components.iframe(url, height=400, scrolling=True)

st.map(df_mammals.loc[lambda d: (d['Mammal'] == selected_mammal) &
                                 d['value']].merge(df_grid_cell, on='cell_id'))
