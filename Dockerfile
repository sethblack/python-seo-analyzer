FROM python:3-alpine

WORKDIR /app

COPY . /app

RUN python3 setup.py install

ENTRYPOINT ["/usr/local/bin/seoanalyze"]
