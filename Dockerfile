FROM python:3.13.2-bookworm

RUN apt-get update -y && apt-get upgrade -y

RUN pip3 install --upgrade pip
RUN pip3 install uv

COPY ./requirements.txt /python-seo-analyzer/

RUN uv pip install --system --verbose --requirement /python-seo-analyzer/requirements.txt
RUN uv cache clean --verbose

COPY . /python-seo-analyzer

# Create a non-root user
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Set ownership of the app directory
RUN chown -R appuser:appgroup /python-seo-analyzer

# Switch to the non-root user
USER appuser

RUN python3 -m pip install /python-seo-analyzer

ENTRYPOINT ["/usr/local/bin/seoanalyze"]
CMD ["--version"]
