from datetime import datetime
from config import *

class Logger(object):

    def __init__(self):
        pass

    @staticmethod
    def timestamp_to_string(timestamp, datetime_fmt="%Y/%m/%d %H:%M:%S:%f"):
        return datetime.fromtimestamp(timestamp).strftime(datetime_fmt)

    @staticmethod
    def print(value):
        if g_logger_enable:
            print("[%s] %s" % (datetime.now().strftime("%m/%d/%Y %H:%M:%S"), value))
