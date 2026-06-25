import math
import os
import re

import pandas as pd
import streamlit as st

DATA_FILE = "res/whova_more.csv"
SAVE_FILE = "res/whova_more_with_interest.csv"

PAGE_SIZE = 20

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

TEXT_COLS = [
    "link",
    "date",
    "designation",
    "country",
    "city",
    "jobPostText",
    "notes",
]


def extract_job_link(text):
    match = re.search(r"https?://\S+", str(text))
    return match.group(0) if match else ""


@st.cache_data(show_spinner=False)
def read_csv_cached(path):
    return pd.read_csv(path)


def normalize_df(df):
    df = df.copy()

    for col in REQUIRED_COLS:
        if col not in df.columns:
            df[col] = ""

    if "interest_score" not in df.columns:
        df["interest_score"] = pd.NA

    if "notes" not in df.columns:
        df["notes"] = ""

    for col in TEXT_COLS:
        df[col] = df[col].fillna("").astype(str)

    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)

    df["jobPostNumber"] = (
        pd.to_numeric(df["jobPostNumber"], errors="coerce")
        .fillna(-1)
        .astype(int)
    )

    df["interest_score"] = pd.to_numeric(
        df["interest_score"],
        errors="coerce",
    )

    return df


def load_data():
    if os.path.exists(SAVE_FILE):
        df = read_csv_cached(SAVE_FILE)
    else:
        df = read_csv_cached(DATA_FILE)

    return normalize_df(df)


def save_data(df):
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    normalize_df(df).to_csv(SAVE_FILE, index=False)
    st.cache_data.clear()


def restore_uploaded_csv(uploaded_file):
    restored_df = pd.read_csv(uploaded_file)
    save_data(restored_df)


@st.cache_data(show_spinner=False)
def filter_jobs_cached(
    df,
    min_score,
    max_score,
    selected_countries,
    selected_cities,
    selected_designations,
    search,
):
    filtered = df.copy()

    filtered = filtered[
        (filtered["score"] >= min_score)
        & (filtered["score"] <= max_score)
    ]

    filtered = filtered[filtered["country"].isin(selected_countries)]
    filtered = filtered[filtered["city"].isin(selected_cities)]
    filtered = filtered[filtered["designation"].isin(selected_designations)]

    if search.strip():
        s = search.lower()

        filtered = filtered[
            filtered["jobPostText"].str.lower().str.contains(s, na=False)
            | filtered["designation"].str.lower().str.contains(s, na=False)
            | filtered["country"].str.lower().str.contains(s, na=False)
            | filtered["city"].str.lower().str.contains(s, na=False)
        ]

    return filtered


@st.cache_data(show_spinner=False)
def sort_jobs_cached(df, sort_mode):
    if df.empty:
        return df

    if sort_mode == "Interest then suitability":
        return df.sort_values(
            ["interest_score", "score"],
            ascending=[False, False],
            na_position="last",
        )

    if sort_mode == "Suitability only":
        return df.sort_values(
            ["score"],
            ascending=False,
        )

    if sort_mode == "Newest first":
        return df.sort_values(
            ["date", "score"],
            ascending=[False, False],
            na_position="last",
        )

    return df.sort_values(
        ["score"],
        ascending=False,
    )


def backup_restore_ui(df):
    st.sidebar.subheader("Backup / Restore")

    uploaded_file = st.sidebar.file_uploader(
        "Restore saved CSV",
        type=["csv"],
    )

    if uploaded_file is not None:
        restore_uploaded_csv(uploaded_file)
        st.sidebar.success("Restored successfully")
        st.rerun()

    st.sidebar.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="whova_more_with_interest.csv",
        mime="text/csv",
    )


