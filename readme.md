## 一、项目概况 & 目录结构

### 1. 项目概况


`Central Communication` 模块主要负责配送机器人执行逻辑的处理, 以及机器人与各个子系统之间的通信协调. 它需要确保任务能攻可靠执行、状态可以实时反馈、机器人发生异常可以及时上报给后台以便实时处理.

#### 1.1 执行逻辑

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/机器人逻辑.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 1 配送机器人执行逻辑</figcaption>
</figure>

如图1, 机器人运行遵循一套明确定义的状态机, 涵盖了从待命到执行、返回以及异常处理的完整生命周期.

* rest (休眠/待命状态)

  机器人处理休眠/待命模式, 等待后端通过MQTT下发指令 (如: 重定位`reset_address`, 移动`move` 和 执行特殊命令`execute_command`等).

  如果指令执行超时或失败, 机器人会回退到该状态, 保证系统安全.

* idle (空闲状态)

  表示机器人已准备好接受新任务. 后台系统一旦分配任务, 机器人状态切换为任务执行阶段.

* task (任务执行状态)

  机器人进入任务执行流程, 包括: 前往目标位置, 扫描/校验二维码, 执行货物投递以及用户取货操作, 上报任务执行结果 (成功或失败).

* back (返回状态)

  新的任务需要补货, 或者任务完成或者任务被取消, 机器人会返回站点或补货点, 该状态包含多种情况: 正常返回、执行任务失败后返回、中途取消任务后的返回、执行新的任务需要返回补货的返回.

* exce (异常状态)

  当机器人遇到严重异常 (如导航失败、目标点不可达) 时, 无论当前处于哪种状态, 都会立即切换到异常模式, 等待后台系统介入或人工协助.

这一状态机机制保证了任务的完整闭环处理, 并为异常恢复与监控提供了清晰的切入点.

#### 1.2 系统通信

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/通信协议.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:60%;" />
  <figcaption>图 2 配送机器人与其他子系统间交互使用的通信协议</figcaption>
</figure>

在通信架构上, 如图2, `central communication` 承担了多层协议的对接与协调:

* ROS层:

  负责机器人底盘控制、传感器数据、定位与导航底层功能.

* MQTT协议:

  用于机器人与后台系统、售货机之间的轻量级实时通信, 包括特殊指令任务下发、状态上报、取货/出货等事件通知.

* RESTful API:

  用于后台系统与机器人 `central communication` 之间的业务数据的交换与控制, 负责具体配送订单信息的通知、电梯流程的初始化与同步、机器人任务执行状态的主动上报等.

### 2. 目录结构

```lua
AIbot_projects/catkin_ws/src/robot_v5
	├── scripts
	│			└── executor.py
	├── src/robot_v5
	│			├── dataInfo.py
	│			├── elevatorFlowGetter.py
	│			├── encryptioin.py
	│			├── executor.py
	│			├── fetchTask.py
	│			├── httpClient.py
	│			├── mock.py
	│			├── mock_ros.py
	│			├── mqttClient.py
	│			├── qrCode.py
	│			├── rosSub.py
	│			├── timeoutMonitor.py
	│			└── vendingMqtt.py
	├── CMakeLists.txt
	├── package.xml
	└── setup.py
```

```lua
AIbot_projects/
	└── vending_test.py
```

内容说明:

* `scripts/`

  * `executor.py`: 项目的入口脚本之一, 用于将 `robot_v5` 以ROS节点的形式运行, 以ROS中的 `rosrun` 或者 `roslaunch` 的方式使用, 也方便编写开机自启脚本 (systemd) 来自动启动机器人逻辑.

* `src/robot_v5/`

  包含项目的核心功能模块, 每个 `.py` 文件对应一个功能单元:

  * `dataInfo.py`: 是项目的核心数据结构与状态管理模块, 主要负责集中存储和维护机器人运行过程中的各种状态信息、任务信息以及与后台/电梯交互的数据.
  * `elevatorFlowGetter.py`: 是电梯任务的状态监听模块, 它通过后台接口轮询实时获取电梯点位和状态, 并同步更新到机器人执行器中, 确保机器人能够正确完成跨楼层任务.
  * `encryption.py`: 通过 MD5 签名 + AES-CBC 加密/解密机制, 为机器人和后台之间的 HTTP 通信提供了身份验证与数据安全保障.
  * `executor.py`: 是项目的核心控制模块, 整合了所有子系统, 通过 多线程 + 定时任务调度 + 超时监控, 保证任务执行的可靠性和健壮性. 所有与任务生命周期相关的操作 (接收、执行、上报、异常处理) 都在这里实现.
  * `fetchTask.py`: 机器人接收任务的入口模块, 保证机器人不会错过任务分配, 并且能够正确响应后台下发的任务变化 (新任务、取消、补货).
  * `httpClient.py`: 是机器人与后台交互的HTTP 通道, 对任务、状态、电梯、异常、图像等接口进行了统一封装, 所有与后台的同步通信都通过它完成.
  * `mock.py`: 是一个调试脚本, 主要目的是模拟发送目标点 (Goal) 消息给导航模块 (tianxin), 方便在没有完整后台/机器人逻辑时进行局部测试.
  * `mock_ros.py`: 是一个调试与模拟工具, 不属于正式执行逻辑, 可以在没有真实硬件的情况下验证机器人上层任务调度逻辑, 便于单独测试 `executor`、`timeoutMonitor`、`rosSub` 等模块对信号的处理能力.
  * `mqttClient.py`: 完成机器人和后台之间的实时消息通信, 保障机器人和后台之间的低延迟双向通信、提供状态上报和指令接收的统一接口以及支持自动重连和掉线检测，提高系统可靠性, 与 `httpClient.py` 的请求/响应模式互补.
  * `rosSub.py`: 是机器人系统的ROS 数据输入层, 将底层传感器和规划模块的消息实时转换为上层逻辑可用的状态.
  * `timeoutMonitor.py`: 是任务状态的超时检测工具, 运行独立线程, 不干扰主逻辑. 与 `executor` 和 `programStatus` 紧密结合, 提供任务执行过程中的超时保护, 从而确保任务流程在异常情况下能够及时检测并转入异常处理逻辑, 而不会无限等待.
  * `vendingMqtt.py`: 是机器人和售货机之间的 MQTT 通信模块, 独立于主控 MQTT, 用于专门处理货物交付相关的消息交互.
  * `qrCode.py`: 本模块是针对扫码枪的独立调试工具, 用于在开发和集成过程中验证扫码器是否能正常工作. 在当前系统架构中, 扫码逻辑已被 `vendingMqtt.py` 的交互替代, 本模块未被调用. 可在需要时单独运行, 进行扫码器功能验证. 不影响主逻辑, 删除或保留均不会影响机器人核心执行流程.
  
* `CMakeLists.txt`: ROS 的标准构建配置文件, 用于定义依赖、编译规则和安装目标.

* `package.xml`: ROS 在构建和依赖解析时读取的元信息文件, 声明了包名、作者、依赖关系等.

* `setup.py`: 用于配置 `robot_v5` Python 包的安装路径, 确保在 ROS 构建过程中可以正确导入和使用该模块.

* `vending_test.py`: 用于验证 `vending/client`/`vending/server` 两个 Topic 的消息格式与收发链路; 不参与主逻辑流程.

## 二、依赖 & 环境准备

### 1. 基础环境

- 操作系统: Ubuntu 20.04
- ROS 版本: ROS Noetic
- Python 版本: 3.12.7
- 虚拟环境: conda, 环境名称为 `aibotenv`

创建环境示例: 

```
conda create -n aibotenv python=3.12.7
conda activate aibotenv
```

### 2. Python 依赖

项目使用的主要 Python 库如下：

#### 2.1 系统库

`datetime`、`enum`、`threading`、`copy`、`subprocess`、`argparse`、`uuid`、`logging`、`json`、`secrets`、`hashlib`、`base64`、`time` (Python 标准库, 自带, 无需额外安装)

#### 2.2 第三方库

- ROS 相关
  - `rospy`
  - `geometry_msgs`
  - `nav_msgs`
  - `std_msgs`
  - `tf.transformations`
  - `woosh_msgs` (自定义消息包，需要在工作空间内编译)
  - `robot_v3.msg.Goal_v3` (自定义消息包，需要在工作空间内编译)
- 网络通信
  - `paho-mqtt` (MQTT 通信)
  - `requests` (HTTP 请求)
  - `flask` (内置调试 HTTP 服务)
  - `werkzeug` (Flask 依赖)
- 加密安全
  - `pycryptodome` (AES CBC 加解密、MD5 签名等)
- 输入设备
  - `evdev` (用于扫码枪输入)
- 任务调度
  - `schedule` (定时任务调度器)

安装示例：

```bash
pip install paho-mqtt requests flask werkzeug pycryptodome evdev schedule
```

### 3. ROS 依赖

确保以下 ROS 包已经安装：

```bash
sudo apt install ros-noetic-geometry-msgs \
                 ros-noetic-nav-msgs \
                 ros-noetic-std-msgs \
                 ros-noetic-tf \
                 ros-noetic-message-generation \
                 ros-noetic-message-runtime
```

此外，需要在 `catkin_ws` 下编译以下自定义消息包：

- `woosh_msgs`
- `robot_v3`

### 4. 环境配置

进入工作空间 `catkin_ws`, 编译项目:

```bash
cd ~/AIbot_projects/catkin_ws
catkin_make
```

设置环境变量:

```bash
source ~/AIbot_projects/catkin_ws/devel/setup.bash
conda activate aibotenv
```

### 5. real sense 摄像头

step 1: 现在home下建一个新的folder "library".

step 2: 把这个 https://github.com/IntelRealSense/librealsense/tree/v2.4.2 放入library 编译

```bash
#在 /home/library 下:
git clone https://github.com/IntelRealSense/librealsense.git
cd librealsense
git fetch --tags
git checkout tags/v2.42.0 -b v2.42.0-local

sudo apt update
sudo apt install -y build-essential cmake git \
  libusb-1.0-0-dev pkg-config libgtk-3-dev libssl-dev \
  libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev

# 安装 RealSense 的 udev 规则
./scripts/setup_udev_rules.sh
# 运行后按提示重新插拔相机或重载 udev
```

