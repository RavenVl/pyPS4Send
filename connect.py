import requests

def send_data(ip: str, api: str,  data: str) -> str:
    url = f'http://{ip}:12800/api/{api}'
    r = requests.post(url, data=data)
    return r.text

