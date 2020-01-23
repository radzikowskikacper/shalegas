# @file web/data/views.py
# @brief The views module for data application

from boreholes.models import _JsonResponse, Borehole
from dictionaries.models import DictionaryMeasurement  # , stratigraphy_list
from measurements.utils import prepareFilter
from values.models import RealMeasurement
from django.db import transaction
from meanings.models import MeaningDict


def data(request):
    if request.method == 'GET':
        with transaction.atomic():
            params, meanings, _, filter = prepareFilter(**request.GET)

            vals = RealMeasurement.objects.filter(**params)
            dicts = DictionaryMeasurement.objects.filter(
                **params).exclude(meaning_id__in=MeaningDict.objects.filter(section='Stratygrafia'))
            boreholes = {bh.id: bh.name for bh in Borehole.objects.all()}

            if filter:
                vals = vals.filter(filter)
                dicts = dicts.filter(filter)

            curdepth = None
            ret = {
                'boreholes': [], 'meanings': [
                    m.id for m in meanings.values()]}
            data = []
            row = None

            for d in sorted(
                list(vals) + list(dicts),
                key=lambda x: (
                    x.depth_from,
                    x.borehole_id,
                    x.meaning_id)):
                if d.depth_from != curdepth:
                    if row:
                        data.append(row)
                    curdepth = d.depth_from
                    row = [float(curdepth) / 100.0]

                if d.borehole_id not in ret['boreholes']:
                    ret['boreholes'].append(d.borehole_id)

                row += ['' for i in range(ret['boreholes'].index(d.borehole_id)
                                          * len(ret['meanings']) - len(row) + 1)]

                if len(ret['meanings']) > 1:
                    row += ['' for i in range(ret['meanings'].index(
                        d.meaning_id) - (len(row) - 1) % len(ret['meanings']))]

                row.append(
                    d.dictionary.value if hasattr(
                        d, 'dictionary') else d.value)

            if row:
                data.append(row)

            for row in data:
                while len(row) <= len(ret['boreholes']) * len(ret['meanings']):
                    row.append('')
            ret['boreholes'] = [boreholes[bh] for bh in ret['boreholes']]

            ret['meanings'] = [{'name': m.name, 'unit': m.unit}
                               for m in meanings.values()]
            ret['data'] = data

            return _JsonResponse(ret)
