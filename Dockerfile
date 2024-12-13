FROM python:3.12-bullseye

RUN apt-get update -y && apt-get upgrade -y

RUN pip3 install --upgrade pip
RUN pip3 install uv

COPY ./requirements.txt /python-seo-analyzer/

RUN uv pip install --system --verbose --requirement /python-seo-analyzer/requirements.txt
RUN uv cache clean --verbose

COPY . /python-seo-analyzer

RUN python3 -m pip install /python-seo-analyzer

ENTRYPOINT ["/usr/local/bin/seoanalyze"]
