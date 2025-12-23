from typing import Dict
from PIL import Image,ImageEnhance
import pytesseract
import pandas as pd
import re
import os

def extract_ocr(ENV_KEYS:Dict[str,str|None]) -> None:
    path=ENV_KEYS.get("IMAGES_PATH")
    orders_data=[]
    files=[file for file in os.listdir(path) if file.lower().startswith("order")]
    files.sort()
    for file in files:
        image=Image.open(f"{path}/{file}")

        enhancer=ImageEnhance.Contrast(image)
        image=enhancer.enhance(1)
        enhancer=ImageEnhance.Sharpness(image)
        image=enhancer.enhance(2)

        text=pytesseract.image_to_string(image,config="--psm 6 -c preserve_interword_spaces=1")

        data=parse_text(text)
        orders_data.append(data)
    
    dataframe=pd.DataFrame(orders_data)
    dataframe.to_csv(f"staging/images/invoices.csv",index=False)

def parse_text(text: str) -> Dict:
    data={}

    order=re.search(r"Ref[:,\.]?\s*([A-Z]+-\d+)",text)
    data["Order_ID"]=order.group(1)
    date=re.search(r"Date[:,\.]?\s*(\d{4}-\d{2}-\d{2})",text)
    data["Date"]=date.group(1)
    client_id=re.search(r"Client ID[:,\.]?\s*([A-Z]\d+)",text)
    data["Customer_ID"]=client_id.group(1)
    client=re.search(r"Nom[:,\.]?\s*([A-Z-a-z]+\s[A-Z-a-z]+)",text)
    data["Full_Name"]=client.group(1)

    for line in text.split("\n"):
        line=line.strip()
        
        if not line or 'Produit' in line or '---' in line or 'Signature' in line:
            continue
        
        if re.search(r'\d+.*\d+.*\d+',line) and not any(keyword in line for keyword in ['Date','Ref','Client ID','Nom']):            
            parts=re.split(r'\s{2,}',line)
            
            if len(parts)>=4:
                data['Product_Name']=parts[0]
                data['Qte']=parts[1]
                data['Unit_Price']=parts[2].replace(' ', '')
                data['Total']=parts[3].replace(' ', '')
            elif len(parts)>0:
                product_match=re.search(r'([A-Za-zÀ-ÿ\s\d]+)\s+(\d+)\s+(\d+)\s+(\d+)',line)
                if product_match:
                    data['Product_Name']=product_match.group(1).strip()
                    data['Qte']=product_match.group(2)
                    data['Unit_Price']=product_match.group(3)
                    data['Total']=product_match.group(4)
    
    return data