FROM python:latest

COPY ./src/* /opt/src/

WORKDIR /opt/src

RUN pip install -r requirements.txt

CMD ["python" "./book_mgt_api.py"]
