include .env

install:
	brew install portaudio;
	python -m pip install -r requirements.txt

sendbook:
	python3 main.py

clean:
	rm -rf __pycache__