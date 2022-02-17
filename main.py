import json

from connect import send_data

if __name__ == '__main__':
    # ip = '192.168.0.134'
    # data = json.dumps({"sub_type": 6})
    # api = 'find_task'

    ip = '192.168.0.134'
    data = json.dumps({"title_id": "CUSA09311"})
    api = 'is_exists'
    print(send_data(ip, api, data))