step 3: 然后sudo make install 到系统

```bash
mkdir build && cd build
cmake .. -DBUILD_EXAMPLES=ON -DBUILD_GRAPHICAL_EXAMPLES=ON
make -j"$(nproc)"
sudo make install
sudo ldconfig

#自检
# 查看 SDK 版本（应显示 2.42.0）
pkg-config --modversion realsense2

# 没装到 viewer 也没关系，至少跑这个看是否能枚举到相机：
rs-enumerate-devices
# 或者如果编出了 viewer
realsense-viewer
```

step 4: 之后在把 https://github.com/IntelRealSense/realsense-ros/tree/2.2.22 这个放入ros里面 编译

```bash
# 建议在 ~/catkin_ws/src 下，而不是 /home/library
# mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src

git clone https://github.com/IntelRealSense/realsense-ros.git
cd realsense-ros
git fetch --tags
git checkout 2.2.22    # 关键：与 SDK 2.42.0 匹配的 ROS1 版本
cd ..

# 依赖（尤其是 ddynamic_reconfigure）：
sudo apt install -y ros-noetic-ddynamic-reconfigure
# 也可以用 rosdep 一次性装：
# rosdep install --from-paths . --ignore-src -r -y

cd ~/catkin_ws
catkin_make

source ~/catkin_ws/devel/setup.bash
roslaunch realsense2_camera rs_camera.launch
```

**摄像头部分还没有在新的机器人上安装驱动, 但是以上方法完全正确(在旧机器人上安装过了), 可以根据后面的业务流程来决定需不需要安装**.



## 三、通信接口定义

### 1. MQTT 

机器人主动向后台上报状态消息.

#### 1.1 机器人主动通信

##### 1.1.1 话题1 - robots/{stationId}/{robotId}/state

消息示例:

```json
{
  "localization": { "x": 12.34, "y": 5.67, "z": 0.00 },
  "ip": "172.1.2.3"
  "floor": "", 
  "house": "",
  "coordinateType": "map",
  "robotStatus": "offline",
  "robotTaskId": 0,
  "connection": "offline",
  "battery": 87,
  "fault": false
}
```

配置:

* QOS: 0
* Retain: False
* 周期性发布

字段说明:

| 字段           | 类型   | 说明                   | 必填 |
| -------------- | ------ | ---------------------- | ---- |
| localization   | object | 机器人当前位置         | 是   |
| ip             | string | 机器人的IP地址         | 是   |
| floor          | string | 机器人当前的楼层       | 是   |
| house          | string | 机器人当前的楼         | 是   |
| coordinateType | string | 地图坐标类型           | 是   |
| robotStatus    | string | 机器人当前的状态       | 是   |
| robotTaskId    | int    | 机器人当前执行的任务ID | 是   |
| battery        | int    | 机器人剩余电量百分比   | 是   |
| connection     | string | 机器人连接状态         | 是   |
| fault          | bool   | 机器人是否发生故障     | 是   |

`robotStatus` 字段说明:

| 值   | 含义                     |
| ---- | ------------------------ |
| rest | 睡眠模式, 不可以接收任务 |
| idle | 空闲模式, 可以接收任务   |
| task | 任务模式, 正在执行任务   |
| exce | 异常模式, 机器人发生异常 |

##### 1.1.2 话题2 - robots/{stationId}/{robotId}/connection

**1** - 机器人上线后主动发布:

```json
{
  "status": "online",
  "reason": "startup"
}
```

**2** - 机器人异常下线则利用MQTT last will 发布离线信息

```json
{
  "status": "offline",
  "reason": "disconnect"
}
```

**3** - 机器人正常退出发布离线消息

```json
{
  "status": "offline",
  "reason": "shutdown"
}
```

配置:

* QOS: 1
* Retain: True
* 需要时发布

##### 1.1.3 话题3 - robots/{stationId}/{robotId}/network/ip

消息示例:

```json
{
  "interface": "wireguard",
  "ip": "10.25.0.6",
  "timestamp": "2025-07-05T10:30:00Z"
}
```

配置:

* QOS: 1
* Retain: False
* 需要时发布

##### 1.1.4 话题4 - robots/{stationId}/{robotId}/signal

消息示例:

```json
{
  "signal": signal
}
```

#### 1.2 后台主动通信

##### 1.2.1 话题5 - robots/{stationId}/{robotId}/command

MQTT 后台发布特殊指令, type: 

* 重定位:`reset_address`

  ```json
  {
    "address":{
      "dock_settings":{"identify":"","verify":""},
      "identity":{"desc":"NIC-2M-HR03","id":3850517013,"no":"E5823A15"},
      "navigation":{"arrival_method":2},
      "pose":{
        "dock":{"theta":-1.5700000524520874,"x":-17.7199993,"y":-0.6800000071525574},
        "real":{"theta":1.5099999904632568,"x":-17.7199993,"y":-0.6800000071525574}},
      "stationId":18839843720,
      "stationName":"小区001",
      "house":"ntuitive",
      "floor":"2m"
    },
    "type":"reset_address"
  }
  ```

* 移动:

  ```json
  {
    'type': 'move', 
    'address': {
      'dock_settings': {'identify': '', 'verify': ''}, 
      'identity': {'desc': 'NIC-2M-HR03', 'id': 3850517013, 'no': 'E5823A15'}, 
      'navigation': {'arrival_method': 2}, 
      'pose': {
        'dock': {'theta': -1.5700000524520874, 'x': -17.7199993, 'y': -0.68000000}, 
        'real': {'theta': 1.5099999904632568, 'x': -17.71999931, 'y': -0.68000000}}, 
      'stationId': 18839843720, 
      'stationName': '小区001', 
      'house': 'ntuitive', 
      'floor': '2m'
    }, 
    'addressList': '[{"dock_settings":{"identify":"","verify":""},"identity":{"desc":"NIC-2M-HR03","id":3850517013,"no":"E5823A15"},"navigation":{"arrival_method":2},"pose":{"dock":{"theta":-1.5700000524520874,"x":-17.719999313354492,"y":-0.6800000071525574},"real":{"theta":1.5099999904632568,"x":-17.719999313354492,"y":-0.6800000071525574}},"stationId":18839843720,"stationName":"小区001","house":"ntuitive","floor":"2m"}]'
  }
  ```

  ```json
  'addressList': [
    {
      "dock_settings":{"identify":"","verify":""},
      "identity":{"desc":"NIC-2M-HR03","id":3850517013,"no":"E5823A15"},
      "navigation":{"arrival_method":2},
      "pose":{
        "dock":{"theta":-1.5700000524520874,"x":-17.71999931,"y":-0.6800000071525574},
        "real":{"theta":1.5099999904632568,"x":-17.7199993,"y":-0.6800000071525574}},
      "stationId":18839843720,
      "stationName":"小区001",
      "house":"ntuitive",
      "floor":"2m"
    }]
  ```

* 模式切换:

  ```json
  {
    'type': 'switch_status', 
    'status': 'rest'
  }
  ```

* 执行 -- 重启:

  ```json
   {
     'type': 'execute_command', 
     'commandContent': 'cd /Personaldata/Program/Ros/\n\n./control.sh stop\n\n./control.sh start'
   }
  ```

### 2. RESTful API

机器人与后台利用此部分接口进行交互. 机器人为Client主动发送请求, 后台为server返回响应.

##### 2.1 接口1 - POST `/api/robot/client/selectTaskInfo`

周期性调用该接口获得任务的最新状态.

机器人请求示例:

```json
{
  "taskId": <int>,
  "floor": <string>,
  "building": <string>
  "timestamp": <string>,
  "uuid": <string>
}
```

参数说明:

| 字段      | 说明                         |
| --------- | ---------------------------- |
| taskId    | 当前机器人正在执行的任务的ID |
| floor     | 当前机器人位于的楼层         |
| building  | 当前机器人位于的楼           |
| timestamp | 发送请求的时间戳             |
| uuid      | 通用唯一标识符               |

根据后台响应中的`status`字段判断任务是否被取消.

后台响应示例:

```json
{
  'code': 0, 
  'data': {
    'code': 'f4140ccd0bc3ab835427593f3f30ce37', 
    'addressList': [
      {'navigation': {'arrival_method': 2}, 
       'pose': {
         'real': {'x': 2.71000003, 'y': -0.56999999, 'theta': -2.1800000}, 
         'dock': {'x': 2.71000003, 'y': -0.56999999, 'theta': -2.28999996}}, 
       'identity': {'no': 'E584FA80', 'id': 3850697344, 'desc': 'PARKINGSITE'}, 
       'stationName': '小区001', 
       'floor': '2m', 
       'house': 'ntuitive_align', 
       'dock_settings': {'identify': '', 'verify': ''}, 
       'stationId': 18839843720
      } ], 
    'taskInfo': {
      'addressList': [
        {'navigation': {'arrival_method': 2}, 
         'pose': {'real': {'x': 2.40000009, 'y': -25.62999, 'theta': -0.66000002}, 
                  'dock': {'x': 2.40000009, 'y': -25.62999, 'theta': -2.23000001}}, 
         'identity': {'no': '30376E4E', 'id': 808939086, 'desc': 'NIC-2M-08'}, 
         'stationName': '小区001', 
         'floor': '2m', 
         'house': 'ntuitive_align', 
         'dock_settings': {'identify': '', 'verify': ''}, 
         'stationId': 18839843720} ], 
      'addressParams': {'$ref': '$.data.taskInfo.addressList[0]'}, 
      'createTime': 1757306301000, 
      'id': 21645501415, 
      'orderId': 20446540381, 
      'robotId': 18950214603, 
      'spaceParams': {
        'spaceList': [
          {'spaceId': 19846681846, 
           'quantity': 1, 
           'productId': 18946654944, 
           'spaceNo': '01'} ] }, 
      'stationId': 18839843720, 
      'status': 30, 
      'updateTime': 1757306301000, 
      'userId': 19253437857
    }, 
    'restArea': {'$ref': '$.data.addressList[0]'}
  }, 
  'msg': '操作成功'
}
```

##### 2.2 接口2 -POST `/api/robot/client/reportTaskProcess`

当机器人到达目的地 / 机器人完成配送 / 机器人配送失败, 调用该接口通知后台.

