##
# @file web/measurements/tests.py
# @brief Unit tests for measurements.views

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, QueryDict
import django.test
from django.utils.importlib import import_module
from io import BytesIO
import json
import os, six
import shutil

from PIL import Image
from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement, stratigraphy_list
from images.models import Image as ImageMeasurement
from meanings.models import MeaningValue, MeaningSection, MeaningDict, MeaningDictValue, \
    MeaningImage
from measurements.export import getRows
from measurements.models import MeasurementsDuplicated, Measurement
from values.models import RealMeasurement, NoDictionaryFile

from . import views
from .export import tmpDir
from .utils import intervals_calculator
from .models import FilterIntersectionEmpty

class MeasurementsModelTestCase(django.test.TestCase):
    tests_num = 2
    test_value = 0.5
    test_meaning_name = 'meaning_name'
    test_dict_value = 'DICT_VALUE'
    test_section_name = 'section_name'
    test_unit = '%'
    test_borehole_name = 'borehole_name'
    test_lat = 12.34567
    test_lon = 123.45678
    test_depth = 10000
    test_geophysical_depth = 10100
    test_username = 'sweetspot'
    test_password = 'sweetspot'
    csv_sample_path = 'test/sample.csv'
    csv_really_big_column = 100
    csv_correct_column = 7
    
    def createTestDictionaries(self):
        sects = list()
        meanings = list();
        bhs = list()
        dictvals= list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i)))
                
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i), unit = 'DICT', 
                                        section = sects[i % self.tests_num]))
        meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(self.tests_num + 1), unit = 'DICT', 
                                   section = sects[i % self.tests_num]))            
            
        for i in range(1, self.tests_num + 1):
            dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[0], value = self.test_dict_value + str(i))) 
            
        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                DictionaryMeasurement.objects.create(dictionary = dictvals[j], meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j * 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j *100)

        meanings, dictvals = list(), list()
       
    def createTestValues(self):
        sects = list()
        meanings = list();
        bhs = list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i + self.tests_num)))
                
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningValue.objects.create(name = self.test_meaning_name + str(i), unit = self.test_unit + str(i), 
                                        section = sects[i % self.tests_num]))
            
        meanings.append(MeaningValue.objects.create(name = self.test_meaning_name + str(self.tests_num + 1), unit = self.test_unit + str(1), 
                                        section = sects[i % self.tests_num]))

        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i + self.tests_num), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                RealMeasurement.objects.create(value = self.test_value + float(i + j), meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j* 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j * 100)
        RealMeasurement.objects.create(value = self.test_value + float(self.tests_num**2 + 1), meaning = meanings[self.tests_num], 
                                               borehole = bhs[0], depth_from = 0, depth_to = 1, geophysical_depth = 0)
        RealMeasurement.objects.create(value = self.test_value + float(self.tests_num**2 + 1), meaning = meanings[0], 
                                               borehole = bhs[1], depth_from = 0, depth_to = 1, geophysical_depth = 0)
        Borehole.objects.create(name = self.test_borehole_name, latitude = self.test_lat + i,
                                               longitude = self.test_lon + i)

    def createTestImages(self):
        sects = list()
        meanings = list();
        bhs = list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i + self.tests_num)))
                
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningImage.objects.create(name = self.test_meaning_name + str(i), unit = 'PICT', 
                                        section = sects[i % self.tests_num]))
            
        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i + self.tests_num), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                ImageMeasurement.objects.create(meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j* 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j * 100)
                
    def createTestStratigraphy(self):
        sects = list()
        meanings = list()
        meaningsv = list()
        bhs = list()
        dictvals= list()
        
        sects.append(MeaningSection.objects.create(name = self.test_section_name + str(0)))
                
        for i in stratigraphy_list:
            meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i), unit = 'DICT', 
                                        section = sects[0], id = i))
            
        for j in range(len(stratigraphy_list)):
            for i in range(1, self.tests_num + 1):
                dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[j], value = self.test_dict_value + str(i))) 
            
        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(1, self.tests_num + 1):
            meaningsv.append(MeaningValue.objects.create(name = self.test_meaning_name + str(i), unit = self.test_unit + str(i), 
                                        section = sects[0]))
            
        meaningsv.append(MeaningValue.objects.create(name = self.test_meaning_name + str(self.tests_num + 1), unit = self.test_unit + str(1), 
                                        section = sects[0]))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                RealMeasurement.objects.create(value = self.test_value + float(i + j), meaning = meaningsv[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j* 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j * 100)
        RealMeasurement.objects.create(value = self.test_value + float(self.tests_num**2 + 1), meaning = meaningsv[self.tests_num], 
                                               borehole = bhs[0], depth_from = 0, depth_to = 1, geophysical_depth = 0)
        RealMeasurement.objects.create(value = self.test_value + float(self.tests_num**2 + 1), meaning = meaningsv[0], 
                                               borehole = bhs[1], depth_from = 0, depth_to = 1, geophysical_depth = 0)
        Borehole.objects.create(name = self.test_borehole_name, latitude = self.test_lat + i,
                                               longitude = self.test_lon + i)
        
        for k in range(len(stratigraphy_list)):
            for i in range(self.tests_num):
                for j in range(self.tests_num):
                    DictionaryMeasurement.objects.create(dictionary = dictvals[self.tests_num * k + i], meaning = meanings[k], 
                                               borehole = bhs[0], depth_from = j * 1000 + i * 10000 + k * 50000, 
                                               depth_to = j * 1000 + i * 10000 + k * 50000 + 1000, 
                                               geophysical_depth = self.test_geophysical_depth + j *100)
                    
        DictionaryMeasurement.objects.create(dictionary = dictvals[0], meaning = meanings[0], 
                                               borehole = bhs[0], depth_from = 9000, 
                                               depth_to = 9995, 
                                               geophysical_depth = self.test_geophysical_depth + j *100)
        
    @classmethod
    def setUpClass(self):
        if not os.path.exists('values/dicts'):
            os.makedirs('values/dicts')
        with open('values/dicts/pl_reverse.json', 'w+') as out:
            json.dump({k : v for (k, v) in [(self.test_dict_value.lower() + str(i), 
                                             self.test_dict_value + str(i)) for i in range(1, self.tests_num+1)]}, out)
        
        with open('values/dicts/en_normal.json', 'w+') as out:
            json.dump({k : v for (k, v) in [(self.test_dict_value + str(i), self.test_dict_value.lower() + str(i)) 
                                             for i in range(1, self.tests_num + 1)] + 
                                            [('DEPTH_FROM', 'Depth'),
                                             ('GEOPHYSICAL_DEPTH', 'Geophysical depth')] +
                                            [(self.test_meaning_name + str(i), self.test_meaning_name.lower() + str(i)) 
                                             for i in range(1, self.tests_num + 10)]}, out)
        
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('values')
        if os.path.exists(tmpDir):
            shutil.rmtree(tmpDir)
            
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.user = self.request.user = User.objects.create_user(self.test_username, '', self.test_password)
        self.imgw = BytesIO()
        Image.new("RGB", (settings.MEASUREMENT_IMAGE_WIDTH_PX, settings.MEASUREMENT_IMAGE_HEIGHT_PX), "white").save(self.imgw, format="JPEG")

    def test01IntervalsCalculator(self):
        self.assertEqual( len(intervals_calculator([])), 0 )

        #check intervals for single entry
        sections = [ (0,100) ]
        self.assertEqual( len(intervals_calculator(sections)), 1 )
        self.assertEqual( intervals_calculator(sections)[0][0], 0 )
        self.assertEqual( intervals_calculator(sections)[0][1], 100 )

        #check intervals the same sections
        sections = [ (0,100), (0,100), (0,100) ]
        self.assertEqual( len(intervals_calculator(sections)), 1 )
        self.assertEqual( intervals_calculator(sections)[0][0], 0 )
        self.assertEqual( intervals_calculator(sections)[0][1], 100 )

    def test02IntervalsCalculator(self):
        #check intervals for consecutive sections
        sections = [ (0,100), (1, 101) ]
        self.assertEqual( len(intervals_calculator(sections)), 1 )
        self.assertEqual( intervals_calculator(sections)[0][0], 0 )
        self.assertEqual( intervals_calculator(sections)[0][1], 101 )

        sections = [ (0,100), (1, 101), (2, 102), (100, 200), (200, 300) ]
        self.assertEqual( len(intervals_calculator(sections)), 1 )
        self.assertEqual( intervals_calculator(sections)[0][0], 0 )
        self.assertEqual( intervals_calculator(sections)[0][1], 300 )

    def test03IntervalsCalculator(self):
        #check intervals for not overlapping sections
        sections = [ (0,100), (101, 200) ]
        self.assertEqual( len(intervals_calculator(sections)), 2 )
        self.assertEqual( intervals_calculator(sections)[0][0], 0 )
        self.assertEqual( intervals_calculator(sections)[0][1], 100 )
        self.assertEqual( intervals_calculator(sections)[1][0], 101 )
        self.assertEqual( intervals_calculator(sections)[1][1], 200 )
        
    def test04IntervalManager(self):
        sects = list()
        meanings = list();
        meaningsdictvals = list()
        bhs = list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i)))
                
        for i in range(self.tests_num):
            meanings.append(MeaningValue.objects.create(name = self.test_meaning_name + str(i), 
                                                        unit = self.test_unit + str(i), 
                                                        section = sects[i % self.tests_num]))        
        for i in range(self.tests_num):
            meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i + self.tests_num),
                                                   unit = 'DICT', section = sects[i % self.tests_num]))
        for i in range(self.tests_num):
            meaningsdictvals.append(MeaningDictValue.objects.create(dict_id = meanings[-2 + i], 
                                                                   value = self.test_dict_value + str(i))) 

        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                RealMeasurement.objects.create(value = self.test_value + float(i + j), meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j* 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j * 100)
                
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                DictionaryMeasurement.objects.create(dictionary = meaningsdictvals[i], 
                                                     meaning = meanings[self.tests_num + i],
                                                     borehole = bhs[i], depth_from = self.test_depth + j * 100,
                                                     depth_to = self.test_depth + (1 + j) * 100,
                                                     geophysical_depth = self.test_geophysical_depth + j * 100)

        req = HttpRequest()
        req.user = self.user
        self.assertRaises(Borehole.DoesNotExist, views.intervals, req, 9999, 0, 500000, 200, 600)
        
        res = views.intervals(req, bhs[0].id, 0, 500000, 200, 600)
        self.assertEqual(Image.open(BytesIO(res.content)).size, (200, 600))
        
        req.GET = QueryDict('filter=%d' % meanings[0].id)
        res = views.intervals(req, bhs[0].id, 0, 500000, 200, 600)
        self.assertEqual(Image.open(BytesIO(res.content)).size, (200, 600))

        req.GET = QueryDict('filter=%d&filter=%d' % (meanings[0].id, meanings[1].id))
        res = views.intervals(req, bhs[0].id, 0, 500000, 200, 600)
        self.assertEqual(Image.open(BytesIO(res.content)).size, (200, 600))
        
    def test05getDictionaries(self):
        self.createTestDictionaries()
        self.request.method = 'GET'
       
        self.assertRaises(Borehole.DoesNotExist, views.measurements, self.request, self.tests_num + 1)
        
        self.request.GET = QueryDict('type=DICT').copy()
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_depth+100, self.test_geophysical_depth, 1, self.test_dict_value + '1', self.test_meaning_name+'1'],
                              [self.test_depth + 100, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_dict_value + '2', self.test_meaning_name+'2']])

        self.request.GET['start_depth'] = self.test_depth / 100 + 2
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth + 100, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_dict_value + '2', self.test_meaning_name+'2']])
        
        del self.request.GET['start_depth']
        self.request.GET['stop_depth'] = self.test_depth / 100
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_depth+100, self.test_geophysical_depth, 1, self.test_dict_value + '1', self.test_meaning_name+'1']])
                
        self.request.GET['start_depth'] = self.test_depth / 100 - 2
        self.request.GET['stop_depth'] = self.test_depth / 100 - 1 
        self.assertListEqual(json.loads(views.measurements(self.request, 2).content.decode('utf-8')), [])
        
        self.request.GET = QueryDict('filter=1&type=DICT')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_depth+100, self.test_geophysical_depth, 1, self.test_dict_value + '1', self.test_meaning_name+'1']])
        
    def test06addDictionary(self):
        self.createTestDictionaries()
        self.request.method = 'POST'
        
        errortab = [KeyError for i in range(3)] + [MeasurementsDuplicated, MeaningValue.DoesNotExist, MeaningDictValue.DoesNotExist] 
        for j, val in enumerate([{}, {'depth_from' : '%d' % self.test_depth}, 
                    {'meaning' : 1},
                    {'meaning' : 1, 'geophysical_depth' : '%d' % (self.test_depth / 100), 'query' : {'type' : 'DICT'}},
                    {'meaning' : self.tests_num + 2, 'depth_from' : '%d' % (self.test_depth / 100), 'query' : {'type' : 'DICT'}},
                    {'meaning' : self.tests_num + 1, 'geophysical_depth' : '%d' % (self.test_depth / 100), 'dictionary' : 1, 'query' : {'type' : 'DICT'}}]):
            self.request.read = lambda: json.dumps(val).encode()
            self.assertRaises(errortab[j], views.measurements, self.request, 1)
        
        self.request.read = lambda: json.dumps({'meaning' : 1, 'query' : {'type' : 'DICT'},
                                                'depth' : '%d' % self.test_depth}).encode()
        self.assertRaises(Borehole.DoesNotExist, views.measurements, self.request, self.tests_num + 1)
        
        self.request.read = lambda: json.dumps({'query' : {'type' : 'DICT'}, u'meaning' : 1, 
                                                'depth_from' : '%d' % (self.test_depth + 1), 
                                                'dictionary' : '1', 'type' : 'DICT'}).encode()
        
        resp = json.loads(views.measurements(self.request, 1).content.decode('utf-8'))
        self.assertEqual(len(resp), self.tests_num + 1)
        
    def test07deleteDictionary(self):
        self.createTestDictionaries()
        self.request.method = 'DELETE'
        self.request.read = lambda: json.dumps({'query' : {'type' : 'DICT'}, 'borehole_id' : 1}).encode()
        self.assertRaises(Measurement.DoesNotExist, views.measurements, self.request, self.tests_num**2 + 2)
                        
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth + 100, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_dict_value + '2', self.test_meaning_name+'2']])
        
        self.assertListEqual(json.loads(views.measurements(self.request, self.tests_num + 1).content.decode('utf-8')), 
                             [[self.test_depth + 100, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_dict_value + '2', self.test_meaning_name+'2']])
        
    def test08getValues(self):
        self.createTestValues()
        self.request.method = 'GET'
        self.request.GET = QueryDict('type=NDICT')

        self.assertRaises(Borehole.DoesNotExist, views.measurements, self.request, self.tests_num + 2)
        
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_value, self.test_depth+100, self.test_geophysical_depth, 1, six.text_type(self.test_meaning_name+'1'), six.text_type(self.test_unit + '1')],
                              [0, self.test_value + float(self.tests_num**2 + 1), 1, 0, 5, six.text_type(self.test_meaning_name + str(self.tests_num + 1)), six.text_type(self.test_unit + '1')],
                              [self.test_depth+100, self.test_value + 1, self.test_depth+200, self.test_geophysical_depth+100, 2, 
                               six.text_type(self.test_meaning_name+'2'), six.text_type(self.test_unit + '2')]])

        self.request.GET = QueryDict('type=NDICT&lang=en&start_depth=%d' % (self.test_depth / 100 + 1))
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_value, self.test_depth + 100, self.test_geophysical_depth, 1, self.test_meaning_name + '1', self.test_unit + '1'],
                              [self.test_depth + 100, self.test_value + 1, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_meaning_name+'2', self.test_unit + '2']])
                        
        self.request.GET = QueryDict('type=NDICT&lang=en&stop_depth=%d' % (self.test_depth / 100 + 1))
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_value, self.test_depth+100, self.test_geophysical_depth, 1, self.test_meaning_name+'1', self.test_unit + '1'],
                              [0, self.test_value + float(self.tests_num**2 + 1), 1, 0, 5, self.test_meaning_name + str(self.tests_num + 1), self.test_unit + '1'],
                              [self.test_depth+100, self.test_value+1, self.test_depth+200, self.test_geophysical_depth + 100, 2, self.test_meaning_name+'2', self.test_unit+'2']])

        self.request.GET = QueryDict('start_depth={}&stop_depth={}&type=NDICT'.format(self.test_depth / 100 - 2, self.test_depth / 100 - 1)) 
        self.assertListEqual(json.loads(views.measurements(self.request, 2).content.decode('utf-8')), [])
        
        self.request.GET = QueryDict('filter=1&type=NDICT')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_value, self.test_depth+100, self.test_geophysical_depth, 1, self.test_meaning_name+'1', self.test_unit + '1']])
                
    def test09addValue(self):
        self.createTestValues()
        self.request.method = 'POST'
        
        errortab = [KeyError for i in range(3)] + [MeasurementsDuplicated, MeaningValue.DoesNotExist] 
        for j, val in enumerate([{}, {'depth_from' : '%d' % (self.test_depth)}, 
                    {'meaning' : 1},
                    {'meaning' : 1, 'geophysical_depth' : '%d' % (self.test_depth / 100), 'query' : {'type' : 'NDICT'}},
                    {'meaning' : self.tests_num + 4, 'depth_from' : '%d' % (self.test_depth / 100), 'query' : {'type' : 'NDICT'}}]):
            self.request.read = lambda: json.dumps(val).encode()
