import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.patches import Wedge

@st.cache_data
def load_data(query):
    conn = sqlite3.connect("techstore_dw.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def target_achievement_gauge(actual, target):
    value = (actual / target) * 100 if target > 0 else 0
    value = min(value, 100)

    # 🔥 VERY small canvas
    fig, ax = plt.subplots(figsize=(2.2, 1.4))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.axis('equal')
    ax.axis('off')

    # Remove all margins
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    radius = 0.8
    thickness = 0.22

    zones = [
        (0, 50, '#ff4d4d'),
        (50, 80, '#ffa500'),
        (80, 100, '#2ecc71')
    ]

    for start, end, color in zones:
        ax.add_patch(
            Wedge(
                (0, 0),
                radius,
                180 * (1 - end / 100),
                180 * (1 - start / 100),
                width=thickness,
                facecolor=color,
                alpha=0.9
            )
        )

    # Needle
    angle = np.pi * (1 - value / 100)
    ax.plot(
        [0, 0.65 * np.cos(angle)],
        [0, 0.65 * np.sin(angle)],
        color='white',
        linewidth=1.2,
        solid_capstyle='round'
    )
    ax.scatter(0, 0, s=18, color='white', zorder=5)

    # Small value text
    ax.text(
        0, -0.13,
        f"{value:.1f}%",
        ha='center',
        fontsize=9,
        color='white'
    )

    # Hard crop (important)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.2, 1)

    return fig




# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="TechStore BI Dashboard",
    layout="wide"
)

st.title("📊 TechStore Business Intelligence Dashboard")

query = """
SELECT
    d.Day AS day,
    d.Month AS month,
    d.Year AS year,
    s.Store_Name AS store,
    p.Category_Name AS category,
    p.Product_Name AS product,
    f.Total_Revenue AS revenue,
    f.Net_Profit AS net_profit,
    f.Marketing_Cost As marketing_cost,
    p.Score AS sentiment,
    p.Competitor_Unit_Price AS competitor_price,
    p.Unit_Price AS our_price,
    s.Monthly_Target AS target
FROM Fact_Sales f
JOIN Dim_Date d ON f.DateKey = d.DateKey
JOIN Dim_Product p ON f.Product_Id = p.Product_Id
JOIN Dim_Store s ON f.Store_Id = s.Store_Id
"""
df_sales = load_data(query)

df_sales["date"] = pd.to_datetime(
    df_sales[["year", "month", "day"]]
)

# -----------------------------
# SIDEBAR FILTERS (Requirement C)
# -----------------------------

st.sidebar.header("🔎 Filters")

date_range = st.sidebar.date_input(
    "Select date range",
    [df_sales["date"].min(), df_sales["date"].max()]
)

store_filter = st.sidebar.multiselect(
    "Select store(s)",
    df_sales["store"].unique(),
)

category_filter = st.sidebar.multiselect(
    "Select category(ies)",
    df_sales["category"].unique(),
)

if len(date_range) == 2 and date_range[0]:
    start_date = pd.to_datetime(date_range[0])
else:
    start_date = df_sales["date"].min()
if len(date_range) == 2 and date_range[1]:
    end_date = pd.to_datetime(date_range[1])
else:
    end_date = df_sales["date"].max()

# Apply filters
filtered_df = df_sales[
    (df_sales["date"] >= start_date) &
    (df_sales["date"] <= end_date) &
    (df_sales["store"].isin(store_filter or df_sales["store"].unique())) &
    (df_sales["category"].isin(category_filter or df_sales["category"].unique()))
]

# -----------------------------
# REQUIREMENT A – GLOBAL KPIs
# -----------------------------

total_revenue = filtered_df["revenue"].sum()
net_profit = filtered_df["net_profit"].sum()
avg_sentiment = filtered_df["sentiment"].mean()

actual_sales = filtered_df["revenue"].sum()
target_sales = filtered_df["target"].unique().sum()
target_achievement = (actual_sales / target_sales) * 100 if target_sales > 0 else 0