机器人请求示例:

```json
{
	"taskId": <int>,
	"taskStatus": <int>,
	"step": <string>
	"timestamp": <string>,
	"uuid": <string>
}
```

参数说明:

| 字段       | 说明                       |
| ---------- | -------------------------- |
| taskId     | 机器人当前执行任务的ID     |
| taskStatus | 机器人向后台上报的关键状态 |
| step       | 机器人执行的步骤           |
| timestamp  | 发送请求的时间戳           |
| uuid       | 通用唯一标识符             |

`taskStatus`字段说明:

| taskStatus                 | 数值 |
| -------------------------- | ---- |
| PENDING_RECEIPT 待签收     | 40   |
| DELIVERY_FAILED 配送失败   | 80   |
| DELIVERY_COMPLETE 配送完成 | 50   |

后台响应示例:

```json
{
	"code":0,
	"msg":"操作成功",
	"data":{}
}
```

##### 2.3 接口3 - POST `/api/robot/client/reportRobotCollect`

机器人达到关键节点上传图像\视频. 以及贩卖机部分出现错误在这里上传.

机器人请求示例:

```json
{
  "type": <string>,
  "data": <base64>,
  "timestamp": <string>,
  "uuid": <string>
}
```

参数说明:

| 字段      | 说明                               |
| --------- | ---------------------------------- |
| type      | "image" 或者 "video" 或者 错误类型 |
| data      | base64-image                       |
| timestamp | 发送请求的时间戳                   |
| uuid      | 通用唯一标识符                     |

##### 2.4 接口4 - POST `/api/robot/client/reportRobotWarn`

机器人遇到需要人为干预才能解决的故障时调用这个接口.

机器人请求示例:

```json
{
  "taskId": <int>,
  "type": <string>,
  "timestamp": <string>,
  "uuid": <string>
}
```

参数说明:

| 字段      | 说明                                                  |
| --------- | ----------------------------------------------------- |
| taskId    | 当前机器人执行的任务ID, 如果不为0则后台会发送取消任务 |
| type      | 错误/故障类型                                         |
| timestamp | 发送请求的时间戳                                      |
| uuid      | 通用唯一标识符                                        |

##### 2.5 接口5 - POST `/api/robot/client/setElevatorControlFlowInfo`

机器人需要坐电梯时主动通过这个接口发送请求, 开启坐电梯的流程.

机器人请求示例:

```json
{
  "flowId": <string>,
  "status": <int>,
  "stamp": <timestamp>,
  "robotId": <string>,
  "taskId": <int>,
  "fromHouse": <string>,
  "toHouse": <string>,
  "fromFloor": <string>,
  "toFloor": <string>,
  "fromElevatorOutAddress": <dict>,
  "fromElevatorInAddress": <dict>,
  "toElevatorOutAddress": <dict>,
  "toElevatorInAddress": <dict>
}
```

参数说明:

| 字段                   | 说明                                  |
| ---------------------- | ------------------------------------- |
| flowId                 | 流程ID, uuid                          |
| status                 | 电梯运行状态                          |
| stamp                  | 时间戳                                |
| robotId                | 机器人ID                              |
| taskId                 | 任务ID                                |
| fromHouse              | 机器人运动起始楼                      |
| toHouse                | 机器人运动目标楼                      |
| fromFloor              | 机器人运动起始层                      |
| toFloor                | 机器人运动目标层                      |
| fromElevatorOutAddress | 机器人出发位置对应电梯/门禁外的坐标点 |
| fromElevatorInAddress  | 机器人出发位置对应电梯/门禁内的坐标点 |
| toElevatorOutAddress   | 机器人目标位置对应电梯/门禁外的坐标点 |
| toElevatorInAddress    | 机器人目标位置对应电梯/门禁内的坐标点 |

后台响应示例:

```json
{
  'id': '58b6f31b-f8ce-4fb3-b2f2-6a68c9093be9', 
  'status': 20, 
  'stamp': 1757031769000, 
  'stationId': 18839843720, 
  'robotId': 18950214603, 
  'fromHouse': 'ntuitive_align', 
  'toHouse': 'ntuitive_align', 
  'fromFloor': '2m', 
  'toFloor': '1', 
  'fromElevatorOutAddress': {
    'navigation': {'arrival_method': 2}, 
    'pose': {
      'real': {'x': 30.06999969482422, 'y': -4.0, 'theta': 0.27000001072883606}, 
      'dock': {'x': 30.06999969482422, 'y': -4.0, 'theta': 0.30000001192092896} }, 
    'identity': {'no': 'F4AE2E9A', 'id': 4105055898, 'desc': 'SL1_ELEVATOR_1_2_2_out'}, 
    'stationName': '小区001', 
    'floor': '2m', 
    'house': 'ntuitive_align', 
    'room': 'SL1_ELEVATOR_1_2_2_out', 
    'dock_settings': {'identify': '', 'verify': ''}, 
    'stationId': 18839843720 
  }, 
  'fromElevatorInAddress': {
    'navigation': {'arrival_method': 2}, 
    'pose': {
      'real': {'x': 33.63999938964844, 'y': -5.6500000, 'theta': 0.3700000047683716}, 
      'dock': {'x': 33.63999938964844, 'y': -5.6500000, 'theta': 0.3699999749660492}}, 
    'identity': {'no': 'E590F085', 'id': 3851481221, 'desc': 'PL1_ELEVATOR_1_1_1_in'}, 
    'stationName': '小区001', 
    'floor': '2m', 
    'house': 'ntuitive_align', 
    'room': 'PL1_ELEVATOR_1_1_1_in', 
    'dock_settings': {'identify': '', 'verify': ''}, 
    'stationId': 18839843720
  }, 
  'toElevatorOutAddress': {}, 
  'toElevatorInAddress': {
    'navigation': {'arrival_method': 2}, 
    'pose': {
      'real': {'x': 32.619998931884766, 'y': -3.23000001, 'theta': -2.809999942779541}, 
      'dock': {'x': 32.619998931884766, 'y': -3.23000001, 'theta': 0.3699999749660492}}, 
    'identity': {'no': 'E578A0C3', 'id': 3849887939, 'desc': 'SL1_ELEVATOR_1_2_2_in'}, 
    'stationName': '小区001', 
    'floor': '1', 
    'house': 'ntuitive_align', 
    'room': 'SL1_ELEVATOR_1_2_2_in', 
    'dock_settings': {'identify': '', 'verify': ''}, 
    'stationId': 18839843720
  }, 
  'createTime': '2025-09-05 16:22:46', 
  'flowId': '58b6f31b-f8ce-4fb3-b2f2-6a68c9093be9'
}
```

##### 2.6 接口6 - POST `/api/robot/client/getElevatorControlFlowInfo`

开始电梯流程后, 机器人主动调用接口获取最新的电梯流程信息

机器人请求示例:

```json
{"flowId": <string> }
```

参数说明:

| 字段   | 说明                        |
| ------ | --------------------------- |
| flowId | 流程ID, uuid, 与set保持一致 |

### 3. ROS 

机器人内部通信使用.

##### 3.1 话题6 -  `/goal_v3`

类型: 自定义消息 - Publisher: 通信系统; Subscriber: 导航系统

```
geometry_msgs/PoseStamped pose
string floor
string house
bool relocation
bool stop
```

机器人收到配送的目标地址后将数据转换成 `geometry_msgs/PoseStamped` 类型, 附加楼层发送给planning部分.

如果是重定位点位, 则设置 relocation 为 True.

如果需要机器人停止运行, 则设置 stop 为 True.

##### 3.2 话题7 -  `/signal`

类型: std_msgs.String - Publisher: 导航系统; Subscriber: 通信系统

参数:

| 参数                | 说明                 |
| ------------------- | -------------------- |
| GOAL_RECEIVED       | 移动目标位置信息收到 |
| GOAL_ARRIVED        | 移动目标位置到达     |
| STOP_RECEIVED       | 停止运动信号收到     |
| STOP_COMPLETE       | 停止运动完成         |
| RELOCATION_RECEIVED | 重定位坐标点信息收到 |
| RELOCATION_COMPLETE | 重定位完成           |
| GOAL_Failed:......  | 发生故障             |

##### 3.3 话题8 -  `/battery`

类型: woosh_msgs/battery - Publisher: 机器人底盘; Subscriber: 通信系统

只需要接收一个字段: 电池电量剩余百分比 - `msg.batteryPercentage`

##### 3.4 话题9 -  `/global_localization`

类型: Odometry - Publisher: 导航系统; Subscriber: 通信系统

接收后转为 x, y, yaw 的形式转发给后台系统



## 四、模块说明

### 1. `dataInfo.py`

#### 1.1 介绍

 `dataInfo.py` 是项目的核心数据结构与状态管理模块, 主要负责集中存储和维护机器人运行过程中的各种状态信息、任务信息以及与后台/电梯交互的数据. 并且提供线程安全的访问与更新接口, 保证多线程环境下的数据一致性.

#### 1.2 作用

* 集中存储: 将机器人运行需要的各种状态与任务信息封装在统一的数据类中, 避免数据分散在各个模块.
* 线程安全: 所有更新和读取方法都基于 `threading.Lock`, 确保多线程环境下不会出现数据竞争.
* 标准接口: 提供了清晰的 `update_*`, `get_*`, `reset_*` 接口, 便于其他模块调用.
* 扩展性: 当后续需要增加新的状态或任务字段时, 可以直接在本模块中扩展, 不会影响其他逻辑模块.

#### 1.3 核心功能

##### 1.3.1 任务状态枚举

```python
class TaskStatus(Enum):
```

定义了机器人执行任务过程中会发生的状态, 用于统一表示任务执行生命周期.

具体定义如下:

| 状态                        | 代表数值 | 是否与机器人相关 |
| --------------------------- | -------- | ---------------- |
| 待确认 PENDING_COMFIRMATION | 0        | 否               |
| 待支付 PENDING_PAYMENT      | 10       | 否               |
| 待配送 PENDING_DELIVERY     | 20       | 是               |
| 配送中 DELIVERING           | 30       | 是               |
| 待签收 PENDING_RECEIPT      | 40       | 是               |
| 已完成 DELIVERY_COMPLETE    | 50       | 是               |
| 已取消 CANCELLED            | 60       | 是               |
| 已关闭 CLOSED               | 70       | 否               |
| 配送失败 DELIVERY_FAILED    | 80       | 是               |
| 补货中 RESTOCKING           | 90       | 是               |

