// Auto-generated. Do not edit!

// (in-package robot.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------

class LocalizationInfo {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.x = null;
      this.y = null;
      this.heading = null;
      this.floor_id = null;
      this.user_id = null;
    }
    else {
      if (initObj.hasOwnProperty('x')) {
        this.x = initObj.x
      }
      else {
        this.x = 0.0;
      }
      if (initObj.hasOwnProperty('y')) {
        this.y = initObj.y
      }
      else {
        this.y = 0.0;
      }
      if (initObj.hasOwnProperty('heading')) {
        this.heading = initObj.heading
      }
      else {
        this.heading = 0.0;
      }
      if (initObj.hasOwnProperty('floor_id')) {
        this.floor_id = initObj.floor_id
      }
      else {
        this.floor_id = '';
      }
      if (initObj.hasOwnProperty('user_id')) {
        this.user_id = initObj.user_id
      }
      else {
        this.user_id = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type LocalizationInfo
    // Serialize message field [x]
    bufferOffset = _serializer.float64(obj.x, buffer, bufferOffset);
    // Serialize message field [y]
    bufferOffset = _serializer.float64(obj.y, buffer, bufferOffset);
    // Serialize message field [heading]
    bufferOffset = _serializer.float64(obj.heading, buffer, bufferOffset);
    // Serialize message field [floor_id]
    bufferOffset = _serializer.string(obj.floor_id, buffer, bufferOffset);
    // Serialize message field [user_id]
    bufferOffset = _serializer.string(obj.user_id, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type LocalizationInfo
    let len;
    let data = new LocalizationInfo(null);
    // Deserialize message field [x]
    data.x = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [y]
    data.y = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [heading]
    data.heading = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [floor_id]
    data.floor_id = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [user_id]
    data.user_id = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.floor_id);
    length += _getByteLength(object.user_id);
    return length + 32;
  }

  static datatype() {
    // Returns string type for a message object
    return 'robot/LocalizationInfo';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '8c3fed3fa27ab9dbf5a4834ff70d5a2e';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    float64 x
    float64 y
    float64 heading
    string floor_id
    string user_id
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new LocalizationInfo(null);
    if (msg.x !== undefined) {
      resolved.x = msg.x;
    }
    else {
      resolved.x = 0.0
    }

    if (msg.y !== undefined) {
      resolved.y = msg.y;
    }
    else {
      resolved.y = 0.0
    }

    if (msg.heading !== undefined) {
      resolved.heading = msg.heading;
    }
    else {
      resolved.heading = 0.0
    }

    if (msg.floor_id !== undefined) {
      resolved.floor_id = msg.floor_id;
    }
    else {
      resolved.floor_id = ''
    }

    if (msg.user_id !== undefined) {
      resolved.user_id = msg.user_id;
    }
    else {
      resolved.user_id = ''
    }

    return resolved;
    }
};

module.exports = LocalizationInfo;
