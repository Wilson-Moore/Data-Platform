import pandas as pd
from pathlib import Path

def extract_locale() -> None:
    input_folder = Path("./data")
    output_folder = Path("./staging")

    output_folder.mkdir(parents=True, exist_ok=True)

    files = [
        "marketing_expenses.xlsx",
        "monthly_targets.xlsx",
        "shipping_rates.xlsx"
    ]

    for file_name in files:
        file_path = input_folder / file_name

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue

        try:
            df = pd.read_excel(file_path)
            out_name = file_name.replace(".xlsx", ".csv")
            out_path = output_folder / out_name

            df.to_csv(out_path, index=False)

        except Exception as e:
            print(f"❌ Error extracting {file_name}: {e}")
