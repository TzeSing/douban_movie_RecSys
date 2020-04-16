package Streaming

import java.sql.{Connection, DriverManager, PreparedStatement}

import org.apache.spark.{SparkConf, SparkContext}
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions.lit
import org.apache.spark.streaming.kafka010.{ConsumerStrategies, KafkaUtils, LocationStrategies}
import org.apache.spark.streaming.{Seconds, StreamingContext}
import org.apache.kafka.common.serialization.StringDeserializer
import CaseClass.MovieRecs

object StreamingRecommend {
  def main(args: Array[String]): Unit = {
    val conf: SparkConf = new SparkConf().setAppName(this.getClass.getName)
      .set("spark.sql.legacy.allowCreatingManagedTableUsingNonemptyLocation", "true")

    val spark: SparkSession = SparkSession.builder()
      .config(conf)
      .enableHiveSupport()
      .getOrCreate()

    import spark.implicits._

    val sc: SparkContext = spark.sparkContext
    val ssc: StreamingContext = new StreamingContext(sc, Seconds(5))

    // sc.setLogLevel("WARN")

    // 把预处理好的movieRecs转为Map，并广播
    val simMovieMatrix: collection.Map[Int, Map[Int, Double]] = spark.read.table("movieRecs")
      .as[MovieRecs]
      .rdd
      .map {
        movieRecs => (movieRecs.mid, movieRecs.recs.map(x => (x.mid, x.score)).toMap)
      }.collectAsMap()
    // 如果没找到，就推荐热门的5部电影，并广播
    val hot5Movies: collection.Map[Int, Double] = spark.sql("select mid from ratings group by mid order by count(mid) desc")
      .limit(5)
      .withColumn("score", lit(5.0))
      .rdd
      .map(x => (x.getInt(0), x.getDouble(1)))
      .collectAsMap()

    val hot5MoviesBroadCast = sc.broadcast(hot5Movies)
    val simMovieMatrixBroadCast = sc.broadcast(simMovieMatrix)

    val topic = "recommend"
    val kafkaParam: Map[String, Object] = Map(
      "bootstrap.servers" -> "master:9092,slave1:9092,slave2:9092",
      "key.deserializer" -> classOf[StringDeserializer],
      "value.deserializer" -> classOf[StringDeserializer],
      "group.id" -> "g1",
      "auto.offset.reset" -> "latest"
    )

    val kafkaStream = KafkaUtils.createDirectStream[String, String](
      ssc,
      LocationStrategies.PreferConsistent,
      ConsumerStrategies.Subscribe[String, String](Array(topic), kafkaParam)
    )

    val ratingStream = kafkaStream.map {
      msg =>
        val attr = msg.value().split(",")
        // uid, mid, score
        (attr(0).replace("\"", "").toInt,
          attr(1).replace("\"", "").toInt,
          attr(2).replace("\"", "").toDouble)
    }

    val MAX_SIM_MOVIES_NUM = 5

    // 实时处理，并写入MySQL
    ratingStream.foreachRDD {
      rdds => {
        var conn: Connection = null
        var ps: PreparedStatement = null
        try {
          Class.forName("com.mysql.jdbc.Driver").newInstance()
          rdds.foreach {
            case (uid, mid, score) => {
              println("rating data coming >>>>>>>>>>>>>>")
              conn = DriverManager.getConnection(
                "jdbc:mysql://49.234.234.234:3306/recommend?useUnicode=true&characterEncoding=utf8",
                "hive",
                "hadoop")
              // 从相似度矩阵取出当前电影最相似的N个电影作为备选列表 Array[mid]
              val candidateMovies = getTopSimMovies(MAX_SIM_MOVIES_NUM, mid, uid,
                simMovieMatrixBroadCast.value, hot5MoviesBroadCast.value)
              // 存到MySQL
              ps = conn.prepareStatement("insert into movieRecs values(?,?,?)")
              ps.setInt(1, uid)
              ps.setInt(2, mid)
              ps.setString(3, candidateMovies.mkString(","))
              ps.executeUpdate()
            }
          }
        } catch {
          case t: Throwable => t.printStackTrace() // TODO: handle error
        } finally {
          if (ps != null) {
            ps.close()
          }
          if (conn != null) {
            conn.close()
          }
        }
      }
    }

    ssc.start()
    println(">>>>>>>>>>>>>>>>>>>>>>>>>>>> streaming start >>>>>>>>>>>>>>>>>>>>>>>>>")
    ssc.awaitTermination()
    spark.stop()
  }

  def getTopSimMovies(num: Int, mid: Int, uid: Int,
                      simMovies: scala.collection.Map[Int, scala.collection.immutable.Map[Int, Double]],
                      hot5Movies: collection.Map[Int, Double]): Array[Int] = {
    // TODO 获取该用户之前评分过的电影，并过滤已评分的
    if (simMovies.contains(mid)) {
      val allSimMovies: Array[(Int, Double)] = simMovies(mid).toArray
      allSimMovies.sortWith(_._2 > _._2)
        .take(num)
        .map(x => x._1)
    } else {
      hot5Movies.toArray.map(x => x._1)
    }
  }

}
