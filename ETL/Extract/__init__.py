from typing import Dict
from .extract_database import extract_erp
from .extract_web import extract_scraper
from .extract_images import extract_ocr

def extract(ENV_KEYS:Dict[str,str|None]) -> None:
    # print("EXTRACT DATABASE")
    # extract_erp(ENV_KEYS)
    # print("DONE EXTRACT DATABASE")
    # print("EXTRACT WEBSITE")
    # extract_scraper(ENV_KEYS)
    # print("DONE EXTRACT WEBSITE")
    print("EXTRACT IMAGES")
    extract_ocr(ENV_KEYS)
    print("DONE EXTRACT IMAGES")
