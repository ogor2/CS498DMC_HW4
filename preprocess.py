from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("HW4").getOrCreate()

# reading clean taxi csv into spark
taxi_df = spark.read.csv("taxi_trips_clean.csv", header = True, inferSchema=True)
# creatign new col named fairs per min which converts the secs to mins
taxi_df = taxi_df.withColumn("fare_per_minute", col("fare") / (col("trip_seconds") / 60))
# renaming table to trips
taxi_df.createOrReplaceTempView("trips")

summary = spark.sql("""
    SELECT company,COUNT(*) AS trip_count,ROUND(AVG(fare), 2) AS avg_fare, ROUND(AVG(fare_per_minute), 2) AS avg_fare_per_minute
    FROM trips
    GROUP BY company
    ORDER BY trip_count DESC
""")

summary.write.mode("overwrite").json("processed_data")
spark.stop()