其中需要由机器人主动发起状态改变的有: 待签收、已完成 和 配送失败:

* 配送中 $\to$ 待签收: 当机器人移动到用户住址, 机器人通过调用*接口2*主动通知后台任务状态改为待签收.
* 待签收 $\to$ 已完成: 当用户成功扫描核对二维码后判定为任务执行完成, 机器人通过调用*接口2*主动通知后台任务状态改为已完成.
* 待签收 $\to$ 配送失败: 当用户没有在规定时间内成功核对二维码, 机器人通过调用*接口2*主动通知后台任务状态改为配送失败.

##### 1.3.2 机器人运行状态

```python
class RobotStateInfo:
```

保存机器人实时状态, 包括: 定位信息、楼层、所在建筑物、IP地址、连接状态、电池电量、是否故障等.

具体字段定义如下:

| 变量           | 类型   | 说明                   | 更新方法                        |
| -------------- | ------ | ---------------------- | ------------------------------- |
| localization   | dict   | 机器人的位置坐标       | update_localzation(x, y, theta) |
| ip             | string | 机器人IP地址           | update_ip(ip)                   |
| floor          | string | 机器人所在楼层         | update_position(floor, house)   |
| house          | string | 机器人所在建筑         | update_position(floor, house)   |
| coordinateType | string | 坐标类型               | 默认为“map“, 没有更新方法       |
| robotStatus    | string | 机器人状态             | update_robotStatus(robotStatus) |
| robotTaskId    | int    | 机器人执行的任务ID     | update_robotTaskId(taskId)      |
| connection     | string | 机器人联网状态         | update_connection(connection)   |
| battery        | int    | 机器热电池电量(百分比) | update_battery(battery)         |
| fault          | bool   | 机器人是否故障         | update_fault(fault)             |

除`update_*` 类的方法用于在运动中动态刷新对应字段外, 提供 `get_state()`  方法方便其他模块获取机器人当下的运行状态.

##### 1.3.3 后台任务状态

```python
class StatusBackend:
```

用于记录和维护后台系统推送的任务执行状态, 方便与最新的任务状态进行核对, 保证任务状态的同步.

| 变量   | 类型 | 说明                       | 更新方法                             |
| ------ | ---- | -------------------------- | ------------------------------------ |
| taskId | int  | 后台推送给机器人的任务ID   | update_statusBackend(taskId, status) |
| status | int  | 机器人执行的任务的后台状态 | update_statusBackend(taskId, status) |

除`update_*` 类的方法用于在运动中动态刷新对应字段外, 提供 `get_statusBackend()`  方法方便其他模块获取后台推送给机器人执行的任务的当下的运行状态.

##### 1.3.4 当前订单信息

```python
class CurrentOrder:
```

保存当前任务的详细信息, 如任务ID、二维码、目标点位、返回点位、货品信息等. 提供增量更新接口 (追加目标点/货品信息), 以及任务结束后的重置方法.

| 变量             | 类型   | 说明                       | 更新方法                                |
| ---------------- | ------ | -------------------------- | --------------------------------------- |
| taskId           | int    | 当前执行任务的ID           | update_deliveryDetails(taskId, code)    |
| code             | string | 当前订单对应的二维码       | update_deliveryDetails(taskId, code)    |
| goal_positions   | list   | 要走到的对应地址的位置信息 | update_goalPositions(goal_pos_dict)     |
| return_positions | list   | 返回的对应地址的位置信息   | update_returnPositions(return_pos_dict) |
| delivery_info    | list   | 要配送的货品的数量与货道号 | update_deliveryInfo(cargo_dict)         |

除`update_*` 类的方法用于更新对应字段外, 提供 `get_currenOrder()`  方法方便其他模块获取当前机器人执行的状态的详细信息, 以及 `reset_currentOrder()` 方便其他模块在需要的时候重置当前任务详细信息.

##### 1.3.5 指令信息

```python
class InstructionInfo:
```

记录后台下发的特殊指令, 包括重定位点位信息、需要移动的点的集合以及命令内容.

| 变量                    | 类型   | 说明           | 更新方法                                          |
| ----------------------- | ------ | -------------- | ------------------------------------------------- |
| relocalization_position | dict   | 重定位坐标信息 | update_relocalizationInfo(position, floor, house) |
| floor                   | string | 重定位楼层信息 | update_relocalizationInfo(position, floor, house) |
| house                   | string | 重定位建筑信息 | update_relocalizationInfo(position, floor, house) |
| movePositions           | list   | 移动坐标点位   | update_movePositions(move_dict)                   |
| command                 | string | 特殊指令       | update_command(commandContent)                    |

除`update_*` 类的方法用于更新对应字段外, 提供 `get_*()`  方法方便其他模块获取需要的数据的详细信息, 以及 `reset_*()` 方便其他模块在需要的时候重置对应数据信息.

##### 1.3.6 程序执行状态

```python
class ProgramStatus:
```

记录程序运行中的执行状态, 提供基于条件变量的通知机制, 便于线程之间的同步.

| 变量          | 类型   | 说明                 | 更新方法                            |
| ------------- | ------ | -------------------- | ----------------------------------- |
| programStatus | string | 机器人程序执行的状态 | update_programStatus(programStatus) |

除`update_programStatus` 类的方法用于更新pogramStatus字段并且通知所有等待状态的线程外, 提供 `get_programStatus()`  方法方便其他模块获取实时程序状态信息, 以及 `reset_programStatus()` 方便其他模块在需要的时候重置程序状态信息.

##### 1.3.7 电梯交互数据

```python
class ElevatorControl:
```

保存机器人与电梯交互的相关数据, 包括机器人ID、任务ID、楼层信息、电梯/门禁门口/内部点位信息等. 提供更新和重置方法, 用于多层楼配送时的电梯控制.

| 变量                   | 类型   | 说明                 | 更新方法                              |
| ---------------------- | ------ | -------------------- | ------------------------------------- |
| status                 | int    | 目前电梯的执行状态   | update_elevatorStatus(elevatorStatus) |
| robotId                | int    | 机器人ID             | update_basicInfo(robotId, taskId)     |
| taskId                 | int    | 正在执行的任务ID     | update_basicInfo(robotId, taskId)     |
| fromFloor              | string | 机器人出发楼层       | update_floorInfo(fromFloor, toFloor)  |
| toFloor                | string | 机器人要走到的楼层   | update_floorInfo(fromFloor, toFloor)  |
| fromElevatorOutAddress | dict   | 起始电梯门口的点位   | update_fromElevatorOutAddress()       |
| fromElevatorInAddress  | dict   | 起始电梯内部的点位   | update_fromElevatorInAddress()        |
| toElevatorOutAddress   | dict   | 目的电梯外部点位     | update_toElevatorOutAddress()         |
| toElevatorInAddress    | dict   | 目的电梯内部(重定位) | update_toElevatorInAddress()          |

除`update_*` 类的方法用于实时更新各个变量外, 提供 `get_elevatorControlParams()`  方法方便其他模块获取实时电梯流程信息, 以及 `reset_elevatorControlParams()` 方便其他模块在电梯流程结束时重置相关数据信息.

##### 1.3.8 信号类

```python
class Signal:
```

用于存储一个简单的字符串信号, 当前没有实际使用, 可考虑删除或者保留作为扩展接口.



### 2. `elevatorFlowGetter.py`

#### 2.1 介绍

`elevatorFlowGetter.py` 模块的主要负责在机器人执行跨楼层任务时, 定期从后台系统获取电梯流程的状态信息, 并同步更新到机器人本地的电梯控制参数中.

#### 2.2 作用

通过定时轮询的方式, 监控指定 `flowId` 的电梯任务进展, 确保机器人在跨楼层任务中始终拥有最新的电梯点位信息和状态, 从而驱动机器人在电梯交互流程中的行为调整, 实现电梯内外点位导航的正确切换.

#### 2.3 核心功能

##### 2.3.1 初始化参数

- `owner`：执行器（executor）实例, 用于调用 HTTP 客户端和更新机器人本地状态.
- `flow_id`：本次电梯流程的唯一标识.
- `period`：轮询周期, 默认 5 秒.

##### 2.3.2 属性

- `_stop`：线程事件标志, 用于控制停止.
- `_sched`：调度器（基于 `schedule` 库）.
- `_thread`：后台线程，定期运行 `get()` 方法.
- `_job`：已注册的定时任务.

##### 2.3.3 方法

- `start()`：启动电梯流程监听线程, 注册定时任务并立即执行一次 `get()`.
- `stop()`：停止监听, 取消定时任务.
- `run()`：后台线程循环运行, 执行调度器里的定时任务.
- `get()`：调用后台接口获取电梯流程状态, 并更新本地状态.

##### 2.3.4 执行逻辑

1. 定时调用后台接口 `http_client.get_elevatorControlFlow(flowId=flow_id)`.

2. 获取后台返回的 `flowInfo`，解析出以下字段：

   - `status`（电梯流程当前状态）

   - `fromElevatorOutAddress`（电梯外部入口坐标）

   - `fromElevatorInAddress`（电梯内部入口坐标）

   - `toElevatorOutAddress`（目标电梯出口坐标）

   - `toElevatorInAddress`（目标电梯内部坐标）

3. 更新到 `owner.elevatorControl` 对象中, 供执行器与导航模块使用.
4. 当电梯流程状态达到结束标志（`status == 100` 或 `10000`）,或机器人程序状态变为 `"ready_move"` 时, 自动停止轮询.



### 3. `encryption.py`

#### 3.1 介绍

`encryption.py` 定义了 HttpEncryption 类, 用于在机器人和后台系统之间的 HTTP 通信过程中, 完成 鉴权、数据加密与解密.

#### 3.2 作用

* 为所有 HTTP 请求生成带签名的鉴权头部,实现身份验证.
* 对传输的 JSON 数据 payload 进行 AES-CBC 加密, 避免明文传输敏感信息.
* 对后台返回的密文进行解密, 还原为可解析的明文.
* 校验后台请求或响应的签名, 保证数据未被篡改.

