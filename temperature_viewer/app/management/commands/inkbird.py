from bluepy import btle
import binascii
import datetime
import time
import ambient
import os
from lib2to3.pytree import Base
from django.core.management.base import BaseCommand
from models import TimeData

# MACアドレス
MAC_ADDRESS = "D8:A9:8B:75:40:D9"
# handle
HANDLE = 0x0028
# Ambient
CHANNEL_ID = "46295"
WRITE_KEY = "4b49c065ac4682f3"
# 保存ファイルの場所
SAVE_PATH = os.path.join(os.path.dirname(__file__), "result.txt")
# 再試行回数
RETRY = 5


class Inkbird:
    def __init__(self, address, handle, channel_id, write_key, save_path) -> None:
        # MACアドレス
        self.address = address
        # handle
        self.handle = handle
        # Ambient
        self.channel_id = channel_id
        self.write_key = write_key
        # 保存場所
        self.save_path = save_path

    def get_data(self):
        # 時間取得
        self.t = datetime.datetime.now()
        # データ取得
        try:
            # peripheral
            self.peripheral = btle.Peripheral(self.address)
            # データ読み取り
            characteristic = self.peripheral.readCharacteristic(self.handle)
        except Exception as e:
            raise e
        # 切断
        else:
            self.peripheral.disconnect
        # 気温取得
        temp_hex = binascii.b2a_hex(bytes([characteristic[1]])) + binascii.b2a_hex(
            bytes([characteristic[0]])
        )
        self.temp = float(int(temp_hex, 16)) / 100
        # 負の値の場合
        if self.temp > 327.67:
            self.temp -= 655.36
        # 湿度取得
        humid_hex = binascii.b2a_hex(bytes([characteristic[3]])) + binascii.b2a_hex(
            bytes([characteristic[2]])
        )
        self.humid = float(int(humid_hex, 16)) / 100
        # 外部プローブが接続されているかどうか
        is_external_hex = binascii.b2a_hex(bytes([characteristic[4]]))
        self.is_external = int(is_external_hex, 16)

    def save(self):
        # DBに保存
        TimeData.objects.create(tm=self.t, temperature=self.temp, humidity=self.humid, is_external=bool(self.is_external))

    def upload_ambient(self):
        # データアップロード
        data = {
            "d1": self.t.strftime("%Y%m%d%H%M"),
            "d2": self.temp,
            "d3": self.humid,
            "d4": self.is_external,
        }
        am = ambient.Ambient(self.channel_id, self.write_key)
        try:
            am.send(data)
        except Exception as e:
            raise e


class Command(BaseCommand):
    def handle(self, *args, **options):
        app = Inkbird(MAC_ADDRESS, HANDLE, CHANNEL_ID, WRITE_KEY, SAVE_PATH)
        # データ取得
        for _ in range(RETRY):
            try:
                app.get_data()
            # エラー
            except Exception as e:
                print(e)
                continue
            # 成功
            else:
                # DBに保存
                app.save()
                # アップロード
                for _ in range(RETRY):
                    try:
                        app.upload_ambient()
                    # エラー
                    except Exception as e:
                        print(e)
                        continue
                    # 成功
                    else:
                        break
                break
