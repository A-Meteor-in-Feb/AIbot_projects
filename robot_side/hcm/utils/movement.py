def validateTarget(target):
    x = target.get('x')
    y = target.get('y')
    z = target.get('z')
    coordinateType = target.get("coordinateType")
    speed = target.get("speed")
    # check whether it is valid

    return True #or False

def startMovement(target):
    success = True
    message = "ok"
    return {"success": success, "message": message}


def calculateDuration(target):
    #calculate duration
    return 0.1