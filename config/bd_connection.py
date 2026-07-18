from pyspark.sql import SparkSession
from config.logging import logger
from typing import Optional
import os
class Database:
    JOB_GROUP_ID = "jdbc_write_job" 
    
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.jdbc = "C:\\spark\\jars\\mssql-jdbc-13.2.1.jre11.jar"
        self.spark: Optional[SparkSession] = None
        self.url: Optional[str] = None
        
        JDBC_DRIVER_CLASS = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
        self.jdbc_properties = {
                "user": self.user,
                "password": self.password,
                "driver": JDBC_DRIVER_CLASS
            } 

        self.df_count = None
        self.last_stage_count = None 
        self.stable_start_time = None 
        self.is_stabilized = False
        
        
        # Environment variables
        os.environ['HADOOP_USER_NAME'] = 'spark' 
        os.environ['SPARK_LOCAL_DIRS'] = 'C:\\SparkTemp'


    def get_connection(self):
        try:
            
            # SparkSession configurations
            self.spark = SparkSession.builder \
            .appName("db_jdbc_connection") \
            .config("spark.driver.extraClassPath", self.jdbc) \
            .config("spark.sql.debug.maxToStringFields", "100")\
            .config("spark.log.redirectToStdout", "true") \
            .config("spark.ui.enabled", "true") \
            .config("spark.executor.memory", "4g") \
            .config("spark.driver.memory", "4g") \
            .config("spark.sql.shuffle.partitions", "16") \
            .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("FATAL")


            # JDBC configurations
            self.url = f"jdbc:sqlserver://{self.host}:1433;databaseName={self.database};trustServerCertificate=true;loginTimeout=8000"
            JDBC_DRIVER_CLASS = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
            
            self.jdbc_properties = {
                "user": self.user,
                "password": self.password,
                "driver": JDBC_DRIVER_CLASS
            } 

            
            return self.spark
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise


    def read(self, table_name: str):
        try:
            if not self.spark:
                raise RuntimeError("Spark session not initialized. Call get_connection() first.") 
            
            if "SELECT" in table_name.upper():
                table_input = f"({table_name}) AS temp"
                return self.spark.read.jdbc(
                    url=self.url,
                    table=table_input,
                    properties=self.jdbc_properties
                )


            return (
                self.spark.read
                .format("jdbc")
                .option("url", self.url)
                .option("dbtable", table_name)
                .option("user", self.user)
                .option("password", self.password)
                .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")
                .option("fetchsize", "100000")
                .option("numPartitions", 15)
                .load()
            )

        except Exception as e:
            logger.error(f"Reading error: {e}")
            raise

    def dispose(self):
        """Encerra a SparkSession."""
        if self.spark:
            self.spark.stop()
            self.spark = None

