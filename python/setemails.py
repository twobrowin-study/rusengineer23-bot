import os, json, dotenv, gspread
import pandas as pd
from ext.database import HashDb
from datetime import datetime

dotenv.load_dotenv()

SHEETS_ACC_JSON = json.loads(os.environ.get('SHEETS_ACC_JSON'))
SHEETS_LINK     = os.environ.get('SHEETS_LINK')
HASH_DB         = os.environ.get('HASH_DB')

SHEET = os.environ.get('SHEET')

NAME_COLUMN = os.environ.get('NAME_COLUMN')
MAIL_COLUMN = os.environ.get('MAIL_COLUMN')

NAME_SHEET_COLUMN = os.environ.get('NAME_SHEET_COLUMN')
MAIL_SHEET_COLUMN = os.environ.get('MAIL_SHEET_COLUMN')

MAIL_INPUT_FILE = os.environ.get('MAIL_INPUT_FILE')

MAIL_ACCREDITATION_STATUS = os.environ.get('MAIL_ACCREDITATION_STATUS')

print(f"Loading user data")

db = HashDb(HASH_DB)

print("Connected to database")

gc = gspread.service_account_from_dict(SHEETS_ACC_JSON)
sh = gc.open_by_url(SHEETS_LINK)

print('Connected to spreadsheet')

users_ws = sh.worksheet(SHEET)
users_df = pd.DataFrame(users_ws.get_all_records())
users_df = users_df.drop(0, axis='index')

print('Loaded users dataframe')

email_df = pd.read_excel(MAIL_INPUT_FILE)

print('Loaded email file dataframe')

avaliable_users = users_df.loc[users_df.accreditation_status == MAIL_ACCREDITATION_STATUS]

update_vals = []
for idx,row in email_df.iterrows():
    user = avaliable_users.iloc[idx]
    user[NAME_COLUMN] = db.add_val(row[NAME_COLUMN])
    user[MAIL_COLUMN] = db.add_val(row[MAIL_COLUMN])

    update_vals += [{
        'range': f"{NAME_SHEET_COLUMN}{user.name + 2}",
        'values': [[user[NAME_COLUMN]]]
    }, {
        'range': f"{MAIL_SHEET_COLUMN}{user.name + 2}",
        'values': [[user[MAIL_COLUMN]]]
    }]
users_ws.batch_update(update_vals)

print('Wrote to cloud emails and users')

print(avaliable_users[[NAME_COLUMN, MAIL_COLUMN, 'accreditation_code']])