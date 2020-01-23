##
# @file web/images/common.py
# @brief Module with common functions used by images services

import settings
from PIL import Image
from io import BytesIO
from measurements.models import MeasurementsDuplicated
from . import models


class BadImageSizeException(Exception):
    pass


def add_image(image_bytes, **kwargs):
    if 'meaning' not in kwargs:
        if models.Image.objects.filter(
                meaning=None,
                borehole=kwargs['borehole'],
                depth_from=kwargs['depth_from'],
                depth_to=kwargs['depth_to']).exists():
            raise MeasurementsDuplicated
    else:
        if models.Image.objects.filter(
                meaning=kwargs['meaning'],
                borehole=kwargs['borehole'],
                depth_from=kwargs['depth_from'],
                depth_to=kwargs['depth_to']).exists():
            raise MeasurementsDuplicated
    return models.Image.objects.create(imagedata=image_bytes, **kwargs)


def imagePosHeight(relative_depth_cm):
    """
    calculate the image height position in pixels.
    """
    image_height_px = int(settings.MEASUREMENT_IMAGE_HEIGHT_PX)
    image_height_cm = int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
    return int((relative_depth_cm * image_height_px) / image_height_cm)


def calculateImgHeight(depthRange):
    imgheight = depthRange
    if depthRange != settings.MAX_BOREHOLE_HEIGHT:
        if depthRange > 1000:
            imgheight = 1000
        elif depthRange > 100:
            imgheight = 100
        elif depthRange > 10:
            imgheight = 10
        else:
            imgheight = 1

    return imgheight
