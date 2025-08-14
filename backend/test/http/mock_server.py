from flask import Flask
from flask import jsonify


app = Flask(__name__)

@app.route('/api/robot/client/selectTaskInfo', methods=['POST'])
def post_taskInfo():

    result = {
        'code': 0, 
        'data': {
            'taskInfo': {
                'addressParams': {
                    'navigation': {'arrival_method': 2}, 
                    'pose': {
                        'real': {'x': 1.25, 'y': -6.320000171661377, 'theta': -0.24000000953674316}, 
                        'dock': {'x': 1.25, 'y': -6.320000171661377, 'theta': 3.049999952316284}
                    }, 
                    'identity': {'no': '30114F8F', 'id': 806440847, 'desc': 'NIC-2M-03'}, 
                    'floor': '2m', 
                    'house': 'ntuitive', 
                    'dock_settings': {'identify': '', 'verify': ''}, 
                    'stationId': '18839843720'
                }, 
            'createTime': 1754620515000, 
            'id': 18959715166, 
            'robotId': 18951151481, 
            'stationId': 18950824776,
            'status': '20',
            'updateTime': 1754620515000}
        }, 
        'msg': '操作成功'
    }

    return jsonify(result), 200


@app.route('/api/robot/client/reportTaskProcess', methods=['POST'])
def post_taskStatus():

    result = { "status": "success"}

    return jsonify(result), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8889)