## Robotics Communication Part

### Background

This project is responsible for the communication functions in the robot system. The system is divided into two main parts - the robot side and the backend side. The communication between them primarily responsible for:

* Status Information:
    During task execution, the robot publishes its status to the backend via MQTT. Status data includes 3D position, battery level, task status, system status (online/connection or offline/disconnection), and cargo load status.
* Control Commands:
    The backend sends control commands to the robot over RESTful APIs to trigger operations. The commands are `move`, `deliver`, `pause`, `resume`, and `abort`.
* Image Transmission:
    At key stages during executing tasks, the robot uploads raw images (e.g., the deliver image and the pickup image) to the backend via RESTful API. The backend then verifies operation results based on these images.
* Video Streaming:
    The robot streams real-time video from its camera; the backend get the video stream via HTTP GET and displays it directly on the frontend.

To ensure security:

* The MQTT broker is configured with TLS/SSL encrytion, and every MQTT client is registered with its own username and password.
* All HTTP endpoints also use TLS/SSL for encrypted transport and require a bearer token in the HTTP header for authentication.

### Structure

backend -----  
            |- backend_commands:  
            |            |------- commands_post.py: Post the control commands from the backend.  
            |- backend_image:  
            |            |------- image_get.py: Get the images from the Robot on the backend.  
            |- backend_mqtt:  
            |            |------- mqtt_sub.py: Subscribe MQTT topics from the Robot on the backend.  
            |            |------- mqtt_pub.py: A MQTT publisher for testing.  
            |- backend_video:  
            |            |------- video_get.py: Get and response the video stream by fastapi.  
            |            |------- video_get2.py: Get and response the video stream by Flask(suggested by the Doc(3)).  
            |- integration: Integrate and review all separate functions.  
                         |------- backend_client.py: Sends control-command requests to the robot.  
                         |------- backend_mqtt_client.py: Subscribes to the robot's MQTT-published messages/.  
                         |------- backend_server.py: Exposes HTTP endpoints to handle image uploads from the robot and video-stream requets from the fronend.  

robot_side---  
            |- func_commands:  
            |            |------- commands_get.py: Get the control commands from the backend.  
            |- func_image:  
            |            |------- image_post.py: Post the images to the backend.  
            |- Func_topic:  
            |            |------- catkin_ws/src/robot/src:  
            |            |                |------- robotNode.py: Publish MQTT topics to the backend.  
            |            |                |------- ros_publisher.py: ros publisher for testing.  
            |- func_video:  
            |            |------- video_stream.py: Response the video stream by fastapi.  
            |            |------- video_stream2.py: Response the video stream by Flask(suggested by the Doc(3)).  
            |- integrate: Integrate and review all separate functions.  
                         |------- catkin_ws/src/robot/src:  
                         |                |------- robot_mqtt_client.py: Subscribe to messages published by ROS1, converts them to JSON, then publishes via MQTT  
                         |                |------- ros_publisher_test.py: Ros publisher for testing.  
                         |------- robot_client.py: Exposes HTTP endpoints to handle command requests and video stream requets from the backend.  
                         |------- robot_server.py: Sends image-data requests to the backend.  
