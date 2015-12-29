## @file web/measurements/utils.py
# @brief Utility functions module for measurements.views and measurements.export

from django.db.models import Q

from boreholes.models import Borehole, _JsonResponse
from dictionaries.models import stratigraphy_list, DictionaryMeasurement
from images.models import Image
from meanings.models import MeaningValue
from values.models import RealMeasurement
from measurements.models import FilterIntersectionEmpty
import settings

def prepareFilter(**kwargs):
    params = {}
    mtype = kwargs.get('type', None)
    mtype = mtype[0] if isinstance(mtype, list) else mtype

    bh = Borehole.objects.get(id=(kwargs['borehole_id'][0] if isinstance(kwargs['borehole_id'], list) 
                                                           else kwargs['borehole_id'])) if mtype != 'ALL_BHS' else None
    
    strattable = None
    if 'strat' in kwargs:
        strats = DictionaryMeasurement.objects.filter(meaning_id__in = stratigraphy_list, dictionary__in = kwargs['strat'])
        if bh:
            strats = strats.filter(borehole_id = bh)
        strattable = intervals_calculator([(m.depth_from, m.depth_to) for m in strats.order_by('depth_from', 'depth_to')])
                        
    if mtype != 'ALL_BHS':
        params['borehole_id'] = bh
        
        if 'start_depth' in kwargs:
            params['depth_to__gte'] = int(float(kwargs['start_depth'][0] if isinstance(kwargs['start_depth'], list) 
                                            else kwargs['start_depth'])) * 100
        if 'stop_depth' in kwargs:
            params['depth_from__lte'] = int(float(kwargs['stop_depth'][0] if isinstance(kwargs['stop_depth'], list) 
                                            else kwargs['stop_depth'])) * 100

        if strattable:
            filter_intersection = False
            measurement_size = int(settings.MEASUREMENT_IMAGE_HEIGHT_CM) if mtype == 'PICT' else 1
            for s in strattable:
                if not(params['depth_to__gte'] - s[1] > measurement_size or s[0] - params['depth_from__lte'] > measurement_size):
                    filter_intersection = True
                    break
        else:
            filter_intersection = True
            
        if not filter_intersection:
            raise FilterIntersectionEmpty
    
    filter = None
    if isinstance(strattable, list):
        if len(strattable):
            filter = Q(depth_to__gte = strattable[0][0]) & Q(depth_from__lte = strattable[0][1])
            for s in strattable[1:]:
                filter |= Q(depth_to__gte = s[0]) & Q(depth_from__lte = s[1])
        else:
            filter = Q(depth_to__gte = settings.MAX_BOREHOLE_HEIGHT) & Q(depth_from__lte = -1)

    meanings = MeaningValue.objects.all()
    if mtype == 'STRAT':
        meanings = meanings.filter(id__in = stratigraphy_list)
    elif 'filter' in kwargs:
        meanings = meanings.filter(id__in = kwargs['filter'])
    params['meaning__in'] = meanings = dict((i.id, i) for i in list(meanings.order_by('id')))
    
    return (params, meanings, mtype, filter)
    
def getMeasurements(**kwargs):
    params, meanings, mtype, filter = prepareFilter(**kwargs)

    ret = list()
    if mtype == 'NDICT':
        data = RealMeasurement.objects.filter(**params).order_by('meaning__unit', 'meaning', 'depth_from')
        if filter:
            data = data.filter(filter)
        ret = [v.to_dict() + [meanings[v.meaning_id].name, meanings[v.meaning_id].unit] for v in data]
    elif mtype == 'DICT':
        data = DictionaryMeasurement.objects.filter(**params).order_by('meaning', 'depth_from')
        if filter:
            data = data.filter(filter)
        ret = [v.to_dict() + [meanings[v.meaning_id].name] for v in data]
    elif mtype == 'PICT':
        data = Image.objects.filter(**params).order_by('depth_from')
        data = data.values_list('id', 'depth_from', 'depth_to', 'geophysical_depth', 'meaning__name')
        if filter:
            data = data.filter(filter)
        ret = [{ "id" : img[0], "depth_from" : img[1], "depth_to" : img[2], "geophysical_depth" : img[3], "meaning" : img[4]} 
                                      for img in data]

    return _JsonResponse(ret)

def intervals_calculator(sections):
    """create overlapping intervals from sorted sections [from, to)"""
    intervals = []
    if sections:
        curr_start = sections[0][0]
        curr_end = sections[0][1]

    for s in sections:
        section_start = s[0]
        section_end = s[1]

        if curr_end < section_start: #the section not overlap existing interval
            intervals.append((curr_start, curr_end))
            curr_start = section_start
            curr_end = section_end
        elif curr_end < section_end: #the section increases existiong interval
            curr_end = section_end

    if sections: #the last section
        intervals.append((curr_start, curr_end))

    return intervals
