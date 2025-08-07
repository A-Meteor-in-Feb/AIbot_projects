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
  :slots (_position _taskStatus ))

(defmethod robot::State
  (:init
   (&key
    ((:position __position) (instance geometry_msgs::Point :init))
    ((:taskStatus __taskStatus) "")
    )
   (send-super :init)
   (setq _position __position)
   (setq _taskStatus (string __taskStatus))
   self)
  (:position
   (&rest __position)
   (if (keywordp (car __position))
       (send* _position __position)
     (progn
       (if __position (setq _position (car __position)))
       _position)))
  (:taskStatus
   (&optional __taskStatus)
   (if __taskStatus (setq _taskStatus __taskStatus)) _taskStatus)
  (:serialization-length
   ()
   (+
    ;; geometry_msgs/Point _position
    (send _position :serialization-length)
    ;; string _taskStatus
    4 (length _taskStatus)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; geometry_msgs/Point _position
       (send _position :serialize s)
     ;; string _taskStatus
       (write-long (length _taskStatus) s) (princ _taskStatus s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; geometry_msgs/Point _position
     (send _position :deserialize buf ptr-) (incf ptr- (send _position :serialization-length))
   ;; string _taskStatus
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _taskStatus (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(setf (get robot::State :md5sum-) "c5c770faa938bccc8c5b6ab129729e91")
(setf (get robot::State :datatype-) "robot/State")
(setf (get robot::State :definition-)
      "geometry_msgs/Point position
string taskStatus
================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

")



(provide :robot/State "c5c770faa938bccc8c5b6ab129729e91")


