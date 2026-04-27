from datetime import date

import altair as alt
import duckdb
import streamlit as st

from data.db import PARQUET_S3_PATH, filter_conditions


def top_companies_chart(
    conn: duckdb.DuckDBPyConnection,
    n: int,
    company: str,
    country: str,
    date_range: tuple[date, date] | None,
) -> None:
    conditions, params = filter_conditions(company, country, date_range)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    df = (
        conn.execute(
            f"""
        SELECT company, COUNT(*) AS "Job Postings"
        FROM read_parquet('{PARQUET_S3_PATH}')
        {where}
        GROUP BY company ORDER BY "Job Postings" DESC LIMIT {n}
        """,
            params,
        )
        .df()
        .set_index("company")
    )
    st.bar_chart(df)


def skills_frequency_chart(conn: duckdb.DuckDBPyConnection, n: int) -> None:
    df = conn.execute(
        f"""
        SELECT skill, COUNT(*) AS "Count"
        FROM (
            SELECT TRIM(UNNEST(string_split(skills_norm, ','))) AS skill
            FROM read_parquet('{PARQUET_S3_PATH}')
            WHERE category IS NOT NULL
        )
        WHERE skill IS NOT NULL AND TRIM(skill) != '' AND LOWER(TRIM(skill)) != 'nan'
        GROUP BY skill ORDER BY "Count" DESC LIMIT {n}
        """,
    ).df()
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("skill:N", sort=None, title="Skill"),
            y=alt.Y("Count:Q", title="Count"),
        )
    )
    st.altair_chart(chart, width="stretch")