st.subheader("📌 Global KPIs")

col1, col2, col3 = st.columns(3)

col1.metric("💰 Total Revenue", f"{target_sales:,.0f} DZD")
col2.metric("📈 Net Profit", f"{net_profit:,.0f} DZD")
col3.metric("⭐ Avg Sentiment", f"{avg_sentiment:.2f}")

col_kpi, col_gauge, col3, col4 = st.columns(4)

# with col_kpi:
col_kpi.metric("🎯 Target Achievement", f"{target_achievement:.2f}%")

# with col_gauge:
with col_gauge:
    st.pyplot(
        target_achievement_gauge(actual_sales, target_sales),
        use_container_width=False
    )


st.divider()

# -----------------------------
# REQUIREMENT B – ADVANCED ANALYTICS
# -----------------------------

col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots(figsize=(6,4))
    # Example: YTD Revenue
    ytd_df = filtered_df.groupby("month")["revenue"].sum().cumsum()/1e6
    ax1.plot(ytd_df.index, ytd_df.values, color='cyan')
    # Black background styling (see above)
    fig1.patch.set_facecolor('black')
    fig1.autofmt_xdate(rotation=45)
    ax1.set_facecolor('black')
    ax1.tick_params(colors='white')
    ax1.spines['bottom'].set_color('white')
    ax1.spines['left'].set_color('white')
    ax1.spines['top'].set_color('white')
    ax1.spines['right'].set_color('white')
    ax1.yaxis.label.set_color('white')
    ax1.xaxis.label.set_color('white')
    ax1.title.set_color('white')
    ax1.set_title("YTD Revenue Growth in Million DZD")
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots(figsize=(6,4))
    roi_df = filtered_df.groupby("category").agg({"revenue":"sum","marketing_cost":"sum"}).reset_index()
    roi_df["ROI (%)"] = (roi_df["revenue"]-roi_df["marketing_cost"])/roi_df["marketing_cost"]
    ax2.bar(roi_df["category"], roi_df["ROI (%)"], color='orange')
    # Black background styling
    fig2.patch.set_facecolor('black')
    ax2.set_facecolor('black')
    ax2.tick_params(colors='white')
    ax2.spines['bottom'].set_color('white')
    ax2.spines['left'].set_color('white')
    ax2.spines['top'].set_color('white')
    ax2.spines['right'].set_color('white')
    ax2.yaxis.label.set_color('white')
    ax2.xaxis.label.set_color('white')
    ax2.title.set_color('white')
    ax2.set_ylabel("ROI (%)")
    ax2.set_title("Marketing ROI by Category")
    st.pyplot(fig2)

# ---- Top Products per Category ----
st.subheader("🏆 Top Products per Category")

top_products = (
    filtered_df
    .groupby(["category", "product"])["revenue"]
    .sum()
    .reset_index()
    .sort_values(["category", "revenue"], ascending=[True, False])
)

st.dataframe(top_products.groupby("category").head(3), use_container_width=True)

# ---- Price Competitiveness ----
st.subheader("💲 Price Competitiveness vs Competitors")

price_df = (
    filtered_df
    .groupby("product")
    .agg({
        "our_price": "mean",
        "competitor_price": "mean"
    })
    .reset_index()
)

st.dataframe(price_df, use_container_width=True)

st.divider()

# -----------------------------
# CUSTOM KPIs (example)
# -----------------------------

st.subheader("🧠 Custom KPIs")

col1, col2, col3 = st.columns(3)

col1.metric(
    "📦 Avg Revenue per Sale",
    f"{filtered_df['revenue'].mean():,.0f} DZD"
)

col2.metric(
    "🚚 Profit Margin (%)",
    f"{(net_profit / total_revenue * 100) if total_revenue > 0 else 0:.2f}%"
)

col3.metric(
    "🛒 Total Units Sold",
    f"{filtered_df.shape[0]:,}"
)