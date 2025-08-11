def success_reponse(data):
    return {
        "success": True,
        "data": data
    }

def error_response(message, code, timestamp):
    return {
        "success": False,
        "data": {
            "status": "error",
            "message": message,
            "error_code": code,
            "timestamp": timestamp
        }
    }

def error_response(bin)