import sys
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType


if __name__ == "__main__":
	if len(sys.argv) != 6:
	    print("""
	    Usage: nyc_aggregations.py <s3_input_path> <s3_output_path> <dag_name> <task_id> <correlation_id>
	    """, file=sys.stderr)
	    sys.exit(-1)
	    
	bike_input_path = sys.argv[1]
	s3_output_path = sys.argv[2]
	dag_task_name = sys.argv[3] + "." + sys.argv[4]
	correlation_id = dag_task_name + " " + sys.argv[5]
	
	# Setting up the Spark Session
	spark = SparkSession\
	        .builder\
	        .appName("BikeData")\
	        .getOrCreate()
	        
	sc = spark.sparkContext
	
	log4jLogger = sc._jvm.org.apache.log4j
	logger = log4jLogger.LogManager.getLogger(dag_task_name)
	logger.info("Spark session started: " + correlation_id)
	
	# Load data for from the S3 path
	print("\n just checking \n", bike_input_path)
	
	#df = spark.read.parquet(bike_input_path)
	df = spark.read.parquet(bike_input_path)
	
	df.printSchema()
	print(df.show(10))
	
	df = spark.read.parquet(bike_input_path)
	df.printSchema()
	
	def distance(lat_p1, lon_p1, lat_p2, lon_p2):
	    return F.acos(
			    	F.sin(F.toRadians(lat_p1)) * 
		    		F.sin(F.toRadians(lat_p2)) + F.cos(F.toRadians(lat_p1)) * 
		    		F.cos(F.toRadians(lat_p2)) * F.cos(F.toRadians(lon_p1) 
		    		- F.toRadians(lon_p2))
	    			) * F.lit(6371.0)
	    
	df = df.withColumn("trip_distance", 
						distance(df.start_station_latitude, df.start_station_longitude, 
								df.end_station_latitude, df.end_station_longitude))
	
	
	# Selet specific columns and exclude missing values
	subset_df = df \
	    .select("starttime", "start_station_name", "tripduration", "trip_distance")
	
	subset_df.printSchema()
	print(subset_df.show(10))
	
	# Parse year and windspeed - scaled backed from the raw data
	wind_date_df = subset_df \
		.withColumnRenamed("tripduration", "trip_duration")\
	    .withColumn("measurement_year", F.year(subset_df.starttime))\
	    .select("start_station_name", "measurement_year", "trip_duration", 
	    		"trip_distance")
	
	wind_date_df.printSchema()
	print(wind_date_df.show(10))
	
	# Find yearly min, avg and max wind speed for each location 
	agg_wind_df = wind_date_df \
	            .groupBy("start_station_name","measurement_year") \
	            .agg(F.min(wind_date_df.trip_duration).alias("min_trip_duration"),\
	                 F.avg(wind_date_df.trip_duration).alias("avg_trip_duration"),\
	                 F.max(wind_date_df.trip_duration).alias("max_trip_duration"),\
	                 F.min(wind_date_df.trip_distance).alias("min_trip_distance"),\
	                 F.avg(wind_date_df.trip_distance).alias("avg_trip_distance"),\
	                 F.max(wind_date_df.trip_distance).alias("max_trip_distance")\
	                )
	
	agg_wind_df.printSchema()
	print(agg_wind_df.show(10))
	
	# Writing the file output to your local S3 bucket
	current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
	agg_wind_df.write.parquet(f"{s3_output_path}/{current_time}/")
	logger.info("Stopping Spark session: " + correlation_id)
	
	spark.stop()