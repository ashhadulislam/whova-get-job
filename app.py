import os
import re
import pandas as pd
import streamlit as st

DATA_FILE = "res/whova_more.csv"
SAVE_FILE = "res/whova_more_with_interest.csv"

FILTER_COLS = [
    "jobPostNumber",
    "score",
    "date",
    "designation",
    "country",
    "city",
]

REQUIRED_COLS = [
    "link",
    "jobPostNumber",
    "score",
    "date",
    "designation",
    "country",
    "city",
    "jobPostText",
]


def extract_job_link(text):
    match = re.search(r"https?://\S+", str(text))
    return match.group(0) if match else ""


def load_data():
    if os.path.exists(SAVE_FILE):
        df = pd.read_csv(SAVE_FILE)
    else:
        df = pd.read_csv(DATA_FILE)

    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = ""

    if "interest_score" not in df.columns:
        df["interest_score"] = 10

    if "notes" not in df.columns:
        df["notes"] = ""

    df["interest_score"] = pd.to_numeric(
        df["interest_score"],
        errors="coerce"
    ).fillna(0).astype(int)

    return df


def save_data(df):
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    df.to_csv(SAVE_FILE, index=False)


st.set_page_config(
    page_title="Whova Job Explorer",
    layout="wide"
)

st.title("🔎 Whova Job Explorer")

df = load_data()

st.sidebar.header("Filters")

min_score, max_score = st.sidebar.slider(
    "Suitability score",
    int(df["score"].min()),
    int(df["score"].max()),
    (
        int(df["score"].min()),
        int(df["score"].max()),
    ),
)


countries = sorted(df["country"].dropna().astype(str).unique())
selected_countries = st.sidebar.multiselect(
    "Country",
    countries,
    default=countries,
)

cities = sorted(df["city"].dropna().astype(str).unique())
selected_cities = st.sidebar.multiselect(
    "City",
    cities,
    default=cities,
)

designations = sorted(df["designation"].dropna().astype(str).unique())
selected_designations = st.sidebar.multiselect(
    "Designation",
    designations,
    default=designations,
)

search = st.sidebar.text_input("Search text")

sort_options = [
    "interest_score",
    "score",
    "date",
    "designation",
    "country",
    "city",
    "jobPostNumber",
]

st.sidebar.subheader("Ranking")

sort_interest_first = st.sidebar.checkbox(
    "⭐ Prioritize my interest score",
    value=True
)






filtered = df.copy()


if sort_interest_first:
    filtered = filtered.sort_values(
        ["interest_score", "score"],
        ascending=[False, False]
    )
else:
    filtered = filtered.sort_values(
        ["score"],
        ascending=False
    )



filtered = filtered[
    (filtered["score"] >= min_score)
    & (filtered["score"] <= max_score)
]

filtered = filtered[filtered["country"].astype(str).isin(selected_countries)]
filtered = filtered[filtered["city"].astype(str).isin(selected_cities)]
filtered = filtered[filtered["designation"].astype(str).isin(selected_designations)]

if search.strip():
    s = search.lower()
    filtered = filtered[
        filtered["jobPostText"].astype(str).str.lower().str.contains(s)
        | filtered["designation"].astype(str).str.lower().str.contains(s)
        | filtered["country"].astype(str).str.lower().str.contains(s)
        | filtered["city"].astype(str).str.lower().str.contains(s)
    ]


st.metric("Visible jobs", len(filtered))

st.download_button(
    "⬇️ Download current saved CSV",
    df.to_csv(index=False),
    file_name="whova_more_with_interest.csv",
    mime="text/csv",
)

st.divider()

view_mode = st.radio(
    "View mode",
    ["Cards", "Table"],
    horizontal=True,
)

if view_mode == "Table":
    edited = st.data_editor(
        filtered[
            [
                "interest_score",
                "score",
                "date",
                "designation",
                "country",
                "city",
                "jobPostNumber",
                "link",
                "jobPostText",
                "notes",
            ]
        ],
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "interest_score": st.column_config.NumberColumn(
                "Interest Score",
                min_value=0,
                max_value=10,
                step=1,
            ),
            "link": st.column_config.LinkColumn("Whova Link"),
            "jobPostText": st.column_config.TextColumn(
                "Job Text",
                width="large",
            ),
        },
    )

else:
    for idx, row in filtered.iterrows():

        with st.container(border=True):

            st.subheader(
                f"{row['designation']} — {row['city']}, {row['country']}"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Suitability", row["score"])
            c2.metric("Interest", row["interest_score"])
            c3.write(f"**Date:** {row['date']}")
            c4.write(f"**Post #:** {row['jobPostNumber']}")

            st.link_button(
                "Open Whova Link",
                row["link"],
            )

            extracted_link = extract_job_link(row["jobPostText"])
            if extracted_link:
                st.link_button(
                    "Open Job / Lab Link",
                    extracted_link,
                )

            new_interest = st.slider(
                "Interest score",
                0,
                10,
                int(row["interest_score"]),
                key=f"interest_{idx}",
            )

            new_notes = st.text_area(
                "Notes",
                value=str(row.get("notes", "")),
                key=f"notes_{idx}",
            )

            if (
                new_interest != int(row["interest_score"])
                or new_notes != str(row.get("notes", ""))
            ):
                df.loc[idx, "interest_score"] = new_interest
                df.loc[idx, "notes"] = new_notes
                save_data(df)
                st.success("Saved")

            st.text_area(
                "Copy job text",
                value=row["jobPostText"],
                height=250,
                key=f"text_{idx}",
            )