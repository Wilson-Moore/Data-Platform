from ETL.Extract import extract
from dotenv import dotenv_values

ENV_KEYS=dotenv_values(".env")

extract(ENV_KEYS)