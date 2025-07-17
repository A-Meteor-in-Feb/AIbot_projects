## Documentation for the Backend Program

### Constants Configuration

* MQTT Broker's address:  

&emsp;BROKER_HOST = "127.0.0.1"  
&emsp;BROKER_PORT = 8445  

* Parameter needed by VDA5050 protocol header:  

&emsp;ORG_ID = "AIbot"  

* URLs needed for testing:  

&emsp;TEST_ROBOT_HOST = "127.0.0.1"  
&emsp;TEST_ROBOT_PORT = 8443  
&emsp;TEST_BACKEND_HOST = "127.0.0.1"  
&emsp;TEST_BACKEND_PORT = 8444  

* For control commands:  

&emsp;COMMAND_MOVE = '0'  
&emsp;COMMAND_DELIVER = '1'  
&emsp;COMMAND_PAUSE = '2'  
&emsp;COMMAND_RESUME = '3'  
&emsp;COMMAND_ABORT = '4'  

&emsp;TASKID_MOVE = 1234  
&emsp;TASKID_DELIVER = 1235  

* For authorization:  

&emsp;ROBOT_ID_1 = "R1234"  
&emsp;ROBOT_ID_2 = "R1235"  
&emsp;ROBOT_VALID_TOKENS = {  
&emsp;&emsp;ROBOT_ID_1: "ABCDEF12345",  
&emsp;&emsp;ROBOT_ID_2: "1234567"  
&emsp;}  

&emsp;DEVICE_TYPE = "backend"  
&emsp;BACKEND_ID = "B1234"  
&emsp;BACKEND_TOKEN = "98765"  

&emsp;CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{BACKEND_ID}"  

* TLS configuration:  
&emsp;cert.pem  
&emsp;key.pem  

### 1. backend_client.py

#### 1.1 Dependency

`requests`
```bash
conda install -c conda-forge requests
```

#### 1.2 Structure

backend_client.py  
&emsp;|- send_command(): Basic HTTP POST encapsulation  
&emsp;|- move_control(): "move" action, the robot will move to the specific 3D coordinates.  
&emsp;|- deliver_control(): "deliver" action, the robot will deliver the cargo.  
&emsp;|- pause_control(): "pause" action, the robot will pause.  
&emsp;|- resume_control(): "resume" action, the robot will continue doing tasks.  
&emsp;|- abort_control(): "abort" action, the robot will stop doing the task.  
&emsp;|- main loop: Run the corresponding function according to the user's input.  

#### 1.3 How to run

```bash
python backend_client.py
```

### 2. backend_mqtt_client.py

#### 2.1 dependencies

`paho.mqtt.client`
```bash
conda install -c conda-forge paho-mqtt
```

#### 2.2 Structure

backend_mqtt_client.py  
&emsp;|- parse_message(vda5050_msg): Parses a VDA5050 formatted MQTT message and return (header, data).  
&emsp;|- state_handler(client, userdata, msg): callback for robot/{robotId}/state topic.  
&emsp;|- connection_handler(client, userdata, msg): callback for robot/{robotId}/connection topic.  
&emsp;|- on_connect(client, userdata, flags, rc, properties): subscribe to each topic in TOPICS and binds the corresponding callback.  
&emsp;|- on_disconnect(client, userdata, rc): Automatically reconnect after a disconnect.  
&emsp;|- entry point: create client, set username and password, configure TLS, attach on_connect, and topic callbacks, start loop_forever().  

#### 2.3 How to run

```bash
python backend_mqtt_client.py
```

### 3. backend_server.py

#### 3.1 dependency

`Flask`
```bash
conda install -c conda-forge Flask
```

`requets`
```bash
conda install -c conda-forge requests
```

#### 3.2 Get Image (POST `/api/robots/<robotId>/images`)

* Authentication: header `Authentication: Bearer <token>`
* Content-type:
    * application/json: `taskId`, `type`, `timestamp`, `image`(base64-encoded)
    * multipart/form-data: `taskId`, `type`, `timestamp`, `image`(binary file)
* Responses:
    * `200 OK` 
    * `401 Unauthorized`
    * `400 Bad Request`
    * `415 Unsupported Media Type`

#### 3.3 Static File Hosting (GET `/` or `/<path>`)

* A request to `/` or `test.html` will return the corresponding file from the projects's base directory.
* If the file does not exist, the server will responds `404 Not Found`.

#### 3.4 Proxy Video Stream (GET `/api/robots/<robotId>/video-stream`)

* Authentication: header `Authentication: Bearer <token>` (forward to robot)
* Forwarding: Issues an HTTPS GET to the robot's `/camera/stream` endpoint.
* Responses:
    * `200 OK`: the flask server proxies the stream back to the fronend.
    * otherwise, an error will be raised.


#### 3.5 How to run

```bash
python backend_server.py
```