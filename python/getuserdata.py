import os, json, dotenv, gspread
import pandas as pd
from ext.database import HashDb
from datetime import datetime

dotenv.load_dotenv()

SHEETS_ACC_JSON = json.loads(os.environ.get('SHEETS_ACC_JSON'))
SHEETS_LINK     = os.environ.get('SHEETS_LINK')
HASH_DB         = os.environ.get('HASH_DB')

SHEET  = os.environ.get('SHEET')
OUTPUT = os.environ.get('OUTPUT')

NAME  = os.environ.get('NAME')
PHONE = os.environ.get('PHONE')

print(f"Loading user data")

db = HashDb(HASH_DB)

print("Connected to database")

gc = gspread.service_account_from_dict(SHEETS_ACC_JSON)
sh = gc.open_by_url(SHEETS_LINK)
ws = sh.worksheet(SHEET)

print('Connected to spreadsheet')

df = pd.DataFrame(ws.get_all_records())

print('Loaded dataframe')

for _,row in df.iterrows():
    row[NAME]  = db.get_val(row[NAME])
    row[PHONE] = db.get_val(row[PHONE])

print('Saving output file to xlsx')

df.to_excel(
    OUTPUT.format(
        datetime=datetime.now().strftime('%Y_%m_%d_%H_%M'),
        sheet=SHEET.lower().replace(' ', '_')),
    sheet_name=SHEET
)