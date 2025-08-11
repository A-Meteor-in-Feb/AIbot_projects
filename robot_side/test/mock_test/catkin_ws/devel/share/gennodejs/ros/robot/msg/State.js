// Auto-generated. Do not edit!

// (in-package robot.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let geometry_msgs = _finder('geometry_msgs');

//-----------------------------------------------------------

class State {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.position = null;
      this.coordinateType = null;
      this.battery = null;
      this.taskStatus = null;
      this.taskId = null;
      this.connection = null;
      this.autonomousMode = null;
      this.fault = null;
      this.binsNum = null;
    }
    else {
      if (initObj.hasOwnProperty('position')) {
        this.position = initObj.position
      }
      else {
        this.position = new geometry_msgs.msg.Point();
      }
      if (initObj.hasOwnProperty('coordinateType')) {
        this.coordinateType = initObj.coordinateType
      }
      else {
        this.coordinateType = '';
      }
      if (initObj.hasOwnProperty('battery')) {
        this.battery = initObj.battery
      }
      else {
        this.battery = 0;
      }
      if (initObj.hasOwnProperty('taskStatus')) {
        this.taskStatus = initObj.taskStatus
      }
      else {
        this.taskStatus = '';
      }
      if (initObj.hasOwnProperty('taskId')) {
        this.taskId = initObj.taskId
      }
      else {
        this.taskId = 0;
      }
      if (initObj.hasOwnProperty('connection')) {
        this.connection = initObj.connection
      }
      else {
        this.connection = '';
      }
      if (initObj.hasOwnProperty('autonomousMode')) {
        this.autonomousMode = initObj.autonomousMode
      }
      else {
        this.autonomousMode = false;
      }
      if (initObj.hasOwnProperty('fault')) {
        this.fault = initObj.fault
      }
      else {
        this.fault = false;
      }
      if (initObj.hasOwnProperty('binsNum')) {
        this.binsNum = initObj.binsNum
      }
      else {
        this.binsNum = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type State
    // Serialize message field [position]
    bufferOffset = geometry_msgs.msg.Point.serialize(obj.position, buffer, bufferOffset);
    // Serialize message field [coordinateType]
    bufferOffset = _serializer.string(obj.coordinateType, buffer, bufferOffset);
    // Serialize message field [battery]
    bufferOffset = _serializer.uint8(obj.battery, buffer, bufferOffset);
    // Serialize message field [taskStatus]
    bufferOffset = _serializer.string(obj.taskStatus, buffer, bufferOffset);
    // Serialize message field [taskId]
    bufferOffset = _serializer.uint32(obj.taskId, buffer, bufferOffset);
    // Serialize message field [connection]
    bufferOffset = _serializer.string(obj.connection, buffer, bufferOffset);
    // Serialize message field [autonomousMode]
    bufferOffset = _serializer.bool(obj.autonomousMode, buffer, bufferOffset);
    // Serialize message field [fault]
    bufferOffset = _serializer.bool(obj.fault, buffer, bufferOffset);
    // Serialize message field [binsNum]
    bufferOffset = _serializer.uint32(obj.binsNum, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type State
    let len;
    let data = new State(null);
    // Deserialize message field [position]
    data.position = geometry_msgs.msg.Point.deserialize(buffer, bufferOffset);
    // Deserialize message field [coordinateType]
    data.coordinateType = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [battery]
    data.battery = _deserializer.uint8(buffer, bufferOffset);
    // Deserialize message field [taskStatus]
    data.taskStatus = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [taskId]
    data.taskId = _deserializer.uint32(buffer, bufferOffset);
    // Deserialize message field [connection]
    data.connection = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [autonomousMode]
    data.autonomousMode = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [fault]
    data.fault = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [binsNum]
    data.binsNum = _deserializer.uint32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.coordinateType);
    length += _getByteLength(object.taskStatus);
    length += _getByteLength(object.connection);
    return length + 47;
  }

  static datatype() {
    // Returns string type for a message object
    return 'robot/State';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'e969d27b0a93712a250988f2dbe8e279';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    geometry_msgs/Point position
    string coordinateType
    uint8 battery
    string taskStatus
    uint32 taskId
    string connection
    bool autonomousMode
    bool fault
    uint32 binsNum
    ================================================================================
    MSG: geometry_msgs/Point
    # This contains the position of a point in free space
    float64 x
    float64 y
    float64 z
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new State(null);
    if (msg.position !== undefined) {
      resolved.position = geometry_msgs.msg.Point.Resolve(msg.position)
    }
    else {
      resolved.position = new geometry_msgs.msg.Point()
    }

    if (msg.coordinateType !== undefined) {
      resolved.coordinateType = msg.coordinateType;
    }
    else {
      resolved.coordinateType = ''
    }

    if (msg.battery !== undefined) {
      resolved.battery = msg.battery;
    }
    else {
      resolved.battery = 0
    }

    if (msg.taskStatus !== undefined) {
      resolved.taskStatus = msg.taskStatus;
    }
    else {
      resolved.taskStatus = ''
    }

    if (msg.taskId !== undefined) {
      resolved.taskId = msg.taskId;
    }
    else {
      resolved.taskId = 0
    }

    if (msg.connection !== undefined) {
      resolved.connection = msg.connection;
    }
    else {
      resolved.connection = ''
    }

    if (msg.autonomousMode !== undefined) {
      resolved.autonomousMode = msg.autonomousMode;
    }
    else {
      resolved.autonomousMode = false
    }

    if (msg.fault !== undefined) {
      resolved.fault = msg.fault;
    }
    else {
      resolved.fault = false
    }

    if (msg.binsNum !== undefined) {
      resolved.binsNum = msg.binsNum;
    }
    else {
      resolved.binsNum = 0
    }

    return resolved;
    }
};

module.exports = State;
