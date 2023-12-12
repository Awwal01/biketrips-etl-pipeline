# from os import path
import os
from datetime import timedelta
import airflow
from airflow import DAG

# from airflow.models.baseoperator import chain
from airflow.providers.amazon.aws.operators.emr import (
    EmrServerlessCreateApplicationOperator,
    EmrServerlessStartJobOperator,
    EmrServerlessStopApplicationOperator,
    EmrServerlessDeleteApplicationOperator,
)
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.sensors.emr import EmrServerlessApplicationSensor
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator

# from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
S3_BUCKET_NAME = "emr-bike-trip"  # "<your-bucket-name>"

glue_role_arn = os.getenv("GLUE_ROLE_ARN")  # "<glue-role-arn>"
emr_role_arn = os.getenv("EMR_ROLE_ARN")
entryPoint = f"s3://{S3_BUCKET_NAME}/test/scripts/emr/test_bike_aggregator.py"
dag_name = "data-pipeline"
emr_serverless_job_task_id = "start_emr_serverless_job"
# Unique identifier for the DAG
correlation_id = "{{ run_id }}"
redshift_role_arn = os.getenv("REDSHIFT_IAM_ROLE")


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": airflow.utils.dates.days_ago(1),
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
    "provide_context": True,
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}


dag = DAG(
    dag_name,
    default_args=default_args,
    dagrun_timeout=timedelta(hours=2),
    schedule_interval="0 3 * * *",
)

s3_sensor = S3KeySensor(
    task_id="s3_sensor",
    bucket_name=S3_BUCKET_NAME,
    bucket_key="data/*",
    wildcard_match=True,
    dag=dag,
)


glue_crawler_config = {
    "Name": "bike-trip-crawler",
    "Role": glue_role_arn,
    "DatabaseName": "emr-serverless-word-count",
    "Targets": {"S3Targets": [{"Path": f"{S3_BUCKET_NAME}/data/"}]},
}


glue_crawler = GlueCrawlerOperator(
    task_id="glue_crawler", config=glue_crawler_config, region_name="us-east-1", dag=dag
)


glue_job = GlueJobOperator(
    task_id="glue_job",
    job_name=f"bike_trip_raw_to_transform_{correlation_id}",
    script_location=f"s3://{S3_BUCKET_NAME}/test/scripts/glue/bike_trip_raw_to_transform.py",
    s3_bucket=S3_BUCKET_NAME,
    iam_role_name="AWSGlueServiceRole-bike-trip-1",
    create_job_kwargs={
        "GlueVersion": "4.0",
        "NumberOfWorkers": 2,
        "WorkerType": "G.1X",
    },
    script_args={
        "--dag_name": dag_name,
        "--task_id": "glue_task",
        "--correlation_id": correlation_id,
    },
    dag=dag,
)

SPARK_JOB_DRIVER = {
    "sparkSubmit": {
        "entryPoint": entryPoint,
        # "entryPointArguments":  # <s3_input_path> <s3_output_path>
        # <dag_name> <task_id> <correlation_id>
        "entryPointArguments": [
            f"s3://{S3_BUCKET_NAME}/test/data/transformed/green/",
            f"s3://{S3_BUCKET_NAME}/test/output_dag",
            dag_name,
            emr_serverless_job_task_id,
            correlation_id,
        ],
        "sparkSubmitParameters": "--conf spark.executor.cores=1 --conf spark.executor.memory=4g\
            --conf spark.driver.cores=1 --conf spark.driver.memory=4g\
            --conf spark.executor.instances=1",
    }
}

SPARK_CONFIGURATION_OVERRIDES = {
    "monitoringConfiguration": {
        "s3MonitoringConfiguration": {"logUri": f"s3://{S3_BUCKET_NAME}/logs"}
    }
}

emr_serverless_app = EmrServerlessCreateApplicationOperator(
    task_id="create_emr_serverless_task",
    release_label="emr-6.15.0",
    job_type="SPARK",
    config={"name": "new_application"},
    dag=dag,
)

emr_serverless_app_id = emr_serverless_app.output

wait_for_app_creation = EmrServerlessApplicationSensor(
    task_id="wait_for_app_creation",
    application_id=emr_serverless_app_id,
    target_states={"CREATED", "STARTED"},
    dag=dag,
)

start_job = EmrServerlessStartJobOperator(
    task_id="start_emr_serverless_job",
    application_id=emr_serverless_app_id,
    execution_role_arn=emr_role_arn,
    job_driver=SPARK_JOB_DRIVER,
    configuration_overrides=SPARK_CONFIGURATION_OVERRIDES,
    dag=dag,
)

stop_app = EmrServerlessStopApplicationOperator(
    task_id="stop_application",
    application_id=emr_serverless_app_id,
    force_stop=True,
    dag=dag,
)

stop_app.waiter_check_interval_seconds = 1

delete_app = EmrServerlessDeleteApplicationOperator(
    task_id="delete_application", application_id=emr_serverless_app_id, dag=dag
)

delete_app.waiter_check_interval_seconds = 1

# Optional
# copy_to_redshift = S3ToRedshiftOperator(
#     task_id='copy_to_redshift',
#     schema='public',
#     table='bike_trip',
#     s3_bucket=S3_BUCKET_NAME,
#     s3_key=test/output_dag/2023-11-29-14-41',
#     copy_options=["FORMAT AS PARQUET"],
#     dag=dag,
# )

(
    s3_sensor
    >> glue_crawler
    >> glue_job
    >> emr_serverless_app
    >> wait_for_app_creation
    >> start_job
    >> stop_app
    >> delete_app
)
