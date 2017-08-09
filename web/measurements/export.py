##
# @file web/measurements/export.py
# @brief Services for exporting measurements as CSV file

'''
File contains functions managing data export in csv format.
First export() creates file on server.
Afterwards, second request downloads it.
'''

from datetime import datetime
from django.core.servers.basehttp import FileWrapper
from django.http import StreamingHttpResponse
import os, json, csv, sys, six

from boreholes.models import Borehole, _JsonResponse
from dictionaries.models import DictionaryMeasurement
from meanings.models import MeaningValue
from values.models import NoDictionaryFile
from values.models import RealMeasurement

tmpDir = 'tmp/'

class ExportRow():
    
    def __init__(self, counter, depth_from, geophysical_depth, meanings_num):
        self.counter = counter
        self.depth_from = depth_from
        self.geophysical_depth = geophysical_depth
        self.meanings = ["" for x in range(meanings_num)]
        
    def insertValue(self, num, value):
        self.meanings[num] = value
    
    def writeRow(self, writer):
        lst = []
        lst.append(self.counter)
        lst.append("{0:.2f}".format(self.depth_from / float(100)))
        lst.append("{0:.2f}".format(self.geophysical_depth / float(100)))
        to_add = [six.text_type(s) for s in self.meanings]
        
        if sys.version_info[:1][0] < 3:
            for i, _ in enumerate(to_add):
                to_add[i] = to_add[i].encode('utf-8')
                
        writer.writerow(lst + to_add)
        
def doExport(request, borehole_id, depth_from, depth_to, lang):
    '''
    Creates csv file and saves it in tmp folder.
    Returns name of generated file.
    '''
    req = request.read()
    chosenMeaningsId = json.loads(req.decode())
    borehole = Borehole.objects.get(id=borehole_id)
    
    filename = generateReportFilename(borehole, depth_from, depth_to)

    if not os.path.exists(tmpDir):
        os.makedirs(tmpDir)
        
    with open(tmpDir + filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter = ';', lineterminator='\n')
        if not os.path.isfile('values/dicts/%s_normal.json' % lang):
            raise NoDictionaryFile
        
        json_file = open('values/dicts/%s_normal.json' % lang)
        dicts = json.load(json_file)
        writeTopHeader(writer, request, borehole)
        writeHeader(writer, chosenMeaningsId, dicts)
                
        meaningColDict = getMeaningDict(chosenMeaningsId)
        rows = getRows(borehole, depth_from, depth_to, chosenMeaningsId, meaningColDict, dicts)
        for r in rows:
            r.writeRow(writer)
        json_file.close()
            
        return _JsonResponse({'filename' : filename})

def writeTopHeader(writer, request, borehole):
    dateFormat = '%d-%m-%Y %H:%M'
    user = ''
    if hasattr(request, 'user') and request.user.is_authenticated():
        user = request.user.username
    
    to_add = [six.text_type(borehole.name), user, six.text_type(datetime.now().strftime(dateFormat))]
    if sys.version_info[:1][0] < 3:
        for i in [0, 2]:
            to_add[i] = to_add[i].encode('utf-8')
            
    writer.writerow(to_add)

def writeHeader(writer, chosenMeaningsId, dicts):
    header = ["L.p.", "%s [m]" % dicts.get('DEPTH_FROM', 'DEPTH_FROM'), "%s [m]" % dicts.get('GEOPHYSICAL_DEPTH', 'GEOPHYSICAL_DEPTH')]
    
    col = 3
    for m in chosenMeaningsId:
        meaning = MeaningValue.objects.get(id=m)
        header.append(dicts.get(meaning.name, meaning.name) + ' [' + meaning.unit + ']')
        col += 1
        
    if sys.version_info[:1][0] < 3:
        for i, _ in enumerate(header):
            header[i] = header[i].encode('utf-8')
        
    writer.writerow(header)

def getMeaningDict(chosenMeaningsId):
    '''
    Meaning dictionary translates meaning id to number of column in csv file
    '''
    ret = {}
    col = 0
    for m in chosenMeaningsId:
        meaning = MeaningValue.objects.get(id=m)
        ret[meaning.id] = col
        col += 1
    
    return ret

def getRows(borehole, depth_from, depth_to, chosenMeaningsId, meaningColDict, dicts):
    '''
    Creates list of ExportRow objects
    '''
    # to cm
    depth_from = int(depth_from) * 100
    depth_to = int(depth_to) * 100
    params = {'meaning_id__in' : chosenMeaningsId, 'depth_from__lte' : depth_to, 'depth_to__gte' : depth_from, 'borehole' : borehole}
    measurements = RealMeasurement.objects.filter(**params).order_by('depth_from')
    dictionaries = DictionaryMeasurement.objects.filter(**params).order_by('depth_from')
    measurements = sorted(list(measurements) + list(dictionaries), key = lambda s : s.depth_from)
    ret = []
    if (len(measurements) > 0):
        row_counter = 1 #counter of rows in csv file
        i = 0 #counter of measurement objects
        while True:
            if (i == len(measurements)):
                break
            row = ExportRow(row_counter, measurements[i].depth_from, measurements[i].geophysical_depth, len(meaningColDict))
            while True:
                if (i == len(measurements) or measurements[i].depth_from != row.depth_from):
                    break
                row.insertValue(meaningColDict[measurements[i].meaning_id], measurements[i].value if hasattr(measurements[i], 'value') 
                                else dicts.get(measurements[i].dictionary.value, measurements[i].dictionary.value))
                i += 1
            
            ret.append(row)
            row_counter += 1
    
    return ret

def doDownload(request, filename, ext):
    '''
    Downloads previously generated file.
    It can be also done directly through application server, but this way we can use django authorization in future.
    '''
    filename = tmpDir + filename + '.' + ext
    wrapper = FileWrapper(open(filename))
    response = StreamingHttpResponse(wrapper, content_type='text/csv')
    response['Content-Length'] = os.path.getsize(filename)
    os.remove(filename)
    return response
                                   
def generateReportFilename(borehole, depth_from, depth_to):
    base = []
    base.append(borehole.name.replace('-', ''))
    base.append(str(depth_from))
    base.append(str(depth_to))
    
    now = datetime.now()
    base.append(str(now.day))
    base.append(str(now.month))
    base.append(str(now.year))
    base.append(str(now.hour))
    base.append(str(now.minute))
    
    return '_'.join(base) + '.csv'