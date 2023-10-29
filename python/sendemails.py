import os, json, dotenv, gspread
import pandas as pd
from ext.database import HashDb
from time import sleep

dotenv.load_dotenv()

from mail import SendMessage

SHEETS_ACC_JSON = json.loads(os.environ.get('SHEETS_ACC_JSON'))
SHEETS_LINK     = os.environ.get('SHEETS_LINK')
HASH_DB         = os.environ.get('HASH_DB')

SHEET    = os.environ.get('SHEET')
SETTINGS = os.environ.get('SETTINGS')
QR_CODES = os.environ.get('QR_CODES')

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

print('Connected to spreadsheet')

settings_ws = sh.worksheet(SETTINGS)
settings_df = pd.DataFrame(settings_ws.get_all_records())
settings_df = settings_df.drop(0, axis='index')

mail_theme = settings_df.loc[settings_df['key'] == 'email_theme'].iloc[0].value
mail_text  = settings_df.loc[settings_df['key'] == 'email_text_template_html'].iloc[0].value

print('Loaded settings')

users_ws = sh.worksheet(SHEET)
df = pd.DataFrame(users_ws.get_all_records())
df = df.drop(0, axis='index')

df = df.loc[~df[EMAIL].isin(['', None])]

print('Loaded users dataframe')

qr_codes_ws = sh.worksheet(QR_CODES)
qr_codes_df = pd.DataFrame(qr_codes_ws.get_all_records())
qr_codes_df = qr_codes_df.drop(0, axis='index')

print('Loaded qr codes')

for _,row in df.iterrows():
    row[NAME]  = db.get_val(row[NAME])
    row[EMAIL] = db.get_val(row[EMAIL])

df[NAME] = df[NAME].apply(lambda s: ' '.join(s.split(' ')[1:]))

print('Replaced name and emails')

df['qr_code'] = df['accreditation_code'].apply(lambda s: qr_codes_df.loc[qr_codes_df.accreditation_code == s].iloc[0]['base64'])

print('Set QR codes')

for idx,row in df.iterrows():
    mail_text_formatted = mail_text.format(
        name = row[NAME],
        qr_code = row['qr_code'],
        accreditation_code = row.accreditation_code
    )
    email_address = row[EMAIL]
    print(f"Sending email to {email_address}")
    SendMessage(email_address, mail_theme, mail_text_formatted)
    sleep(5 if idx % 5 == 0 else 1)