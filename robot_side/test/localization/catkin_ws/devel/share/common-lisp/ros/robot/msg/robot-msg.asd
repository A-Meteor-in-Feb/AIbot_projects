
(cl:in-package :asdf)

(defsystem "robot-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "Pub" :depends-on ("_package_Pub"))
    (:file "_package_Pub" :depends-on ("_package"))
    (:file "Sub" :depends-on ("_package_Sub"))
    (:file "_package_Sub" :depends-on ("_package"))
  ))