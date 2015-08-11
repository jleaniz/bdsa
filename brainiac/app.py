# import the Flask class from the flask module
from flask import Flask, render_template
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql.types import *
from config import config as conf


# create the application object
app = Flask(__name__)

appConfig = conf.Config()
sc = SparkContext(conf=appConfig.setSparkConf())

# use decorators to link the function to a url
@app.route('/')
def home():
    return "Hello, World!"  # return a string


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

'''
@app.route('/spark')
def spark():
    sc = SparkContext("local[8]", "SparkVolatility", pyFiles=['/home/cloudera/SparkVolatility/parser.py'])
    sqlContext = SQLContext(sc)
    df = sqlContext.load('BlueCoat/accessLog')
    output = []
    sqlContext.registerDataFrameAsTable(df, "accesslog")
    data = sqlContext.sql(
        "SELECT host, count(*) as hits FROM accesslog WHERE action LIKE '%DENIED%' GROUP BY host ORDER BY hits DESC")
    for i in data.take(10):
        output.append(i)
    return render_template('spark.html', output=output)
'''

@app.route('/user/vpn/barChart')
def renderUserVpnBarChart():
    sqlctx = SQLContext(sc)
    df = sqlctx.load('ciscovpn')
    sqlctx.registerDataFrameAsTable(df, 'vpn')
    data = sqlctx.sql(
        "select remoteip, count(*) as hits from vpn where user=%s group by remoteip order by hits" %('"juan.leaniz@ubisoft.com"')
    )
    for i in data.collect():
        return render_template('spark.html', output=i)

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host='mtl-ah374.ubisoft.org')
