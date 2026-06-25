import streamlit as st

from lib import load_data, page_layout

st.set_page_config(
    page_title="High Interest Jobs",
    layout="wide",
)

full_df = load_data()

df = full_df[
    full_df["interest_score"].notna()
    & (full_df["interest_score"] >= 5)
].copy()

page_layout(
    title="🟢 High Interest Jobs",
    df=df,
    full_df=full_df,
    page_key="high_interest_page",
)