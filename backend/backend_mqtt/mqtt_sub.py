import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the result code {reason_code}")
    client.subscribe("test/topic")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


host = "192.168.123.61"
port = "1883"

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="test_subscriber")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(host, port, 60)
mqtt_client.loop_forever()