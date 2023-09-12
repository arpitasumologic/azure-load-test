FROM python:3.9

# Install Azure Event Hub PythonSDK Module
RUN pip install azure-eventhub==1.3.3

# Remove Unneeded PIP Cache after Install
RUN rm -rf /.cache

RUN apt-get autoremove -o APT::Autoremove::RecommendsImportant=0 -o APT::Autoremove::SuggestsImportant=0

COPY . /app

WORKDIR /app

ENTRYPOINT ["python3", "azure_load.py"]