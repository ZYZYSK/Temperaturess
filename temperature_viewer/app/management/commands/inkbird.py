import datetime
from time import time
import traceback

from django.db import IntegrityError
from django.db.models import Avg, Sum
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
RETRY_BLUETOOTH = 10
RETRY_NET = 2


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
        self.tm = timezone.make_aware(self.tm)
        # peripheral
        self.peripheral = btle.Peripheral(self.address)
        # データ読み取り
        characteristic = self.peripheral.readCharacteristic(self.handle)
        self.peripheral.disconnect
        # 気温取得
        temp_hex = binascii.b2a_hex(bytes([characteristic[1]])) + binascii.b2a_hex(
            bytes([characteristic[0]])
        )
        self.temperature = float(int(temp_hex, 16)) / 100
        # 負の値の場合
        if self.temperature > 327.67:
            self.temperature -= 655.36
        # 湿度取得
        humid_hex = binascii.b2a_hex(bytes([characteristic[3]])) + binascii.b2a_hex(
            bytes([characteristic[2]])
        )
        self.humidity = float(int(humid_hex, 16)) / 100
        # 外部プローブが接続されているかどうか
        is_external_hex = binascii.b2a_hex(bytes([characteristic[4]]))
        self.is_external = int(is_external_hex, 16)

    def save(self):
        # TimeData
        try:
            # DBに保存
            TimeData.objects.create(tm=self.tm, temperature=self.temperature, humidity=self.humidity, is_external=bool(self.is_external))
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
                timedata_sorted_temperature = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by('temperature')
                timedata_sorted_humidity = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by('humidity')
                timedata_sorted_dict = timedata_sorted_temperature.values()
                # 最低気温と最高気温
                temperature_min = timedata_sorted_temperature.first()
                temperature_max = timedata_sorted_temperature.last()
                # 最低湿度と最高湿度
                humidity_min = timedata_sorted_humidity.first()
                humidity_max = timedata_sorted_humidity.last()
                # 平均気温と平均湿度
                tm_past = datetime.datetime(day.year, day.month, day.day, 0, 0)
                temperature_sum = timedata_sorted_temperature.aggregate(Sum('temperature'))['temperature__sum']
                temperature_temp = timedata_sorted_temperature.aggregate(Avg('temperature'))['temperature__avg']
                humidity_sum = timedata_sorted_humidity.aggregate(Sum('humidity'))['humidity__sum']
                humidity_temp = timedata_sorted_humidity.aggregate(Avg('humidity'))['humidity__avg']
                for _ in range(288):
                    timedata_temp = list(filter(lambda item: item['tm'].hour == tm_past.hour and item['tm'].minute == tm_past.minute, timedata_sorted_dict))
                    # timedata_temp = timedata_sorted_temperature.filter(tm__hour=tm_past.hour, tm__minute=tm_past.minute).values()
                    # その時間のデータが存在する場合、一時的に値を記録しておく(初期値はその日の平均値)
                    if len(timedata_temp) > 0:
                        temperature_temp = timedata_temp[0]['temperature']
                        humidity_temp = timedata_temp[0]['humidity']
                    # その時間のデータが存在しない場合、前の時刻のデータを使う
                    else:
                        temperature_sum += temperature_temp
                        humidity_sum += humidity_temp
                    tm_past += datetime.timedelta(minutes=5)
                is_incomplete = timedata_sorted_temperature.count() != 288
                # DBへの登録
                DayData.objects.create(day=day, temperature_min=temperature_min, temperature_max=temperature_max, temperature_avg=temperature_sum / 288, humidity_min=humidity_min, humidity_max=humidity_max, humidity_avg=humidity_sum / 288, is_incomplete=is_incomplete)
            # [例外処理]重複エラー
            except IntegrityError:
                daydata = DayData.objects.filter(day__year=day.year, day__month=day.month, day__day=day.day).first()
                daydata.day = day
                daydata.temperature_min = temperature_min
                daydata.temperature_max = temperature_max
                daydata.temperature_avg = temperature_sum / 288
                daydata.humidity_min = humidity_min
                daydata.humidity_max = humidity_max
                daydata.humidity_avg = humidity_sum / 288
                daydata.is_incomplete = is_incomplete
                daydata.save()
            # [例外処理]エラー
            except Exception:
                self.error_log()

    def upload_ambient(self):
        # データアップロード
        data = {
            "d1": self.tm.strftime("%Y%m%d%H%M"),
            "d2": self.temperature,
            "d3": self.humidity,
            "d4": self.is_external,
        }
        am = ambient.Ambient(self.channel_id, self.write_key)
        am.send(data)

    def error_log(self):
        os.makedirs('logs', exist_ok=True)
        # ログを記述
        with open(f"logs/error-{timezone.datetime.now().strftime('%Y_%m_%d_%H%M%S')}.log", mode='a') as f:
            traceback.print_exc(file=f)


class Command(BaseCommand):
    def handle(self, *args, **options):
        app = Inkbird(MAC_ADDRESS, HANDLE, CHANNEL_ID, WRITE_KEY, SAVE_PATH)
        # データ取得
        for _ in range(RETRY_BLUETOOTH):
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
                for _ in range(RETRY_NET):
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
