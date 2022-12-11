FROM python:3.10
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scrapper.py .
COPY models.py .

CMD [ "python", "./daemon.py" ]