#### 3.3 核心功能

##### 3.3.1 MD5 签名计算

```python
def md5_hex(self, s: str) -> str:
```

输入字符串 → 输出 32 位 MD5 十六进制摘要, 用于生成鉴权签名.

##### 3.3.2 构建鉴权头部

```python
def build_auth_headers(self) -> dict:
```

生成包含随机数 `R`、时间戳 `T`、签名 `S`、机器人编号 `Robot-Id` 的 HTTP 请求头部, 提高安全性, 防止重放攻击.

##### 3.3.3 AES-CBC 加密

```python
def aes_cbc_encrypt(self, plaintext: bytes) -> bytes:
def encrypted_data(self, payload: dict):
```

使用后台分配的 `private_key` 与 `iv_vector`, 对 JSON payload 进行 AES-CBC 模式加密. 输出密文经过 Base64 编码, 保证可安全传输.

##### 3.3.4 AES-CBC 解密

```python
def aes_cbc_decrypt(self, cipher_bytes: bytes) -> bytes:z
def decrypt_response_data(self, data_b64: str) -> dict:
```

将后台返回的密文（Base64 编码）解码并解密, 还原为明文 JSON. 保证后台响应可直接被业务逻辑解析.

##### 3.3.5 签名校验

```python
def verify_headers(self, headers):
```

校验后台请求头中的签名是否正确, 若签名不一致, 则返回 `False`, 防止伪造请求.

**注意**: 虽然目前没有启用加密和解密, 但是相关功能已经测试过, 目前由于处在开发阶段, 暂时决定在接口没有完全确定的情况下先不使用加密解密功能. 在未来如果有需要, 需要与后台配合添加该功能.



### 4. `executor.py`

#### 4.1 介绍

`executor.py` 是项目的核心执行器模块, 负责整合机器人运行时的各个子系统 (ROS、MQTT、HTTP、任务状态机、电梯流程、售卖机交互等), 并以ROS 节点的形式运行.

#### 4.2 作用

1. 系统集成入口
   * 初始化机器人所需的全部核心组件（状态管理、加密认证、MQTT、HTTP 客户端、ROS 发布订阅、售卖机通信等）。
   * 将机器人以 `executor` 节点形式运行，方便与 ROS 生态无缝对接。
2. 任务逻辑驱动
   * 执行完整的任务状态机：从 待命 → 接收任务 → 导航移动 → 电梯交互 → 二维码核对 → 出货 → 返回 的全流程。
   * 提供任务完成、异常、返回、取消等分支处理机制。
3. 多线程控制
   * `MqttThread`：维持与后台的心跳通信，定时上报机器人状态。
   * `InteractionThread`：负责业务逻辑执行、任务调度与跨系统交互。
   * 子线程内部配合 `schedule` 和 `timeoutMonitor`，实现周期性调度与超时监控。
4. 对外通信
   * MQTT：任务下发、状态上报、售卖机交互。
   * HTTP：任务状态更新、拍照上传、电梯流程管理。
   * ROS：向路径规划模块发布目标点（`goal_v3`），订阅机器人底层状态。

#### 4.3 核心功能

##### 4.3.1 MQTT心跳线程

```python
class MqttThread(threading.Thread):
```

定期调用 `publish_state()` 上报机器人当前状态, 在未连接前阻塞等待, 保证通信可靠性.

##### 4.3.2 交互逻辑线程

```python
class InteractionThread(threading.Thread):
```

周期性执行 `logic()`，根据 `robotStatus` + `programStatus` 判断机器人当前处于哪个阶段，并调度相应的处理逻辑。

主要状态逻辑：

- rest: 空闲/待命, 支持重定位、move、执行命令.
- idle: 启动 `fetchTask` 获取任务.
- task: 执行任务, 包括移动、二维码核对、货物投递.
- back: 任务结束后返回仓库/基站.
- exce: 异常处理, 上报后台警告, 清理数据.

##### 4.3.3 电梯交互

```python
def move_with_lift(self, taskId, robot_floor, to_pos, to_floor, to_house, robot_house):
```

结合 `elevatorFlowGetter`, 实时获取电梯流程状态, 按照电梯口 → 电梯内 → 重定位 → 出电梯 的完整流程控制机器人行为.

##### 4.3.4 二维码核对

```python
def qrCheck_handler(self, code):
```

使用售卖机扫描的二维码与任务二维码进行比对, 成功则上报任务完成, 失败则上报任务失败.

##### 4.3.5 货物投递

```python
def cargoDelivery_handler(self, delivery_info):
```

通过 MQTT 向售卖机发送吐货指令, 监听售卖机的回执, 确认用户是否取货.

##### 4.3.6 异常与收尾处理

```python
def finalize_task(self):
```

任务完成或异常时, 清空任务信息, 重置机器人状态.

```python
def toBackend_reportWarn(self, taskId, type):
```

上报异常给后台.

##### 4.3.7 程序入口

```python
def main():
```

* 初始化所有数据类与通信模块; 
* 启动 `MqttThread` 与 `InteractionThread`; 
* 调用 `rospy.spin()` 保持 ROS 节点运行; 
* 优雅退出时回收线程并上报离线状态.

##### 4.3.8 模拟测试

在main()函数中注释部分:

```python
"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot-id", required=True, help="Unique ID of this robot")
    parser.add_argument("--private-key", required=True, help="Encryption private key")
    parser.add_argument("--iv-vector", required=True, help="Encryption IV vector")
    args = parser.parse_args()
    
    global ROBOTID, PRIVATE_KEY, IV_VECTOR
    ROBOTID = args.robot_id
    PRIVATE_KEY = args.private_key
    IV_VECTOR = args.iv_vector
"""
```

如果反注释掉, 配合docker使用, 可以模拟多台设备进行测试.



### 5. `fetchTask.py`

#### 5.1 介绍

`fetchTask.py` 模块定义了 FetchTask 类, 用于周期性地从后台系统拉取任务信息, 保证机器人本地任务状态与后台保持一致. 它以独立线程运行, 通过定时轮询的方式获取任务分配、取消、补货等事件, 从而驱动机器人进入相应的执行状态. 

#### 5.2 作用

1. 任务拉取与同步
   * 周期性调用后台接口 `select_taskInfo`, 获取任务分配和状态更新.
   * 确保机器人不会因为网络延迟或丢包而错过最新任务.
2. 任务状态机驱动
   * 当后台分配新任务时, 触发机器人状态从 `idle` → `task`.
   * 当后台取消任务时, 触发机器人状态从 `task` → `back`.
   * 当后台分配补货任务时, 触发机器人状态从 `idle` → `back` (补货).
3. 数据结构更新
   * 将后台返回的任务详情写入 `CurrentOrder`(任务详情)、`StatusBackend`(任务状态)、`ElevatorControl`(电梯参数)、`RobotStateInfo` (机器人状态) .
   * 确保执行器(executor.py)可以基于最新数据调度任务.

#### 5.3 核心功能

##### 5.3.1 线程控制

```python
def start(self):
```

启动后台任务拉取线程, 并立即执行一次 `fetchTask()`, 之后每 5 秒执行一次轮询.

```python
def stop(self):
```

停止线程运行, 并取消调度任务.

```python
def run(self):
```

后台循环调度器, 定期执行任务拉取逻辑.

##### 5.3.2 任务拉取

```python
def fetchTask(self):
```

调用后台接口 `select_taskInfo(taskId, floor, building)`, 获取最新任务数据.

根据返回结果更新：

- 新任务分配 (status=30/40) → 更新 `CurrentOrder`, 并将机器人状态切换为 `task`.
- 任务取消 (status=60) → 清空任务, 设置机器人状态为 `back`.
- 补货任务 (status=90) → 设置机器人状态为 `back`, programStatus 更新为 `restock`.
- 补货后重新分配任务 (90→30) → 再次更新 `CurrentOrder`, 机器人重新进入任务状态.

##### 5.3.3 任务数据存储

```python
def store_goalPositions(self, goal, addrList):
```

解析后台返回的地址信息, 存储配送目标点和返回点.

```python
def store_deliveryInfo(self, spaceLists):
```

存储配送货物信息 (货道号、数量), 更新到 `CurrentOrder`.



### 6. `httpClient.py`

#### 6.1 介绍

`httpClient.py` 封装了机器人与后台系统之间的所有 HTTP 请求接口, 提供了统一的客户端类 `HttpClient`. 
它的核心作用是将机器人运行过程中的关键数据 (任务信息、执行进度、电梯交互、异常上报、图像采集等) 通过标准 HTTP 协议上报后台, 同时支持从后台获取任务和电梯流程更新.

#### 6.2 作用

1. 统一接口调用：对后台的 API 封装成 Python 方法，方便逻辑模块调用。
2. 加密与鉴权：结合 `encryption.py`，在请求头部添加签名与安全字段，确保通信安全。
3. 数据交互：提供任务获取、任务进度上报、图像/视频上传、电梯流程同步等接口。
4. 重试机制：在请求失败时自动重试，增强通信稳定性。

#### 6.3 核心功能

##### 6.3.1 基础工具

```python
def post_request(self, url, data):
```

通用 POST 请求方法, 负责请求发送、返回结果解析和错误重试.

##### 6.3.2 任务相关接口

```python
def select_taskInfo(self, taskId, floor, building):
```

机器人主动从后台获取任务信息, 用于 `fetchTask` 定期轮询任务状态.

```python
def update_taskStatus(self, taskId, taskStatus):
```

上报机器人当前任务进度 (执行中、已送达、失败等).

##### 6.3.3 数据采集接口

```python
def report_image(self):
```

上传关键节点的照片 (例如电梯门口、投递点), 图片以 base64 编码后通过 HTTP 发送.

```python
def report_video(self):
```

上传关键节点的视频.

以上接口已定义, 但实现待完善, 需要业务流程的确认.

##### 6.3.4 异常上报接口

```python
def report_warn(self, taskId, type):
```

当机器人遇到需要人工介入的异常 (例如电梯卡住、货物堵塞), 调用此接口上报, 后台会中止该任务, 等待人工处理.

##### 6.3.5 电梯流程接口

