;; Auto-generated. Do not edit!


(when (boundp 'robot::State)
  (if (not (find-package "ROBOT"))
    (make-package "ROBOT"))
  (shadow 'State (find-package "ROBOT")))
(unless (find-package "ROBOT::STATE")
  (make-package "ROBOT::STATE"))

(in-package "ROS")
;;//! \htmlinclude State.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))


(defclass robot::State
  :super ros::object
  :slots (_position _coordinateType _battery _taskStatus _taskId _connection _autonomousMode _fault _binsNum ))

(defmethod robot::State
  (:init
   (&key
    ((:position __position) (instance geometry_msgs::Point :init))
    ((:coordinateType __coordinateType) "")
    ((:battery __battery) 0)
    ((:taskStatus __taskStatus) "")
    ((:taskId __taskId) 0)
    ((:connection __connection) "")
    ((:autonomousMode __autonomousMode) nil)
    ((:fault __fault) nil)
    ((:binsNum __binsNum) 0)
    )
   (send-super :init)
   (setq _position __position)
   (setq _coordinateType (string __coordinateType))
   (setq _battery (round __battery))
   (setq _taskStatus (string __taskStatus))
   (setq _taskId (round __taskId))
   (setq _connection (string __connection))
   (setq _autonomousMode __autonomousMode)
   (setq _fault __fault)
   (setq _binsNum (round __binsNum))
   self)
  (:position
   (&rest __position)
   (if (keywordp (car __position))
       (send* _position __position)
     (progn
       (if __position (setq _position (car __position)))
       _position)))
  (:coordinateType
   (&optional __coordinateType)
   (if __coordinateType (setq _coordinateType __coordinateType)) _coordinateType)
  (:battery
   (&optional __battery)
   (if __battery (setq _battery __battery)) _battery)
  (:taskStatus
   (&optional __taskStatus)
   (if __taskStatus (setq _taskStatus __taskStatus)) _taskStatus)
  (:taskId
   (&optional __taskId)
   (if __taskId (setq _taskId __taskId)) _taskId)
  (:connection
   (&optional __connection)
   (if __connection (setq _connection __connection)) _connection)
  (:autonomousMode
   (&optional (__autonomousMode :null))
   (if (not (eq __autonomousMode :null)) (setq _autonomousMode __autonomousMode)) _autonomousMode)
  (:fault
   (&optional (__fault :null))
   (if (not (eq __fault :null)) (setq _fault __fault)) _fault)
  (:binsNum
   (&optional __binsNum)
   (if __binsNum (setq _binsNum __binsNum)) _binsNum)
  (:serialization-length
   ()
   (+
    ;; geometry_msgs/Point _position
    (send _position :serialization-length)
    ;; string _coordinateType
    4 (length _coordinateType)
    ;; uint8 _battery
    1
    ;; string _taskStatus
    4 (length _taskStatus)
    ;; uint32 _taskId
    4
    ;; string _connection
    4 (length _connection)
    ;; bool _autonomousMode
    1
    ;; bool _fault
    1
    ;; uint32 _binsNum
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; geometry_msgs/Point _position
       (send _position :serialize s)
     ;; string _coordinateType
       (write-long (length _coordinateType) s) (princ _coordinateType s)
     ;; uint8 _battery
       (write-byte _battery s)
     ;; string _taskStatus
       (write-long (length _taskStatus) s) (princ _taskStatus s)
     ;; uint32 _taskId
       (write-long _taskId s)
     ;; string _connection
       (write-long (length _connection) s) (princ _connection s)
     ;; bool _autonomousMode
       (if _autonomousMode (write-byte -1 s) (write-byte 0 s))
     ;; bool _fault
       (if _fault (write-byte -1 s) (write-byte 0 s))
     ;; uint32 _binsNum
       (write-long _binsNum s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; geometry_msgs/Point _position
     (send _position :deserialize buf ptr-) (incf ptr- (send _position :serialization-length))
   ;; string _coordinateType
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _coordinateType (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; uint8 _battery
     (setq _battery (sys::peek buf ptr- :char)) (incf ptr- 1)
   ;; string _taskStatus
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _taskStatus (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; uint32 _taskId
     (setq _taskId (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; string _connection
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _connection (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; bool _autonomousMode
     (setq _autonomousMode (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; bool _fault
     (setq _fault (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; uint32 _binsNum
     (setq _binsNum (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get robot::State :md5sum-) "e969d27b0a93712a250988f2dbe8e279")
(setf (get robot::State :datatype-) "robot/State")
(setf (get robot::State :definition-)
      "geometry_msgs/Point position
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

")



(provide :robot/State "e969d27b0a93712a250988f2dbe8e279")


