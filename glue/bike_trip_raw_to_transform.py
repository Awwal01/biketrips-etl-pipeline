import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

# @params: [JOB_NAME]
args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "dag_name", "task_id", "correlation_id"]
)

s3_bucket = "emr-bike-trip"  # "airflow-yourname-bucket"

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

logger = glueContext.get_logger()
correlation_id = args["dag_name"] + "." + args["task_id"] + " " + args["correlation_id"]
logger.info("Correlation ID from GLUE job: " + correlation_id)

# @type: DataSource
# @args: [database = "default", table_name = "green", transformation_ctx = "datasource0"]
# @return: datasource0
# @inputs: []
datasource0 = glueContext.create_dynamic_frame.from_catalog(
    database="emr-serverless-word-count",
    table_name="data",
    transformation_ctx="datasource0",
)
logger.info("After create_dynamic_frame.from_catalog: " + correlation_id)
"""
# # @type: ApplyMapping
# # @args: [mapping = [("vendorid", "long", "vendorid", "long"),
        # ("lpep_pickup_datetime", "string", "lpep_pickup_datetime", "string"),
        # ("lpep_dropoff_datetime", "string", "lpep_dropoff_datetime", "string"),
        # ("store_and_fwd_flag", "string", "store_and_fwd_flag", "string"),
        # ("ratecodeid", "long", "ratecodeid", "long"),
        # ("pulocationid", "long", "pulocationid", "long"),
        # ("dolocationid", "long", "dolocationid", "long"),
# ("passenger_count", "long", "passenger_count", "long"),
# ("trip_distance", "double", "trip_distance", "double"),
# ("fare_amount", "double", "fare_amount", "double"),
# ("extra", "double", "extra", "double"),
# ("mta_tax", "double", "mta_tax", "double"),
# ("tip_amount", "double", "tip_amount", "double"),
# ("tolls_amount", "double", "tolls_amount", "double"),
# ("ehail_fee", "string", "ehail_fee", "string"),
# ("improvement_surcharge", "double", "improvement_surcharge", "double"),
# ("total_amount", "double", "total_amount", "double"),
# ("payment_type", "long", "payment_type", "long"),
# ("trip_type", "long", "trip_type", "long")], transformation_ctx = "applymapping1"]
# # @return: applymapping1
# # @inputs: [frame = datasource0]
"""
mapping = [
    ("tripduration", "bigint", "tripduration", "bigint"),
    ("starttime", "string", "starttime", "string"),
    ("stoptime", "string", "stoptime", "string"),
    ("start station id", "bigint", "start_station_id", "bigint"),
    ("start station name", "string", "start_station_name", "string"),
    ("start station latitude", "double", "start_station_latitude", "double"),
    ("start station longitude", "double", "start_station_longitude", "double"),
    ("end station id", "bigint", "end_station_id", "bigint"),
    ("end station name", "string", "end_station_name", "string"),
    ("end station latitude", "double", "end_station_latitude", "double"),
    ("end station longitude", "double", "end_station_longitude", "double"),
    ("bikeid", "bigint", "bikeid", "bigint"),
    ("usertype", "string", "usertype", "string"),
    ("birth year", "bigint", "birth_year", "bigint"),
    ("gender", "bigint", "gender", "bigint"),
]
applymapping1 = ApplyMapping.apply(
    frame=datasource0, mappings=mapping, transformation_ctx="applymapping1"
)
logger.info("After ApplyMapping: " + correlation_id)

# @type: ResolveChoice
# @args: [choice = "make_struct", transformation_ctx = "resolvechoice2"]
# @return: resolvechoice2
# @inputs: [frame = applymapping1]
resolvechoice2 = ResolveChoice.apply(
    frame=applymapping1, choice="make_struct", transformation_ctx="resolvechoice2"
)
logger.info("After ResolveChoice: " + correlation_id)

# @type: DropNullFields
# @args: [transformation_ctx = "dropnullfields3"]
# @return: dropnullfields3
# @inputs: [frame = resolvechoice2]
dropnullfields3 = DropNullFields.apply(
    frame=resolvechoice2, transformation_ctx="dropnullfields3"
)
logger.info("After DropNullFields: " + correlation_id)

# @type: DataSink
# @args: [connection_type = "s3",
# connection_options = {"path": "s3://airflow-yourname-bucket/data/transformed/green"},
# format = "parquet", transformation_ctx = "datasink4"]
# @return: datasink4
# @inputs: [frame = dropnullfields3]
print(" **here line before s3 write, just verifying...\n ")
datasink4 = glueContext.write_dynamic_frame.from_options(
    frame=dropnullfields3,
    connection_type="s3",
    connection_options={"path": f"s3://{s3_bucket}/test/data/transformed/green"},
    format="parquet",
    transformation_ctx="datasink4",
)
logger.info("After write_dynamic_frame.from_options: " + correlation_id)

job.commit()
