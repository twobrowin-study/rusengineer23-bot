import os, json, dotenv, gspread

import pandas as pd

from ext.database import HashDb

dotenv.load_dotenv()

SHEETS_ACC_JSON = json.loads(os.environ.get('SHEETS_ACC_JSON'))
SHEETS_LINK     = os.environ.get('SHEETS_LINK')
HASH_DB         = os.environ.get('HASH_DB')

USERS      = os.environ.get('USERS')
FROM_FIELD = os.environ.get('FROM_FIELD')
YES        = os.environ.get('YES')

NAME  = os.environ.get('NAME')
PHONE = os.environ.get('PHONE')

print(f"Loading user data by field ${FROM_FIELD}")

db = HashDb(HASH_DB)

print("Connected to database")

gc = gspread.service_account_from_dict(SHEETS_ACC_JSON)
sh = gc.open_by_url(SHEETS_LINK)
ws = sh.worksheet(USERS)

print('Connected to spreadsheet')

df = pd.DataFrame(ws.get_all_records())
df = df.drop(0, axis='index')

print('Loaded dataframe')

df_by_field: pd.DataFrame = df.loc[df[FROM_FIELD] == YES][[NAME, PHONE]]

print("Printing report now...\n")

print(f"{FROM_FIELD}:")

for _,row in df_by_field.iterrows():
    name  = db.get_val(row[NAME])
    phone = db.get_val(row[PHONE])
    print(f"  {name}: {phone}")

print()