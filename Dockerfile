FROM python:3.10-buster

WORKDIR /blockchain-insights-subnet

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED 1

COPY . .

RUN chmod +x scripts/*