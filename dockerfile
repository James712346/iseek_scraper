FROM python:3.11-alpine

WORKDIR /root/iseek_scraper/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scrapper.py .
COPY models.py .
COPY Database.py .
CMD [ "python", "-u", "./Database.py" ]
