FROM python:3.9.19-slim-bullseye

COPY ./src/* /opt/src/

WORKDIR /opt/src

RUN pip install -r requirements.txt

CMD ["python3" "./book_mgt_api.py"]
