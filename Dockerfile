FROM python:latest

COPY ./src/* /opt/src/

WORKDIR /opt/src

RUN pip install -r requirements.txt

ENTRYPOINT ['/usr/local/bin/python' 'book_mgt_api.py']
