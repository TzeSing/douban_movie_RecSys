package Offline

import org.apache.spark.SparkConf
import org.apache.spark.ml.evaluation.RegressionEvaluator
import org.apache.spark.ml.recommendation.{ALS, ALSModel}
import org.apache.spark.sql.{DataFrame, SparkSession}

/**
 * 网格搜索超参数
 */
object GridSearch {
  def main(args: Array[String]): Unit = {
    val conf: SparkConf = new SparkConf().setAppName(this.getClass.getName)
      .set("spark.sql.legacy.allowCreatingManagedTableUsingNonemptyLocation", "true")

    val spark: SparkSession = SparkSession.builder()
      .config(conf)
      .enableHiveSupport()
      .getOrCreate()

    val ratings: DataFrame = spark.read.table("ratings")
    ratings.cache()

    val Array(training, test): Array[DataFrame] = ratings.randomSplit(Array(0.8, 0.2))

    val evaluator = new RegressionEvaluator()
      .setMetricName("rmse")
      .setLabelCol("rating")
      .setPredictionCol("prediction")

    val result: Array[(Int, Double, Double)] = for (rank <- Array(10, 20, 30); lambda <- Array(0.001, 0.01, 0.1))
      yield {
        // Build the recommendation model using ALS on the training data
        val als: ALS = new ALS()
          .setRank(rank)
          .setMaxIter(50)
          .setRegParam(lambda)
          .setUserCol("uid")
          .setItemCol("mid")
          .setRatingCol("score")
        val model: ALSModel = als.fit(training)

        // Evaluate the model by computing the RMSE on the test data
        // Note we set cold start strategy to 'drop' to ensure we don't get NaN evaluation metrics
        model.setColdStartStrategy("drop")
        val predictions = model.transform(test)
        val rmse = evaluator.evaluate(predictions)
        (rank, lambda, rmse)
      }
    println(result.minBy(_._3))

    spark.stop()
  }
}
