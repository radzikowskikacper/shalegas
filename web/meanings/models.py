## @file web/meanings/models.py
#  @brief Models for meanings and sections

from django.db import models
import six
from boreholes.models import _JsonResponse
#from dictionaries.models import stratigraphy_list


class MeaningSection(models.Model):
    name = models.CharField(max_length = 64, primary_key = True)

class MeaningValue(models.Model):
    name = models.CharField(max_length = 64)
    unit = models.CharField(max_length = 64)
    section = models.ForeignKey(MeaningSection, to_field='name')

    class Meta:
        unique_together = ("name", "section")
        
class MeaningImage(MeaningValue):
    pass

class MeaningDict(MeaningValue):
    pass

class MeaningDictValue(models.Model):
    dict_id = models.ForeignKey('MeaningDict')
    value = models.CharField(max_length = 64)
    
    def to_dict(self):
        return {'id' : self.id, 'value' : self.value, 'dict_id' : self.dict_id.id}

class SectionsDuplicated(Exception):
    def __init__(self):
        Exception.__init__(self, 'section_exists')

class MeaningsDuplicated(Exception):
    def __init__(self):
        Exception.__init__(self, 'meaning_exists')

def getMeanings(**kwargs):
    def createElement(obj): 
        ret = {attr : six.text_type(getattr(obj, attr)) for attr in ("id", "name")}        
        if 'mid' in kwargs:
            
            if obj.unit == 'DICT':
                ret['dictvals'] = [val.to_dict() for val in MeaningDictValue.objects.filter(dict_id = obj)]
                ret['type'] = 'dict'
            elif obj.unit != 'PICT':
                ret['unit'] = obj.unit
                ret['type'] = 'normal'
            else:
                ret['type'] = 'pict'
        else:
            ret['unit'] = obj.unit
        ret['section'] = obj.section.name
        return ret
    
    ret = None
    if 'mid' in kwargs:
        ret = createElement(MeaningValue.objects.get(id = kwargs['mid'])) 
    else:
        if 'filter' in kwargs:
            if kwargs['filter'][0] == 'DICT':
                ret = [{'name' : s.name, 'meanings' : [createElement(u) for u in MeaningDict.objects.filter(section = s)
                                                       .order_by('name')]}
                        for s in MeaningSection.objects.order_by('name').exclude(name='Stratygrafia')]
            elif kwargs['filter'][0] == 'NDICT':
                ret = [{'name' : s.name, 'meanings' : [createElement(u) for u in MeaningValue.objects.filter(section = s)
                                                       .exclude(unit__in = ['DICT', 'PICT']).order_by('name')]}
                        for s in MeaningSection.objects.order_by('name')]
            elif kwargs['filter'][0] == 'PICT':
                ret = [{'name' : s.name, 'meanings' : [createElement(u) for u in MeaningImage.objects.filter(section = s).order_by('name')]}
                        for s in MeaningSection.objects.order_by('name')]
            elif kwargs['filter'][0] == 'STRAT':
                ret = [createElement(u) for u in MeaningDict.objects.filter(section = 'Stratygrafia').order_by('id')]
        else:
            ret = [{'name' : s.name, 'meanings' : [createElement(u) for u in MeaningValue.objects.filter(section = s)
                                                   .order_by('name')]}
                    for s in MeaningSection.objects.order_by('name')]

    return _JsonResponse(ret)

def getSections(sid=None):
    return _JsonResponse([s.name for s in MeaningSection.objects.order_by('name')])