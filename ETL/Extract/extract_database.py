from typing import Dict
import mysql.connector
import pandas as pd

def extract_erp(ENV_KEYS:Dict[str,str|None]) -> None:
    try:
        connection=mysql.connector.connect(
            host=ENV_KEYS.get("DB_HOST"),
            database=ENV_KEYS.get("DB_NAME"),
            user=ENV_KEYS.get("DB_USERNAME"),
            password=ENV_KEYS.get("DB_PASSWORD")
        )
        
        dataframe=pd.read_sql("SHOW TABLES",connection)
    
        for column in dataframe.columns:
            for table in dataframe[column]:
                tmp=pd.read_sql(f"SELECT * FROM {table}",connection)
                tmp.to_csv(f"staging/database/{table}.csv",index=False)
        
        connection.close()
    except mysql.connector.Error as e:
        print(f"Error extracting database: {e}")