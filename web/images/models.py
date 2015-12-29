##
# @file web/images/models.py
# @brief Model for image, image is measurement with binary field storing bitmap

from django.db import models
from measurements.models import Measurement
from meanings.models import MeaningImage

#version = 1

class Image(Measurement):
    imagedata = models.BinaryField()
    meaning = models.ForeignKey(MeaningImage, null=True, default=None)
