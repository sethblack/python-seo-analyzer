FROM python:3.12-bullseye

RUN apt-get update -y && apt-get upgrade -y

RUN pip3 install --upgrade pip
RUN pip3 install uv

COPY ./requirements.txt /app/

RUN uv pip install --system --verbose --requirement /app/requirements.txt
RUN uv cache clean --verbose

WORKDIR /app

COPY . /app

RUN python3 setup.py install

ENTRYPOINT ["/usr/local/bin/seoanalyze"]
