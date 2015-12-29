##
# @file web/measurements/models.py
# @brief Model for measurement, which is abstract data connected with given borehole, described by drilling depth and geophysical depth

from django.db import models
from boreholes.models import Borehole

class MeasurementsDuplicated(Exception):
    def __init__(self):
        Exception.__init__(self, 'measurement_exists')

class FilterIntersectionEmpty(Exception):
    def __init__(self):
        Exception.__init__(self, 'filter_intersection_empty')

class Measurement(models.Model):
    borehole = models.ForeignKey(Borehole)
    depth_from = models.IntegerField() #in 0.01m (in cm)
    depth_to = models.IntegerField() #in 0.01m (in cm)
    geophysical_depth = models.IntegerField() #in 0.01m (in cm)
    
    def to_dict(self):
        "Returns dict representation of the object"
        '''
        return { "id" : self.id, "borehole" : self.borehole.id,
                 "depth_from" : self.depth_from, "depth_to" : self.depth_to, "geophysical_depth" : self.geophysical_depth  }
        '''
        return [self.depth_from, self.depth_to, self.geophysical_depth, self.id]

