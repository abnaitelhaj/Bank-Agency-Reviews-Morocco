# Customer Reviews of Bank Agencies in Morocco

Collect, process, and analyze Google Maps reviews for bank agencies in Morocco to surface sentiment trends, common topics, and branch performance.

## Pipeline

1. **Extract** — Google Places API → raw JSON  
2. **Stage** — flatten reviews to CSV + PostgreSQL staging table  
3. **Clean** — SQL encoding fixes + dbt text normalization / deduplication  
4. **Enrich** — language detection, BERT sentiment, topic classification  
5. **Model** — dbt star schema (`fact_reviews_star`, `dim_branch`, `dim_reviewer`, `dim_date`)  
6. **Orchestrate** — daily Airflow DAG with retries and failure email alerts  
7. **Visualize** — Looker Studio dashboards

## Tech stack

| Stage | Technology |
|---|---|
| Collection | Python, Google Places API |
| Storage | PostgreSQL |
| Transformation | dbt |
| Orchestration | Apache Airflow |
| NLP | BERT (sentiment), zero-shot topics, language detection |
| BI | Looker Studio |

## Project layout

```
data/                 raw JSON + cities list + staging CSV output
scripts/              extract.py, stage.py, enrich.py
sql/                  staging DDL + cleaning SQL
dbt_project/          staging → intermediate → marts (star schema)
airflow/              daily ETL DAG
Projet-DW.docx.pdf    project report
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in API key and database credentials

# optional: re-run extraction (raw sample already under data/raw/)
python scripts/extract.py

# stage into PostgreSQL
python scripts/stage.py

# enrich with language + BERT sentiment + topics
python scripts/enrich.py

# transform
cd dbt_project
cp profiles.yml.example ~/.dbt/profiles.yml   # or merge into existing profiles
dbt deps
dbt run
dbt test
```

## Airflow

1. Point Airflow `dags_folder` to `airflow/` (or copy the DAG there).  
2. Set `PROJECT_ROOT`, `DBT_PROJECT_DIR`, `DBT_PROFILES_DIR`, and `AIRFLOW_EMAIL` in the environment.  
3. Start the webserver and scheduler. The DAG runs daily:

`extract → stage → enrich → dbt run → dbt test`

## Documentation

Project report: [`Projet-DW.docx.pdf`](Projet-DW.docx.pdf)

## Data model

- **Fact:** `fact_reviews_star`  
- **Dimensions:** `dim_branch`, `dim_reviewer`, `dim_date`  

Reviews are analyzed for sentiment (positive / negative / neutral), topic (10 service themes), language, and branch-level satisfaction.
