;; Auto-generated. Do not edit!


(when (boundp 'robot::Pub)
  (if (not (find-package "ROBOT"))
    (make-package "ROBOT"))
  (shadow 'Pub (find-package "ROBOT")))
(unless (find-package "ROBOT::PUB")
  (make-package "ROBOT::PUB"))

(in-package "ROS")
;;//! \htmlinclude Pub.msg.html


(defclass robot::Pub
  :super ros::object
  :slots (_x _y _heading _floor_id _status ))

(defmethod robot::Pub
  (:init
   (&key
    ((:x __x) 0.0)
    ((:y __y) 0.0)
    ((:heading __heading) 0.0)
    ((:floor_id __floor_id) "")
    ((:status __status) "")
    )
   (send-super :init)
   (setq _x (float __x))
   (setq _y (float __y))
   (setq _heading (float __heading))
   (setq _floor_id (string __floor_id))
   (setq _status (string __status))
   self)
  (:x
   (&optional __x)
   (if __x (setq _x __x)) _x)
  (:y
   (&optional __y)
   (if __y (setq _y __y)) _y)
  (:heading
   (&optional __heading)
   (if __heading (setq _heading __heading)) _heading)
  (:floor_id
   (&optional __floor_id)
   (if __floor_id (setq _floor_id __floor_id)) _floor_id)
  (:status
   (&optional __status)
   (if __status (setq _status __status)) _status)
  (:serialization-length
   ()
   (+
    ;; float64 _x
    8
    ;; float64 _y
    8
    ;; float64 _heading
    8
    ;; string _floor_id
    4 (length _floor_id)
    ;; string _status
    4 (length _status)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float64 _x
       (sys::poke _x (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _y
       (sys::poke _y (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _heading
       (sys::poke _heading (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; string _floor_id
       (write-long (length _floor_id) s) (princ _floor_id s)
     ;; string _status
       (write-long (length _status) s) (princ _status s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float64 _x
     (setq _x (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _y
     (setq _y (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _heading
     (setq _heading (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; string _floor_id
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _floor_id (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _status
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _status (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(setf (get robot::Pub :md5sum-) "35f729d6fcfa7579cc74b5d51f397ebb")
(setf (get robot::Pub :datatype-) "robot/Pub")
(setf (get robot::Pub :definition-)
      "float64 x
float64 y
float64 heading
string floor_id
string status
")



(provide :robot/Pub "35f729d6fcfa7579cc74b5d51f397ebb")