```python
def set_elevatorControlFlow(self, flowId, elevatorStatus, robotId, taskId, fromFloor, toFloor, fromHouse, toHouse, from_elevator_out ={}, from_elevator_in = {}, to_elevator_out = {}, to_elevator_in = {}):
```

机器人在电梯任务中调用, 用于通知后台当前电梯状态 (到电梯口、进入电梯、重定位完成等), 同时上传电梯点位信息 (内外点).

```python
def get_elevatorControlFlow(self, flowId):
```

轮询后台获取电梯流程的最新状态, 与 `elevatorFlowGetter` 配合使用.

##### 6.3.6 模块单独测试功能

```python
"""
if __name__ == "__main__":
...
"""
```

把注释掉的程序入口反注释掉, 然后运行命令:

```python
python httpClient.py
```

即可对后台与机器人利用HTTP通信的接口进行单独测试.



### 7. `mqttClient.py`

#### 7.1 介绍

`mqttClient.py` 封装了机器人与后台的MQTT 通信逻辑, 提供了连接、状态上报、信号发布、指令接收等功能. 该模块基于 `paho-mqtt` 库实现, 运行后会与指定的 MQTT Broker 建立长连接, 保持机器人与后台的实时消息交互.

#### 7.2 作用

1. 建立连接: 与后台 MQTT Broker 建立和维持连接, 并支持掉线自动重连.
2. 状态上报: 周期性将机器人当前状态 (位置、电量、任务 ID、网络 IP 等) 通过主题发布给后台.
3. 异常监控: 通过 last will 机制, 当机器人掉线/崩溃时后台能立即感知.
4. 指令接收: 订阅后台下发的控制命令 (如重定位、移动、切换状态、执行系统指令), 并更新到机器人内部状态.
5. 辅助通信: 发布信号/事件信息 (如调试信号、路径状态), 供后台或其他系统订阅.

#### 7.3 核心功能

##### 7.3.1 连接与心跳

```python
def on_connect(self, client, userdata, flags, reason_code, properties):
def on_disconnect(self, client, userdata, flags, reason_code, properties):
def connect(self):
def stop(self):
```

建立/关闭 MQTT 连接, 进入消息循环.

```python
def set_lastWill(self):
```

设置遗嘱消息, 当机器人异常下线时通知后台 (`robots/{stationId}/{robotId}/connection` → offline).

##### 7.3.2 状态与网络信息上报

```python
def publish_connection(self, status, reason):
```

发布机器人连接状态 (online/offline), 同时更新内部状态.

```python
def publish_ip(self):
```

获取机器人当前网络 IP 并上报.

```python
def publish_state(self):
```

发布机器人完整运行状态 (位置、电量、任务等) 到 `robots/{stationId}/{robotId}/state`.

##### 7.3.3 信号与事件上报

```python
def publish_signal(self, signal):
```

发布机器人运行中的各种信号 (调试或规划模块传来的信息). 

##### 7.3.4 后台指令接收与处理

```python
def command_handler(self, client, userdata, msg):
```

订阅 `robots/{stationId}/{robotId}/command`，处理后台下发的指令。支持的指令包括：

- reset_address: 重定位到指定坐标点.
- move: 移动到多个目标点位.
- switch_status: 切换机器人状态 (rest / task / back / offline).
- execute_command: 在系统上执行指定命令 (通常是调试/远程控制). 



### 8. `rosSub.py`

#### 8.1 介绍

`rosSub.py` 封装了对机器人运行过程中多个 ROS 话题的订阅逻辑, 用于实时获取机器人底层状态 (位置、电量、规划信号等), 并将其同步到系统内部状态对象 (`RobotStateInfo`、`ProgramStatus`) 或转发到后台( 通过 `mqttClient`). 

#### 8.2 作用

1. 订阅机器人底层 ROS 话题 (位置、电量、导航信号).
2. 更新机器人内部运行状态, 保证逻辑层随时获取到最新数据.
3. 驱动状态机转换: 根据 `signal` 话题触发 `programStatus` 状态的变化 (如 moving → arrived).
4. 转发关键信号到后台: 通过 MQTT 将规划/执行信号转发到后台, 用于监控和调试.

#### 8.3 核心功能

##### 8.3.1 机器人实时位置的订阅

```python
def callback_localization(self, msg: Odometry):
```

订阅 `/global_localization`解析机器人实时位姿(x, y, theta), 并更新到 `robotState`.

##### 8.3.2 电池电量信息订阅

```python
def callback_battery(self, msg: Battery):
```

订阅 `/battery`更新机器人电池电量(battery %)到 `robotState`.

##### 8.3.3 导航信号订阅

```python
def callback_signal(self, msg: String):
```

订阅 `/signal`, 转发信号给后台(通过 MQTT 发布).

驱动状态机转换：

- `GOAL_RECEIVED` → 切换至 moving 状态。
- `GOAL_ARRIVED` → 根据当前 programStatus/robotStatus 切换为 arrived /move_complete /back_arrived 等。
- `RELOCATION_RECEIVED` / `RELOCATION_COMPLETE` → 控制重定位过程。
- `STOP_RECEIVED` → 停止完成。
- `GOAL_FAILED` → 标记机器人异常，进入 exce 状态。



### 9. `timeoutMonitor.py`

#### 9.1 介绍

`timeoutMonitor.py` 实现了一个独立运行的超时监控线程, 用于监控机器人在特定状态下的执行时间. 它会在某些状态进入后, 设定一个超时时间, 若超过期限还未进入目标状态, 就触发超时回调. 该模块由 `executor.py` 使用, 用来保障机器人任务流程 (移动、重定位、电梯操作等) 不会因异常而无限卡住.

#### 9.2 作用

1. 状态机安全保护: 监控任务执行状态, 防止卡死.
2. 异常检测与恢复: 当超时发生时，触发回调逻辑，将机器人状态标记为异常，并执行停止/重置操作。
3. 提升系统鲁棒性: 在网络抖动、传感器异常、规划失败等情况下，避免机器人陷入死循环。

#### 9.3 核心功能

##### 9.3.1 记录与监控

```python
def record(self, startStatus, stopStatus, timeout, on_timeout=None):
```

注册一个超时监控任务: 从 `startStatus` 开始计时, 期望最终进入 `stopStatus`, 如果超时未达成则触发回调.

##### 9.3.2 取消与清理

```python
def cancel_record(self, startStatus):
```

主动取消某个状态的超时监控.

```python
def cancel_record(self, startStatus):
```

清空所有监控记录 (常用于任务结束或异常恢复).

##### 9.3.3 运行逻辑

```python
def run(self):
```

独立线程循环执行, 检查每个注册状态是否超时. 如果达到 deadline 且未进入目标状态 → 调用回调 (默认 `on_timeout`).

##### 9.3.4 默认超时处理

```python
def on_timeout(self, startStatus, stopStatus):
```

默认行为：

- 更新 `programStatus` 为 `"{startStatus}:timeout"`.
- 发布一个 `stop` 目标, 让机器人立即停止.
- 更新机器人状态为 `exce` (异常).



### 10. `vendingMqtt.py`

#### 10.1 介绍

`vendingMqtt.py` 封装了机器人与售货机之间的MQTT 通信逻辑. 该模块运行后, 会与指定的 MQTT Broker 建立连接, 向售货机发送吐货或条码验证指令, 并接收售货机返回的执行结果或扫码信息. 它与 `executor.py` 配合使用, 是配送任务中货物交付环节的核心通信模块.

#### 10.2 作用

1. 命令下发: 向售货机发送指令 (如吐货 `shipment`、条码比对 `barcode`).
2. 结果接收: 监听售货机返回的执行结果 (吐货完成、扫码结果).
3. 任务驱动: 根据售货机反馈更新机器人当前的任务执行状态 (如 `cargo_delivery_complete`).
4. 状态同步: 维护消息编号 (msg 序号), 保证通信过程中的消息顺序.

#### 10.3 核心功能

##### 10.3.1 连接与会话管理

```python
def connect(self):
def stop(self):
```

建立或关闭与 MQTT Broker 的连接, 进入或退出消息循环.

##### 10.3.2 发布指令

```python
def publish_client(self, cmd, data):
```

发布消息到 `vending/client`.

根据不同的指令类型：

- shipment: 发送吐货指令, 携带货道号与数量.
- barcode: 扫码指令或扫码结果校对.

内部维护 `msg_client` 递增编号, 确保消息唯一性.

##### 10.3.3 接收售货机反馈

```python
def server_handler(self, client, userdata, msg):
```

订阅 `vending/server` 主题.

根据返回的 `cmd` 字段进行处理：

- barcode: 更新扫码结果, 如果机器人状态为 `arrived`, 则记录二维码信息, 用于和订单核对.
- shipment: 售货机完成吐货后, 更新 `programStatus` 为 `"cargo_delivery_complete"`.

##### 10.3.4 内部状态维护

* 使用 `lock` 确保扫码结果在多线程场景下的安全更新.
* 保存 `msg_server`, 记录售货机返回的最新消息编号.
* 提供 `scanned_code` 属性, 供 `executor.py` 的二维码核对逻辑调用.



### 11. `qrCode.py`

#### 11.1 介绍

`qrCode.py` 封装了对 Newland扫码枪的事件监听与二维码解析功能,该模块基于 `evdev` 库，通过直接读取 Linux 输入设备节点来获取扫码结果.

**注意: 此模块目前不在主任务逻辑中使用,仅用于扫码器的功能测试与验证.**

#### 11.2 作用

1. 识别并绑定扫码器对应的输入设备节点.
2. 将扫码枪输入的按键事件转换为字符序列.
3. 提供扫码功能接口 `scan()`, 可在指定超时时间内校验二维码是否与目标值一致.
4. 提供 `close()` 方法, 安全释放扫码器资源.

#### 11.3 核心功能

##### 11.3.1 设备绑定

```python
self.path = ""
	for path in list_devices():
	dev = InputDevice(path)
	name = (dev.name or "").lower()
	phys = (dev.phys or "").lower()
	if "newland" in name or "newland" in phys:
		self.path = path
	self.dev = InputDevice(self.path)
```

在初始化时搜索设备列表, 自动识别 `Newland` 相关的输入节点, 并绑定到对应的 `InputDevice`.

