### SENDBOOKS


**sendbooks** sends the latest downloaded book to your ebook reader,
while keeping a log of sent books.

The script will optionally copy the book to 'calibre_add' folder.   
[Calibre](https://calibre-ebook.com/) is an excellent ebooks management tool.

Usage: run `python main.py` from the script's folder. 
More convenient way is to add `alias sb="cd <script's folder> && python3 main.py"`line in #Aliases section of `.bash_profile`: running `sb` command in Terminal will launch sendbooks.
    
Configuration (in .env file):
    
``` 
  BOOKSPATH='...'
  CALIBRE_ADD_PATH='...'
  EMAIL='...'
  PASSWORD='...'
  SENDER_NAME='...'
  EMAIL_TO='...'
  MAX_FILE_SIZE=2e7
```
Apple Mac OS X specific features:
**sendbooks** makes use of OSX voice features, including `ask` and `say`.

Use Homebrew to install the prerequisite portaudio library, then install PyAudio and other libraries using pip:

```
  brew install portaudio   
  pip install -r requirements.txt
```

Alternatively, run `make` command in source folder.

Script has been tested with Python 3.8-3.10 on Mac OS 10.14 and ebook reader  PocketBookX.
