package Loader

import org.apache.spark.SparkConf
import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}
import org.apache.spark.sql.types.{DoubleType, IntegerType, StructField, StructType}

/**
 * 从hdfs读取csv并写入Hive
 */
object DataLoader {
  def main(args: Array[String]): Unit = {
    val conf: SparkConf = new SparkConf().setAppName(this.getClass.getName)

    val spark: SparkSession = SparkSession.builder()
      .config(conf)
      .enableHiveSupport()
      .getOrCreate()

    val ratingSchema: StructType = new StructType(Array(
      StructField("uid", IntegerType),
      StructField("mid", IntegerType),
      StructField("score", DoubleType)
    ))

    val ratings: DataFrame = spark.read.format("csv")
      .option("header", "true")
      .schema(ratingSchema)
      .load("/ratings.csv")

    ratings.write.mode(SaveMode.Overwrite).saveAsTable("ratings")

    spark.close()
  }
}
