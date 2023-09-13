export EVENT_HUB_CONNECTION_STR="Endpoint=sb://arpitaload1.servicebus.windows.net/;SharedAccessKeyName=arpitapol;SharedAccessKey=I87qVfPTZc7+El0xIRDz9pgdG6zSMnzRe+AEhNZTHsg=;EntityPath=arpita_loadtest1"
export EVENTHUB="arpita_loadtest1"
export DURATION=60
export PAYLOAD=512
export BATCH=128

export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

docker build -t azure_send .
docker rm -f azure_send || true
docker run -e DURATION=$DURATION -e PAYLOAD=$PAYLOAD -e BATCH=$BATCH -e EVENTHUB=$EVENTHUB -e EVENT_HUB_CONNECTION_STR=$EVENT_HUB_CONNECTION_STR, -e ADDRESS=$ADDRESS -e SAS_POLICY=$SAS_KEY -e SAS_KEY=$SAS_KEY --name azure_send azure_send
