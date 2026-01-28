
from .load_dw import load_dw_data


def load():
    print("LOADING DATA WAREHOUSE")
    # load dimensions + fact
    load_dw_data()
    print("DONE LOADING DATA WAREHOUSE")
