##
# @file web/version/views.py
# @brief Interface of version module, contains function to return database version, database connecting strings and application build version.

from django.conf import settings
from . import models

def get(params):
    """versions"""
    return {
        "paramsVer" : 1,
        "server": models.getVersionString(),
        "database": models.getDBVersionString(),
        "image_height_cm": settings.MEASUREMENT_IMAGE_HEIGHT_CM,
        "image_width_px": settings.MEASUREMENT_IMAGE_WIDTH_PX,
        "image_height_px": settings.MEASUREMENT_IMAGE_HEIGHT_PX,
        "borehole_max_height" : settings.MAX_BOREHOLE_HEIGHT
    }