##### 11.3.2 二维码扫描

```python
def scan(self, code):
```

在设定的超时时间内监听扫码枪输入:

- 如果扫码结果与传入的 `code` 一致 → 返回 `True`;
- 如果不一致 → 继续等待输入;
- 超时未匹配 → 返回 `False`.

##### 11.3.3 资源管理

```python
def close(self):
```

释放扫码器占用的设备资源, 确保不会阻塞后续使用.



### 12. `mock.py`

#### 12.1 介绍

`mock.py` 是一个用于调试和验证的辅助模块, 不属于机器人正式执行逻辑, 其功能是通过 ROS 节点发布目标点(goal) 消息, 模拟任务下发, 从而测试导航模块(tianxin)的响应情况.

#### 12.2 作用

1. 辅助测试: 在没有后台任务下发时, 模拟机器人接收到任务目标点的场景.
2. 验证规划模块: 检查路径规划模块是否能正确接收和解析目标点信息.
3. 开发联调工具: 为机器人导航、定位、电梯交互等模块的调试提供输入数据.

#### 12.3 核心功能

##### 12.3.1 转换数据格式

```python
def position_transform(position):
```

将字典格式的 `{x, y, theta}` 转换为 ROS 的 `PoseStamped` 对象.

- 输入: 位置字典.
- 输出: 带有时间戳和坐标系信息的 `PoseStamped`.

##### 12.3.2 发布相应话题

```python
def publish_goal():
```

构造 `Goal_v3` 消息并发布到 `/goal_v3` 话题: 

- 包含目标位置 (坐标 + 朝向).
- 包含任务相关参数 (楼层、房号、是否重定位、停止标志). 
- 将消息交给 `tianxin` 模块进行路径规划.

##### 12.3.3 程序入口

```python
if __name__ == "__main__":
```

初始化 ROS 节点, 创建发布者, 并调用 `publish_goal()` 模拟发布一次目标点.



### 13. `mock_ros.py`

#### 13.1 介绍

`mock_ros.py` 是一个 ROS 调试工具模块, 用于在没有真实路径规划或底盘执行模块的情况下, 模拟任务执行过程中的反馈信号. 它通过订阅 `/goal_v3` 话题并发布 `signal` 话题, 帮助验证上层任务调度逻辑与状态机是否能正确处理各种执行结果.

#### 13.2 作用

1. 模拟底盘反馈: 代替真实的导航与动作执行模块, 向上层逻辑返回虚拟执行状态.
2. 验证状态机: 测试 `executor` 等上层逻辑是否能正确响应 `"GOAL_RECEIVED"`, `"GOAL_ARRIVED"`, `"STOP_RECEIVED"`, `"RELOCATION_COMPLETE"` 等信号.
3. 调试流程: 帮助在早期开发或脱离硬件环境时快速联调任务分配、状态更新等逻辑.

#### 13.3 核心功能

##### 13.3.1 订阅goal_v3消息

```python
def goal_callback(msg: Goal_v3):
```

订阅 `goal_v3` 消息, 并根据 `Goal_v3` 的参数决定模拟的执行流程: 

- `relocation = True` → 依次返回 `"RELOCATION_RECEIVED"` 与 `"RELOCATION_COMPLETE"` (或 `"RELOCATION_FAILURE"`).
- `stop = True` → 返回 `"STOP_RECEIVED"`.
- 普通任务 → 返回 `"GOAL_RECEIVED"` 与 `"GOAL_ARRIVED"`.

##### 13.3.2 发布signal话题

```python
def publish_signal(signal):
```

将生成的信号发布到 `/signal` 话题, 模拟底盘执行状态的上报.

##### 13.3.3 程序入口

```python
if __name__ == "__main__":
```

* 初始化 ROS 节点.
* 订阅 `/goal_v3`, 发布 `/signal`.
* 进入 ROS 主循环, 持续模拟反馈.



### 14. `vending_test.py`

#### 14.1 介绍

`vending_test.py` 是用于 售货机 MQTT 通道联调的测试脚本. 脚本以“后端模拟端”的身份连接到指定 MQTT Broker, 按照协议向 `vending/client` 发布吐货指令, 并订阅 `vending/server` 接收售货机返回结果, 用于验证售货机与消息链路是否正常.

#### 14.2 作用

1. 在无完整后端/机器人参与的情况下, 独立验证售货机侧 MQTT 收发是否正常.
2. 复现“吐货”业务最小闭环: 发布 `shipment` 指令 → 接收 `vending/server` 回执.
3. 辅助定位通信问题 (Broker 连通性、Topic 配置、消息格式、SN 识别等).

#### 14.3 核心功能

##### 14.3.1 Broker 连接与订阅

```python
def on_connect(client, userdata, flags, reason_code, properties):
```

`on_connect(...)`: 建立连接后订阅 `vending/server`, 并绑定回调 `subscribe_client_topic_handler`.

##### 14.3.2 指令发布

```python
def publish_topic(cmd, parameters):
```

`publish_topic(cmd, parameters)`: 向 `vending/client` 发布 JSON 指令, 字段包含:

- `msg`: 本地自增消息号 (用于排查顺序/丢包)
- `sn`: 售货机序列号 (示例：`SN25063001`) 
- `cmd`: 命令名 (脚本示例发送 `shipment`)
- `data`: 命令参数 (示例：`{"n":["1301"]}` 表示吐货道 1301)

##### 14.3.3 结果接收与打印

```python
def subscribe_client_topic_handler(client, userdata, msg):
```

`subscribe_client_topic_handler(...)`: 解析 `vending/server` 回执并输出到终端, 便于人工校验.



## 五、启动流程

### 1. 手动启动方式

#### 1.1 vscode - terminal

```bash
conda activate aibotenv
rosrun robot_v5 executor.py
```

先激活环境, 然后就可以直接用rosrun运行节点.

#### 1.2 Ubuntu - bash

启动服务:

```bash
sudo systemctl start robot-executor.service
```

查看输出:

```bash
journalctl -fu robot-executor.service
```

### 2. 开机自启配置

1. 设置wireguard自动连接

   ```bash
   sudo systemctl enable wg-quick@wg0.service
   sudo systemctl start wg-quick@wg0.service
   sudo systemctl status wg-quick@wg0.service
   ```

2. run_executor.py (`/home/amov/run_executor.sh`)

   ```sh
   set -e -o pipefail
   
   echo "[run_executor] starting..."
   
   # 1. Conda 环境
   source /home/amov/anaconda3/etc/profile.d/conda.sh
   conda activate aibotenv
   
   # 2. ROS 环境
   source /opt/ros/noetic/setup.bash
   source /home/amov/yangtianjiao/AIbot_project/robot/catkin_ws/devel/setup.bash
   
   # 3. 网络参数（按你之前 bashrc 里的）
   export ROS_MASTER_URI=http://192.168.1.10:11311
   export ROS_IP=192.168.1.5
   
   # 4. 启动你的程序
   export PYTHONUNBUFFERED=1                 # Python 无缓冲
   export PYTHONIOENCODING=UTF-8             # 避免编码拖延
   export ROSCONSOLE_STDOUT_LINE_BUFFERED=1  # roscpp用，rospy无害
   # 用 rospack 找脚本路径，直接 python3 -u 跑；再套一层 stdbuf 行缓冲（双保险）
   PKG_DIR=$(rospack find robot_v5)
   exec stdbuf -oL -eL python3 -u "$PKG_DIR/src/robot_v5/executor.py"
   ```

3. robot-executor.service (`/etc/systemd/system/robot-executor.service`)

   ```sh
   [Unit]
   Description=ROS robot_v5 executor auto-start
   After=network-online.target wg-quick@wg0.service
   Requires=wg-quick@wg0.service
   
   [Service]
   Type=simple
   User=amov
   Group=amov
   ExecStart=/home/amov/run_executor.sh
   
   # 出错时自动重启
   Restart=always
   RestartSec=3
   
   # 用 SIGINT 优雅退出，超时则强制 kill
   KillSignal=SIGINT
   TimeoutStopSec=20
   SendSIGKILL=yes
   
   [Install]
   WantedBy=multi-user.target
   ```

4. robot-executor-log.desktop (`~/.config/autostart/robot-executor-log.desktop`)

   ```sh
   [Desktop Entry]
   Type=Application
   Name=Robot Executor Logs
   Comment=Follow systemd logs of robot-executor
   Terminal=true
   Exec=gnome-terminal -- bash -lc 'journalctl -fu robot-executor.service'
   X-GNOME-Autostart-enabled=true
   ```


### 3. 停止流程

- 手动运行: `Ctrl + C` 停止节点.

- systemd 管理:

  ```bash
  sudo systemctl stop robot-executor.service
  ```



## 六、测试流程示例 

机器人成功开始运行后, 可以在终端看到如下图状态:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/15.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 3 机器人程序成功运行</figcaption>
</figure>

其中 **MQTT client connected with rc: Success** 代表机器人成功连网并且连接到MQTT broker.

### 1. 后台利用MQTT发布特殊指令测试

