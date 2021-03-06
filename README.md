## RecSys

目录：

- 在线演示
- 运行环境
    - 硬件
    - 软件
    - 集群(主从架构)
- 实现
    - 离线
    - 实时
    - 热评
- ALS算法原理——矩阵分解



### 在线演示

[tzesing.xyz](tzesing.xyz)

**演示用户名：**

麦克阿瑟

Kala

水木荒

---

### 运行环境

本系统运行在四台云服务器上。

#### 硬件

- 腾讯云master：2核 4GB 3Mbps
- 滴滴云slave1：2核 4GB 1Mbps
- 滴滴云slave2：1核 2GB 1Mbps
- 滴滴云slave3：1核 2GB 1Mbps

#### 软件

- Linux：Ubuntu 18.04
- Hadoop 2.7.7
- flume 1.9.0
- Kafka 0.10.2.0
- Spark 2.4.5
- zookeeper 3.5.7
- MySQL 5.7
- Hive 2.3.6

#### 集群(主从架构)

|           | master          | slave1        | slave2          | slave3                         |
| --------- | --------------- | ------------- | --------------- | ------------------------------ |
| HDFS      | NameNode        | DataNode      | DataNode        | SecondaryNameNode<br/>DataNode |
| YARN      | ResourceManager | NodeManager   | NodeManager     | NodeManager                    |
| Spark     | Master          | Worker        | Worker          | Worker                         |
| Zookeeper | zkServer(pid:2) |               | zkServer(pid:3) | zkServer(pid:4)                |
| Kafka     | broker(bid:0)   | broker(bid:1) |                 | broker(bid:2)                  |
| MySQL     | √               | -             | -               | -                              |

---



### 实现

整体架构如下：

- 展示网站
    - 后端：Flask
    - 前端：Bootstrap、jQuery
- 推荐引擎
    - 离线：Spark ML的ALS
    - 实时：Flume、Kafka、Spark Streaming
    - 热评

#### 离线

离线用的是Spark ML的ALS模型对评分数据进行训练，模型原理是根据矩阵分解的协同过滤算法，训练后分别得出用户隐向量与电影隐向量。

根据当前用户的隐向量与所有未看过的电影的隐向量做内积，得出预估评分，根据预估评分由大到小排序，选出最大的TopN个进行推荐。

![offtime](https://github.com/TzeSing/douban_movie_RecSys/blob/master/pic/offtime.gif?raw=true)



#### 实时

实时部分是flume从MySQL抽取实时的评分数据，flume的Sink接Kafka的producer(为什么接Kafka？因为发布订阅+高容错+offset)，Spark Streaming从Kafka消费数据，并对DStream进行数据处理，计算实时评分数据(uid,mid,score)的mid与其余所有电影的两两相似度内积，排序后得出TopN个最相似的电影进行实时推荐。

![ontime](https://github.com/TzeSing/douban_movie_RecSys/blob/master/pic/realtime.gif?raw=true)



#### 热评

如果遇到的是冷启动问题，新用户实时对某电影评分，但因为没有历史数据导致模型没有该用户的隐向量，就推荐最多人评分过的电影。

---



### ALS算法原理——矩阵分解

UserCF与ItemCF天然的缺陷是——头部效应明显，处理稀疏向量能力弱

为了增加模型泛化能力，提出了矩阵分解，使用更稠密的隐向量表示用户和物品，一定程度上弥补了协同过滤处理稀疏矩阵能力不足的问题

![MF](https://github.com/TzeSing/douban_movie_RecSys/blob/master/pic/MF.png?raw=true)



Spark ALS 模型代码如下

```scala
// Build the recommendation model using ALS on the training data
val als = new ALS()
  .setRank(2)
  .setMaxIter(5)
  .setRegParam(0.01)
  .setUserCol("userId")
  .setItemCol("movieId")
  .setRatingCol("rating")
val model = als.fit(training)
```

 `setRank` 就是上面图中分解成多少维隐向量，即用多少维隐向量来表示一个用户或者一个物品，这里设为2

一个用户的隐向量与一个物品的隐向量的内积就是该用户对该物品的预测评分

这个隐向量维度 k 决定隐向量表达能力的强弱，k 越小包含信息越少，泛化程度高，k 越大包含信息越多，泛化程度会降低 



