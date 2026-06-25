import streamlit as st

from lib import load_data, page_layout

st.set_page_config(
    page_title="Unrated Jobs",
    layout="wide",
)

full_df = load_data()

df = full_df[full_df["interest_score"].isna()].copy()

df = df.sort_values(
    ["score"],
    ascending=False,
)

page_layout(
    title="🟡 Unrated Jobs",
    df=df,
    full_df=full_df,
    page_key="unrated_page",
)