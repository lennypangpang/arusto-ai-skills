import pandas as pd
import streamlit as st


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    top_companies = ["All"] + df["company"].value_counts().head(50).index.tolist()
    selected_company = st.sidebar.selectbox("Company", top_companies)

    top_locations = ["All"] + df["job_location"].value_counts().head(50).index.tolist()
    selected_location = st.sidebar.selectbox("Location", top_locations)

    mask = pd.Series(True, index=df.index)
    if selected_company != "All":
        mask &= df["company"] == selected_company
    if selected_location != "All":
        mask &= df["job_location"] == selected_location
    filtered = df[mask]

    st.sidebar.markdown(f"**{len(filtered):,}** postings shown")
    return filtered
