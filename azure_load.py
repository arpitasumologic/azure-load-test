#!/usr/bin/env python

import argparse
import time
import os
import sys
import random
import string
import subprocess
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from azure.eventhub import EventHubClient, Sender, EventData

def getTimestamp():
    original_timestamp = datetime.now().astimezone()
    # Convert datetime object to a string representation in PST
    timestamp_string = original_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "+0530"
    # print(timestamp_string)
    # OUTPUT: 2019-08-17T00:00:00+0530
    return timestamp_string

def get_logger(filename, level=logging.INFO):
    azure_logger = logging.getLogger("azure.eventhub")
    azure_logger.setLevel(level)
    uamqp_logger = logging.getLogger("uamqp")
    uamqp_logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    if not azure_logger.handlers:
        azure_logger.addHandler(console_handler)
    if not uamqp_logger.handlers:
        uamqp_logger.addHandler(console_handler)

    if filename:
        file_handler = RotatingFileHandler(filename, maxBytes=20*1024*1024, backupCount=3)
        file_handler.setFormatter(formatter)
        azure_logger.addHandler(file_handler)
        uamqp_logger.addHandler(file_handler)

    return azure_logger

logger = get_logger("send_test.log", logging.INFO)


def check_send_successful(outcome, condition):
    if outcome.value != 0:
        print("Send failed {}".format(condition))


def main(client, duration, payload, batch, payload_data=None):
    sender = client.add_sender()
    client.run()
    deadline = time.time() + duration
    total = 0

    def data_generator():
        for i in range(batch):
            if payload_data:
                yield payload_data
            else:
                rand = ''.join(random.choices(string.ascii_uppercase, k=payload))
                yield getTimestamp() + ' test poc event ' + str(i) + ' ' + str(rand)

    if batch > 1:
        print("Sending batched messages")
    else:
        print("Sending single messages")

    try:
        while time.time() < deadline:
            if batch > 1:
                data = EventData(batch=data_generator())
            else:
                data = payload_data if payload_data else EventData(body=b"D" * payload)
            sender.transfer(data, callback=check_send_successful)
            total += batch
            if total % 10000 == 0:
               sender.wait()
               print("Send total {}".format(total))
    except Exception as err:
        print("Send failed {}".format(err))
    finally:
        client.stop()
    print("Sent total {}".format(total))


def test_long_running_send():
    if sys.platform.startswith('darwin'):
        import pytest
        pytest.skip("Skipping on OSX")
    duration = os.environ.get('DURATION', 30)
    payload = os.environ.get('PAYLOAD', 1024)
    #json should be one of minified json https://microsoftedge.github.io/Demos/json-dummy-data/
    payload_json_size = os.environ.get('PAYLOAD_JSON_SIZE', None)
    batch = os.environ.get('BATCH', 1)
    eventhub = os.environ.get('EVENTHUB')
    conn_str = os.environ.get('EVENT_HUB_CONNECTION_STR', None)
    address = os.environ.get('ADDRESS', None)
    sas_policy =  os.environ.get('SAS_POLICY', None)
    sas_key = os.environ.get('SAS_KEY', None)

    if conn_str:
        client = EventHubClient.from_connection_string(
            conn_str,
            eventhub=eventhub)
    elif address:
        client = EventHubClient(
            address,
            username=sas_policy,
            password=sas_key)
    else:
        try:
            import pytest
            pytest.skip("Must specify either 'EVENT_HUB_CONNECTION_STR' or 'ADDRESS' ENV variable")
        except ImportError:
            raise ValueError("Must specify either 'EVENT_HUB_CONNECTION_STR' or 'ADDRESS'")
    payload_data = None
    if payload_json_size:
        payload_json_url = f'https://microsoftedge.github.io/Demos/json-dummy-data/{payload_json_size}-min.json'
        result = subprocess.run(
            ['wget', '-O', 'payload.json', 'https://www.webscrapingapi.com/images/logo/logo-white.svg'])
        with open('payload.json', 'r') as file:
            payload_data = file.read().rstrip()
    try:
        print (f"Duration ={duration}")
        print(f"Batch ={batch}")
        print(f"Payload ={payload}")
        if payload_data:
            print(f"Payload data ={payload_data}")
            payload = 0
        else:
            print(f"Payload ={payload}")
        main(client, int(duration), int(payload), int(batch), payload_data)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    test_long_running_send()