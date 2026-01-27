import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .helper_functions import (
    handle_neg_values,
    clean_id,
    clean_date,
    usd_to_dzd,
    standarize_names,
    remove_duplicates,
    normalize_number
)

def transform_marketing_expenses() -> None:
    df = pd.read_csv("staging/marketing_expenses.csv")

    # 1) Clean date and prices
    df = clean_date(df, "Date")
    df = normalize_number(df, ["Marketing_Cost_USD"])

    # 2) Add Month column (start of month)
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Month"] = pd.to_datetime(df["Month"], errors="coerce")

    # 5) Negatives -> NULL
    df = handle_neg_values(df, ["Marketing_Cost_USD"])

    # 7) Convert USD -> DZD and rename
    df = usd_to_dzd(df, "Marketing_Cost_USD")  # creates Marketing_Cost_DZD

    # 3) Standardize names
    df = standarize_names(df, ["Category", "Campaign_Type"])

    # 6) Fill NULL with avg of same (Category, Campaign_Type)
    df["Marketing_Cost_DZD"] = df["Marketing_Cost_DZD"].fillna(
        df.groupby(["Category", "Campaign_Type"])["Marketing_Cost_DZD"].transform("mean")
    )

    # 8) Add monthly average marketing for this Category (Month + Category)
    df["Avg_Monthly_Category_Marketing_Cost"] = df.groupby(
        ["Month", "Category"]
    )["Marketing_Cost_DZD"].transform("mean")

    # 9) Remove duplicates
    df = remove_duplicates(df)

    df.to_csv("staging/marketing_expenses.csv", index=False)



def transform_cities() -> None:
    cities = pd.read_csv("staging/table_cities.csv")
    shipping = pd.read_csv("staging/shipping_rates.csv") 

    # average shipping cost per region
    avg_shipping = (
        shipping.groupby("region_name", as_index=False)["shipping_cost"]
        .mean()
        .rename(columns={
            "region_name": "Region",
            "shipping_cost": "Avg_Region_Shipping_Cost"
        })
    )

    # add Avg_Region_Shipping_Cost to cities by Region
    cities = cities.merge(
        avg_shipping,
        on="Region",
        how="left"
    )
    avg_value = cities["Avg_Region_Shipping_Cost"].mean()
    cities["Avg_Region_Shipping_Cost"] = cities["Avg_Region_Shipping_Cost"].fillna(avg_value)

    cities.to_csv("staging/table_cities.csv", index=False)

def transform_monthly_targets() -> None:
    df = pd.read_csv("staging/monthly_targets.csv")

    # 1) Clean Store_ID like: S1, Store_5 -> 1, 5 ...
    df = clean_id(df, "Store_ID")

    # 2) Clean Month (handles "Feb-2023", "Apr-2023", "2023-01-01 00:00:00", etc.)
    df = clean_date(df, "Month")

    # 3) Clean Target_Revenue (remove commas, spaces, etc.)
    df = normalize_number(df, ["Target_Revenue"])

    # 4) Fill null Target_Revenue with the average of the same store
    # (if a store has all NaNs, this will remain NaN)
    df["Target_Revenue"] = df["Target_Revenue"].fillna(
        df.groupby("Store_ID")["Target_Revenue"].transform("mean")
    )
    # 5) Standardize Manager_Name
    df = standarize_names(df, ["Manager_Name"])

    # 6) Remove duplicates
    df = remove_duplicates(df)

    df.to_csv("staging/monthly_targets.csv", index=False)

def transform_subcategories() -> None:
    sub = pd.read_csv("staging/table_subcategories.csv")
    cat = pd.read_csv("staging/table_categories.csv")

    sub = sub.merge(
        cat[["Category_ID", "Category_Name"]],
        on="Category_ID",
        how="left"
    )

    # remove foreign key
    sub.drop(columns=["Category_ID"], inplace=True)

    sub.to_csv("staging/table_subcategories.csv", index=False)

