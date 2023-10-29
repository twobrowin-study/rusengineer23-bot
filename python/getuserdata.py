import os, json, dotenv, gspread
import pandas as pd
from ext.database import HashDb
from datetime import datetime

dotenv.load_dotenv()

SHEETS_ACC_JSON = json.loads(os.environ.get('SHEETS_ACC_JSON'))
SHEETS_LINK     = os.environ.get('SHEETS_LINK')
HASH_DB         = os.environ.get('HASH_DB')

SHEET = os.environ.get('SHEET')

NAME     = os.environ.get('NAME')
PHONE    = os.environ.get('PHONE')
EMAIL    = os.environ.get('EMAIL')
CATEGORY = os.environ.get('CATEGORY')

ACCREDITATION_CODE   = os.environ.get('ACCREDITATION_CODE')
ACCREDITATION_STATUS = os.environ.get('ACCREDITATION_STATUS')

ACTIVE = os.environ.get('ACTIVE')

REGISTRATION_PREFIX  = os.environ.get('REGISTRATION_PREFIX')
REGISTRATION_COLNAME = os.environ.get('REGISTRATION_COLNAME')

YES = os.environ.get('YES')
NO  = os.environ.get('NO')

OUTPUT_FILENAME = os.environ.get('OUTPUT_FILENAME')

print(f"Loading user data")

db = HashDb(HASH_DB)

print("Connected to database")

gc = gspread.service_account_from_dict(SHEETS_ACC_JSON)
sh = gc.open_by_url(SHEETS_LINK)
ws = sh.worksheet(SHEET)

print('Connected to spreadsheet')

df = pd.DataFrame(ws.get_all_records())
df = df.drop(0, axis='index')

print('Loaded dataframe')

for _,row in df.iterrows():
    row[NAME]  = db.get_val(row[NAME])
    row[PHONE] = db.get_val(row[PHONE])
    row[EMAIL] = db.get_val(row[EMAIL]) if row[EMAIL] not in ['', None] else ''

print('Replaced name and phone number')

registration_cols = [
    col for col in df.columns
    if col.startswith(REGISTRATION_PREFIX)
]

output_data = []
for _,row in df.iterrows():
    output_data += [{
        NAME:     row[NAME],
        PHONE:    row[PHONE],
        EMAIL:    row[EMAIL],
        CATEGORY: row[CATEGORY],

        ACCREDITATION_CODE:   row.accreditation_code,
        ACCREDITATION_STATUS: row.accreditation_status,

        ACTIVE: row.is_active
    }]
    for col in registration_cols:
        if row[col] == YES:
            output_data += [{
                NAME:     row[NAME],
                PHONE:    row[PHONE],
                EMAIL:    row[EMAIL],
                CATEGORY: row[CATEGORY],

                ACCREDITATION_CODE:   row.accreditation_code,
                ACCREDITATION_STATUS: row.accreditation_status,

                ACTIVE: row.is_active,

                REGISTRATION_COLNAME: col.removeprefix(REGISTRATION_PREFIX),
            }]

print('Created output dataframe')

pd.DataFrame(output_data).to_excel(
    OUTPUT_FILENAME.format(datetime=datetime.now().strftime('%Y_%m_%d_%H_%M')),
    sheet_name=SHEET
)

print('Saved output file')