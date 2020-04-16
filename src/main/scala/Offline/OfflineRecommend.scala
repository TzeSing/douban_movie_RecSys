package Offline

import org.apache.spark.SparkConf
import org.apache.spark.ml.recommendation.{ALS, ALSModel}
import org.apache.spark.sql.{DataFrame, SaveMode, SparkSession}
import org.apache.spark.rdd.RDD
import org.jblas.FloatMatrix
import scala.collection.mutable

import CaseClass._

/**
 * 训练ALS模型
 */
object OfflineRecommend {
  def main(args: Array[String]): Unit = {
    val conf: SparkConf = new SparkConf().setAppName(this.getClass.getName)
      .set("spark.sql.legacy.allowCreatingManagedTableUsingNonemptyLocation", "true")

    val spark: SparkSession = SparkSession.builder()
      .config(conf)
      .enableHiveSupport()
      .getOrCreate()

    import spark.implicits._

    val ratings: DataFrame = spark.read.table("ratings")
    ratings.cache()

    // Build the recommendation model using ALS on the training data
    val als: ALS = new ALS()
      .setRank(30)
      .setMaxIter(10)
      .setRegParam(0.01)
      .setUserCol("uid")
      .setItemCol("mid")
      .setRatingCol("score")
    val model: ALSModel = als.fit(ratings)

    // 得到用户的推荐列表
    val userRecs: DataFrame = model.recommendForAllUsers(10)
    userRecs.write.mode(SaveMode.Overwrite).saveAsTable("userRecs")

    // 计算电影两两相似度矩阵，得到电影电影相似度列表
    val movieFeatures: RDD[(Int, FloatMatrix)] = model.itemFactors.rdd
      .map(x => (x.getInt(0), x.getAs[mutable.WrappedArray[Float]](1))) // 先把Row转成tuple
      .map {
        case (mid, features) => (mid, features.toArray) // 再把mutable.WrappedArray转Array
      }
      .map {
        case (mid, features) => (mid, new FloatMatrix(features)) // 再把Array[Float]转FloatMatrix
      }

    val movieRecs: DataFrame = movieFeatures.cartesian(movieFeatures)
      .filter {
        case (m1, m2) => m1._1 != m2._1
      }
      .map {
        case (m1, m2) =>
          val simScore = this.cosineSimilarity(m1._2, m2._2)
          (m1._1, (m2._1, simScore))
      }
      .filter(_._2._2 > 0.7) // 过滤出>0.7的电影配对
      .groupByKey()
      .map {
        case (mid, items) => MovieRecs(mid, items.toList.sortWith(_._2 > _._2).map(x => Recommendation(x._1, x._2)))
      }
      .toDF()
    movieRecs.write.mode(SaveMode.Overwrite).saveAsTable("movieRecs")

    spark.stop()
  }

  def cosineSimilarity(vec1: FloatMatrix, vec2: FloatMatrix): Double = {
    vec1.dot(vec2) / (vec1.norm2() * vec2.norm2())
  }
}
