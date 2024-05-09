from airflow import models
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateBatchOperator,
    DataprocDeleteBatchOperator,
    DataprocGetBatchOperator,
    DataprocListBatchesOperator,
)

with models.DAG(
    'Data_Proc',
    schedule_interval=None,
    start_date = days_ago(2),
    catchup=False,
) as dag_serverless_batch:
    create_batch = DataprocCreateBatchOperator(
        task_id="CREATE_BATCH",
        project_id="enduring-branch-413218",
        region="us-central1",
        batch_id='script-spark-airflow-10',
        batch={
                "pyspark_batch": {
                    "main_python_file_uri": "gs://dags-airflow-breno/scripts/spark.py"
                }
            }
            )
    create_batch