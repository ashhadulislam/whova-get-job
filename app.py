import streamlit as st

from lib import backup_restore_ui, load_data

st.set_page_config(
    page_title="Whova Job Explorer",
    layout="wide",
)

st.title("🔎 Whova Job Explorer")

df = load_data()

backup_restore_ui(df)

unrated = df["interest_score"].isna().sum()
high = (df["interest_score"] >= 5).sum()
low = (df["interest_score"] < 5).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total jobs", len(df))
c2.metric("Unrated", unrated)
c3.metric("Interest ≥ 5", high)
c4.metric("Interest < 5", low)

st.info(
    """
    Use the sidebar pages:

    - **Unrated Jobs**: jobs waiting for your interest score
    - **High Interest**: jobs with interest score 5 or above
    - **Low Interest**: jobs with interest score below 5

    Download your CSV backup regularly on Streamlit Community Cloud.
    """
)

preview_cols = [
    "interest_score",
    "score",
    "date",
    "designation",
    "country",
    "city",
    "jobPostNumber",
    "link",
]

st.dataframe(
    df[preview_cols],
    use_container_width=True,
)