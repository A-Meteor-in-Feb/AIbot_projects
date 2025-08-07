FROM ros:noetic-ros-core

COPY requirements.txt /tmp/

RUN apt-get update && \
    apt-get install -y \
      build-essential \
      cmake \
      python3-catkin-tools \
      python3-rosdep \
      ros-noetic-catkin \
      ros-noetic-tf \
      ros-noetic-tf2-ros \
      ros-noetic-tf2-tools \
      python3-pip && \
    pip3 install -r /tmp/requirements.txt && \
    pip3 install \
    paho-mqtt \
    rospkg \
    catkin_pkg \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init && rosdep update
