# Plan: Skills-in-Demand Dashboard

## Overview

Streamlit dashboard analyzing 1.3M LinkedIn job postings to surface which skills
are in demand. Hosted on Streamlit Cloud (unlisted — link-only access). Zero cloud
cost: data pulled from Kaggle API at runtime and cached in session.

## Team

| Person | Owns |
|--------|------|
| Leo | Architecture, data loading, deployment, ML integration |
| Mindy | Data processing, EDA, charts |
| Sirui | ML model training, .pkl pipeline |

## Directory Structure

```
skills-dashboard/
├── app.py                        # Entry point, page navigation
├── pages/
│   ├── 01_overview.py            # Top companies chart (skeleton)
│   ├── 02_skills.py              # Skills demand analysis
│   └── 03_model.py               # ML model predictions placeholder
├── data/
│   ├── loader.py                 # Kaggle API download + st.cache_data
│   └── processor.py              # Merge 3 CSVs, clean, feature engineer
├── models/
│   ├── train.py                  # Training script (run locally, output .pkl)
│   └── predict.py                # Load .pkl + run inference
├── components/
│   ├── charts.py                 # Reusable chart functions (matplotlib/seaborn)
│   └── filters.py                # Sidebar filter widgets
├── assets/
│   └── models/                   # Committed .pkl files
├── .streamlit/
│   ├── config.toml               # Theme, layout
│   └── secrets.toml.example      # KAGGLE_USERNAME, KAGGLE_KEY template
├── requirements.txt
└── README.md
```

## Data Sources

Kaggle dataset: `asaniczka/1-3m-linkedin-jobs-and-skills-2024`

Three CSVs:
- `linkedin_job_postings.csv` — job metadata (title, company, location, description)
- `job_skills.csv` — job_link → skill mappings
- `job_industries.csv` — job_link → industry mappings

**Loading strategy** (zero cost):
1. On app start, check if `/tmp/data/merged.parquet` exists
2. If yes, load directly — skip all CSV processing
3. If no, download CSVs via `kaggle.api.dataset_download_files()`, merge + clean, write `merged.parquet`
4. Cache loaded DataFrame with `@st.cache_data` (TTL: 1 session)
5. Kaggle credentials stored in Streamlit Cloud secrets, never committed

**Why parquet**: columnar format reads 5-10x faster than CSV at this scale; preserves
dtypes; `pd.read_parquet()` supports column projection so pages only load what they need.

**Scale**: 1.3M rows is heavy for Streamlit. Default to 200k row sample on load;
provide a toggle for full dataset. Apply sampling before writing parquet to keep file small.

## Pages

### 01_overview.py — skeleton (Mindy)

- Sidebar filters: company, location, date range
- Chart: Top 10 Companies by job count (horizontal bar, seaborn/matplotlib)
- Stub placeholders for future charts

### 02_skills.py (Mindy)

- Top N skills by frequency across all postings
- Skills breakdown by industry or company (filterable)
- Trend over time using `first_seen` / `last_processed_time` if available

### 03_model.py (Sirui + Leo)

- Input: free-text job title or description
- Output: predicted `category` label from loaded `.pkl`
- Displays confusion matrix and classification report on held-out test split
- Placeholder UI until model is finalized

## ML Model

Baseline pipeline (TF-IDF + Logistic Regression):

```python
Pipeline(steps=[
    ("tfidf", TfidfVectorizer(
        lowercase=True, stop_words="english",
        ngram_range=(1, 2), min_df=2, max_df=0.9, max_features=50000,
    )),
    ("clf", LogisticRegression(
        max_iter=2000, class_weight="balanced", solver="saga",
    )),
])
```

Input (`combined_text`): `job_title + job_description + skills`
Target (`category`): **open decision — see below**
Artifact: `assets/models/baseline.pkl` (committed to repo)

### Open Decision: `category` Column

The Kaggle dataset has no native `category` label. Two options:

| Option | Source | Pros | Cons |
|--------|--------|------|------|
| Derive from `industry` | `job_industries.csv` join | Semantically rich | Industries are noisy/inconsistent |
| Derive from `job_type` | `linkedin_job_postings.csv` | Already present | Shallow (Full-time / Contract etc.) |

**Recommendation**: use `industry`, mapped to ~10 coarse buckets
(e.g. Technology, Finance, Healthcare, Education, etc.).
Sirui to finalize and document the mapping in `data/processor.py`.

## Shared Contracts

```python
# data/loader.py
def download_kaggle_data(dest_dir: str) -> None: ...

# data/processor.py
def load_raw_data(sample_n: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: ...
def merge_datasets(
    jobs: pd.DataFrame,
    skills: pd.DataFrame,
    industries: pd.DataFrame,
) -> pd.DataFrame: ...
def build_features(df: pd.DataFrame) -> pd.DataFrame: ...
# adds: combined_text, skills_list, category

def get_merged(parquet_path: str, sample_n: int) -> pd.DataFrame: ...
# checks for parquet → loads it; otherwise runs full pipeline and writes parquet

# components/charts.py
def top_companies_chart(df: pd.DataFrame, n: int) -> None: ...  # st.bar_chart
def skills_frequency_chart(df: pd.DataFrame, n: int) -> None: ...  # st.bar_chart

# models/predict.py
def load_model(path: str) -> Pipeline: ...
def predict_category(model: Pipeline, text: str) -> str: ...
```

## Key Technical Decisions

- **Streamlit unlisted**: not indexed publicly; accessible by link. Set in Streamlit Cloud dashboard under app settings.
- **Kaggle secrets**: `KAGGLE_USERNAME` and `KAGGLE_KEY` stored in Streamlit Cloud secrets. Access via `st.secrets["KAGGLE_USERNAME"]`.
- **No GCP**: all data lives in `/tmp/` during session. No persistence across cold starts — acceptable for demo.
- **`.pkl` in repo**: model expected to be small (<100MB). Committed directly. If it exceeds GitHub's limit, document a manual upload step.
- **Sampling**: default 200k rows for performance; toggle in sidebar for full load.
- **Native Streamlit charts**: use `st.bar_chart`, `st.line_chart`, `st.dataframe` etc. No matplotlib/seaborn unless a chart type is unsupported natively.

## Dependencies

```
streamlit
kaggle
pandas
pyarrow
scikit-learn
joblib
```

## Deployment

1. Push repo to GitHub
2. Connect at share.streamlit.io → New app
3. Add secrets: `KAGGLE_USERNAME`, `KAGGLE_KEY`
4. Set visibility to **Unlisted**
5. Share URL with team

## Verification Checklist

- [ ] `streamlit run app.py` starts locally without errors
- [ ] Kaggle download completes, CSVs appear in `/tmp/data/`
- [ ] Merged DataFrame has non-zero rows
- [ ] Top companies chart renders with real data
- [ ] `.pkl` loads without error, `predict_category()` returns a string
- [ ] Streamlit Cloud deploy succeeds, unlisted URL is accessible

## Out of Scope (for now)

- Auth / login
- Real-time data refresh
- Database or cloud storage
- Additional chart pages beyond skeleton stubs
- Model retraining in-app
- `category` mapping finalized (Sirui's open item)
