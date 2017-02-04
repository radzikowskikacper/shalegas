##
# @file web/measurements/views.py
# @brief The views module for measurements, provides services for getting the list of measurements connected with given borehole and for consecutive measurements named intervals.

import csv
from decimal import Decimal
import json, six
import logging
import os, settings, codecs, io, sys

from PIL import Image, ImageDraw
from boreholes.models import Borehole, _JsonResponse
from dictionaries.models import DictionaryMeasurement#, stratigraphy_list
from django.db import transaction
from django.http import HttpResponse
from .export import doExport, doDownload
from images.common import add_image
from images.models import Image as Img
from meanings.models import MeaningValue, MeaningDict, MeaningDictValue, \
    MeaningImage
from .models import MeasurementsDuplicated
from .utils import getMeasurements, intervals_calculator
from values.models import RealMeasurement, NoDictionaryFile


logger = logging.getLogger('sweetspot.measurements')

def measurements(request, id = None):
    '''
    The service for getting a list of all measurements or getting particular measurement
    '''
    if request.method == 'GET':
        with transaction.atomic():
            return getMeasurements(**dict(request.GET, **{'borehole_id' : id}))
        
    elif request.method == 'POST':
        params = json.loads(request.read().decode('utf-8')) if not len(request.FILES) else request.POST
        
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
        depth_to = drilldepth + 1

        with transaction.atomic():
            borehole = Borehole.objects.get(id = id)
            if not 'query' in params and params['type'] == 'PICT':
                depth_to = drilldepth + int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
                meaning = MeaningImage.objects.get(id = params['meaning'])
                add_image(request.FILES["image_path"].read(), borehole = borehole, depth_from = drilldepth,
                    depth_to = depth_to, geophysical_depth = geodepth, meaning = meaning)
                logger.info("User %s added new photo measurement" % request.user.username)
                
                return getMeasurements(**dict(params, **{'borehole_id' : id}))
                
            elif params['query']['type'] == 'NDICT':
                if not RealMeasurement.objects.filter(borehole = borehole, depth_from = drilldepth, 
                                                      meaning = MeaningValue.objects.get(id = params['meaning'])).exists():
                    RealMeasurement.objects.create(borehole = borehole, geophysical_depth = geodepth,
                                                   depth_from = drilldepth, depth_to = depth_to,
                                                   value = float(params['value'].replace(',', '.')), meaning = MeaningValue.objects.get(
                                                                                        id = params['meaning']))
                    logger.info("User %s added new real measurement" % request.user.username)
                          
                    return getMeasurements(**dict(params['query'], **{'borehole_id' : id}))
                else:
                    raise MeasurementsDuplicated
            elif params['query']['type'] == 'DICT':
                meaning = MeaningDict.objects.get(id = params['meaning'])
                if not DictionaryMeasurement.objects.filter(borehole = borehole, depth_from = drilldepth, meaning = meaning).exists():
                    DictionaryMeasurement.objects.create(borehole = borehole, geophysical_depth = geodepth, depth_from = drilldepth,
                                                         depth_to = depth_to, meaning = meaning,
                                                         dictionary = MeaningDictValue.objects.get(id = params['dictionary'],
                                                                                            dict_id = meaning))
                    logger.info("User %s added new dictionary measurement" % request.user.username)
                        
                    return getMeasurements(**dict(params['query'], **{'borehole_id' : id}))

                else:
                    raise MeasurementsDuplicated
                
    elif request.method == 'DELETE':
        with transaction.atomic():
            params = json.loads(request.read().decode('utf-8'))
            if params['query']['type'] == 'NDICT':
                RealMeasurement.objects.get(id = id).delete()
            elif params['query']['type'] == 'DICT':
                DictionaryMeasurement.objects.get(id = id).delete()
            elif params['query']['type'] == 'MEANING':
                chosenMeanings = params['meanings']
                borehole = Borehole.objects.get(id=id)
                RealMeasurement.objects.filter(borehole = borehole, meaning__in = MeaningValue.objects.filter(id__in = chosenMeanings)).delete()
                DictionaryMeasurement.objects.filter(borehole = borehole, meaning__in = MeaningDict.objects.filter(id__in = chosenMeanings)).delete()
                Img.objects.filter(borehole = borehole, meaning__in = chosenMeanings).delete()
                return HttpResponse()

            elif params['query']['type'] == 'PICT':
                Img.objects.get(id = id).delete()
            logger.info("User %s deleted measurement" % request.user.username)
            
            return getMeasurements(**dict(params['query'], **{'borehole_id' : params['borehole_id']}))
    
