import argparse

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import avg, max as spark_max, sum as spark_sum
except ImportError as error:
    raise SystemExit(
        "PySpark is not installed. Install it with: pip install -r requirements-bigdata.txt"
    ) from error


def summarize(input_dir: str) -> None:
    spark = (
        SparkSession.builder.appName("PeopleCountingStorageAnalytics")
        .master("local[*]")
        .getOrCreate()
    )

    try:
        results = spark.read.json(input_dir)
        summary = (
            results.groupBy("camera_id")
            .agg(
                spark_sum("people_count").alias("total_people_detections"),
                avg("people_count").alias("avg_people_per_frame"),
                spark_max("people_count").alias("max_people_in_frame"),
            )
            .orderBy("camera_id")
        )
        summary.show(truncate=False)
    finally:
        spark.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze stored detection results with PySpark.")
    parser.add_argument("--input", default="data/results", help="Input folder containing JSONL partitions.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    summarize(args.input)
