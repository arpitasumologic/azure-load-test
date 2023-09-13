#!/usr/bin/env python

import asyncio
import time
import os
import sys
import random
import string
import subprocess
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

def getTimestamp():
    original_timestamp = datetime.now().astimezone()
    timestamp_string = original_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "+0530"
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

async def main(producer, duration, payload, batch, payload_data=None):
    deadline = time.time() + duration
    try:
        while time.time() < deadline:
            event_data_batch = await producer.create_batch()
            for i in range(batch):
                try:
                    if payload_data :
                        event_data_batch.add(EventData('Message inside EventBatchData'))
                    else:
                        event_data_batch.add(EventData(''.join(random.choices(string.ascii_uppercase, k=payload))))
                except ValueError:
                    await producer.send_batch(event_data_batch)
                    event_data_batch = await producer.create_batch()
            await producer.send_batch(event_data_batch)
    finally:
        # Close down the producer handler.
        await producer.close()


def test_long_running_send():
    duration = os.environ.get('DURATION', 30)
    payload = os.environ.get('PAYLOAD', 1024)
    #json should be one of minified json https://microsoftedge.github.io/Demos/json-dummy-data/
    payload_json_size = os.environ.get('PAYLOAD_JSON_SIZE', None)
    batch = os.environ.get('BATCH', 1)
    eventhub = os.environ.get('EVENTHUB')
    conn_str = os.environ.get('EVENT_HUB_CONNECTION_STR', None)

    producer = EventHubProducerClient.from_connection_string(
        conn_str=conn_str,
        eventhub_name=eventhub  # EventHub name should be specified if it doesn't show up in connection string.
    )

    payload_data = None
    if payload_json_size:
        payload_json_url = f'https://microsoftedge.github.io/Demos/json-dummy-data/{payload_json_size}-min.json'
        result = subprocess.run(
            ['wget', '-O', 'payload.json', payload_json_url])
        with open('payload.json', 'r') as file:
            payload_data = file.read()
    try:
        print (f"Duration ={duration}")
        print(f"Batch ={batch}")
        print(f"Payload ={payload}")
        if payload_data:
            print(f"Payload data ={payload_data}")
        else:
            print(f"Payload ={payload}")
        asyncio.run(main(producer, int(duration), int(payload), int(batch), payload_data))
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    test_long_running_send()