def apply_sidebar_filters(df):
    if df.empty:
        return df.copy()

    st.sidebar.header("Filters")

    score_min = int(df["score"].min())
    score_max = int(df["score"].max())

    if score_min == score_max:
        min_score = max_score = score_min
        st.sidebar.caption(f"Suitability score: {score_min}")
    else:
        min_score, max_score = st.sidebar.slider(
            "Suitability score",
            score_min,
            score_max,
            (score_min, score_max),
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

    return filter_jobs_cached(
        df,
        min_score,
        max_score,
        tuple(selected_countries),
        tuple(selected_cities),
        tuple(selected_designations),
        search,
    )


def pagination_ui(total_rows, page_key, location="top"):
    total_pages = max(1, math.ceil(total_rows / PAGE_SIZE))

    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    st.session_state[page_key] = max(
        1,
        min(st.session_state[page_key], total_pages),
    )

    c1, c2, c3 = st.columns([1, 2, 1])


    with c1:
        if st.button(
            "⬅ Previous",
            key=f"{page_key}_{location}_prev",
            disabled=st.session_state[page_key] <= 1,
        ):
            st.session_state[page_key] -= 1
            st.rerun()



    with c2:
        st.markdown(
            f"<div style='text-align:center;'>Page "
            f"{st.session_state[page_key]} / {total_pages}</div>",
            unsafe_allow_html=True,
        )

    with c3:
        if st.button(
            "Next ➡",
            key=f"{page_key}_{location}_next",
            disabled=st.session_state[page_key] >= total_pages,
        ):
            st.session_state[page_key] += 1
            st.rerun()


    start = (st.session_state[page_key] - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    return start, end


def render_table(df):
    show_cols = [
        "interest_score",
        "score",
        "date",
        "designation",
        "country",
        "city",
        "jobPostNumber",
        "link",
        "notes",
        "jobPostText",
    ]

    existing_cols = [c for c in show_cols if c in df.columns]

    st.dataframe(
        df[existing_cols],
        width='content'
    )


def interest_display(value):
    if pd.isna(value):
        return "Blank"
    return str(int(value))


def interest_select_index(value, options):
    if pd.isna(value):
        return 0

    value = int(value)

    if value in options:
        return options.index(value)

    return 0


def render_job_cards(page_df, full_df):
    interest_options = [""] + list(range(1, 11))

    for idx, row in page_df.iterrows():
        title = (
            f"{row['designation']} | "
            f"{row['city']}, {row['country']} | "
            f"AI score: {row['score']} | "
            f"Interest: {interest_display(row['interest_score'])}"
        )

        with st.expander(title, expanded=False):
            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Suitability", row["score"])
            c2.metric("Interest", interest_display(row["interest_score"]))
            c3.write(f"**Date:** {row['date']}")
            c4.write(f"**Post #:** {row['jobPostNumber']}")

            link_col1, link_col2 = st.columns(2)

            with link_col1:
                if str(row["link"]).strip():
                    st.link_button("Open Whova Link", row["link"])

            extracted_link = extract_job_link(row["jobPostText"])

            with link_col2:
                if extracted_link:
                    st.link_button("Open Job / Lab Link", extracted_link)

            with st.form(f"job_form_{idx}"):
                new_interest = st.selectbox(
                    "Interest score",
                    interest_options,
                    index=interest_select_index(
                        row["interest_score"],
                        interest_options,
                    ),
                    key=f"interest_{idx}",
                )

                new_notes = st.text_area(
                    "Notes",
                    value=str(row.get("notes", "")),
                    key=f"notes_{idx}",
                    height=100,
                )

                st.text_area(
                    "Copy job text",
                    value=row["jobPostText"],
                    height=240,
                    disabled=True,
                    key=f"text_{idx}",
                )

                submitted = st.form_submit_button("💾 Save")

                if submitted:
                    if new_interest == "":
                        full_df.loc[idx, "interest_score"] = pd.NA
                    else:
                        full_df.loc[idx, "interest_score"] = int(new_interest)

                    full_df.loc[idx, "notes"] = (
                        "" if pd.isna(new_notes) else str(new_notes)
                    )

                    save_data(full_df)

                    st.success("Saved")
                    st.rerun()


def page_layout(title, df, full_df, page_key):
    st.title(title)

    backup_restore_ui(full_df)

    if df.empty:
        st.info("No jobs in this category yet.")
        return

    filtered = apply_sidebar_filters(df)

    sort_mode = st.sidebar.selectbox(
        "Sort",
        [
            "Interest then suitability",
            "Suitability only",
            "Newest first",
        ],
    )

    filtered = sort_jobs_cached(filtered, sort_mode)

    st.metric("Visible jobs", len(filtered))

    view_mode = st.radio(
        "View mode",
        ["Cards", "Table"],
        horizontal=True,
    )

    if filtered.empty:
        st.info("No jobs match the current filters.")
        return

    st.divider()

    if view_mode == "Table":
        render_table(filtered)
        return

    start, end = pagination_ui(len(filtered), page_key,location="top",)
    page_df = filtered.iloc[start:end]

    st.caption(f"Showing jobs {start + 1}–{min(end, len(filtered))} of {len(filtered)}")

    render_job_cards(page_df, full_df)

    st.divider()
    pagination_ui(len(filtered), page_key,location="bottom",)