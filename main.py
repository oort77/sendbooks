#!/Users/gm/opt/anaconda3/bin/python3.9
# -*- coding: utf-8 -*-

#  File: sendbook.py
#  Project: 'Send book to PocketbookX'
#  Created by Gennady Matveev (gm@og.ly) on 10-09-2021.
#  Updated for GitHub on 21=06-2022
#  Copyright 2021. All rights reserved.
#  Parts from: https://gist.github.com/elprup/3205948

"""
    sendbook.py sends the latest downloaded book to PocketbookX,
    while keeping a log of sent books.

    The script will optionally copy the book to 'calibre_add' folder.

    Usage: python sendbook.py from 'Downloads' folder
    
    Configuration (in .env file):
    
        BOOKSPATH='...'
        CALIBRE_ADD_PATH="..."
        EMAIL='...'
        PASSWORD='...'
        SENDER_NAME='...'
        EMAIL_TO='...'
        MAX_FILE_SIZE=2e7
"""

# Import modules
import os
import sys
import smtplib
import ssl
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
import mimetypes
import pickle
from sys import exit
from shutil import copy
import pandas as pd
from dotenv import load_dotenv
import speech_recognition as sr

load_dotenv()

email = os.environ.get("EMAIL")
password = os.environ.get("PASSWORD")
sender_name = os.environ.get("SENDER_NAME")
email_to = os.environ.get("EMAIL_TO")
max_file_size = os.environ.get("MAX_FILE_SIZE")

recognizer = sr.Recognizer()
mic = sr.Microphone()


# Speech recognition
def ask(phrase: str) -> None:
    fail = True
    while fail:
        os.system(f"say {phrase}")
        with mic as source:
            audio = recognizer.listen(source, timeout=7)
        try:
            fail = False
            return recognizer.recognize_google(audio)

        except sr.UnknownValueError:
            os.system(
                f'say "Did not get it, please answer the question loud and clear"'
            )
            fail = True


# Downloaded books normally live in Downloads:
books_path = os.environ.get("BOOKSPATH")
# Calibre expects new books in:
calibre_add_path = os.environ.get("CALIBRE_ADD_PATH")


# Get list of books
def file_info(dir_name: str) -> list:
    file_list = {}
    extensions = [".pdf", ".epub", ".fb2", ".mobi", ".djvu"]
    for f in os.listdir(dir_name):
        if [i for i in extensions if i in f]:
            a = os.stat(os.path.join(dir_name, f))
            file_list[f] = a.st_ctime
    return file_list


# Get last book
def get_last_book(dir_name: str):
    # Get all
    books = file_info(dir_name)
    # Get the last one
    return max(books, key=books.get)


# Send mail
def send_email(sender_mail: str, sender_pass: str, filename: str):
    # Create email
    subject = f"New book - {filename}"
    body = ""
    from_sender = formataddr((str(Header(f"sender_name", "utf-8")), sender_mail))

    password = sender_pass

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = from_sender
    message["To"] = email_to
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain", "UTF-8"))

    print(f"\nSending {filename}")
    os.system('say "sending the book"')

    # Check if the file can be emailed (<20MB)
    if os.path.getsize(filename) > max_file_size:

        print("File is too large to be emailed")
        os.system('say "the file is too large to be emailed"')

    else:

        # Open file in binary mode
        with open(filename, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment

            # Find application type
            ctype, encoding = mimetypes.guess_type(filename)
            # ****************************************************************
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = "application/octet-stream"
            # ****************************************************************
            maintype, subtype = ctype.split("/", 1)
            # part = MIMEBase("application", "octet-stream")
            part = MIMEBase(maintype, subtype)
            part.replace_header("Content-Type", f'{ctype};name="{filename}"')
            part.add_header(
                "Content-Disposition", f'attachment; filename= "{filename}"'
            )
            part.add_header("X-Attachment-Id", "0")
            part.add_header("Content-ID", "<0>")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add attachment to message and convert message to string
        message.attach(part)
        text = message.as_string()
        recipients = [email_to]

        # Log in to server using secure context and send email
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                "smtp.gmail.com", port=465, timeout=30, context=context
            ) as server:
                server.login(sender_mail, password)
                server.sendmail(sender_mail, recipients, text)
                os.system('say "the book has been sent"')

        except smtplib.SMTPException as e:
            print(f"Unable to send email : {e}")


# Check if df record exists or particular field is not null

def check_record(df: pd.DataFrame, filename: str, field: str = "book_file"):
    if filename in df["book_file"].values:
        if df.loc[df["book_file"] == filename][field].notnull().any():

            return True, True
        else:
            return True, False
    else:
        return False, False


# Update/create record
def update_create_record(df: pd.DataFrame, filename: str, field: str, value):
    if filename in df["book_file"].values:
        df.loc[df["book_file"] == filename, field] = value

    else:
        df.loc[df.index.max() + 1, "book_file"] = filename
        df.loc[df.index.max(), field] = value
    # Write df to pickle
    with open("./booksdb.pkl", "wb") as f:
        pickle.dump(df, f, protocol=pickle.HIGHEST_PROTOCOL)


def main():
    # Check if the book is already on the reader
    filename = get_last_book(books_path)
    print(f"\nLast downloaded book:\n{filename}\n")
    # Load books dataframe df
    with open("./data/booksdb.pkl", "rb") as f:
        df = pickle.load(f)

    if check_record(df, filename, "on_reader")[1]:

        proceed = ask("The book is already on reader. Proceed?")
        print(proceed)
        if proceed == "yes":
            send_email(
                email,
                password,
                filename,
            )
        else:
            print("\nOperation aborted by user.\n")
    else:
        send_email(
            email,
            password,
            filename,
        )
        update_create_record(df, filename, "on_reader", datetime.now())

    add_to_calibre = ask("Add the book to calibre library?")
    print(add_to_calibre)

    # Check if the book is already in calibre library
    if add_to_calibre == "yes": 

        if check_record(df, filename, "on_reader")[1]:
            print("\nThe book is already in calibre library. Aborting.\n")
            exit(1)
        else:
            # Proceed with copying and add exception handling
            try:
                copy(filename, calibre_add_path + "/" + filename)
                print(calibre_add_path + "/" + filename)
            except IOError as e:
                print(f"Unable to copy file. {e}")
                exit(1)
            except:
                print("Unexpected error:", sys.exc_info())
                exit(1)

            update_create_record(df, filename, "on_reader", datetime.now())

            os.system('say "Book added to library, sir!"')
            print("\nBook added to calibre!\n")
    else:
        print("\nOperation aborted by user.\n")


if __name__ == "__main__":
    main()

