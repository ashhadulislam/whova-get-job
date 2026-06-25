import streamlit as st

from lib import load_data, page_layout

st.set_page_config(
    page_title="Low Interest Jobs",
    layout="wide",
)

full_df = load_data()

df = full_df[
    full_df["interest_score"].notna()
    & (full_df["interest_score"] < 5)
].copy()

page_layout(
    title="🔴 Low Interest Jobs",
    df=df,
    full_df=full_df,
    page_key="low_interest_page",
)