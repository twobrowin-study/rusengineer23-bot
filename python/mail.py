import os

from smtplib import SMTP
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MAIL_FROM_ALIAS = os.environ["MAIL_FROM_ALIAS"]
MAIL_FROM_MAIL  = os.environ["MAIL_FROM_MAIL"]

SMTP_ADDRESS  = os.environ["SMTP_ADDRESS"]
SMTP_PORT     = int(os.environ["SMTP_PORT"])

def SendMessage(mail_to: str, subject: str, text: str):
    mail_message = MIMEMultipart()
    mail_message['Subject'] = subject
    mail_message['From'] = f"{Header(MAIL_FROM_ALIAS).encode()} <{MAIL_FROM_MAIL}>"
    mail_message['To'] = mail_to

    mail_message.attach(MIMEText(text, 'html', _charset = 'utf8'))

    # for filename, doc in documents or []:
    #     doc.save(f"/tmp/{filename}")
    #     with open(f"/tmp/{filename}", 'rb') as file:
    #         part = MIMEApplication(
    #             file.read(),
    #             Name=filename
    #         )
    #     part['Content-Disposition'] = f"attachment; filename=\"{filename}\""
    #     mail_message.attach(part)

    smtp = SMTP(SMTP_ADDRESS, SMTP_PORT)
    # smtp.login(SMTP_LOGIN, SMTP_PASSWORD)
    smtp.send_message(mail_message)