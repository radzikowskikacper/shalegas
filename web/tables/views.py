## @file web/tables/views.py
# @brief The views module for tables application

from dictionaries.models import DictionaryMeasurement, stratigraphy_list
from measurements.utils import prepareFilter
from values.models import RealMeasurement
from boreholes.models import _JsonResponse
from django.db import transaction


def tables(request, borehole_id):
    if request.method == 'GET':
        with transaction.atomic():
            params, meanings, _, filter = prepareFilter(**dict(request.GET, **{'borehole_id' : borehole_id}))
            
            rmeasurements = RealMeasurement.objects.filter(**params).order_by('depth_from', 'meaning')
            dmeasurements = DictionaryMeasurement.objects.filter(**params).exclude(meaning_id__in = stratigraphy_list).order_by('depth_from', 'meaning')
            if filter:
                rmeasurements = rmeasurements.filter(filter)
                dmeasurements = dmeasurements.filter(filter)
                
            measurements = sorted(list(rmeasurements) + list(dmeasurements), key = lambda x : (x.depth_from, x.meaning_id))
        
            curdepth = None
            ret = {'header' : [{'name' : 'DEPTH_FROM'}]}
            data = []
            row = None
            temp = list()
            temp2 = list()

            for d in measurements:
                if d.meaning_id not in temp2:
                    temp.append(d)
                    temp2.append(d.meaning_id)
            temp = sorted(temp, key=lambda x: x.meaning_id)
            ret['header'] += ([{'name' : meanings[d.meaning_id].name, 'unit' : meanings[d.meaning_id].unit} for d in temp])
            temp = [d.meaning_id for d in temp]

            for d in measurements:
                #if d.meaning_id not in temp:
                 #   ret['header'].append({'name' : meanings[d.meaning_id].name, 'unit' : meanings[d.meaning_id].unit})
                    #temp.append(d.meaning_id)
        
                if d.depth_from != curdepth:
                    if row:
                        data.append(row)
                    curdepth = d.depth_from
                    row = [float(curdepth) / 100]
                    
                while len(row) <= temp.index(d.meaning_id):
                    row.append('')
                row.append(d.dictionary.value if hasattr(d, 'dictionary') else d.value)
        
            if row:
                data.append(row)
            for row in data:
                while len(row) <= len(temp):
                    row.append('')
        
            ret['data'] = data
            return _JsonResponse(ret)