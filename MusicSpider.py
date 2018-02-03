# _*_ coding: utf-8 _*_
import json
import os
import time
from threading import Thread

import requests

from Crypto.Cipher import AES
from base64 import b64encode


class CloudMusic:
    def __init__(self):
        self.requests = requests.session()
        self.f = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.e = "010001"
        self.iv = "0102030405060708"
        self.HotTop = '{"id":"3778678","n":"1000","csrf_token":"6fc550b926aebb5e82fcf90ee0e04cc4"}'  # 最热排行榜
        self.NewTop = '{"id":"3779629","n":"1000","csrf_token":"6fc550b926aebb5e82fcf90ee0e04cc4"}'  # 最热排行榜
        self.SurgeTop = '{"id":"19723756","n":"1000","csrf_token":"6fc550b926aebb5e82fcf90ee0e04cc4"}'  # 最热排行榜
        self.OriginalTop = '{"id":"2884035","n":"1000","csrf_token":"6fc550b926aebb5e82fcf90ee0e04cc4"}'  # 最热排行榜
        self.folder_name = ""
        self.music_info = {}

    # function b(d, g)
    def aes_encrypt(self, d, g):
        cipher = AES.new(g, AES.MODE_CBC, self.iv)
        pad = 16 - len(d) % 16
        d = d + pad * chr(pad)
        aes_result = cipher.encrypt(d)
        return b64encode(aes_result)

    def get_params(self, d):
        g = "0CoJUm6Qyw8W8jud"
        a = "F" * 16
        aes_result = self.aes_encrypt(d, g)
        params = self.aes_encrypt(aes_result.decode(), a)
        return params

    def get_encSeckey(self):
        enc_sec_key = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c "
        return enc_sec_key

    def post_data(self, params):
        data = {'params': params, "encSecKey": self.get_encSeckey()}
        return data

    def headers(self):
        headers = {
            # "Accept": "*/*",
            # "Content-Type": "application/x-www-form-urlencoded",
            # "Host": "music.163.com",
            # "Origin": "http://music.163.com",
            # "Proxy-Connection": "keep-alive",
            # "Referer": "http://music.163.com/discover/toplist?id=3778678",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        }
        return headers

    def get_rankling_list(self, option):
        url = "http://music.163.com/weapi/v3/playlist/detail?csrf_token="
        self.folder_name = option
        if option == "飙升":
            params = self.get_params(self.SurgeTop)
        elif option == "新歌":
            params = self.get_params(self.NewTop)
        elif option == "原创":
            params = self.get_params(self.OriginalTop)
        elif option == "热歌":
            params = self.get_params(self.HotTop)
        else:
            print("输入错误!")
            return

        time_local = time.localtime(time.time())
        dt = time.strftime("%Y-%m-%d", time_local)
        self.folder_name = "云音乐" + self.folder_name + "榜" + dt
        if not os.path.exists(self.folder_name):
            os.mkdir(self.folder_name)

        data = self.post_data(params)
        playlist = self.requests.post(url, data=data, headers=self.headers())
        if playlist.status_code == 200:
            plist = playlist.json()
            self.write_readme(plist['playlist'])
            tracks = plist['playlist']['tracks']
            count = 0
            for music in tracks:
                count += 1
                name = music['name']
                _id = music['id']
                self.write_ranking_list(name, str(count))
                self.music_info[name] = _id

    def download_hot_rankling_list(self, name, _id):
        # 转换成localtime

        music_value = '{"ids":"[%s]","br":128000,"csrf_token":""}' % _id
        params = self.get_params(music_value)
        data = self.post_data(params)
        post_url = "http://music.163.com/weapi/song/enhance/player/url?csrf_token="
        try:
            html = requests.post(post_url, data=data, headers=self.headers())
        except Exception as f:
            print(f.args)
            return

        if html.status_code == 200:
            music_json = html.json()
            url = music_json['data'][0]['url']
            if url is None:
                return
            music_content = requests.get(url, headers=self.headers()).content
            with open(self.folder_name + "/" + name.replace("^", "") + ".mp3", "wb+") as f:
                f.write(music_content)
            print(name, "下载完毕!")

    def write_readme(self, plist):
        response = json.dumps(plist, ensure_ascii=False)
        folder_name = self.folder_name + "/json"
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        with open(folder_name + "/response.json", "wb") as f:
            f.write(response.encode("utf-8"))

    def write_ranking_list(self, name, count):
        folder_name = self.folder_name + "/排行"
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        with open(folder_name + "/排行.txt", "ab+") as f:
            f.write((count + "\t\t" + name + "\r\n").encode("utf-8"))


def menu():
    print("*" * 30)
    print("*\t输入飙升下载飙升歌曲榜\t*:")
    print("*\t输入新歌下载新歌新歌榜\t*:")
    print("*\t输入原创下载原创歌曲榜\t*:")
    print("*\t输入热歌下载热歌歌曲榜\t*:")
    print("*" * 30)


def hot_top():
    cm = CloudMusic()
    menu()
    switch = input("请输入你的选择: ")
    cm.get_rankling_list(switch)
    count = 0
    for name, _id in cm.music_info.items():
        count += 1
        if count > 10:
            time.sleep(5)
            count = 0
        t = Thread(target=cm.download_hot_rankling_list, args=(name, _id))
        t.start()


if __name__ == "__main__":
    hot_top()
