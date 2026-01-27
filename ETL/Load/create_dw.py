import sqlite3
from pathlib import Path

DB_PATH = Path("techstore_dw.db")

def create_dw_schema() -> None:
    # recreate DB
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    PRAGMA foreign_keys = ON;

    -- =====================
    -- DIMENSIONS
    -- =====================

    CREATE TABLE Dim_Product (
        Product_ID            TEXT PRIMARY KEY,
        Product_Name          TEXT,
        SubCat_Name           TEXT,
        Category_Name         TEXT,
        Unit_Price            REAL,
        Unit_Cost             REAL,
        Score                 REAL,
        Competitor_Unit_Price REAL
    );

    CREATE TABLE Dim_Store (
        Store_ID           INTEGER PRIMARY KEY,
        Store_Name         TEXT,
        City_Name          TEXT,
        Region             TEXT,
        Monthly_Target REAL
    );

    CREATE TABLE Dim_Customer (
        Customer_ID              TEXT PRIMARY KEY,
        Full_Name                TEXT,
        City_Name                TEXT,
        Region                   TEXT,
        Avg_Region_Shipping_Cost REAL
    );

    CREATE TABLE Dim_Date (
        DateKey  INTEGER PRIMARY KEY, -- YYYYMMDD
        Day      INTEGER,
        Month    INTEGER,
        Year     INTEGER,
        DayName  TEXT
    );

    -- =====================
    -- FACT TABLE
    -- =====================

    CREATE TABLE Fact_Sales (
        Trans_ID      INTEGER PRIMARY KEY,
        DateKey       INTEGER NOT NULL,
        Store_ID      INTEGER NOT NULL,
        Product_ID    TEXT NOT NULL,
        Customer_ID   TEXT NOT NULL,

        Quantity      INTEGER,
        Total_Revenue REAL,
        Net_Profit    REAL,
        Marketing_Cost  REAL,

        FOREIGN KEY (DateKey)    REFERENCES Dim_Date(DateKey),
        FOREIGN KEY (Store_ID)   REFERENCES Dim_Store(Store_ID),
        FOREIGN KEY (Product_ID) REFERENCES Dim_Product(Product_ID),
        FOREIGN KEY (Customer_ID) REFERENCES Dim_Customer(Customer_ID)
    );

    -- =====================
    -- INDEXES (performance)
    -- =====================

    CREATE INDEX idx_fact_date     ON Fact_Sales(DateKey);
    CREATE INDEX idx_fact_store    ON Fact_Sales(Store_ID);
    CREATE INDEX idx_fact_product  ON Fact_Sales(Product_ID);
    CREATE INDEX idx_fact_customer ON Fact_Sales(Customer_ID);
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_dw_schema()
    print("✅ Data warehouse schema created (no data loaded).")
