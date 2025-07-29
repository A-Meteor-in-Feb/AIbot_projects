## Documentation for the Robot Program

### Constants Configuration

* MQTT Broker's address:  

    * BROKER_HOST = "10.25.0.3"  
    * BROKER_PORT = 1883  
  
    > This MQTT broker runs in the internal network of the company, you have to connect to VPN first to use it.  

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


* For image types:  

    * DELIVER_TYPE = '0'  
    * PICKUP_TYPE = '1'  

* For authorization:  

    * DEVICE_TYPE = "robot"  
    * ROBOTID = "R1234"  
    * TOKEN = "ABCDEF12345"  
    * BACKEND_ID = "B1234"  
    * BACKEND_VALID_TOKENS = {BACKEND_ID: "12345ABCDEF" }  
    * CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{ROBOTID}"  

     > This part need more precise and practical data in the future. These are just test data.  

* VDA 5050 header constants:  

    * ORG_ID = "AIbot"  
    * STATE_HEADER_ID = 0  
    * CONN_HEADER_ID = 0  
    * VERSION = "version"  
    * MANUFACTURER = "manu"  
    * SERIAL_NUMBER = "serial"  
  
* For different tasks:  
  
    * TASK_IMAGE_DELIVER_TYPE = '0'  
    * TASK_IMAGE_PICKUP_TYPE = '1'  
    * TASK_BINID = '2'  
    * TASK_INVENTORY = '3'  
    * TASK_ORDERS = '4'  
    * TASK_NOTIFY = '5'  
    * TASK_AUTHCODE = '6'  
    * TASK_COMPLETE = '7'  

    * TASKID_IMAGE = 1011  
    * TASKID_BINID = 1012  
    * TASKID_INVENTORY = 1013  
    * TASKID_ORDERS = 1014  
    * TASKID_NOTIFY = 1015  
    * TASKID_AUTHCODE = 1016  
    * TASKID_COMPLETE = 1017  
  
    > This part is not for practical use. Just use in tests. To test the interfaces. Enter the number then the corresponding interface will start working.  


### 1. robot_client.py

#### 1.1 Dependency

`requests`
```bash
conda install -c conda-forge requests
```
```Python
import requests
import base64
from pathlib import Path
from datetime import datetime
from datetime import timezone
```

#### 1.2 Structure
robot_client.py  
&emsp;|-upload_image_base64(taskId, type, image_path): upload the specific image by base64.  
&emsp;|-upload_image_form(taskId, type, image_path): upload the specific image by form-data.  
&emsp;|-deliver_type(image_path): specify the deliver image.  
&emsp;|-pickup_type(image_path): specify the pickup image.  
&emsp;|-search_cargo_binId(bin_id): search for the cargo info of a specific bin, in cache, by request or backup.  
&emsp;|-search_cargo_inventory(): search for the cargo info of all inventory, in cache, by request or backup.
&emsp;|-get_orders(): Robot gets the uncompleted orders from the backend.
&emsp;|-notify_pickup(order_id): According to the order id, post notification request to the backend. Backend will notify the user by message or in app.  
&emsp;|-get_authCode(order_id): Get a new auth-code, or refresh one new auth-code.  
&emsp;|-notify_taskComplete(order_id): Notify the backend that one specific order is completed.  
&emsp;|-entry point: decide upload which type of image.  

#### 1.3 How to run

```bash
python robot_client.py
```

### 2. robot_server.py

#### 2.1 Dependency

`Flask`
```bash
conda install -c conda-forge Flask
conda install -c conda-forge opencv
```
```Python
from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask import abort
from flask import make_response
from pathlib import Path
import threading
import base64
import cv2
import os
import time
```

#### 2.2 Get Control Commands (POST `/api/robots/<robotId>/<command>`)

* Authentication: header `Authrntication: Bearer <token>`.  
* Responses: 
    * `200 OK`
    * `401 Unauthorized`
    * `400 Bad Request`
    * `404 Not Found`


#### 2.3 Response Video Stream Request (GET `/camera/stream`)

* Authentication: header `Authentication: Bearer <token>`.  
* Resonses:
    * `401 Unauthorized`
    * video stream - 'multipart/x-mixed-replace;boundry=--frame'


#### 2.4 Response the Tasks' Queue Request (GET `/api/JKROBOT/<string:robotId>/tasks`)

* Authentication: header `Authrntication: Bearer <token>`.  
* Responses: 
    * `200 OK`.  
    * `401 Unauthorized`.  


#### 2.5 Delete the Specific Task (DELETE `/api/JKROBOT/<string:robotId>/tasks/<string:taskId>`)

* Authentication: header `Authrntication: Bearer <token>`.  
* Responses: 
    * `200 OK`.  
    * `400 Bad Request`.  
    * `401 Unauthorized`.  


#### 2.6 Response the Snapshot Request (GET `/camera/snapshot`)

* Authentication: header `Authrntication: Bearer <token>`.  
* Responses: 
    * `200 OK`.  
    * `400 Bad Request`.  
    * `401 Unauthorized`.  
    * `500 Internal Error`.  


#### 2.7 How to run

```bash
python robot_server.py
```

### 3. robot_mqtt_client.py

#### 3.1 Dependency

`paho.mqtt.client`
```bash
conda install -c conda-forge paho-mqtt
```

`rospy` `std_msgs` `message_generation`
```bash
catkin_create_pkg robot std_msgs rospy message_generation
```
(or, include them in the package.xml and CMakeLists.txt)

#### 3.2 Structure

robot_mqtt_client.py  
&emsp;|- VDA_5050_header(header_id, version, manufacturer, serial_number): generate the header contents for every topic.  
&emsp;|- on_connect(client, userdata, flags, reason_code, properties): callback for connection with MQTT broker.  
&emsp;|- state_callback(msg): receive state msg from ros then convert to json then combine the header, publish by MQTT.  
&emsp;|- error_callback(msg): receive error msg from ros then convert to json then combine the header, publish by MQTT.  
&emsp;|- cargo_callback(msg): receive cargo msg from ros then convert to json then combine the header, publish by MQTT.  
&emsp;|- ip_notification(): Publish the robot's ip and netwrok interface by MQTT.
&emsp;|- online_notification(): send a MQTT connection topic to the backend to notify its online state.  
&emsp;|- last_will_set(): set the last will function to notify the backend that the robot side disconnects.  
&emsp;|- entry point: initiate ros node, mqtt client, configure authentication and TLS encryption, then set last will, then connect and start looping for message publish and subscription.  

#### 3.3 How to run

```bash
~/catkin_ws
catkin_make
source devel/setup.bash
~/catkin/src/robot/src
python robot_mqtt_client.py
```
