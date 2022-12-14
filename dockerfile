FROM python:3.11
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scrapper.py .
COPY InfluxDB.py .

CMD [ "python", "-u", "./InfluxDB.py" ]
