import pandas as pd
from sqlalchemy import create_engine

# ---- CONFIG ----
EXCEL_FILE = "All Drafts Data Compiled.xlsx"
DB_PATH = "sqlite:///PokemonDraftData.db"

# ----------------

engine = create_engine(DB_PATH)

# Load Excel file
xls = pd.ExcelFile(EXCEL_FILE)

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)

    # Normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    table_name = sheet_name.lower().replace(" ", "_")

    df.to_sql(
        table_name,
        engine,
        if_exists="replace",   # use "append" if rerunning later
        index=False
    )

    print(f"Inserted sheet '{sheet_name}' → table '{table_name}'")