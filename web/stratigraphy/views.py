## @file web/stratigraphy/views.py
# @brief The views module for stratigraphy application

from decimal import Decimal
import json, logging

from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement#, stratigraphy_list
from django.db import transaction
from meanings.models import MeaningDict, MeaningDictValue
from stratigraphy.utils import getStratigraphy

logger = logging.getLogger('sweetspot.stratigraphy')

def stratigraphy(request, borehole_id):
    if request.method == 'GET':
        with transaction.atomic():
            return getStratigraphy(**dict(request.GET, **{'borehole_id' : borehole_id}))
    
    elif request.method == 'POST':
        params = json.loads(request.read().decode('utf-8'))
                        
        geodepth = None
        if "geophysical_depth" in params:
            geodepth = params["geophysical_depth"]
        elif "depth_from" in params:
            geodepth = params["depth_from"]
        else:
            geodepth = params["depth"]
                
        geodepth = int(Decimal(geodepth.replace(',', '.')) * 100)
        drilldepth = None
        if "depth_from" in params:
            drilldepth = params["depth_from"]
        elif "geophysical_depth" in params:
            drilldepth = params["geophysical_depth"]
        else:
            drilldepth = params['depth']
                   
        drilldepth = int(Decimal(drilldepth.replace(',', '.')) * 100)

        with transaction.atomic():
            depth_to = int(Decimal(params['depth_to'].replace(',', '.')) * 100)
            for d in MeaningDict.objects.filter(section = 'Stratygrafia'):
                if str(d.id) in params:
                    meaningdict = MeaningDict.objects.get(id = d.id)
                    DictionaryMeasurement.objects.create(borehole = Borehole.objects.get(id = borehole_id), geophysical_depth = geodepth, depth_from=drilldepth,
                                                              depth_to = depth_to, meaning = meaningdict,
                                                              dictionary = MeaningDictValue.objects.get(id = int(params[str(d.id)]),
                                                                                                       dict_id = meaningdict))
                elif d.id == 603:
                    raise KeyError
                
            logger.info("User %s added stratigraphy entry" % request.user.username)
            return getStratigraphy(**dict(params['query'], **{'borehole_id' : borehole_id}))
