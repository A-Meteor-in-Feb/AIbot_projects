Header header
uint8 submodule
uint8 batteryPercentage
uint8 chargeMode
uint8 chargeStatus
float32 batteryVoltage
float32 batteryCurrent
float32 timeRemain
int8 tempMax
int8 tempMin
float32 capacityRemain
float32 capacityFull
float32 capacityDesign
uint16 chargeCycle
uint16 batteryCycle
float32 cellVoltageMax
float32 cellVoltageMin
uint32 bmsStatus

#chargeMode
uint8 manualMode = 0
uint8 autoMode = 1

#chargeStatus
uint8 discharge = 0
uint8 charging = 1