def archive(request, borehole_id, data_col, meaning_id, lang):
    if not os.path.isfile('values/dicts/%s_reverse.json' % lang):
        raise NoDictionaryFile
    
    data_col = int(data_col) - 1 # Users don't count from zero
    geodepth_col = 2
    depth_from_col = 1
    rows_added = 0
    jsonfile = open('values/dicts/%s_reverse.json' % lang)
    dicts = json.load(jsonfile)
    csvfile = request.FILES['archive']

    if sys.version_info[:1][0] >= 3:
        csvfile = io.StringIO(csvfile.read().decode(), newline='\n')
    reader = csv.reader(csvfile, delimiter = ';')
    dict_measurement = True
    counter = 0

    with transaction.atomic():
        try:
            meaning = MeaningDict.objects.get(id=meaning_id)
        except MeaningDict.DoesNotExist:
            meaning = MeaningValue.objects.get(id=meaning_id)
            dict_measurement = False

        borehole = Borehole.objects.get(id = borehole_id)
        for row in reader:
            # ignore rows with blank data field
            counter += 1
            if(counter <= 2 or len(row[data_col]) == 0):
                continue

            depth_from = None
            try:
                depth_from =  float(row[depth_from_col].replace(',', '.'))
            except ValueError:
                depth_from = float(row[geodepth_col].replace(',', '.'))    
            depth_from = int(depth_from * 100)
            depth_to = depth_from + 1
            
            geodepth = None
            try:
                geodepth = int(float((row[geodepth_col]).replace(',', '.')) * 100)
            except ValueError:
                geodepth = depth_from
                
            value = row[data_col]

            if not dict_measurement:
                if not RealMeasurement.objects.filter(borehole = borehole, depth_from = depth_from, 
                                                      meaning = meaning).exists():
                    RealMeasurement.objects.create(borehole = borehole,
                                                   geophysical_depth = geodepth, depth_from = depth_from,
                                                   depth_to = depth_to, value = float(value.replace(',', '.')), 
                                                   meaning = meaning)
                else:
                    raise MeasurementsDuplicated
            else:
                if not DictionaryMeasurement.objects.filter(borehole = borehole, depth_from = depth_from, 
                                                      meaning = meaning).exists():
                    if sys.version_info[:1][0] < 3:
                        value = value.decode('utf-8')
                    DictionaryMeasurement.objects.create(borehole = borehole,
                                                   geophysical_depth = geodepth, depth_from = depth_from,
                                                   depth_to = depth_to, 
                                                   dictionary = MeaningDictValue.objects.get(value=dicts.get(value, value), dict_id=meaning), 
                                                   meaning = meaning)
                else:
                    raise MeasurementsDuplicated
            rows_added += 1
        jsonfile.close()

        logger.info('User %s added %d rows from csv file: ' % (request.user.username, rows_added))
    return _JsonResponse({'rows' : rows_added})

def export(request, borehole_id, depth_from, depth_to, lang):
    return doExport(request, borehole_id, depth_from, depth_to, lang)

def download(request, filename, ext):
    return doDownload(request, filename, ext)

def intervals(request, borehole_id, start_depth, stop_depth, outimg_width, outimg_height):
    '''
    The service returns intervals for given borehole
    '''
    start_depth = int(start_depth) * 100
    stop_depth = int(stop_depth) * 100
    outimg_width = int(outimg_width)
    outimg_height = int(outimg_height)
         
    borehole = Borehole.objects.get(id = int(borehole_id))
    paramsvals = {'depth_from__lte' : stop_depth, 'depth_to__gte' : start_depth, 'borehole' : borehole}
    paramsdicts = {'depth_from__lte' : stop_depth, 'depth_to__gte' : start_depth, 'borehole' : borehole}
    paramspicts = {'depth_from__lte' : stop_depth, 'depth_to__gte' : start_depth, 'borehole' : borehole}
        
    if 'filter' in request.GET:
        filters = request.GET.getlist('filter')
        paramsvals['meaning__in'] = MeaningValue.objects.filter(id__in = filters)
        paramsdicts['meaning__in'] = MeaningDict.objects.filter(id__in = filters)
        paramspicts['meaning__in'] = MeaningImage.objects.filter(id__in = filters)
    else:
        paramsdicts['meaning__in'] = MeaningDict.objects.all()
        
    paramsdicts['meaning__in'] = paramsdicts['meaning__in'].exclude(section = 'Stratygrafia')
            
    valssects = [(m.depth_from, m.depth_to) for m in RealMeasurement.objects.filter(**paramsvals)]
    dictsects = [(m.depth_from, m.depth_to) for m in DictionaryMeasurement.objects.filter(**paramsdicts)]
    pictsects = [(m.depth_from, m.depth_to) for m in Img.objects.filter(**paramspicts).exclude(meaning__isnull = True)]
    sections = intervals_calculator(sorted(valssects + dictsects + pictsects, key = lambda s : s[0]))

    response = HttpResponse()
    response['content-type'] = 'image/jpeg'
        
    img = Image.new("RGBA", (outimg_width, outimg_height))
    draw = ImageDraw.Draw(img)
    width = float(outimg_height) / (stop_depth - start_depth)

    for s in sections:
        height = int((width * (s[0] - start_depth) + (width * (s[1] - start_depth))) / 2)
        draw.line([(0, height), (outimg_width, height)], fill='#ff0000', width = int(width * (s[1] - start_depth) - height) * 2)
    img.save(response, format="JPEG")

    return response