#!/bin/bash
 curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"payload": "{\"status\" :\"MOTION\"}", "topic": "home/downstairs/playroom/sensor/motion", "retain": "True"}' \
  http://<HA_IP>:8123/api/services/mqtt/publish
