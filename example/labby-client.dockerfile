FROM python:3.8-slim

ARG DEBIAN_FRONTEND=noninteractive

# Set extra properties and initial tools
RUN apt-get clean && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends vim git

RUN pip install --upgrade pip

WORKDIR /$HOME

RUN pip install git+https://github.com/davidban77/labby

ENTRYPOINT [ "bash" ]