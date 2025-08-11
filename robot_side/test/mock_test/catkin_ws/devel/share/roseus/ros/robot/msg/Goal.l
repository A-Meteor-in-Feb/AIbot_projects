;; Auto-generated. Do not edit!


(when (boundp 'robot::Goal)
  (if (not (find-package "ROBOT"))
    (make-package "ROBOT"))
  (shadow 'Goal (find-package "ROBOT")))
(unless (find-package "ROBOT::GOAL")
  (make-package "ROBOT::GOAL"))

(in-package "ROS")
;;//! \htmlinclude Goal.msg.html


(defclass robot::Goal
  :super ros::object
  :slots (_x _y _z _address _taskId _binId ))

(defmethod robot::Goal
  (:init
   (&key
    ((:x __x) 0.0)
    ((:y __y) 0.0)
    ((:z __z) 0.0)
    ((:address __address) "")
    ((:taskId __taskId) 0)
    ((:binId __binId) 0)
    )
   (send-super :init)
   (setq _x (float __x))
   (setq _y (float __y))
   (setq _z (float __z))
   (setq _address (string __address))
   (setq _taskId (round __taskId))
   (setq _binId (round __binId))
   self)
  (:x
   (&optional __x)
   (if __x (setq _x __x)) _x)
  (:y
   (&optional __y)
   (if __y (setq _y __y)) _y)
  (:z
   (&optional __z)
   (if __z (setq _z __z)) _z)
  (:address
   (&optional __address)
   (if __address (setq _address __address)) _address)
  (:taskId
   (&optional __taskId)
   (if __taskId (setq _taskId __taskId)) _taskId)
  (:binId
   (&optional __binId)
   (if __binId (setq _binId __binId)) _binId)
  (:serialization-length
   ()
   (+
    ;; float64 _x
    8
    ;; float64 _y
    8
    ;; float64 _z
    8
    ;; string _address
    4 (length _address)
    ;; uint32 _taskId
    4
    ;; uint32 _binId
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float64 _x
       (sys::poke _x (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _y
       (sys::poke _y (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _z
       (sys::poke _z (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; string _address
       (write-long (length _address) s) (princ _address s)
     ;; uint32 _taskId
       (write-long _taskId s)
     ;; uint32 _binId
       (write-long _binId s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float64 _x
     (setq _x (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _y
     (setq _y (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _z
     (setq _z (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; string _address
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _address (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; uint32 _taskId
     (setq _taskId (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; uint32 _binId
     (setq _binId (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get robot::Goal :md5sum-) "4870beac0f8c447426c89ad9a47b4d3b")
(setf (get robot::Goal :datatype-) "robot/Goal")
(setf (get robot::Goal :definition-)
      "float64 x
float64 y
float64 z
string address
uint32 taskId
uint32 binId
")



(provide :robot/Goal "4870beac0f8c447426c89ad9a47b4d3b")


