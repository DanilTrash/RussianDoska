import logging
from telethon import TelegramClient, sync

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from os.path import basename


def logger(name, mode='w'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    formatter = logging.Formatter('%(asctime)s ~ %(levelname)s: %(message)s')
    fileHandler = logging.FileHandler('log.log', encoding='utf_8_sig', mode=mode)
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    return logger


api_id = 4345538
api_hash = '49313b839c59755f6d4ed52c002576f9'


def tg_alert(message, entity=585403132, file=None):
    with TelegramClient(f'+79687580328', api_id, api_hash) as client:
        client.send_message(entity, message, file=file)


def email_alert(subject, text, files=None):
    username = "daniltrashjob@gmail.com"
    password = 'Zxcasdqwe123'

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = username
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            ext = f.split('.')[-1:]
            attachedfile = MIMEApplication(fil.read(), _subtype = ext)
            attachedfile.add_header(
                'content-disposition', 'attachment', filename=basename(f))
        msg.attach(attachedfile)

    smtp = smtplib.SMTP(host="smtp.gmail.com", port=587)
    smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(username, username, msg.as_string())
    smtp.close()