#            self.assertEqual(views.measurements(self.request, 1).content, errortab[j])
            self.assertRaises(errortab[j], views.measurements, self.request, 1)
            
        self.request.read = lambda: json.dumps({'meaning' : 1, 
                                                'depth' : '%d' % self.test_depth, 'query' : {'type' : 'NDICT'}}).encode()
        self.assertRaises(Borehole.DoesNotExist, views.measurements, self.request, self.tests_num + 2)
        
        self.request.read = lambda: json.dumps({u'query' : {'type' : 'NDICT'}, u'meaning' : 1, u'value' : '%d' % self.test_value, 'depth_from' : '%d' % (self.test_depth + 1)}).encode()
        resp = json.loads(views.measurements(self.request, 1).content.decode('utf-8'))
        self.assertEqual(len(resp), self.tests_num + 2)
        
    def test10deleteValue(self):
        self.createTestValues()
        self.request.method = 'DELETE'
        self.request.read = lambda: json.dumps({u'query' : {'type' : 'NDICT'}, 'borehole_id' : 1}).encode()
        self.assertRaises(RealMeasurement.DoesNotExist, views.measurements, self.request, self.tests_num**2 + 3)
                        
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')), 
                             [[0, self.test_value + float(self.tests_num**2 + 1), 1, 0, 5, self.test_meaning_name + str(self.tests_num + 1), self.test_unit + '1'],
                              [self.test_depth + 100, self.test_value + 1, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_meaning_name+'2', self.test_unit + '2']])
        
        self.assertListEqual(json.loads(views.measurements(self.request, self.tests_num + 1).content.decode('utf-8')), 
                             [[0, self.test_value + float(self.tests_num**2 + 1), 1, 0, 5, self.test_meaning_name + str(self.tests_num + 1), self.test_unit + '1'],
                              [self.test_depth + 100, self.test_value + 1, self.test_depth+200, self.test_geophysical_depth+100, 2, self.test_meaning_name+'2', self.test_unit + '2']])
        
    def test11csvArchive(self):
        self.createTestValues()
        self.createTestDictionaries()
        
        path = os.path.join(os.path.dirname(__file__), self.csv_sample_path)
        f = open(path, 'rb')
        request = HttpRequest()
        request.FILES = dict(archive=f)
        
        bhs_id = 1
        meaning_id = 1

        'No dict file'
        request.user = self.user
        self.assertRaises(NoDictionaryFile, views.archive, request, bhs_id, self.csv_really_big_column, meaning_id, 'be')
        f.seek(0)
        
        'Wrong column number'
        self.assertRaises(IndexError, views.archive, request, bhs_id, self.csv_really_big_column, meaning_id, 'pl')
        f.seek(0)
        'Everything ok'
        res = views.archive(request, self.tests_num + 1, self.csv_correct_column, meaning_id, 'pl')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content.decode('utf-8'))['rows'], 5)
        
        self.assertEqual(len(RealMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 362900,
                                                          depth_to = 362901, geophysical_depth = 362890, 
                                                          meaning_id = 1, value = 2.83)), 1)
        self.assertEqual(len(RealMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 364891,
                                                          depth_to = 364892, geophysical_depth = 364891, 
                                                          meaning_id = 1, value=2.82)), 1)
        self.assertEqual(len(RealMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 365734,
                                                          depth_to = 365735, geophysical_depth = 365734, 
                                                          meaning_id = 1, value = 2.84)), 1)
        self.assertEqual(len(RealMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 366828,
                                                          depth_to = 366829, geophysical_depth = 366815, 
                                                          meaning_id = 1, value = 2.84)), 1)
        self.assertEqual(len(RealMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 369191,
                                                          depth_to = 369192, geophysical_depth = 369223, 
                                                          meaning_id = 1, value = 2.84)), 1)
        
        f.seek(0)
        'Duplicated entries'
        self.assertRaises(MeasurementsDuplicated, views.archive, request, self.tests_num + 1, self.csv_correct_column, meaning_id, 'pl')
        
        meaning_id = self.tests_num + 3
        f.seek(0)        
        self.assertRaises(MeaningDictValue.DoesNotExist, views.archive, request, self.tests_num + 1, 4, meaning_id, 'pl')

        meaning_id = self.tests_num + 2
        f.seek(0)        
        res = views.archive(request, self.tests_num + 1, 4, meaning_id, 'pl')
        self.assertEqual(json.loads(res.content.decode('utf-8'))['rows'], 2)
        self.assertEqual(len(DictionaryMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 362900,
                                                          depth_to = 362901, geophysical_depth = 362890, 
                                                          meaning_id = meaning_id, dictionary_id = 1)), 1)
        self.assertEqual(len(DictionaryMeasurement.objects.filter(borehole = Borehole.objects.get(id=self.tests_num + 1), depth_from = 365734,
                                                          depth_to = 365735, geophysical_depth = 365734, 
                                                          meaning_id = meaning_id, dictionary_id=2)), 1)
        self.assertEqual(len(Measurement.objects.filter(borehole_id = self.tests_num + 1)), 7)

        f.seek(0)        
        self.assertRaises(MeaningDictValue.DoesNotExist, views.archive, request, bhs_id, 5, meaning_id, 'pl')
        
        f.seek(0)        
        self.assertRaises(MeasurementsDuplicated, views.archive, request, self.tests_num + 1, 8, meaning_id, 'pl')
    
        f.close()

    def test12getRows(self):
        self.createTestValues()
        meaningColDict = {1 : 0}
        rows = getRows(Borehole.objects.get(id=1), self.test_depth / 100, (self.test_depth + 100) / 100, [1], meaningColDict, {})
        self.assertEqual(len(rows), 1)
    
    def test13exportDownload(self):
        self.createTestValues()
        
        if os.path.exists(tmpDir):
            shutil.rmtree(tmpDir)
        
        req = HttpRequest()
        req.method = 'POST'
        req.read = lambda: json.dumps([1]).encode()
        
        req.user = self.user
        self.assertRaises(NoDictionaryFile, views.export, req, 1, self.test_depth / 100, (self.test_depth + 100) / 100, 'aa')
