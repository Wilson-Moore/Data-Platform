from typing import Dict
from .helper_functions import clean_date
from .transform_files import transform_erp

clean_date = clean_date
def transfrom() -> None:
    print("TRANSFROMING ERP")
    transform_erp()
    print("DONE TRANSFROMING ERP")