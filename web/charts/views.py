# @file web/charts/views.py
# @brief Views module for charts application

import json
import os

from images.views import _JsonResponse
from values.models import NoDictionaryFile, RealMeasurement
from measurements.utils import prepareFilter
from django.http import HttpResponse


def charts(request, borehole_id):
    if request.method == 'GET':
        params, meanings, _, filter = prepareFilter(
            **dict(request.GET, **{'borehole_id': borehole_id}))
        data = RealMeasurement.objects.filter(
            **params).order_by('meaning__unit', 'meaning', 'depth_from')
        if filter:
            data = data.filter(filter)

        lang = request.GET['lang']
        if not os.path.isfile('values/dicts/%s_normal.json' % lang):
            raise NoDictionaryFile
        dicts = json.load(open('values/dicts/%s_normal.json' % lang))

        ret = list()
        if 'unit_pair' not in request.GET:
            for v in data:
                temp = next(
                    (item for item in ret if item['name'] == dicts[meanings[v.meaning_id].name]), None)
                to_add = v.to_dict()
                for i in [0, 2, 3]:
                    to_add[i] /= 100.0
                if not temp:
                    ret.append({'name': dicts[meanings[v.meaning_id].name],
                                'unit': meanings[v.meaning_id].unit, 'data': [[to_add]]})
                else:
                    temp['data'][0].append(to_add)
        elif request.GET['unit_pair']:
            curunit = curmeaning = None
            for v in data:
                if curunit != meanings[v.meaning_id].unit:
                    curunit = meanings[v.meaning_id].unit
                    ret.append({'unit': curunit, 'data': list(),
                                'names': list()})

                if curmeaning != meanings[v.meaning_id].name:
                    curmeaning = meanings[v.meaning_id].name
                    ret[-1]['data'].append(list())
                    ret[-1]['names'].append({'label': dicts[curmeaning]})
                to_add = v.to_dict()
                for i in [0, 2, 3]:
                    to_add[i] /= 100.0
                ret[-1]['data'][-1].append(to_add)

        return _JsonResponse(ret)
    else:
        return HttpResponse(status=405)
