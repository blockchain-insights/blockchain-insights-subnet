FROM python:3.12
WORKDIR /blockchain-insights-subnet
COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y \
    python3-dev \
    cmake \
    make \
    gcc \
    g++ \
    libssl-dev

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x scripts/*