from datetime import date

import duckdb
import streamlit as st

from data.db import PARQUET_S3_PATH, filter_conditions


@st.cache_data
def _filter_options(
    _conn: duckdb.DuckDBPyConnection,
) -> tuple[list[str], list[str], date, date]:
    companies = (
        _conn.execute(
            f"""
            SELECT company FROM read_parquet('{PARQUET_S3_PATH}')
            GROUP BY company ORDER BY COUNT(*) DESC LIMIT 50
            """
        )
        .df()["company"]
        .tolist()
    )
    countries = (
        _conn.execute(
            f"""
            SELECT search_country FROM read_parquet('{PARQUET_S3_PATH}')
            WHERE search_country IS NOT NULL
            GROUP BY search_country ORDER BY COUNT(*) DESC LIMIT 50
            """
        )
        .df()["search_country"]
        .tolist()
    )
    row = _conn.execute(
        f"""
        SELECT MIN(first_seen)::DATE, MAX(first_seen)::DATE
        FROM read_parquet('{PARQUET_S3_PATH}')
        WHERE first_seen IS NOT NULL
        """
    ).fetchone()
    min_date: date = row[0] if row and row[0] else date(2024, 1, 1)
    max_date: date = row[1] if row and row[1] else date.today()
    return companies, countries, min_date, max_date


@st.cache_data
def _posting_count(
    _conn: duckdb.DuckDBPyConnection,
    company: str,
    country: str,
    date_range: tuple[date, date],
) -> int:
    conditions, params = filter_conditions(company, country, date_range)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    row = _conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{PARQUET_S3_PATH}') {where}", params
    ).fetchone()
    return int(row[0]) if row else 0


def sidebar_filters(
    conn: duckdb.DuckDBPyConnection,
) -> tuple[str, str, tuple[date, date]]:
    companies, countries, min_date, max_date = _filter_options(conn)

    st.sidebar.header("Filters")
    selected_company = st.sidebar.selectbox("Company", ["All"] + companies)
    selected_country = st.sidebar.selectbox("Country", ["All"] + countries)
    selected = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        date_range: tuple[date, date] = (selected[0], selected[1])
    else:
        date_range = (min_date, max_date)

    count = _posting_count(conn, selected_company, selected_country, date_range)
    st.sidebar.markdown(f"**{count:,}** postings shown")

    return selected_company, selected_country, date_range
