import mysql.connector
import pandas as pd

def extract_erp(host: str,database: str,user: str,password: str) -> None:
    try:
        connection=mysql.connector.connect(host=host,database=database,user=user,password=password)
        
        dataframe=pd.read_sql("SHOW TABLES",connection)
    
        for column in dataframe.columns:
            for table in dataframe[column]:
                tmp=pd.read_sql(f"SELECT * FROM {table}",connection)
                tmp.to_csv(f"staging/{table}.csv",index=False)
        
        connection.close()
    except mysql.connector.Error as e:
        print(f"Error extracting database: {e}")