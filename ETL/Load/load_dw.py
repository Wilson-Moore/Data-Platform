# load_db.py
import sqlite3
import pandas as pd
from pathlib import Path
from .create_dw import create_dw_schema

DB_PATH = Path("techstore_dw.db")

STAGING = Path("staging")
PRODUCTS_CSV   = STAGING / "table_products.csv"
STORES_CSV     = STAGING / "table_stores.csv"
CUSTOMERS_CSV  = STAGING / "table_customers.csv"
SALES_CSV      = STAGING / "table_sales.csv"


def load_dw_data() -> None:
    # 1) create DB if not exists
    if not DB_PATH.exists():
        create_dw_schema()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # 2) read staging
    products  = pd.read_csv(PRODUCTS_CSV)
    stores    = pd.read_csv(STORES_CSV)
    customers = pd.read_csv(CUSTOMERS_CSV)
    sales     = pd.read_csv(SALES_CSV)

    # 3) build Dim_Date from sales Date
    sales["Date"] = pd.to_datetime(sales["Date"], errors="coerce", format="mixed")
    dates = pd.Series(sales["Date"].dropna().dt.normalize().unique(), name="Date")
    dim_date = pd.DataFrame({"Date": dates})
    dim_date["DateKey"] = dim_date["Date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["Day"] = dim_date["Date"].dt.day
    dim_date["Month"] = dim_date["Date"].dt.month
    dim_date["Year"] = dim_date["Date"].dt.year
    dim_date["DayName"] = dim_date["Date"].dt.strftime("%A")
    dim_date = dim_date.drop(columns=["Date"])

    sales["DateKey"] = sales["Date"].dt.strftime("%Y%m%d").astype("Int64")

    # 4) clear old rows
    cur.executescript("""
        DELETE FROM Fact_Sales;
        DELETE FROM Dim_Date;
        DELETE FROM Dim_Customer;
        DELETE FROM Dim_Store;
        DELETE FROM Dim_Product;
    """)

    conn.commit()

    # 5) load dimensions
    prod_cols = ["Product_ID","Product_Name","SubCat_Name","Category_Name",
                 "Unit_Price","Unit_Cost","Score","Competitor_Unit_Price"]
    products[[c for c in prod_cols if c in products.columns]].to_sql(
        "Dim_Product", conn, if_exists="append", index=False
    )

    store_cols = ["Store_ID","Store_Name","City_Name","Region","Avg_Monthly_Target"]
    stores[[c for c in store_cols if c in stores.columns]].to_sql(
        "Dim_Store", conn, if_exists="append", index=False
    )

    cust_cols = ["Customer_ID","Full_Name","City_Name","Region","Avg_Region_Shipping_Cost"]
    customers[[c for c in cust_cols if c in customers.columns]].to_sql(
        "Dim_Customer", conn, if_exists="append", index=False
    )

    dim_date.to_sql("Dim_Date", conn, if_exists="append", index=False)

    # 6) load fact
    fact_cols = ["Trans_ID","DateKey","Store_ID","Product_ID","Customer_ID",
                 "Quantity","Total_Revenue","Net_Profit", "Marketing_Cost"]
    fact = sales[[c for c in fact_cols if c in sales.columns]].copy()
    fact = fact.dropna(subset=["Trans_ID","DateKey","Store_ID","Product_ID","Customer_ID"])
    fact["DateKey"] = fact["DateKey"].astype(int)

    fact.to_sql("Fact_Sales", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    load_dw_data()
    print("✅ DW loaded into techstore_dw.db")
