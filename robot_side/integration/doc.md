## Documentation for the Robot Program

### Constants Configuration

* MQTT Broker's address:  
&emsp;BROKER_HOST = "127.0.0.1"  
&emsp;BROKER_PORT = 8445  

* URLs needed for testing:  

&emsp;TEST_BACKEND_HOST = "127.0.0.1"  
&emsp;TEST_BACKEND_PORT = 8444  
&emsp;TEST_ROBOT_HOST = "127.0.0.1"  
&emsp;TEST_ROBOT_PORT = 8443  

* For image types:  

&emsp;DELIVER_TYPE = '0'  
&emsp;PICKUP_TYPE = '1'  

* For authorization:  
&emsp;DEVICE_TYPE = "robot"  
&emsp;ROBOTID = "R1234"  
&emsp;TOKEN = "ABCDEF12345"  
&emsp;BACKEND_ID = "B1234"  
&emsp;BACKEND_VALID_TOKENS = {  
&emsp;&emsp;BACKEND_ID: "12345ABCDEF"  
&emsp;}  

&emsp;CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{ROBOTID}"  

* VDA 5050 header constants:  

&emsp;ORG_ID = "AIbot"  
&emsp;STATE_HEADER_ID = 0  
&emsp;CONN_HEADER_ID = 0  
&emsp;VERSION = "version"  
&emsp;MANUFACTURER = "manu"  
&emsp;SERIAL_NUMBER = "serial"  


### 1. robot_client.py

#### 1.1 Dependency

`requests`
```bash
conda install -c conda-forge requests
```

#### 1.2 Structure
robot_client.py
&emsp;|-upload_image_base64(taskId, type, image_path): upload the specific image by base64.  
&emsp;|-upload_image_form(taskId, type, image_path): upload the specific image by form-data.  
&emsp;|-deliver_type(image_path): specify the deliver image.  
&emsp;|-pickup_type(image_path): specify the pickup image.  
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
```

#### 2.2 Structure




#### 2.3 How to run


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


#### 3.3 How to run

