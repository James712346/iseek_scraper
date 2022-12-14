FROM python:3.11-alpine
# Install dependencies
RUN apk --no-cache add curl gnupg build-base unixodbc-dev openssl

#Download the desired package(s)
RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/msodbcsql18_18.1.2.1-1_amd64.apk
RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/mssql-tools18_18.1.1.1-1_amd64.apk


#(Optional) Verify signature, if 'gpg' is missing install it using 'apk add gnupg':
RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/msodbcsql18_18.1.2.1-1_amd64.sig
RUN curl -O https://download.microsoft.com/download/8/6/8/868e5fc4-7bfe-494d-8f9d-115cbcdb52ae/mssql-tools18_18.1.1.1-1_amd64.sig

RUN curl https://packages.microsoft.com/keys/microsoft.asc  | gpg --import -
RUN gpg --verify msodbcsql18_18.1.2.1-1_amd64.sig msodbcsql18_18.1.2.1-1_amd64.apk
RUN gpg --verify mssql-tools18_18.1.1.1-1_amd64.sig mssql-tools18_18.1.1.1-1_amd64.apk


#Install the package(s)
RUN apk add --allow-untrusted msodbcsql18_18.1.2.1-1_amd64.apk
RUN apk add --allow-untrusted mssql-tools18_18.1.1.1-1_amd64.apk


WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scrapper.py .
COPY models.py .
COPY Database.py .

CMD [ "python", "-u", "./Database.py" ]
