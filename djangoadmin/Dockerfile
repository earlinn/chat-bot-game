FROM python:3.12-slim

LABEL author='Earlinn' version=1

# prevent python from writing .pyc files
ENV PYTHONUNBUFFERED 1
# ensure python output is sent directly to the terminal without buffering
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY . /app/
