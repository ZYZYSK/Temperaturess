import datetime
import json
import logging
import os
import numpy as np
import traceback
import ambient
from bluepy import btle
import binascii

from django.db import IntegrityError
from django.utils import timezone
from django.core.management.base import BaseCommand

from ...models import *


def create_log(is_debug: bool = False) -> logging.Logger:
    # set log level
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if is_debug:
        logger.setLevel(logging.DEBUG)
    # create directory "logs" if not exists
    os.makedirs("logs", exist_ok=True)
    # set save log path
    log_handler = logging.FileHandler(
        datetime.datetime.now().strftime("logs/%Y_%m_%d_%H_%M_%S.log")
    )
    # set log format
    log_format = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(filename)s %(funcName)s  %(lineno)s : %(message)s"
    )
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    return logger


class Inkbird:
    def __init__(
        self,
        address: str,
        handle: str,
        channel_id: str,
        write_key: str,
        logger: logging.Logger,
    ) -> None:
        # MAC address
        self.address = address
        # handle
        self.handle = int(handle, 16)
        # Ambient
        self.channel_id = channel_id
        self.write_key = write_key
        # Log
        self.logger = logger
        # for debugging
        self.logger.debug(
            f"MAC address: {self.address}, handle: {self.handle}, Channel ID: {self.channel_id}, write_key: {self.write_key}."
        )

    def get_data(self) -> None:
        # get current time
        self.tm = timezone.datetime.now()
        self.tm = timezone.make_aware(self.tm)
        self.tm = self.tm.replace(minute=5 * (self.tm.minute // 5))
        # peripheral
        self.peripheral = btle.Peripheral(self.address)
        # read data
        characteristic = self.peripheral.readCharacteristic(self.handle)
        self.peripheral.disconnect
        # get temperature from data
        temp_hex = binascii.b2a_hex(bytes([characteristic[1]])) + binascii.b2a_hex(
            bytes([characteristic[0]])
        )
        self.temperature = float(int(temp_hex, 16)) / 100
        if self.temperature > 327.67:
            self.temperature -= 655.36
        # get humidity from data
        humid_hex = binascii.b2a_hex(bytes([characteristic[3]])) + binascii.b2a_hex(
            bytes([characteristic[2]])
        )
        self.humidity = float(int(humid_hex, 16)) / 100
        # whether or not using external probe
        is_external_hex = binascii.b2a_hex(bytes([characteristic[4]]))
        self.is_external = bool(int(is_external_hex, 16))

    def save(self):
        # TimeData
        try:
            # save data to database
            TimeData.objects.create(
                tm=self.tm,
                temperature=self.temperature,
                humidity=self.humidity,
                is_external=self.is_external,
            )
        # exception: Data Duplication
        except IntegrityError:
            self.logger.error("Error: This TimeData already exists!")
        # exception: Others
        except Exception:
            self.logger.error(traceback.format_exc())
        # for debugging
        else:
            self.logger.debug(
                f"Successfully created TimeData ({self.tm}, {self.temperature}C, {self.humidity}%)."
            )
        # DayData
        # if True:
        if self.tm.hour == 0 and self.tm.minute == 0:
            try:
                # 作成
                day = datetime.datetime.date(self.tm - datetime.timedelta(days=1))
                # day = day.replace(year=2023, month=7, day=24)
                timedatas = TimeData.objects.filter(
                    tm__year=day.year, tm__month=day.month, tm__day=day.day
                )
                datas = timedatas.values()

                # get min & max temperature
                temperature_min = min([data.get("temperature") for data in datas])
                temperature_max = max([data.get("temperature") for data in datas])
                timedata_temperature_min = timedatas.filter(
                    temperature=temperature_min
                ).first()
                timedata_temperature_max = timedatas.filter(
                    temperature=temperature_max
                ).first()
                # get min & max humidity
                humidity_min = min([data.get("humidity") for data in datas])
                humidity_max = max([data.get("humidity") for data in datas])
                timedata_humidity_min = timedatas.filter(humidity=humidity_min).first()
                timedata_humidity_max = timedatas.filter(humidity=humidity_max).first()

                # get average temperature & humidity
                time_past = datetime.datetime(day.year, day.month, day.day, 0, 0)
                temperature_sum = np.sum([data.get("temperature") for data in datas])
                humidity_sum = np.sum([data.get("humidity") for data in datas])
                temperature_temp0 = np.mean([data.get("temperature") for data in datas])
                humidity_temp0 = np.mean([data.get("humidity") for data in datas])
                cnt_errors = 0
                for index in range(288):
                    timedata_temp = list(
                        filter(
                            lambda item: item["tm"].hour == time_past.hour
                            and item["tm"].minute == time_past.minute,
                            datas,
                        )
                    )
                    # record the data temporary if exists
                    if len(timedata_temp) > 0:
                        temperature_temp1 = timedata_temp[0]["temperature"]
                        humidity_temp1 = timedata_temp[0]["humidity"]
                        if cnt_errors > 0:
                            temperature_sum += (
                                cnt_errors * (temperature_temp0 + temperature_temp1) / 2
                            )
                            humidity_sum += (
                                cnt_errors * (humidity_temp0 + humidity_temp1) / 2
                            )
                            cnt_errors = 0
                        temperature_temp0 = temperature_temp1
                        humidity_temp0 = humidity_temp1
                    # use the previous data if doesn't exist
                    else:
                        cnt_errors += 1
                        # if it is the last timedata in that day
                        if index == 288:
                            temperature_temp1 = np.mean(
                                [data.get("temperature") for data in datas]
                            )
                            humidity_temp1 = np.mean(
                                [data.get("humidity") for data in datas]
                            )
                            temperature_sum += (
                                cnt_errors * (temperature_temp0 + temperature_temp1) / 2
                            )
                            humidity_sum += (
                                cnt_errors * (humidity_temp0 + humidity_temp1) / 2
                            )
                            cnt_errors = 0

                    # advance the time
                    time_past += datetime.timedelta(minutes=5)
                # check if all datas were recorded
                is_incomplete = len(datas) != 288
                # register data into database
                DayData.objects.create(
                    day=day,
                    temperature_min=timedata_temperature_min,
                    temperature_max=timedata_temperature_max,
                    temperature_avg=temperature_sum / 288,
                    humidity_min=timedata_humidity_min,
                    humidity_max=timedata_humidity_max,
                    humidity_avg=humidity_sum / 288,
                    is_incomplete=is_incomplete,
                )
            # exception: Data Duplication
            except IntegrityError:
                self.logger.warning("Warning: This DayData already exists!")
                daydata = DayData.objects.filter(
                    day__year=day.year, day__month=day.month, day__day=day.day
                ).first()
                daydata.day = day
                daydata.temperature_min = timedata_temperature_min
                daydata.temperature_max = timedata_temperature_max
                daydata.temperature_avg = temperature_sum / 288
                daydata.humidity_min = timedata_humidity_min
                daydata.humidity_max = timedata_humidity_max
                daydata.humidity_avg = humidity_sum / 288
                daydata.is_incomplete = is_incomplete
                daydata.save()
                # for debugging
                self.logger.debug(
                    f"Successfully created DayData ({day}, {temperature_min}C, {temperature_max}C, {temperature_sum/288}C,{humidity_min}%, {humidity_max}%, {humidity_sum/288}%)."
                )
            # exception: Others
            except Exception as e:
                self.logger.error(traceback.format_exc())
            # for debugging
            else:
                self.logger.debug(
                    f"Successfully created DayData ({day}, {temperature_min}C, {temperature_max}C, {temperature_sum/288}C,{humidity_min}%, {humidity_max}%, {humidity_sum/288}%)."
                )

    def upload_ambient(self):
        # upload data to ambient
        data = {
            "d1": self.tm.strftime("%Y%m%d%H%M"),
            "d2": self.temperature,
            "d3": self.humidity,
            "d4": self.is_external,
        }
        try:
            am = ambient.Ambient(self.channel_id, self.write_key)
            am.send(data)
        except Exception as e:
            self.logger.error(traceback.format_exc())
        else:
            self.logger.debug("Successfully uploaded to Ambient.")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # load settings
        _settings = open("../settings.json")
        settings = json.load(_settings)
        MAC_ADDRESS = settings["mac_address"]
        HANDLE = settings["handle"]
        CHANNEL_ID = settings["channel_id"]
        WRITE_KEY = settings["write_key"]
        RETRY_BLUETOOTH = settings["retry_bluetooth"]
        RETRY_NET = settings["retry_net"]
        IS_DEBUG = settings["is_debug"]

        # set log
        logger = create_log(IS_DEBUG)
        logger.debug("Successfully created log.")

        app = Inkbird(MAC_ADDRESS, HANDLE, CHANNEL_ID, WRITE_KEY, logger)
        # データ取得
        for _ in range(RETRY_BLUETOOTH):
            # データ取得
            try:
                app.get_data()
            # エラー
            except Exception as e:
                logger.error(traceback.format_exc())
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
                        logger.error(traceback.format_exc())
                        continue
                    # 成功
                    else:
                        break
                break
