"""Daily Airflow DAG for the bank agency reviews pipeline."""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
DBT_PROJECT_DIR = os.getenv("DBT_PROJECT_DIR", str(PROJECT_ROOT / "dbt_project"))
DBT_PROFILES_DIR = os.getenv("DBT_PROFILES_DIR", str(Path.home() / ".dbt"))
ALERT_EMAIL = os.getenv("AIRFLOW_EMAIL", "alerts@example.com")


def run_script(script_name: str):
    script_path = PROJECT_ROOT / "scripts" / script_name
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {process.returncode}")


def extract_task():
    run_script("extract.py")


def stage_task():
    run_script("stage.py")


def enrich_task():
    run_script("enrich.py")


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email": [ALERT_EMAIL],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="bank_agency_reviews_etl",
    default_args=default_args,
    description="Extract, stage, enrich, and transform bank agency reviews",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["bank_reviews", "etl"],
) as dag:

    extract = PythonOperator(task_id="extract", python_callable=extract_task)
    stage = PythonOperator(task_id="stage", python_callable=stage_task)
    enrich = PythonOperator(task_id="enrich", python_callable=enrich_task)

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd '{DBT_PROJECT_DIR}' && dbt deps && dbt run",
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR},
        append_env=True,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd '{DBT_PROJECT_DIR}' && dbt test",
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR},
        append_env=True,
    )

    extract >> stage >> enrich >> dbt_run >> dbt_test
