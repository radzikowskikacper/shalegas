# -*- coding: utf-8 -*-
##
# @file web/meanings/tests.py
# @brief Unit tests for meanings services

from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement#, stratigraphy_list
from django.contrib.auth.models import User, AnonymousUser
from django.db import DataError
from django.http import HttpRequest, QueryDict
import django.test, json, six
from meanings.models import MeaningsDuplicated, SectionsDuplicated, MeaningImage
from .models import MeaningValue, MeaningSection, MeaningDict, MeaningDictValue
from . import views

import sys

stratigraphy_list = [603, 604, 605, 606]

class MeaningsViewTestCase(django.test.TestCase):
    '''
    Main test case for testing meanings
    '''
    
    tests_num = 2
    test_borehole_name = 'borehole_name'
    test_lat = 12.34567
    test_lon = 123.45678
    test_depth = 10000
    test_geophysical_depth = 10100
    test_dict_value = 'DICT_VALUE'
    test_meaning_name = 'meaning_name'
    test_section_name = 'section_name'
    test_dict_name= "dict_name"
    test_dict_value_name = 'dict_value_name'
    
    test_unit = u'°C'
    test_long_name = 'long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name \
                        long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name \
                        long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name'
    test_username = 'sweetspot'
    test_password = 'sweetspot'

    def createTestMeanings(self):
        sects = list()
        
        for i in range(2):
            s = MeaningSection.objects.create(name = self.test_section_name + str(i))
            sects.append(s)
                
        for i in range(1, 3):
            MeaningValue.objects.create(name = self.test_meaning_name + str(i), unit = self.test_unit + str(i), 
                                        section = sects[i % 2])
            
        for i in range(1, 3):
            temp = MeaningDict.objects.create(name = self.test_dict_name + str(i), section = sects[i % 2], unit='DICT')
            for j in range(2):
                MeaningDictValue.objects.create(value = self.test_dict_value_name + str(j), dict_id = temp)
                
        MeaningImage.objects.create(name = self.test_meaning_name + str(10), unit = 'PICT', section = MeaningSection.objects.create(name = 'test_section'))
                
    def createTestDictionaries(self, stratigraphy = False):
        sects = list()
        meanings = list();
        bhs = list()
        dictvals= list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i)))
        MeaningSection.objects.create(name = 'Stratygrafia')
                
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i), unit = 'DICT', 
                                        section = sects[i % self.tests_num]))
        meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(self.tests_num + 1), unit = 'DICT', 
                                   section = sects[i % self.tests_num]))            
            
        for i in range(1, self.tests_num + 1):
            dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[i - 1], value = self.test_dict_value + str(i))) 
            
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
        if stratigraphy:
            for index, i in enumerate(stratigraphy_list):
                meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i), section = MeaningSection.objects.get(name='Stratygrafia'), unit = 'DICT', id = i))
                for i in range(20 + index * 2, 20 + self.tests_num + index * 2):
                    dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[-1], value = self.test_dict_value + str(i), id = i))
                    for j in range(2):
                        DictionaryMeasurement.objects.create(dictionary = dictvals[-1], meaning = meanings[-1], borehole = bhs[0],
                                                         depth_from = self.test_depth + j * 100, depth_to = self.test_depth + (j + i) * 100,
                                                         geophysical_depth = self.test_geophysical_depth + j * 100)
            
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.req = HttpRequest()
        self.user = self.req.user = User.objects.create_user(self.test_username, '', self.test_password)

    def test01getMeanings(self):
        self.createTestMeanings()
        self.req.method = 'GET'
                             
        resp = json.loads(views.meanings(self.req).content.decode('utf-8'))
        
        self.assertDictEqual(resp[0], {u'name' : six.text_type(self.test_section_name + str(0)), u'meanings' : 
                                        sorted([{u'name' : six.text_type(self.test_dict_name + str(2)), u'id' : six.text_type(4), 
                                                 u'unit' : u'DICT', u'section' : six.text_type(self.test_section_name + str(0))},
                                                {u'name' : six.text_type(self.test_meaning_name + str(2)), u'id' : six.text_type(2), 
                                                 u'unit' : six.text_type(self.test_unit + str(2)), u'section' : six.text_type(self.test_section_name + str(0))}], 
                                                                                                                  key=lambda k: k['name'])})

        self.assertDictEqual(resp[1], {u'name' : six.text_type(self.test_section_name + str(1)), u'meanings' : 
                                        sorted([{u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(3), 
                                                 u'unit' : u'DICT', u'section' : six.text_type(self.test_section_name + str(1))},
                                                {u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1), 
                                                 u'unit' : six.text_type(self.test_unit + str(1)), u'section' : six.text_type(self.test_section_name + str(1))}],
                                               key=lambda k: k['name'])})
        
        self.req.GET = {'filter' : ['DICT']}
        self.assertListEqual(json.loads(views.meanings(self.req).content.decode('utf-8')),
                             [{u'name' : six.text_type(self.test_section_name + str(0)), u'meanings' :
                               [{u'name' : six.text_type(self.test_dict_name + str(2)), u'id' : six.text_type(4), 
                                 u'unit' : u'DICT', u'section' : six.text_type(self.test_section_name + str(0))}]},
                              {u'name' : six.text_type(self.test_section_name + str(1)), u'meanings' :
                               [{u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(3), 
                                 u'unit' : u'DICT', u'section' : six.text_type(self.test_section_name + str(1))}]},
                              {u'name' : 'test_section', u'meanings' : []}])
        
        self.req.GET = {'filter' : ['NDICT']}
        self.assertListEqual(json.loads(views.meanings(self.req).content.decode('utf-8')),
                             [{u'name' : six.text_type(self.test_section_name + str(0)), u'meanings' : 
                               [{u'name' : six.text_type(self.test_meaning_name + str(2)), u'id' : six.text_type(2), 
                                 u'unit' : six.text_type(self.test_unit + str(2)), u'section' : six.text_type(self.test_section_name + str(0))}]},
                              {u'name' : six.text_type(self.test_section_name + str(1)), u'meanings' : 
                               [{u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1), 
                                 u'unit' : six.text_type(self.test_unit + str(1)), u'section' : six.text_type(self.test_section_name + str(1))}]},
                              {u'name' : 'test_section', u'meanings' : []}])
        
        self.req.GET = {'filter' : ['PICT']}
        self.assertListEqual(json.loads(views.meanings(self.req).content.decode('utf-8')),
                             [{u'name' : self.test_section_name + str(0), u'meanings' : []},
                              {u'name' : self.test_section_name + str(1), u'meanings' : []},                              
                              {u'name' : 'test_section', u'meanings' : [{u'name' : self.test_meaning_name + str(10), u'id' : str(5),
                                                                         u'unit' : 'PICT', u'section' : u'test_section'}]}])
                                         
    def test02getMeaning(self):
        self.createTestMeanings()
        self.req.method = 'GET'
        
        resp = json.loads(views.meanings(self.req, 1).content.decode('utf-8'))
        self.assertDictEqual(resp, 
                             {u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1),
                              u'unit' : six.text_type(self.test_unit + str(1)), 'type' : 'normal',
                              u'section' : self.test_section_name + str(1)})
                      
        resp = json.loads(views.meanings(self.req, 3).content.decode('utf-8'))   
        self.assertDictEqual(resp,
                             {u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(3),
                              u'dictvals' : [{'value' : self.test_dict_value_name + str(0), 'id' : 1, 
                                              u'dict_id' : 3},
                                             {'value' : self.test_dict_value_name + str(1), 'id' : 2,
                                              u'dict_id' : 3}], 
                              u'section' : self.test_section_name + str(1), 'type' : 'dict'})
        
        self.assertRaises(MeaningValue.DoesNotExist, views.meanings, self.req, 50)

        self.assertDictEqual(json.loads(views.meanings(self.req, 5).content.decode('utf-8')),
                             {u'name' : six.text_type(self.test_meaning_name + str(10)), u'id' : six.text_type(5),
                              u'section' : 'test_section', 'type' : 'pict'})
                
    def test02addMeaning(self):
        self.req.method = 'POST'
        
        for test_content in ['', '5', json.dumps({'name' : self.test_meaning_name}), 
                             json.dumps({'unit' : self.test_unit}), 
                             json.dumps({'name' : self.test_meaning_name, u'section' : self.test_section_name})]:
            self.req.read = lambda: test_content.encode('utf-8')
            temp = 0
            try:
                views.meanings(self.req)
            except (ValueError, TypeError, KeyError):
                temp = 1
            self.assertEqual(temp, 1)
            
        MeaningSection.objects.create(name = self.test_section_name + str(0))
        
        temp_query = {'name' : self.test_long_name, 'type' : 'normal', 'unit' : self.test_unit, 'section' : self.test_section_name + str(1)}
        
        self.req.read = lambda: json.dumps(temp_query).encode()
        self.assertRaises(MeaningSection.DoesNotExist, views.meanings, self.req)
        
        temp_query['section'] = self.test_section_name + str(0)
        self.req.read = lambda: json.dumps(temp_query).encode()
        self.assertRaises(DataError, views.meanings, self.req)
        
        temp_query['name'] = self.test_meaning_name + str(0)
        self.req.read = lambda: json.dumps(temp_query).encode()
        self.assertListEqual(json.loads(views.meanings(self.req).content.decode('utf-8')), 
                             [{u'name' : self.test_section_name + str(0), u'meanings' : 
                              [{u'name' : six.text_type(self.test_meaning_name + str(0)), 
                                u'unit' : six.text_type(self.test_unit), u'id' : six.text_type(1),
                                u'section' : self.test_section_name + str(0)}]}])
    
        temp_query['unit'] += '_modified'
        self.req.read = lambda: json.dumps(temp_query).encode()
        self.assertRaises(MeaningsDuplicated, views.meanings, self.req)
        
        temp_query['name'] = self.test_meaning_name + str(1)
        
        self.req.read = lambda: json.dumps(temp_query).encode()
        self.assertEqual(len(json.loads(views.meanings(self.req).content.decode('utf-8'))[0]['meanings']), 2)
        
        MeaningSection.objects.create(name = self.test_section_name + str(1))
        self.req.read = lambda: json.dumps({'type' : 'dict', 'name' : self.test_dict_name + str(0), 'section' : self.test_section_name + str(1),
                    'dictvals' : [self.test_dict_value_name + str(i) for i in range(2)]}).encode()
        
        self.assertDictEqual(json.loads(views.meanings(self.req).content.decode('utf-8'))[1], 
                             {u'name' : six.text_type(self.test_section_name + str(1)), 
                               u'meanings' : [{u'name' : six.text_type(self.test_dict_name + str(0)), u'id' : six.text_type(3),
                                               u'unit' : u'DICT', u'section' : six.text_type(self.test_section_name + str(1))}]})
                
        vals = MeaningDictValue.objects.filter(dict_id = MeaningDict.objects.get(name = self.test_dict_name + str(0))).order_by('value')
        for i in range(2):
            self.assertEqual(vals[i].value, self.test_dict_value_name + str(i))

        MeaningSection.objects.create(name = self.test_section_name + str(2))
        self.req.read = lambda: json.dumps({'type' : 'pict', 'name' : self.test_dict_name + str(0), 'section' : self.test_section_name + str(2),
                    'dictvals' : [self.test_dict_value_name + str(i) for i in range(2)]}).encode()
        
        self.assertDictEqual(json.loads(views.meanings(self.req).content.decode('utf-8'))[2], 
                             {u'name' : six.text_type(self.test_section_name + str(2)), 
                               u'meanings' : [{u'name' : six.text_type(self.test_dict_name + str(0)), u'id' : str(4),
                                               u'unit' : u'PICT', u'section' : six.text_type(self.test_section_name + str(2))}]})

        self.req.read = lambda: json.dumps({'type' : 'p', 'name' : self.test_dict_name + str(20), 
                                            'section' : self.test_section_name + str(2),
                    'dictvals' : [self.test_dict_value_name + str(i) for i in range(2)]}).encode()
        self.assertRaises(KeyError, views.meanings, self.req)
        
    def test03modifyMeaning(self):
        self.req.method = 'PUT'
        
        self.createTestMeanings()
        
        self.req.read = lambda: ''.encode()
        self.assertRaises(ValueError, views.meanings, self.req, 1)
            
        self.req.read = lambda: '5'.encode()
        self.assertRaises(TypeError, views.meanings, self.req, 1)

        self.req.read = lambda: json.dumps({'name' : self.test_meaning_name + '_modified', 'type' : 'normal'}).encode()
        self.assertRaises(MeaningValue.DoesNotExist, views.meanings, self.req, 50)

        self.req.read = lambda: json.dumps({'name' : self.test_meaning_name + '_modified', 'type' : 'normal',
                                            u'unit' : six.text_type(self.test_unit + str(1))}).encode()
              
        resp = json.loads(views.meanings(self.req, 1).content.decode('utf-8'))
        self.assertDictEqual(resp[1]['meanings'][1], 
                             {u'name' : six.text_type(self.test_meaning_name + '_modified'), u'unit' : six.text_type(self.test_unit + str(1)), 
                               u'id' : six.text_type(1), u'section' : resp[1]['name']})
        
        self.req.read = lambda: json.dumps({'type' : 'normal', 'unit' : self.test_unit + '_modified'}).encode()
        resp = json.loads(views.meanings(self.req, 1).content.decode('utf-8'))
        
        self.assertDictEqual(resp[1]['meanings'][1],
                              {u'name' : six.text_type(self.test_meaning_name + '_modified'), u'id' : six.text_type(1), 
                               u'unit' : six.text_type(self.test_unit + '_modified'),
                               u'section' : resp[1]['name']})
        
        self.req.read = lambda: json.dumps({'section' : self.test_section_name + '_modified', 'type' : 'normal',
                                            u'unit' : six.text_type(self.test_unit + '_modified')}).encode()
        self.assertRaises(MeaningSection.DoesNotExist, views.meanings, self.req, 1)
        
        self.req.read = lambda: json.dumps({'section' : self.test_section_name + str(0), 'type' : 'normal', 
                                            u'unit' : six.text_type(self.test_unit + '_modified')}).encode()
        resp = json.loads(views.meanings(self.req, 1).content.decode('utf-8'))
        self.assertDictEqual(resp[0]['meanings'][2],
                              {u'name' : six.text_type(self.test_meaning_name + '_modified'), u'id' : six.text_type(1), 
                               u'unit' : six.text_type(self.test_unit + '_modified'),
                               u'section' : resp[0]['name']})

        self.req.read = lambda: json.dumps({'section' : self.test_section_name + str(0), 'type' : 'pict',
                                            u'name' : 'a'}).encode()
        resp = json.loads(views.meanings(self.req, 1).content.decode('utf-8'))
        self.assertDictEqual(resp[0]['meanings'][0],
                              {u'name' : 'a', u'id' : six.text_type(6), 
                               u'unit' : 'PICT',
                               u'section' : resp[0]['name']})
        
        self.req.read = lambda: json.dumps({u'name' : 'a', 'type' : 'normal',
                                            u'unit' : six.text_type(self.test_unit + '_modified')}).encode()
        self.assertRaises(MeaningsDuplicated, views.meanings, self.req, 2)
        
        self.req.read = lambda: json.dumps({'name' : self.test_long_name, 'type' : 'normal',
                                            u'unit' : six.text_type(self.test_unit + '_modified')}).encode()
        self.assertRaises(DataError, views.meanings, self.req, 2)
        
        

    def test04modifyDictMeaning(self):
        self.createTestMeanings()
        self.req.method = 'PUT'
        
        self.req.read = lambda: json.dumps({'name' : self.test_dict_name + '_modified', 'type' : 'dict',
                                            'dictvals' : [self.test_dict_value_name + str(0) + '_modified']}).encode()
        
        resp = json.loads(views.meanings(self.req, 4).content.decode('utf-8'))
        self.assertDictEqual(resp[0], {u'name' : six.text_type(self.test_section_name + str(0)), u'meanings' : 
                                      sorted([{u'name' : six.text_type(self.test_meaning_name + str(2)), u'id' : six.text_type(2), 
                                               u'unit' : six.text_type(self.test_unit + str(2)),
                                               u'section' : six.text_type(self.test_section_name + str(0))},
                                              {u'name' : six.text_type(self.test_dict_name + '_modified'), u'id' : six.text_type(4), 
                                               u'unit' : u'DICT',
                                               u'section' : six.text_type(self.test_section_name + str(0))}],
                                             key = lambda k: k['name'])})
        
        self.assertDictEqual(resp[1], {u'name' : six.text_type(self.test_section_name + str(1)), u'meanings' : 
                                       sorted([{u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1),
                                                u'unit' : six.text_type(self.test_unit + str(1)),
                                                u'section' : six.text_type(self.test_section_name + str(1))},
                                               {u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(3),
                                                u'unit' : u'DICT',
                                                u'section' : six.text_type(self.test_section_name + str(1))}], 
                                              key = lambda k: k['name'])})

        self.assertDictEqual(resp[2], {u'name' : 'test_section', u'meanings' : [{u'section' : 'test_section', u'id' : six.text_type(5),
                                                      u'unit' : 'PICT', u'name' : six.text_type(self.test_meaning_name + str(10))}]})
                                            
        vals = MeaningDictValue.objects.filter(dict_id = MeaningDict.objects.get(name = self.test_dict_name + '_modified')).order_by('value')
        self.assertEqual(len(vals), 1)
        self.assertEqual(vals[0].value, self.test_dict_value_name + str(0) + '_modified')
        
        self.req.read = lambda: json.dumps({'dictvals' : [self.test_dict_value_name + '_modified'], u'section' : self.test_section_name + str(1),
                                            'type' : 'dict'}).encode()
        resp = json.loads(views.meanings(self.req, 2).content.decode('utf-8'))
        self.assertDictEqual(resp[0], {u'name' : six.text_type(self.test_section_name + str(0)), u'meanings' : 
                                      [{u'name' : six.text_type(self.test_dict_name + '_modified'), u'id' : six.text_type(4), 
                                        u'unit' : u'DICT', u'section' : six.text_type(self.test_section_name + str(0))}]})
        self.assertDictEqual(resp[1], {u'name' : self.test_section_name + str(1), u'meanings' : 
                                       sorted([{u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1),
                                                u'unit' : six.text_type(self.test_unit + str(1)),
                                                u'section' : six.text_type(self.test_section_name + str(1))},
                                               {u'name' : six.text_type(self.test_meaning_name + str(2)), u'id' : six.text_type(6),
                                                u'unit' : 'DICT', u'section' : six.text_type(self.test_section_name + str(1))},
                                               {u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(3),
                                                u'unit' : 'DICT',
                                                u'section' : six.text_type(self.test_section_name + str(1))}], 
                                              key = lambda k : k['name'])})
        self.assertDictEqual(resp[2], {u'name' : 'test_section', u'meanings' : [{u'section' : 'test_section', u'id' : six.text_type(5),
                                                      u'unit' : 'PICT', u'name' : six.text_type(self.test_meaning_name + str(10))}]})
                                       
        
        vals = MeaningDictValue.objects.filter(dict_id = MeaningDict.objects.get(name = self.test_meaning_name + str(2))).order_by('value')
        self.assertEqual(len(vals), 1)
        self.assertEqual(vals[0].value, self.test_dict_value_name + '_modified')
        self.assertEqual(len(MeaningValue.objects.filter(id=2)), 0)
        
        self.req.read = lambda: json.dumps({'unit' : self.test_unit + '_modified', 'section' : self.test_section_name + str(0), 'type' : 'normal'}).encode()
        resp = json.loads(views.meanings(self.req, 3).content.decode('utf-8'))
        self.assertDictEqual(resp[0], {u'name' : six.text_type(self.test_section_name + str(0)), u'meanings':
                                       sorted([{u'name' : six.text_type(self.test_dict_name + '_modified'), u'id' : six.text_type(4), 
                                               u'unit' : u'DICT', u'section' : resp[0]['name']},
                                               {u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(7),
                                                u'unit' : six.text_type(self.test_unit + '_modified'),
                                                u'section' : resp[0]['name']}], key = lambda k : k['name'])})
        self.assertDictEqual(resp[1], {u'name' : six.text_type(self.test_section_name + str(1)), u'meanings' :
                                       sorted([{u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1),
                                                u'unit' : six.text_type(self.test_unit + str(1)),
                                                u'section' : resp[1]['name']},
                                               {u'name' : six.text_type(self.test_meaning_name + str(2)), u'id' : six.text_type(6),
                                                u'unit' : 'DICT',
                                                u'section' : resp[1]['name']}], key = lambda k: k['name'])})
        self.assertDictEqual(resp[2], {u'name' : 'test_section', u'meanings' : [{u'section' : 'test_section', u'id' : six.text_type(5),
                                                      u'unit' : 'PICT', u'name' : six.text_type(self.test_meaning_name + str(10))}]})
        
        self.assertEqual(len(MeaningValue.objects.filter(id = 3)), 0)
        self.assertEqual(len(MeaningDictValue.objects.all()), 2)

    def test05deleteMeaning(self):
        self.req.method = 'DELETE'
        
        self.createTestMeanings()
        self.assertEqual(len(MeaningValue.objects.all()), 5)
        
        self.assertRaises(MeaningValue.DoesNotExist, views.meanings, self.req, 50)
        
        resp = json.loads(views.meanings(self.req, 4).content.decode('utf-8'))
        self.assertEqual(len(resp[0]['meanings']) + len(resp[1]['meanings']), 3)
        self.assertEqual(len(MeaningDictValue.objects.all()), 2)
        
        
        
    def test06getSections(self):
        self.req.method = 'GET'
        
        self.createTestMeanings()
        self.assertListEqual(json.loads(views.sections(self.req).content.decode('utf-8')), [self.test_section_name + str(i) for i in range(2)] + ['test_section'])

    def test07addSection(self):
        self.req.method = 'POST'
        
        self.assertEqual(len(MeaningSection.objects.all()), 0)
        for cont in ['', '4', {}, []]:
            self.req.read = lambda: json.dumps(cont).encode()
            temp = 0
            try:
                views.sections(self.req)
            except (ValueError, TypeError, KeyError):
                temp = 1
            self.assertEqual(temp, 1)
        self.req.read = lambda: json.dumps({'name' : self.test_long_name}).encode()
        self.assertRaises(DataError, views.sections, self.req)
        
        self.req.read = lambda: json.dumps({'name' : self.test_section_name + str(0)}).encode()
        self.assertListEqual(json.loads(views.sections(self.req).content.decode('utf-8')), [self.test_section_name + str(0)])
        self.assertRaises(SectionsDuplicated, views.sections, self.req)

    def test08ModifySection(self):
        self.req.method = 'PUT'
        
        self.createTestMeanings()

        self.req.read = lambda: json.dumps({'name' : self.test_long_name}).encode()
        self.assertRaises(MeaningSection.DoesNotExist, views.sections, self.req, self.test_section_name + str(2))
        
        self.assertRaises(DataError, views.sections, self.req, self.test_section_name + str(0))
        
        self.req.read = lambda: ''.encode()
        self.assertRaises(ValueError, views.sections, self.req, self.test_section_name + str(0))
            
        self.req.read = lambda: '4'.encode()
        self.assertRaises(TypeError, views.sections, self.req, self.test_section_name + str(0))

        self.req.read = lambda: json.dumps({'name' : self.test_section_name + str(1)}).encode()
        self.assertRaises(SectionsDuplicated, views.sections, self.req, self.test_section_name + str(0))
        
        self.req.read = lambda: json.dumps({'name' : self.test_section_name + '_modified'}).encode()
        self.assertListEqual(json.loads(views.sections(self.req, self.test_section_name + str(0)).content.decode('utf-8')),
                                                [six.text_type(self.test_section_name + str(1)), six.text_type(self.test_section_name + '_modified'), 'test_section'])

        self.assertListEqual(json.loads(views.getMeanings().content.decode('utf-8')), 
                                    [{u'name' : six.text_type(self.test_section_name + str(1)), u'meanings' : 
                                      [{u'name' : six.text_type(self.test_dict_name + str(1)), u'id' : six.text_type(3), u'unit' : u'DICT',
                                        u'section' : six.text_type(self.test_section_name + str(1))},
                                       {u'name' : six.text_type(self.test_meaning_name + str(1)), u'id' : six.text_type(1), 
                                        u'unit' : six.text_type(self.test_unit + str(1)), u'section' : six.text_type(self.test_section_name + str(1))}]},
                                     {u'name' : six.text_type(self.test_section_name + '_modified'), u'meanings' : 
                                      [{u'name' : six.text_type(self.test_dict_name + str(2)), u'id' : six.text_type(4), u'unit' : u'DICT',
                                        u'section' : six.text_type(self.test_section_name + '_modified')},
                                       {u'name' : six.text_type(self.test_meaning_name + str(2)), u'id' : six.text_type(2), u'unit' : six.text_type(self.test_unit + str(2)),
                                        u'section' : six.text_type(self.test_section_name + '_modified')}]},
                                      {u'name' : 'test_section', u'meanings' : [{u'section' : 'test_section', u'id' : six.text_type(5),
                                                      u'unit' : 'PICT', u'name' : six.text_type(self.test_meaning_name + str(10))}]}])

    def test09deleteSection(self):
        self.req.method = 'DELETE'
        
        self.createTestMeanings()
        
        self.assertEqual(len(MeaningSection.objects.all()), 3)
        self.assertEqual(json.loads(views.sections(self.req, self.test_section_name + str(0)).content.decode('utf-8')), [self.test_section_name + str(1), 'test_section']);   
        self.assertRaises(MeaningSection.DoesNotExist, views.sections, self.req, self.test_section_name + str(2))
        
    def test09getStratigraphyMeanings(self):
        self.createTestDictionaries(True)
        
        self.req.method = 'GET'
        self.req.GET = QueryDict('filter=STRAT').copy()
        self.assertListEqual(json.loads(views.meanings(self.req).content.decode('utf-8')), 
                             [{u'id' : str(m.id), u'name' : m.name, u'section' : m.section.name, u'unit' : m.unit} 
                              for m in MeaningDict.objects.filter(section = 'Stratygrafia').order_by('id')])
