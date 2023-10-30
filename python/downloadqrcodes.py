import pandas as pd
import requests as r
import base64

import os, dotenv

dotenv.load_dotenv()

CSV_NAME = os.environ.get('CSV_NAME')
XLSX_QR_NAME = os.environ.get('XLSX_QR_NAME')

df = pd.read_csv(CSV_NAME, names=['num', 'url'], delimiter=',')

df['image'] = df['url'].apply(lambda url: base64.b64encode(r.get(url).content).decode())

df.to_excel(XLSX_QR_NAME)