def fix_sales_ids() -> None:
    sales = pd.read_csv("staging/table_sales.csv")
    sales = clean_id(sales, "Trans_ID")
    sales.to_csv("staging/table_sales.csv", index=False)

def add_invoices() -> None:

    sales = pd.read_csv("staging/table_sales.csv")
    invoices = pd.read_csv("staging/invoices.csv")
    products = pd.read_csv("staging/table_products.csv")


    invoices = invoices.merge(
        products[["Product_ID", "Product_Name"]],
        on="Product_Name",
        how="left"
    )


    existing_ids = pd.to_numeric(sales["Trans_ID"], errors="coerce")
    max_id = int(existing_ids.max()) if existing_ids.notna().any() else 0

    new_ids = pd.RangeIndex(start=max_id + 1, stop=max_id + 1 + len(invoices))
    invoices["Trans_ID"] = new_ids.astype(int)

    # safety: ensure no collision (very unlikely, but guaranteed)
    existing_set = set(pd.to_numeric(sales["Trans_ID"], errors="coerce").dropna().astype(int).tolist())
    while invoices["Trans_ID"].isin(existing_set).any():
        max_id += len(invoices)
        invoices["Trans_ID"] = pd.RangeIndex(start=max_id + 1, stop=max_id + 1 + len(invoices)).astype(int)

    # ---- rename / select columns to match sales ----
    invoices = invoices.rename(columns={
        "Qte": "Quantity",
        "Total": "Total_Revenue",
    })

    invoices_sales = invoices[[
        "Trans_ID",
        "Date",
        "Customer_ID",
        "Product_ID",
        "Quantity",
        "Total_Revenue",
    ]]

    # ---- append into sales ----
    sales = pd.concat([sales, invoices_sales], ignore_index=True)

    sales.to_csv("staging/table_sales.csv", index=False)

def transform_products() -> None:
    products = pd.read_csv("staging/table_products.csv")
    subcats = pd.read_csv("staging/table_subcategories.csv")
    competitor = pd.read_csv("staging/competitor.csv")

    products = clean_id(products, "Product_ID")

    # 1) add SubCat_Name + Category_Name
    products = products.merge(
        subcats[["SubCat_ID", "SubCat_Name", "Category_Name"]],
        on="SubCat_ID",
        how="left"
    )

    # 2) remove foreign key
    products.drop(columns=["SubCat_ID"], inplace=True)

    # 3) add competitor price (if exists)
    products = products.merge(
        competitor[["Product_Name", "Unit_Price"]]
            .rename(columns={"Unit_Price": "Competitor_Unit_Price"}),
        on="Product_Name",
        how="left"
    )

    products.to_csv("staging/table_products.csv", index=False)


def transform_customers() -> None:
    customers = pd.read_csv("staging/table_customers.csv")
    cities = pd.read_csv("staging/table_cities.csv")

    customers = clean_id(customers, "Customer_ID")

    customers = customers.merge(
        cities[["City_ID", "City_Name", "Region", "Avg_Region_Shipping_Cost"]],
        on="City_ID",
        how="left"
    )

    # remove foreign key
    customers.drop(columns=["City_ID"], inplace=True)

    customers.to_csv("staging/table_customers.csv", index=False)


