import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders


def send_mail(send_from, send_to, subject, text, file_name, server, port, username, password, isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(file_name, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="Manual_Entries.xlsx"')
    msg.attach(part)

    #context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
    #SSL connection only working on Python 3+
    smtp = smtplib.SMTP(server, port)
    if isTls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


# send can be a string e.g. 'abc@yopmail.com' or a list ['abc@yopmail.com', 'bcd@yopmail.com', ...]
def initiate_email(send_to, subject, content, file_name):
    send_from = "ocr_admin@yopmail.com"
    if isinstance(send_to, list):
        multiple = True
    else:
        multiple = False

    server_name = "smtp.mailtrap.io"
    port = 2525
    username = "f4fdd35ad13909"
    password = "dc246271a3eb7e"
    if multiple:
        for sender_email in send_to:
            send_mail(send_from, sender_email, subject, content, file_name, server_name, port, username, password)
    else:
        send_mail(send_from, send_to, subject, content, file_name, server_name, port, username, password)
