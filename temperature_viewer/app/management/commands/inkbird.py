import datetime
import traceback

from django.db import IntegrityError
from django.db.models import Avg
from bluepy import btle
import binascii
from django.utils import timezone
import ambient
import os
from django.core.management.base import BaseCommand
from ...models import *

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
RETRY = 10


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
        self.tm = timezone.datetime.now()
        # peripheral
        self.peripheral = btle.Peripheral(self.address)
        # データ読み取り
        characteristic = self.peripheral.readCharacteristic(self.handle)
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
        # TimeData
        try:
            # DBに保存
            TimeData.objects.create(tm=self.tm, temperature=self.temp, humidity=self.humid, is_external=bool(self.is_external))
        # [例外処理]重複エラー
        except IntegrityError:
            pass
        # [例外処理]エラー
        except Exception:
            self.error_log()
        # DayData
        if self.tm.hour == 0 and self.tm.minute == 0:
            try:
                # 作成
                day = datetime.datetime.date(self.tm - datetime.timedelta(days=1))
                temperature_sorted = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by('temperature')
                humidity_sorted = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by('humidity')
                temperature_min = temperature_sorted.first()
                temperature_max = temperature_sorted.last()
                temperature_avg = temperature_sorted.aggregate(Avg('temperature'))
                humidity_min = humidity_sorted.first()
                humidity_max = humidity_sorted.last()
                humidity_avg = humidity_sorted.aggregate(Avg('humidity'))
                is_incomplete = temperature_sorted.count() != 288
                # DBへの登録
                DayData.objects.create(day=day, temperature_min=temperature_min, temperature_max=temperature_max, temperature_avg=temperature_avg['temperature__avg'], humidity_min=humidity_min, humidity_max=humidity_max, humidity_avg=humidity_avg['humidity__avg'], is_incomplete=is_incomplete)
            # [例外処理]重複エラー
            except IntegrityError:
                daydata = DayData.objects.filter(day__year=day.year, day__month=day.month, day__day=day.day).first()
                daydata.day = day
                daydata.temperature_min = temperature_min
                daydata.temperature_max = temperature_max
                daydata.temperature_avg = temperature_avg['temperature__avg']
                daydata.humidity_min = humidity_min
                daydata.humidity_max = humidity_max
                daydata.humidity_avg = humidity_avg['humidity__avg']
                daydata.is_incomplete = is_incomplete
                daydata.save()
            # [例外処理]エラー
            except Exception:
                self.error_log()

    def upload_ambient(self):
        # データアップロード
        data = {
            "d1": self.t.strftime("%Y%m%d%H%M"),
            "d2": self.tmemp,
            "d3": self.humid,
            "d4": self.is_external,
        }
        am = ambient.Ambient(self.channel_id, self.write_key)
        am.send(data)

    def error_log(self):
        # ログを記述
        with open(f"error-{timezone.datetime.now().strftime('%Y_%m_%d_%H%M%S')}.log", mode='a') as f:
            traceback.print_exc(file=f)


class Command(BaseCommand):
    def handle(self, *args, **options):
        app = Inkbird(MAC_ADDRESS, HANDLE, CHANNEL_ID, WRITE_KEY, SAVE_PATH)
        # データ取得
        for _ in range(RETRY):
            # データ取得
            try:
                app.get_data()
            # エラー
            except Exception as e:
                print(f'{e.__class__.__name__}: {e}')
                app.error_log()
                continue
            # 成功
            else:
                # DBに保存
                app.save()
                for _ in range(RETRY):
                    # アップロード
                    try:
                        app.upload_ambient()
                    # エラー
                    except Exception as e:
                        print(f'{e.__class__.__name__}: {e}')
                        app.error_log()
                        continue
                    # 成功
                    else:
                        break
                break
