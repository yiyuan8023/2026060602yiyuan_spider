"""
作者: 韩潇
时间: 2026-12-02
功能: 获取当前电脑的外网IP
版本: v1.0
"""
import requests
from urllib3 import disable_warnings
disable_warnings()


# warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class MyIp(object):
    def __init__(self):
        print("开始获取ip")
        self.ip = self.get_ip()

    @staticmethod
    def get_ip():
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'}
        res = requests.get(url='https://myip.ipip.net/', headers=headers, verify=False)
        return res.text

    def print_ip(self):
        print(self.ip)



if __name__ == '__main__':
    MyIp().print_ip()
