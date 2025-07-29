## Documentation for the Backend Program

### Constants Configuration

* MQTT Broker's address:  

    * BROKER_HOST = "10.25.0.3" 
    * BROKER_PORT = 1883  

    > This MQTT broker runs in the internal netork of the company, you have to connect to VPN first to use it. 


* Parameter needed by VDA5050 protocol header:  

    * ORG_ID = "AIbot"  

* URLs needed for testing:  

    * HTTP_HEAD = "http"  
    * HTTPS_HEAD = "https"  
    * ROBOT_HTTP = 80  
    * ROBOT_HTTPS = 8443  
    * BACKEND_HTTP = 81  
    * BACKEND_HTTPS = 8444
    * TEST_ROBOT_HOST = "127.0.0.1"  
    * TEST_BACKEND_HOST = "127.0.0.1"  

    > For testing, if you are using VPN now, change the host address and keep using HTTP head and ROBOT_HTTP and BACKEND_HTTP. If not and you wish to use https, then use the HTTPS head and ROBOT HTTPS and BACKEND HTTPS.

* For control commands:  

    * COMMAND_TASK = '0'  
    * COMMAND_MOVE = '1'  
    * COMMAND_DELIVER = '2'  
    * COMMAND_PAUSE = '3'  
    * COMMAND_RESUME = '4'  
    * COMMAND_ABORT = '5'  
    * COMMAND_RESTOCK = '6'  
    * COMMAND_CHARGE = '7'  
    * COMMAND_TASKS = '8'  
    * COMMAND_DELETE = '9'  
    * COMMAND_SNAPSHOT = '10'  

    * TASKID_TASK = 1000  
    * TASKID_MOVE = 1001  
    * TASKID_DELIVER = 1002  
    * TASKID_PAUSE = 1003  
    * TASKID_RESUME = 1004  
    * TASKID_ABORT = 1005  
    * TASKID_RESTOCK = 1006  
    * TASKID_CHARGE = 1007  
    * TASKID_TASKS = 1008  
    * TASKID_DELETE = 1009  
    * TASKID_SNAPSHOT = 1010  

    > This part is not for practical use. Just use in tests. To test the interfaces. Enter the number then the corresponding interface will start working.

* For authorization:  

    * ROBOT_ID_1 = "R1234"  
    * ROBOT_ID_2 = "R1235"  
    * ROBOT_VALID_TOKENS = { ROBOT_ID_1: "ABCDEF12345", ROBOT_ID_2: "1234567" }  

    * DEVICE_TYPE = "backend"  
    * BACKEND_ID = "B1234"  
    * BACKEND_TOKEN = "98765"  

    * CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{BACKEND_ID}"  

    > This part need more precise and practical data in the future. These are just test data.

* TLS configuration:  

    * cert.pem  
    * key.pem  

    > if you are using wireguard and connect to the internal network, then you don't need to use SSL.

### 1. backend_client.py

#### 1.1 Dependency

`requests`
```bash
conda install -c conda-forge requests
```
```Python
import requests
import os
import base64
from datetime import datetime
from datetime import timezone
```

#### 1.2 Structure

backend_client.py  
&emsp;|- post_command(): Basic HTTP POST encapsulation  
&emsp;|- task_control(): "task" action, the robot will deliver according to the command.  
&emsp;|- move_control(): "move" action, the robot will move to the specific 3D coordinates.  
&emsp;|- deliver_control(): "deliver" action, the robot will deliver the cargo.  
&emsp;|- pause_control(): "pause" action, the robot will pause.  
&emsp;|- resume_control(): "resume" action, the robot will resume doing one task.  
&emsp;|- abort_control(): "abort" action, the robot will stop doing the task.  
&emsp;|- restock_control(): "restock" action, the robot will conduct restock action.  
&emsp;|- charge_control(): "charge" action, the robot will go to charge.  
&emsp;|- get_tasks(): The backend requets to get the tasks' queue from the robot.  
&emsp;|- delete_task(): The backend asks the robot to try to delete the specific task.  
&emsp;|- get_current_snapshot(): The backend requests for the snapshot from robot's camera.  
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
```Python
import json
import ssl
import paho.mqtt.client as mqtt
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