首先要进入后台管理系统 (http://10.25.0.17:5000), 点击 **station management** 进入站点管理界面, 然后点击 **station name** 中 **小区001** 对应的 **view** 按钮进入小区001的管理界面 (如图3).

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/3.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 4 进入小区001站点管理界面方式</figcaption>
</figure>

进入小区001对应站点管理界面后点击 **robot** 按钮 (如图4):

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/4.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 5 进入小区001机器人管理界面</figcaption>
</figure>

然后点击 **send command** 按钮便可以进入直接通过MQTT向机器人发送特殊指令的状态 (如图5):

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/5.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 6 利用MQTT向机器人发送特殊指令界面</figcaption>
</figure>

#### 1.1 重定位测试步骤

点击 **reset_address** 后出现两个按钮: **select robot current address** 以及 **select other address** (如图6), 目前 **se lect robot current address** 不能使用, 因为机器人本身的坐标点和朝向有可能会使得重定位失败, 最好从 **select other address** 中点击具体地图位置来完成重定位指令(如图7). 

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/6.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 7 重定位指令方法</figcaption>
</figure>

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/7.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 8 选择重定位位置界面</figcaption>
</figure>

地图中 ntuitive_align $\to$ 2m $\to$ "desc": "PARKINGSITE" 为当前机器人所在办公室位置.

机器人端收到重定位指令后会将重定位信息发送给导航部分, 并且在收到 “RELOCATION_RECEIVED”信号后更改程序状态为 “resetting“, 如图9:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/16.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 9 机器人收到重定位指令后相应处理</figcaption>
</figure>

在重定位完成, 收到信号 “RELOCATION_COMPLETE” 后, 程序状态更改为 “reset_success", 如图10:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/17.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 10 机器人完成重定位指令后的状态</figcaption>
</figure>

#### 1.2 移动测试步骤

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/8.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 11 移动命令发布界面</figcaption>
</figure>

点击 **select** 按钮可以选择地图上的具体位置来发布目标位置坐标.

机器人端收到移动指令后会先判断是否需要使用电梯, 并且改变为相应的程序状态, 如图12:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/18.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 12 机器人接收移动命令后相应处理</figcaption>
</figure>

 然后会从指令中提取出目标位置并发送给导航部分, 收到导航部分返回的信号“GOAL_RECEIVED”后, 程序状态会改变为moving, 如图13:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/19.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 13 机器人发送目标位置以及相应程序状态变化情况</figcaption>
</figure>

当机器人到达目标位置后, 导航部分会发送 “GOAL_ARRIVED” 信号, 机器人程序状态改为 “move_complete”, 如图14:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/20.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 14 机器人到达目标位置后的程序状态</figcaption>
</figure>

#### 1.3 切换状态测试步骤

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/9.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 15 切换状态发布界面</figcaption>
</figure>

点击 **rest** 就可以切换机器人到睡眠/待机状态, 点击 **idle** 就可以切换机器人到空闲状态 (可以从后台获得任务).

机器人相应程序状态改变可以从终端观察到 robotStatus 由 rest 改为 idle, 如图16:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/21.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 16 机器人程序状态改变</figcaption>
</figure>

#### 1.4 执行命令测试步骤

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/10.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 17 发布特殊执行命令界面</figcaption>
</figure>

点击 **status** 可以选择要执行的特殊指令, 是为了重启或关闭 tianxin 部分的程序.

这部分待修改, 需要tianxin将自己的程序写为一个可以用systemd控制启动和关闭的脚本后再进行优化和测试.

### 2. 机器人配送任务测试

#### 2.1 普通配送流程

当用户在 APP 中提交订单后, 后台系统会将未完成的订单同步至站点管理后台的 Order 与 Task 界面. 机器人在从 **rest** 状态切换至 **idle** 状态后, 即具备接单和执行配送任务的条件. 对于单层配送, 系统直接下发路径任务并由机器人执行; 若涉及跨楼层配送或需要通过门禁, 则会自动触发电梯流程 (Elevator Flow), 该流程由后台的 Elevator Flow 模块 (如图18) 统一管理.

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/11.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 18 电梯流程控制界面</figcaption>
</figure>

涉及到电梯流程的情况, 需要后台和机器人相互配合, 更新电梯状态. 

电梯状态表示如下:

| 步骤编号/<br />elevatorStatus | 步骤描述           | 机器人操作                     | 后台操作                 |
| ----------------------------- | ------------------ | ------------------------------ | ------------------------ |
| 0                             | 开始               | 创建梯控流程                   | 向机器人发送电梯口位置   |
| 10                            | 正在赶往电梯口     |                                | 监听机器人到达信号       |
| 20                            | 已到达电梯口       | 机器人发送到达信号             | 发送电梯指令             |
| 30                            | 已发送电梯外部指令 |                                | 监听电梯状态             |
| 40                            | 电梯门已开         | 机器人发送正在赶往电梯内部信号 | 向机器人发送电梯内部位置 |
| 50                            | 正在赶往电梯内部   |                                | 监听机器人到达信号       |
| 60                            | 已到达电梯内部     | 机器人发送到达电梯内部信号     | 发送电梯指令             |
| 70                            | 已发送电梯内部指令 |                                | 监听电梯状态             |
| 80                            | 电梯门已开         | 机器人发送可以重定位信号       | 向机器人发送电梯内部位置 |
| 90                            | 机器人正在重置地图 | 机器人发送正在重定位信号       | 监听机器人重置成功信号   |
| 100                           | 机器人重置地图成功 | 机器人发送重定位成功信号       | 向机器人发送目的地位置   |

后台管理人员需要在合适的时机改变 **elevator flow** 中的 **status** 字段的数值.

#### 2.2 补货配送流程

当用户在 APP 中提交订单后, 若检测到机器人货仓内的库存不足, 机器人将优先返回站点进行补货 (programStatus: restock), 如图19:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/22.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 19 机器人补货状态</figcaption>
</figure>

站点管理人员在完成补货后, 可通过站点管理后台的机器人管理界面 → Space 按钮 记录补充的货品信息, 

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/23.jpg" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:30%;" />
  <figcaption>图 20 机器人管理界面</figcaption>
</figure>

补货信息提交并确认后, 通过重置机器人状态, 即可使机器人自动进入任务流程, 开始正常执行配送.

#### 2.3 取消配送流程

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/14.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:80%;" />
  <figcaption>图 21 任务管理中取消配送操作界面</figcaption>
</figure>

在 **task** 界面中点击 **cancel** 按钮则可取消当前配送任务.

机器人在接收到取消配送命令后, 会更改自身状态为 ”back“, 与此同时程序状态更改为 “cancel_delivery”, 并且向导航部分发送返回位置坐标, 如图22:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/24.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:80%;" />
  <figcaption>图 22 机器人收到取消任务后返回站点</figcaption>
</figure>

导航部分收到目标位置, 首先发送信号 "GOAL_RECEIVED", 机器人程序状态改为 “moving”, 等待到达目标位置, 机器人程序状态改为 “back_arrived”, 如图23:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/25.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:80%;" />
  <figcaption>图 23 机器人收到取消任务后返回站点状态变化</figcaption>
</figure>

#### 2.4 解除机器人异常状态流程

当机器人发生异常状态 (可能由于导航部分导航失败、遇到路障无法通过、或者各种状态下任务执行超时), 机器人会向导航部分发送停止运动话题, 如图24:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/26.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:80%;" />
  <figcaption>图 24 机器人异常状态</figcaption>
</figure>

在站点管理中的机器人管理中, 可以通过reset status 按钮重置机器人状态, 从而解除异常状态, 如图25:

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/24.jpg" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:80%;" />
  <figcaption>图 25 解除机器人异常状态界面</figcaption>
</figure>

### 3. 重定位单独测试

在测试过程中, 如果需要脱离机器人配送逻辑单独测试某个点位的重定位性能, 可以利用 `robot_v5` 中的 `mock.py` 文件单独向导航部分发送重定位信息, 需要注意在代码中正确更改 (goal_pos部分) 某个位置的具体坐标:

```python
def publish_goal():
    """
    给tianxin发布他规划路径需要的数据
    参数:
        outside_lift: 电梯外面的坐标
        inside_lift: 电梯内部的坐标
        final_position: 最后机器人需要到达的坐标
        final_floor: 最后机器人需要到达的楼层
    """

    goal = Goal_v3()
    goal_pos = {
      "theta": 0.32999998331069946,
      "x": 32.720001220703125,
      "y": -3.1600000858306885
    }
    goal_floor = "2m"
    relocation = True
    house = "ntuitive_align"
    stop = False
    goal.pose = position_transform(goal_pos)
    goal.floor = goal_floor
    goal.relocation = relocation
    goal.house = house
    goal.stop = stop
    publisher.publish(goal)
    rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")
```

程序运行方法:

```bash
cd ~/yangtianjiao/AIbot_project/robot/catkin_ws/src/robot_v5
python mock.py
```

### 4. 贩卖机单独测试

#### 4.1 MQTTX 应用端测试

<figure style="text-align:center;">
  <img src="/Users/yangtianjiao/Desktop/27.png" 
       alt="Screenshot 2025-09-14 at 22.54.01" 
       style="zoom:80%;" />
  <figcaption>图 26 MQTTX客户端通信测试配置</figcaption>
</figure>

#### 4.2 代码测试

路径: `~/yangtianjiao/AIbot_project/robot/` 下代码文件: `vending_test.py` 可以直接运行来测试贩卖机的MQTT通信情况, 程序运行方法:

```python
cd ~/yangtianjiao/AIbot_project/robot/catkin_ws/src/robot_v5
python vending_test.py
```



## 七、其他

### 1. 其他参考文档

* 售货机通信接口: https://s.apifox.cn/f7f64cac-cdc9-4d8d-8f9a-c0cca13cb555
* 后台管理操作手册: https://vsg3dd1a832u.sg.larksuite.com/wiki/Jcg7wHeyFijGMQky3fNlhqtCg5f?from=auth_notice&hash=a33a21252bdc25e2f79d2f84cd126496
* `central_communication`程序逻辑: https://vsg3dd1a832u.sg.larksuite.com/wiki/LTmbwbeURihlgpkrPIolXpBrgif#mindmap

### 2. 注意

1. 每次机器人开机启动程序后, 需要后台首先发送一次重定位命令, 否则机器人无法知道自己的位置, 然后再进行其他操作.
2. 机器人一定要进入电梯并且完全停稳之后再关电梯门, 然后操作电梯上楼或下楼, 否则影响机器人后续重定位功能.
3. 机器人到达新的楼层后一定要等待电梯停稳且电梯门完全打开后, 后台才能发送重定位命令, 否则重定位有失败的概率.
4. 贩卖机货仓门打开之后, 如果关闭时间持续3秒 (3秒内没有推开门的动作), 货仓门会关闭, 无法取货, 可以找厂家修改参数.
5. 机器人的实时位置只有在tianxin的程序也在运行中时才能成功获取, 否则参数均为0 (不是bug).
6. 后台管理网页账号密码: admin; 123456
7. app登录先填手机号, 点击 send 按钮后, 再将手机号后六位作为验证码填入即可登录.
8. 站点管理中订单管理 (order) 中的code不是真的二维码, 后期需要更改, 目前测试使用二维码生成网站: https://cli.im 
9. 隔壁办公室有一个女生怀孕, 测试时注意安全.
