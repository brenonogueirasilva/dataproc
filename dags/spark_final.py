from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.sql.functions import col, udf, instr, struct, regexp_replace, lit, from_json
from pyspark.sql.types import StructType, StringType, StructField, IntegerType, FloatType
from pyspark.sql.functions import regexp_extract, monotonically_increasing_id, from_unixtime

def main():
    crowdfunding_folder_path = 'gs://projeto-dataproc-breno/crowdfunding/' #'./input/crowdfunding/'
    contacts_folder_path = 'gs://projeto-dataproc-breno/contacts/' #'./input/contacts/'

    category_parquet_folder =  'gs://bucket_teste_conta_nova/category/'         #'./output/category/'
    subcategory_parquet_folder = 'gs://bucket_teste_conta_nova/subcategory/'    #'./output/subcategory/'
    campaign_parquet_folder = 'gs://bucket_teste_conta_nova/campaign/'  #'./output/campaign/'
    contacts_parquet_folder = 'gs://bucket_teste_conta_nova/contacts/'  #'./output/contacts/'

    spark = SparkSession.builder.appName("ETL Pyspark").getOrCreate()
    spark.sparkContext.setLogLevel('INFO')

    df_crowd = spark.read.options(header = True, inferSchema = True).csv(crowdfunding_folder_path)

    #Category
    df_category = df_crowd.withColumn("category", regexp_extract(df_crowd["category & sub-category"], r".+(?=\/)", 0)).select('category').dropDuplicates() \
            .withColumn("category_id", monotonically_increasing_id())
    categorize_udf = udf(lambda x: 'cat' + str(x) , StringType())
    df_category = df_category.withColumn('category_id' , categorize_udf(col('category_id')))
    print('Category Parquet File Writed With Sucess!')
    df_category.write.mode("overwrite").parquet(category_parquet_folder)

    #Subcategory
    df_subcategory = df_crowd.withColumn("subcategory", regexp_extract(df_crowd["category & sub-category"], r"(?<=\/).+", 0)).select('subcategory').dropDuplicates() \
            .withColumn("subcategory_id", monotonically_increasing_id())
    categorize_udf = udf(lambda x: 'subcat' + str(x) , StringType())
    df_subcategory = df_subcategory.withColumn('subcategory_id' , categorize_udf(col('subcategory_id')))
    print('Sub Category Parquet File Writed With Sucess!')
    df_subcategory.write.mode("overwrite").parquet(subcategory_parquet_folder)

    #Campaign
    df_campaign = df_crowd.withColumnRenamed('blurb', 'description') \
            .withColumnRenamed('launched_at', 'launch_date') \
            .withColumnRenamed('deadline', 'end_date') \
            .withColumn("goal", col("goal").cast(FloatType())) \
            .withColumn("pledged", col("pledged").cast(FloatType())) \
            .withColumn("category", regexp_extract(df_crowd["category & sub-category"], r".+(?=\/)", 0)) \
            .withColumn("subcategory", regexp_extract(df_campaign["category & sub-category"], r"(?<=\/).+", 0)) \

    df_campaign = df_campaign.withColumn("launch_date", from_unixtime(df_campaign["launch_date"])) \
            .withColumn("end_date", from_unixtime(df_campaign["end_date"]))
    
    df_campaign = df_campaign.join(df_category, how='left' , on = df_campaign['category'] == df_category['category'])
    df_campaign = df_campaign.join(df_subcategory, how='left' , on = df_campaign['subcategory'] == df_subcategory['subcategory'])
    df_campaign = df_campaign.select(
        "cf_id", 
        "contact_id",
        'company_name',
        'description',
        'goal',
        'pledged',
        'backers_count',
        'country',
        'currency',
        'launch_date',
        'end_date',
        'category_id', 
        'subcategory_id')
    print('Campaign Parquet File Writed With Sucess!')
    df_campaign.write.mode("overwrite").parquet(campaign_parquet_folder)

    #Contacts
    df_contacts = spark.read.options(inferSchema = True).option("delimiter", "|").csv('./folder_download/input/aux_contacts_1.csv' )
    df_contacts = df_contacts.filter(instr(col("_c0"), '"') != 0)
    df_contacts = df_contacts.withColumn("_c0", regexp_replace("_c0", '""', '"')) \
            .withColumn("_c0", regexp_replace("_c0", '"\{', "\{")) \
            .withColumn("_c0", regexp_replace("_c0", '\}"', "\}"))

    schema = StructType([
        StructField("contact_id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True)
    ])

    df_contacts = df_contacts.withColumn("_c0", from_json(lit(df_contacts._c0), schema)) \
            .withColumn("contact_id", col('_c0.contact_id')) \
            .withColumn("name", col('_c0.name')) \
            .withColumn("email", col('_c0.email'))
    df_contacts = df_contacts.withColumn("first_name", regexp_extract(df_contacts['name'], r'.+(?= )', 0)) \
            .withColumn("last_name", regexp_extract(df_contacts['name'], r'(?<= ).+', 0))
    df_contacts = df_contacts.select(col('contact_id'), col('first_name'), col('last_name'), col('email'))
    print('Contacts Parquet File Writed With Sucess!')
    df_contacts.write.mode("overwrite").parquet(contacts_parquet_folder)

    spark.stop()



