#
# This file is part of BDSA (Big Data Security Analytics)
#
# BDSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# BDSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BDSA.  If not, see <http://www.gnu.org/licenses/>.
#
from pyspark.streaming import StreamingContext, StreamingListener
from pyspark.sql import SQLContext, SparkSession
from pyspark.sql.types import Row
from pyspark import SparkContext
from pyspark import StorageLevel
from lib.parser import Parser
from config import config as conf
import logging
import datetime


logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


class batchInfoCollector(StreamingListener):

    def __init__(self):
        super(StreamingListener, self).__init__()
        self.batchInfosCompleted = []
        self.batchInfosStarted = []
        self.batchInfosSubmitted = []

    def onBatchSubmitted(self, batchSubmitted):
        self.batchInfosSubmitted.append(batchSubmitted.batchInfo())


    def onBatchStarted(self, batchStarted):
        self.batchInfosStarted.append(batchStarted.batchInfo())


    def onBatchCompleted(self, batchCompleted):
        self.batchInfosCompleted.append(batchCompleted.batchInfo())
        logger.warning(self.batchInfosCompleted[0].outputOperationInfos[0].endtime())


def getSqlContextInstance():
    if ('sparkSession' not in globals()):
        globals()['sparkSession'] = SparkSession \
        .builder \
        .appName("BDSA v0.1 alpha") \
        .enableHiveSupport() \
        .getOrCreate()
    return globals()['sparkSession']


def parse(line):
    if '-fw' in line:
        return logParser.parseIPTables(line)
    elif '-net-bc' in line:
        return logParser.parseBCAccessLogIter(line)
    else:
        return line


def save(rdd, type):
    spark = getSqlContextInstance()
    if rdd.isEmpty():
        logger.warning('Empty RDD. Skipping.')
    else:
        df = spark.createDataFrame(rdd)
        logger.warning("Saving DataFrame - %s." % (type))
        df.write.saveAsTable('dw_srm.fw', format='parquet', mode='append', partitionBy='date')

def save_fw(rdd):
    save(rdd, 'fw')


def save_proxy(rdd):
    save(rdd, 'proxysg')

def process_fw(time, rdd):
    if not rdd.isEmpty():
        output_rdd = rdd.filter(lambda x: '-fw' in x) \
            .map(parse) \
            .filter(lambda x: isinstance(x, Row))
        return output_rdd


#https://issues.apache.org/jira/browse/PARQUET-222 - Parquet writer memory allocation
def process_proxy(time, rdd):
    output_rdd = rdd.map(lambda x: str(time) + ' ' + x[0]['host'] + ' ' + x[1]) \
        .filter(lambda x: '-net-bc' in x).map(parse) \
        .filter(lambda x: isinstance(x, Row)).repartition(10)
    return output_rdd


'''Main function'''
if __name__ == '__main__':
    appConfig = conf.Config()
    current_ssc_date = datetime.date.today().strftime("%Y%m%d")
    sc = SparkContext(conf=appConfig.setSparkConf())
    ssc = StreamingContext(sc, 30)

    collector = batchInfoCollector()
    ssc.addStreamingListener(collector)
    #batchInfosCompleted = collector.batchInfosCompleted
    #for info in batchInfosCompleted:
        #print info

    logParser = Parser(type='iptables')
    stream = ssc.textFileStream('/data/datalake/dbs/dl_raw_infra.db/syslog_log/dt=%s' % current_ssc_date )
    fwDStream = stream.transform(process_fw)
    fwDStream.foreachRDD(save_fw)
    ssc.start()
    ssc.awaitTermination()

    # At this point, ssc was stopped
