from typing import Dict
import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_scraper(ENV_KEYS:Dict[str,str|None]) -> None:
    base_url=ENV_KEYS.get("WEBSITE")

    all_products=[]
    all_prices=[]

    current_url=base_url

    while current_url:

        try:
            res=requests.get(current_url)
            soup=BeautifulSoup(res.content,"html.parser")


            for tag in soup.find_all(["h5"],class_=["product-name"]):
                all_products.append(tag.text)
            for tag in soup.find_all(["span"],class_=["product-price"]):
                all_prices.append(tag.text)

            next_link=soup.find(["a"],id="next-page-btn")
            
            if next_link and next_link.get("href"):
                current_url="".join([base_url,"/",next_link.get("href")])
            else:
                current_url=None

        except requests.RequestException as e:
            print(f"Error scraping {current_url}: {e}")
            break

    dataframe=pd.DataFrame({
        "Product_Name": all_products,
        "Unit_Price": all_prices
    })
    
    dataframe.to_csv("staging/web/competitor.csv",index=False)