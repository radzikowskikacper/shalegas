##
# @file web/current/models.py
# @brief Empty model for current state of application
import datetime


def time(params):
    """server UTC time"""
    return str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
