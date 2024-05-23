import os
import sys
import time
import json
import random
import requests
from urllib.parse import unquote
from base64 import b64decode
from colorama import *
from typing import List

init(autoreset=True)

merah = Fore.LIGHTRED_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
hitam = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
putih = Fore.LIGHTWHITE_EX


class Bot:
    def __init__(self):
        self.peer = "theYescoin_bot"
        self.base_headers = {
            "content-length": "2",
            "accept": "application/json, text/plain, */*",
            "user-agent": "",
            "content-type": "application/json",
            "origin": "https://www.yescoin.gold",
            "x-requested-with": "org.telegram.messenger",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.yescoin.gold/",
            "accept-language": "en,en-US;q=0.9",
        }

    def main(self):
        banner = f"""

    {hijau}AUTO SWAP-SWAP / TAP-TAP {putih}THEYESCOIN_BOT

    {hijau}By: {putih}t.me/AkasakaID
    {hijau}Github: {putih}@AkasakaID"""
        arg = sys.argv
        if len(arg) <= 1:
            os.system("cls" if os.name == "nt" else "clear")

        res = requests.get(
            "https://raw.githubusercontent.com/akasakaid/they3scoin/main/version.json"
        )
        open(".http_request.log", "a").write(res.text + "\n")
        version = res.json()["version"]
        message = res.json()["message"]
        banner += f"""
    {hijau}version : {putih}{version}
    {hijau}message : {putih}{message}
        """
        print(banner)
        if not os.path.exists("user-agent"):
            print(f"{merah}user-agent file is not found !")
            user_agent = input(f"{putih}input your user-agent : ")
            open("user-agent", "w").write(user_agent)

        user_agent = open("user-agent", "r").read()
        self.base_headers["user-agent"] = user_agent

        config = json.loads(open("config.json", "r").read())
        interval = int(config["interval"])
        sleep = int(config["sleep"])
        tap_start = int(config["tap_range"]["start"])
        tap_end = int(config["tap_range"]["end"])
        energy_limit = int(config["energy_limit"])
        coinlimit = config["auto_upgrade"]["coinlimit"]
        fillrate = config["auto_upgrade"]["fillrate"]
        multivalue = config["auto_upgrade"]["multivalue"]

        if not os.path.exists("data"):
            open("data", "a")

        data_read = open("data", "r").read().splitlines()
        if len(data_read) <= 0:
            print(f"{kuning}your data file is none/ empty")
            print(f"{kuning}please fill data file first !")
            sys.exit()

        data_read = open("data", "r").read().splitlines()[0]

        if not os.path.exists("data.json"):
            open("data.json", "w").write(
                json.dumps({"token": "", "exp": "1600000000"}, indent=4)
            )

        data = self.data_parsing(data_read)
        user = json.loads(data["user"])
        first_name = user["first_name"]
        last_name = None
        username = None
        if "last_name" in user.keys():
            last_name = user["last_name"]
        if "username" in user.keys():
            username = user["username"]

        self.log(f"{hijau}name : {putih}{first_name} {last_name}")
        self.log(f"{hijau}username : {putih}{username}")

        while True:
            print("~" * 50)
            datajs = self.refresh_datajs()
            if int(datajs["exp"]) < int(time.time()):
                data = self.gen_data_login(data_read)
                res = self.login(data)
                if res is False:
                    self.log(f"{merah}check you data file !")
                    sys.exit()

            datajs = self.refresh_datajs()
            token = datajs["token"]
            self.base_headers["token"] = token
            self.user_info(show_id=True)
            build = self.get_build_info()
            if isinstance(build, bool):
                continue

            coin = random.randint(tap_start, tap_end)
            energy_used = coin * int(build["multivalue"]["value"])
            res_energy = self.get_energy()
            if res_energy is False or int(energy_used) > int(res_energy):
                headers = self.base_headers
                if build["energy_recovery"] != 0:
                    recovery_url = "https://api.yescoin.gold/game/recoverCoinPool"
                    headers["content-length"] = "0"
                    res = requests.post(recovery_url, headers=headers)
                    open(".http_request.log", "a").write(res.text + "\n")
                    if '"message":"Success"' in res.text:
                        self.log(f"{hijau}success recovery energy !")
                        continue

                if build["box_recovery"] != 0:
                    self.open_box()
                    continue

                self.log(f"{kuning}limit energy reacted, login sleep mode !")
                self.countdown(sleep)
                continue
            self.collect_coin(coin)
            self.countdown(interval)
            res_coin = self.user_info(show_balance=True)
            build = self.get_build_info()
            if isinstance(build, bool):
                continue

            if multivalue:
                if int(res_coin) > int(build["multivalue"]["cost"]):
                    self.levelup(1, "multivalue")
                    continue
                self.log(f"{kuning}coins not enough to upgrade multivalue !")

            if coinlimit:
                if int(res_coin) > int(build["coinlimit"]["cost"]):
                    self.levelup(3, "coinlimit")
                    continue
                self.log(f"{kuning}coins not enough to upgrade coinlimit !")

            if fillrate:
                if int(res_coin) > int(build["fillrate"]["cost"]):
                    self.levelup(2, "fillrate")
                    continue
                self.log(f"{kuning}coins not enough to upgrade fillrate !")

            continue

    def open_box(self):
        special_box_url = "https://api.yescoin.gold/game/recoverSpecialBox"
        special_box_info_url = "https://api.yescoin.gold/game/getSpecialBoxInfo"
        special_box_collect_url = "https://api.yescoin.gold/game/collectSpecialBoxCoin"
        headers = self.base_headers
        headers["content-length"] = "0"
        res = requests.post(special_box_url, headers=headers)
        open(".http_request.log", "a").write(res.text + "\n")
        if '"message":"Success"' in res.text:
            res = self.http(special_box_info_url, headers)
            if '"message":"Success"' in res.text:
                data = None
                if res.json()["data"]["autoBox"] is not None:
                    box_type = res.json()["data"]["autoBox"]["boxType"]
                    box_count = res.json()["data"]["autoBox"]["specialBoxTotalCount"]
                    box_status = res.json()["data"]["autoBox"]["boxStatus"]
                    if box_status:
                        coin = random.randint(100, int(box_count))
                        data = {"boxType": box_type, "coinCount": coin}

                if res.json()["data"]["recoveryBox"] is not None:
                    box_type = res.json()["data"]["recoveryBox"]["boxType"]
                    box_count = res.json()["data"]["recoveryBox"][
                        "specialBoxTotalCount"
                    ]
                    box_status = res.json()["data"]["recoveryBox"]["boxStatus"]
                    if box_status:
                        coin = random.randint(100, int(box_count))
                        data = {"boxType": box_type, "coinCount": coin}

                if data is None:
                    return False

                self.countdown(30)
                data = json.dumps(data)
                res = self.http(special_box_collect_url, headers, data)
                open(".http_request.log", "a").write(res.text + "\n")
                if '"message":"Success"' in res.text:
                    coll_amount = res.json()["data"]["collectAmount"]
                    self.log(f"{hijau}success collect {coll_amount} from special box !")
                    return True

                self.log(f"{merah}failed collect coins !")
                return

        self.log(f"{merah}failed open box !")
        return False

    def levelup(self, data, name=None):
        url = "https://api.yescoin.gold/build/levelUp"
        headers = self.base_headers
        data = json.dumps(data)
        headers["content-length"] = str(len(data))
        res = self.http(url, headers, data)
        if '"message":"Success"' in res.text:
            self.log(f"{hijau}upgrade {name} successfully !")
            return True

        self.log(f"{merah}upgrade {name} failure !")
        return False

    def user_info(self, show_id=False, show_balance=False):
        url = "https://api.yescoin.gold/account/getAccountInfo"
        headers = self.base_headers
        res = self.http(url, headers)
        if '"message":"Success"' in res.text:
            coin = res.json()["data"]["currentAmount"]
            rank = res.json()["data"]["rank"]
            uid = res.json()["data"]["userId"]
            level = res.json()["data"]["userLevel"]
            if show_id:
                self.log(
                    f"{hijau}user id : {putih}{uid} {biru}| {hijau}level : {putih}{level}"
                )
            if show_balance:
                self.log(
                    f"{hijau}coins : {putih}{coin} {biru}| {hijau}rank : {putih}{rank}"
                )
            return coin

        return False

    def get_energy(self):
        url = "https://api.yescoin.gold/game/getGameInfo"
        headers = self.base_headers
        res = self.http(url, headers)
        if '"message":"Success"' in res.text:
            pool_left = res.json()["data"]["coinPoolLeftCount"]
            pool_total = res.json()["data"]["coinPoolTotalCount"]
            self.log(f"{hijau}energy remaining : {putih}{pool_left}/{pool_total}")
            return pool_left

        self.log(f"{merah}failed fetch get_energy data!")
        return False

    def collect_coin(self, data):
        url = "https://api.yescoin.gold/game/collectCoin"
        headers = self.base_headers
        data = json.dumps(data)
        headers["content-length"] = str(len(data))
        res = self.http(url, headers, data)
        if '"message":"Success"' in res.text:
            self.log(f"{hijau}success add {putih}{data} {hijau}coins !")
            return True

        self.log(f"{merah}failed add {putih}{data} {merah}coins !")
        return False

    def get_build_info(self):
        url = "https://api.yescoin.gold/build/getAccountBuildInfo"
        headers = self.base_headers
        res = self.http(url, headers)
        open(".http_request.log", "a").write(res.text + "\n")
        if '"message":"Success"' in res.text:
            data = {}
            data["multivalue"] = {}
            data["multivalue"]["cost"] = res.json()["data"]["singleCoinUpgradeCost"]
            data["multivalue"]["value"] = res.json()["data"]["singleCoinValue"]
            data["coinlimit"] = {}
            data["coinlimit"]["cost"] = res.json()["data"]["coinPoolTotalUpgradeCost"]
            data["fillrate"] = {}
            data["fillrate"]["cost"] = res.json()["data"]["coinPoolRecoveryUpgradeCost"]
            data["box_recovery"] = res.json()["data"]["specialBoxLeftRecoveryCount"]
            data["energy_recovery"] = res.json()["data"]["coinPoolLeftRecoveryCount"]
            return data

        self.log(f"{merah}failed fetch get_build_info !")
        return False

    def refresh_datajs(self):
        return json.loads(open("data.json", "r").read())

    def gen_data_login(self, data):
        data = self.data_parsing(data)
        user = json.loads(data["user"])
        data_login = {}
        data_login["id"] = user["id"]
        data_login["first_name"] = user["first_name"]
        if "last_name" in user.keys():
            data_login["last_name"] = user["last_name"]

        if "username" in user.keys():
            data_login["username"] = user["username"]

        data_login["language_code"] = user["language_code"]

        if "is_premium" in data.keys():
            data_login["is_premium"] = True

        data_login["allows_write_to_pm"] = user["allows_write_to_pm"]
        string_data = ""
        data_encode = json.dumps(data_login, separators=(",", ":"))
        string_data += "user=" + data_encode
        string_data += "&chat_instance=" + data["chat_instance"]
        string_data += "&chat_type=sender&auth_date=" + data["auth_date"]
        string_data += "&hash=" + data["hash"]
        return string_data

    def log(self, message):
        year, mon, day, hour, minute, second, a, b, c = time.localtime()
        mon = str(mon).zfill(2)
        hour = str(hour).zfill(2)
        minute = str(minute).zfill(2)
        second = str(second).zfill(2)
        print(f"{hitam}[{year}-{mon}-{day} {hour}:{minute}:{second}] {message}")

    def countdown(self, t):
        while t:
            menit, detik = divmod(t, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"waiting until {jam}:{menit}:{detik} ", flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def data_parsing(self, data):
        res = unquote(data)
        data = {}
        for i in res.split("&"):
            j = unquote(i)
            y, z = j.split("=")
            data[y] = z

        return data

    def login(self, data):
        login_url = "https://api.yescoin.gold/user/login"
        headers = self.base_headers
        if "token" in headers.keys():
            headers.pop("token")

        data = json.dumps({"code": data})
        # print(json.dumps(data))
        headers["content-length"] = str(len(json.dumps(data)))

        res = self.http("https://api.yescoin.gold/user/login", headers, data)
        open(".http_request.log", "a").write(res.text + "\n")
        if '"message":"Success"' in res.text:
            token = res.json()["data"]["token"]
            header, payload, sign = token.split(".")
            payload = json.loads(b64decode(payload + "==").decode("utf-8"))
            _data = {}
            _data["token"] = token
            _data["exp"] = payload["exp"]
            open("data.json", "w").write(json.dumps(_data, indent=4))
            self.log(f"{hijau}login success")
            return True

        self.log(f"{merah}login failure")
        return False

    def http(self, url: str, headers: dict, data: List[str, dict] = None):
        while True:
            try:
                if data is None:
                    headers["Content-Length"] = "0"
                    res = requests.get(url, headers=headers)
                    open(".http_request.log", "a").write(res.text + "\n")
                    return res

                headers["Content-Length"] = str(len(json.dumps(data)))
                res = requests.post(url, headers=headers, data=data)
                open(".http_request.log", "a").write(res.text + "\n")
                return res
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
            ):
                self.log(f"{merah}connection error / connection timeout !")
                continue


if __name__ == "__main__":
    try:
        app = Bot()
        app.main()
    except KeyboardInterrupt:
        sys.exit()