def transform_table_stores() -> None:
    stores = pd.read_csv("staging/table_stores.csv")
    cities = pd.read_csv("staging/table_cities.csv")
    targets = pd.read_csv("staging/monthly_targets.csv")

    # ---- add City_Name + Region ----
    stores = stores.merge(
        cities[["City_ID", "City_Name", "Region"]],
        on="City_ID",
        how="left"
    )

    # ---- compute average monthly target per store ----
    targets["Target_Revenue"] = (
        targets["Target_Revenue"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )
    targets["Target_Revenue"] = pd.to_numeric(targets["Target_Revenue"], errors="coerce")

    avg_targets = (
        targets.groupby("Store_ID", as_index=False)["Target_Revenue"]
        .sum()
        .rename(columns={"Target_Revenue": "Monthly_Target"})
    )

    # ---- merge avg target into stores ----
    stores = stores.merge(
        avg_targets,
        on="Store_ID",
        how="left"
    )

    # ---- drop foreign key ----
    stores.drop(columns=["City_ID"], inplace=True)

    stores.to_csv("staging/table_stores.csv", index=False)



def transform_sales() -> None:
    sales = pd.read_csv("staging/table_sales.csv")
    products = pd.read_csv("staging/table_products.csv")
    customers = pd.read_csv("staging/table_customers.csv")
    marketing = pd.read_csv("staging/marketing_expenses.csv", parse_dates=["Month"])

    sales = clean_id(sales, "Customer_ID")
    sales = clean_id(sales, "Product_ID")
    sales = clean_date(sales, "Date")

    # 1) month of the sale
    sales["Month"] = pd.to_datetime(sales["Date"]).dt.to_period("M").dt.to_timestamp()

    # 2) bring category + unit cost into sales
    sales = sales.merge(
        products[["Product_ID", "Unit_Cost", "Category_Name"]],
        on="Product_ID",
        how="left"
    )

    # 3) shipping cost directly from customers
    sales = sales.merge(
        customers[["Customer_ID", "Avg_Region_Shipping_Cost"]],
        on="Customer_ID",
        how="left"
    )
    sales["Shipping_Cost"] = sales["Avg_Region_Shipping_Cost"]

    # 4) marketing monthly by (Month + Category)
    monthly_cat_marketing = marketing[["Month", "Category", "Avg_Monthly_Category_Marketing_Cost"]]

    sales = sales.merge(
        monthly_cat_marketing,
        left_on=["Month", "Category_Name"],
        right_on=["Month", "Category"],
        how="left"
    )

    sales["Marketing_Cost"] = sales["Avg_Monthly_Category_Marketing_Cost"].fillna(0)

    # count of sales rows in same Month+Category
    sales["cat_monthly_sales"] = sales.groupby(["Month", "Category_Name"])["Product_ID"].transform("count")

    # avoid division by zero
    sales["cat_monthly_sales"] = sales["cat_monthly_sales"].replace(0, 1)

    sales["Marketing_Cost"] = sales["Marketing_Cost"] / sales["cat_monthly_sales"]

    # 5) net profit (split marketing fairly)
    sales["Net_Profit"] = (
        sales["Total_Revenue"]
        - (sales["Unit_Cost"] * sales["Quantity"])
        - sales["Shipping_Cost"]
        - sales["Marketing_Cost"]
    )

    sales.drop(columns=["Month", "Category", "Avg_Monthly_Category_Marketing_Cost"], inplace=True, errors="ignore")

    sales.to_csv("staging/table_sales.csv", index=False)



def review_text_to_score() -> None:
    dataframe=pd.read_csv("staging/table_reviews.csv")
    sid_obj=SentimentIntensityAnalyzer()
    
    score=[]
    
    for product in dataframe.groupby("Product_ID"):
        count=0
        sum=0
        for sentence in product[1]["Review_Text"]:
            sentiment_dict=sid_obj.polarity_scores(sentence)
            count+=1
            sum+=sentiment_dict['compound']
        score.append(sum/count)
    
    dataframe=pd.read_csv("staging/table_products.csv")
    dataframe.sort_values(by=["Product_ID"])
    dataframe["Score"]=score

    dataframe.to_csv("staging/table_products.csv",index=False)



def transform_erp() -> None:
    transform_marketing_expenses()
    transform_cities()
    transform_monthly_targets()
    transform_subcategories()
    fix_sales_ids()
    add_invoices()
    transform_products()
    transform_customers()
    transform_table_stores()
    transform_sales()
    review_text_to_score()
