import pandas as pd
import requests as r
import base64

df = pd.read_csv('skud.csv', names=['num', 'url'], delimiter=';')

df['image'] = df['url'].apply(lambda url: base64.b64encode(r.get(url).content).decode())

df.to_excel('output.xlsx')