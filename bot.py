import os
import sys
import time
import json
import random
import requests
from datetime import datetime
from urllib.parse import unquote, parse_qs
from base64 import b64decode, urlsafe_b64decode
from colorama import *

init(autoreset=True)

merah = Fore.LIGHTRED_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
hitam = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
putih = Fore.LIGHTWHITE_EX
line = putih + "~" * 50


class Bot:
    def __init__(self):
        self.peer = "theYescoin_bot"
        self.base_headers = {
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
        self.marin_kitagawa = lambda data: {
            key: value[0] for key, value in parse_qs(data).items()
        }
        self.token_file = ".tokens.json"

    def load_config(self):
        config = json.loads(open("config.json", "r").read())
        self.interval = int(config["interval"])
        self.sleep = int(config["sleep"])
        self.tap_start = int(config["tap_range"]["start"])
        self.tap_end = int(config["tap_range"]["end"])
        self.energy_limit = int(config["energy_limit"])
        self.coinlimit = config["auto_upgrade"]["coinlimit"]
        self.fillrate = config["auto_upgrade"]["fillrate"]
        self.multivalue = config["auto_upgrade"]["multivalue"]

    def is_expired(self, token):
        header, payload, sign = token.split(".")
        jeload = json.loads(urlsafe_b64decode(payload + "=="))
        exp = jeload.get("exp")
        now = int(time.time())
        if now > exp:
            return True
        return False

    def convert(self, data):
        out = ""
        key = list(data.keys())
        for i in key:
            out += i + "=" + data[i]
            if i == key[len(key) - 1]:
                break
            out += "&"
        return out

    def main(self):
        banner = f"""

    {hijau}AUTO SWAP-SWAP / TAP-TAP {putih}THEYESCOIN_BOT

    {hijau}By: {putih}t.me/AkasakaID
    {hijau}Github: {putih}@AkasakaID"""
        if not os.path.exists(self.token_file):
            open(self.token_file, "w").write(json.dumps({}))
        print(banner)
        self.load_config()
        while True:
            datas = [i for i in open("data.txt").read().splitlines() if len(i) > 0]
            for no, data in enumerate(datas):
                print(line)
                parser = self.marin_kitagawa(data)
                _user = parser.get("user")
                if _user is None:
                    self.log(f"{merah}something wrong with your data line {no + 1}")
                    continue
                user = json.loads(_user)
                self.id = str(user.get("id"))
                first_name = user.get("first_name")
                last_name = user.get("last_name")
                username = user.get("username")

                self.log(f"{hijau}name : {putih}{first_name} {last_name}")
                self.log(f"{hijau}username : {putih}{username}")
                tokens = json.loads(open(self.token_file).read())
                token = tokens.get(self.id)
                _data = self.convert(parser)
                if not token:
                    token = self.login(_data)
                if self.is_expired(token):
                    token = self.login(_data)
                self.base_headers["token"] = token
                while True:
                    self.user_info()
                    build = self.get_build_info()
                    if isinstance(build, bool):
                        continue

                    coin = random.randint(self.tap_start, self.tap_end)
                    energy_used = coin * int(build["multivalue"]["value"])
                    res_energy = self.get_energy()
                    if res_energy is False or int(energy_used) > int(res_energy):
                        if build["energy_recovery"] != 0:
                            recovery_url = (
                                "https://api.yescoin.gold/game/recoverCoinPool"
                            )
                            res = self.http(recovery_url, self.base_headers, "")
                            if res.json().get("code") != 0:
                                self.log(f"{merah}recoverty energy failure !")
                                continue
                            self.log(f"{hijau}success recovery energy !")
                            continue

                        if build["box_recovery"] != 0:
                            self.open_box()
                            continue

                        self.log(f"{kuning}limit energy reacted, login sleep mode !")
                        res_coin = self.user_info()
                        build = self.get_build_info()
                        if isinstance(build, bool):
                            break

                        if self.multivalue:
                            if int(res_coin) > int(build["multivalue"]["cost"]):
                                self.levelup(1, "multivalue")
                                continue
                            self.log(
                                f"{kuning}coins not enough to upgrade multivalue !"
                            )

                        if self.coinlimit:
                            if int(res_coin) > int(build["coinlimit"]["cost"]):
                                self.levelup(3, "coinlimit")
                                continue
                            self.log(f"{kuning}coins not enough to upgrade coinlimit !")

                        if self.fillrate:
                            if int(res_coin) > int(build["fillrate"]["cost"]):
                                self.levelup(2, "fillrate")
                                continue
                            self.log(f"{kuning}coins not enough to upgrade fillrate !")
                            break
                    self.collect_coin(coin)
                    self.countdown(self.interval)

                    continue
                self.countdown(self.sleep)

    def open_box(self):
        special_box_url = "https://api.yescoin.gold/game/recoverSpecialBox"
        special_box_info_url = "https://api.yescoin.gold/game/getSpecialBoxInfo"
        special_box_collect_url = "https://api.yescoin.gold/game/collectSpecialBoxCoin"
        res = self.http(special_box_url, self.base_headers, "")
        code = res.json().get("code")
        if code != 0:
            self.log(f"{merah}dont worry,get special box failure")
            return False
        res = self.http(special_box_info_url, self.base_headers)
        code = res.json().get("code")
        if code != 0:
            self.log(f"{merah}dont worry, get special box info failure ")
            return False
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
            box_count = res.json()["data"]["recoveryBox"]["specialBoxTotalCount"]
            box_status = res.json()["data"]["recoveryBox"]["boxStatus"]
            if box_status:
                coin = random.randint(100, int(box_count))
                data = {"boxType": box_type, "coinCount": coin}
        if data is None:
            return False
        self.countdown(30)
        data = json.dumps(data)
        res = self.http(special_box_collect_url, self.base_headers, data)
        code = res.json().get("code")
        if code != 0:
            self.log(f"collect coin failure !")
            return
        coll_amount = res.json()["data"]["collectAmount"]
        self.log(f"{hijau}success collect {coll_amount} from special box !")
        return True

    def levelup(self, data, name=None):
        url = "https://api.yescoin.gold/build/levelUp"
        data = json.dumps(data)
        res = self.http(url, self.base_headers, data)
        if res.json().get("code") != 0:
            self.log(f"{merah}upgrade {name} failure !")
            return False

        self.log(f"{hijau}upgrade {name} successfully !")
        return True

    def user_info(self):
        url = "https://api.yescoin.gold/account/getAccountInfo"
        headers = self.base_headers
        res = self.http(url, headers)
        code = res.json().get("code")
        if code != 0:
            self.log(f"{merah}something wrong, check http.log !")
            return False

        coin = res.json()["data"]["currentAmount"]
        rank = res.json()["data"]["rank"]
        uid = res.json()["data"]["userId"]
        level = res.json()["data"]["userLevel"]
        self.log(f"{hijau}total coin : {putih}{coin}")

        return coin

    def get_energy(self):
        url = "https://api.yescoin.gold/game/getGameInfo"
        res = self.http(url, self.base_headers)
        if res.json().get("code") != 0:
            self.log(f"{merah}failed fetch get_energy data !")
            return False

        pool_left = res.json()["data"]["coinPoolLeftCount"]
        pool_total = res.json()["data"]["coinPoolTotalCount"]
        self.log(f"{hijau}energy remaining : {putih}{pool_left}/{pool_total}")
        return pool_left

    def collect_coin(self, data):
        url = "https://api.yescoin.gold/game/collectCoin"
        headers = self.base_headers
        data = json.dumps(data)
        res = self.http(url, self.base_headers, data)
        if res.json().get("code") != 0:
            self.log(f"{merah}failed add {putih}{data} {merah}")
            return False

        self.log(f"{hijau}success add {putih}{data} {hijau}coins !")
        return True

    def get_build_info(self):
        url = "https://api.yescoin.gold/build/getAccountBuildInfo"
        res = self.http(url, self.base_headers)
        code = res.json().get("code")
        if code != 0:
            self.log(f"{merah}something wrong, check http.log !")
            return False

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

    def log(self, message):
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{hitam}[{now}]{putih} {message}{reset}")

    def countdown(self, t):
        for t in range(t, 0, -1):
            menit, detik = divmod(t, 60)
            jam, menit = divmod(menit, 60)
            jam = str(jam).zfill(2)
            menit = str(menit).zfill(2)
            detik = str(detik).zfill(2)
            print(f"waiting until {jam}:{menit}:{detik} ", flush=True, end="\r")
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def save_token(self, id, token):
        data = json.loads(open(self.token_file).read())
        data[id] = token
        open(self.token_file, "w").write(json.dumps(data))

    def login(self, data):
        login_url = "https://api.yescoin.gold/user/login"
        if self.base_headers.get("token"):
            self.base_headers.pop("token")

        data = {"code": data}
        res = self.http(login_url, self.base_headers, json.dumps(data))
        if res.status_code != 200:
            self.log(f"{merah}something wrong,check http.log !")
            return False
        code = res.json().get("code")
        if code is None:
            self.log(f"{merah}something wrong, check http.log")
            return False
        if code != 0:
            self.log(f"{merah}something wrong, check http.log")
            return False
        token = res.json().get("data").get("token")
        self.save_token(self.id, token)
        self.log(f"{putih}login {hijau}successfully !")
        return token

    def http(self, url: str, headers: dict, data=None):
        while True:
            try:
                if data is None:
                    res = requests.get(url, headers=headers)
                elif data == "":
                    res = requests.post(url, headers=headers)
                else:
                    res = requests.post(url, headers=headers, data=data)

                open("http.log", "a", encoding="utf-8").write(
                    f"{res.status_code} {res.text}\n"
                )
                return res
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ):
                self.log(f"{merah}connection error / connection timeout !")
                continue


if __name__ == "__main__":
    try:
        app = Bot()
        app.main()
    except KeyboardInterrupt:
        sys.exit()
