FROM python:3.11
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scrapper.py .
COPY Database.py .

CMD [ "python", "-u", "./Database.py" ]
