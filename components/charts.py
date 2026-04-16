from collections import Counter

import pandas as pd
import streamlit as st


def top_companies_chart(df: pd.DataFrame, n: int) -> None:
    top = df["company"].value_counts().head(n).rename("Job Postings")
    st.bar_chart(top)


def skills_frequency_chart(df: pd.DataFrame, n: int) -> None:
    all_skills = [s for xs in df["skills_norm"] for s in xs]
    counts = Counter(all_skills)
    top = pd.Series(dict(counts.most_common(n)), name="Count")
    st.bar_chart(top)
