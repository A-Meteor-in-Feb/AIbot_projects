import paho.mqtt.client as mqtt

BROKER_HOST = "10.25.0.2"
BROKER_PORT = 1883

def on_connect(client, userdata, flags, reason_code, properties):
    """
        connect callback
    """
    print(f"robot connected with the result code {reason_code}")

def mqtt_state(status):
    """
        publish state topic to the backend
    """
    