ARG BASE_IMAGE
FROM ${BASE_IMAGE}

WORKDIR /blockchain-insights-subnet

COPY . .
RUN pip install -r requirements.txt # Running again to make sure all dependencies are installed
RUN chmod +x scripts/*