#        self.assertEqual(res.status_code, 500)
#        self.assertEqual(res.content, 'export_error')
        
        res = views.export(req, 1, self.test_depth / 100, (self.test_depth + 100) / 100, 'en')
        self.assertEqual(res.status_code, 200)
        
        self.assertTrue(os.path.exists(tmpDir))
        files = [name for name in os.listdir(tmpDir)]
        self.assertEqual(len(files), 1)
        
        filename = files[0][0:-4]
        ext = files[0][-3:]
        
        req.user = self.user
        res = views.download(req, filename, ext)
        self.assertEqual(res.status_code, 200)       
        self.assertEqual(len([name for name in os.listdir(tmpDir)]), 0)
        
        user = User.objects.create_user('a', '', 'a')
        engine = import_module(settings.SESSION_ENGINE)
        session_key = None
        req.session = engine.SessionStore(session_key)
        req.user = user
        self.assertEqual(views.export(req, 1, self.test_depth / 100, (self.test_depth + 100) / 100, 'en').status_code,
                         200)
        
    def test14getPicts(self):
        self.createTestImages()
        self.request.GET = QueryDict('type=PICT').copy()
        self.request.method = 'GET'
        
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')), 
                             [{'id' : 1, 'depth_from' : self.test_depth, 'depth_to' : self.test_depth + 100,
                               'geophysical_depth' : self.test_geophysical_depth, 
                               'meaning' : self.test_meaning_name + '1'},
                              {'id' : 2, 'depth_from' : self.test_depth + 100, 'depth_to' : self.test_depth + 200,
                               'geophysical_depth' : self.test_geophysical_depth + 100, 
                               'meaning' : self.test_meaning_name + '2'}])
        
    def test15addMeaningImage(self):
        self.createTestImages()
        self.request.method = 'POST'
        self.request.POST  = QueryDict('depth_from=900&geophysical_depth=900&meaning=1&type=PICT')
        self.request.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        
        ImageMeasurement.objects.create(meaning = None, borehole_id = 1, depth_from = 90000, depth_to = 90100,
                                        geophysical_depth = 90000)

        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')), 
                             [{'id' : 1, 'depth_from' : self.test_depth, 'depth_to' : self.test_depth + 100,
                               'geophysical_depth' : self.test_geophysical_depth, 
                               'meaning' : self.test_meaning_name + '1'},
                              {'id' : 2, 'depth_from' : self.test_depth + 100, 'depth_to' : self.test_depth + 200,
                               'geophysical_depth' : self.test_geophysical_depth + 100, 
                               'meaning' : self.test_meaning_name + '2'},
                              {'id' : 6, 'depth_from' : 90000, 'depth_to' : 90100,
                               'geophysical_depth' : 90000, 
                               'meaning' : self.test_meaning_name + '1'}])

        self.request.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        self.assertRaises(MeasurementsDuplicated, views.measurements, self.request, 1)
        
        self.request.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        self.assertEqual(len(json.loads(views.measurements(self.request, 2).content.decode('utf-8'))), 3)
        
    def test16deleteMeaningImage(self):
        self.createTestImages()
        self.request.method = 'DELETE'
        
        self.request.read = lambda: json.dumps({u'query' : {'type' : 'PICT'}, 'borehole_id' : 1}).encode()
        
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')), 
                             [{'id' : 2, 'depth_from' : self.test_depth + 100, 'depth_to' : self.test_depth + 200,
                               'geophysical_depth' : self.test_geophysical_depth + 100, 
                               'meaning' : self.test_meaning_name + '2'}])
        
        self.assertRaises(ImageMeasurement.DoesNotExist, views.measurements, self.request, 1)
        
    def test17getValuesByStratigraphy(self):
        self.createTestStratigraphy()
        self.request.method = 'GET'
        self.request.GET = QueryDict('type=NDICT')
        
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[self.test_depth, self.test_value, self.test_depth+100, self.test_geophysical_depth, 1, six.text_type(self.test_meaning_name+'1'), six.text_type(self.test_unit + '1')],
                              [0, self.test_value + float(self.tests_num**2 + 1), 1, 0, 5, six.text_type(self.test_meaning_name + str(self.tests_num + 1)), six.text_type(self.test_unit + '1')],
                              [self.test_depth+100, self.test_value + 1, self.test_depth+200, self.test_geophysical_depth+100, 2, 
                               six.text_type(self.test_meaning_name+'2'), six.text_type(self.test_unit + '2')]])
        
        self.request.GET = QueryDict('type=NDICT&strat=1&start_depth=101&stop_depth=5000')
        self.assertRaises(FilterIntersectionEmpty, views.measurements, self.request, 1)

        self.request.GET = QueryDict('type=NDICT&strat=1&start_depth=99&stop_depth=200')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [])
        
        self.request.GET = QueryDict('type=NDICT&strat=1&start_depth=0&stop_depth=5000')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[0, self.test_value + float(self.tests_num**2 + 1), 1, 0, 5, six.text_type(self.test_meaning_name + str(self.tests_num + 1)), 
                               six.text_type(self.test_unit + '1')]])

        self.request.GET = QueryDict('type=NDICT&strat=3&start_depth=100&stop_depth=600')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')), [])

        self.request.GET = QueryDict('type=DICT&strat=1&start_depth=0&stop_depth=5000')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')),
                             [[0, 1000, 10100, 7, six.text_type('DICT_VALUE1'), six.text_type('meaning_name12')],
                              [1000, 2000, 10200, 8, six.text_type('DICT_VALUE1'), six.text_type('meaning_name12')],
                              [9000, 9995, 10200, 23, six.text_type('DICT_VALUE1'), six.text_type('meaning_name12')]])

        self.request.GET = QueryDict('type=PICT&strat=1&start_depth=0&stop_depth=5000')
        self.assertListEqual(json.loads(views.measurements(self.request, 1).content.decode('utf-8')), [])
        