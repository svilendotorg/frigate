#!/usr/bin/env python3
"""Auto-transcribe Frigate speech events via MQTT."""
import json
import logging
import os
import requests
import paho.mqtt.client as mqtt

MQTT_HOST = os.environ.get("FRIGATE_MQTT_HOST", "")
MQTT_PORT = int(os.environ.get("FRIGATE_MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("FRIGATE_MQTT_USER", "")
MQTT_PASS = os.environ.get("FRIGATE_MQTT_PASSWORD", "")
FRIGATE_API = os.environ.get("FRIGATE_API_URL", "http://127.0.0.1:5000")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("auto-transcribe")


def on_connect(client, userdata, flags, rc, props=None):
    log.info("Connected to MQTT, subscribing to frigate/events")
    client.subscribe("frigate/events")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
    except Exception:
        return

    event_type = payload.get("type")
    after = payload.get("after", {})
    label = after.get("label", "")
    event_id = after.get("id", "")

    if label != "speech" or event_type != "end" or not event_id:
        return

    log.info(f"Speech event ended: {event_id} — triggering transcription")
    try:
        r = requests.put(
            f"{FRIGATE_API}/api/audio/transcribe",
            json={"event_id": event_id},
            timeout=10,
        )
        log.info(f"Transcription response: {r.status_code} {r.text}")
    except Exception as e:
        log.error(f"Failed to call transcription API: {e}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="frigate-auto-transcribe")
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()
