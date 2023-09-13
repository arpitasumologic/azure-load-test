FROM python:3.9

#install wget
RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

# Install Azure Event Hub PythonSDK Module
RUN pip install azure-eventhub \
 && rm -rf /.cache \
 && apt-get autoremove -o APT::Autoremove::RecommendsImportant=0 -o APT::Autoremove::SuggestsImportant=0

COPY . /app

WORKDIR /app

ENTRYPOINT ["python3", "azure_load.py"]