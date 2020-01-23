##
# @file web/similarities/tests.py
# @brief Unit tests for similarities.views

from collections import namedtuple, defaultdict
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, QueryDict
import django.test
import json
import math
import random
import settings
import time

from . import views
from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement  # , stratigraphy_list
from meanings.models import MeaningSection, MeaningValue, MeaningDict, \
    MeaningDictValue
from similarities.calculations import calculateAVGs, calculateMetrics, calculateVariances, calculatePeriods
from similarities.views import similarities
from values.models import RealMeasurement

stratigraphy_list = [603, 604, 605, 606]

#import matplotlib.pyplot as plt


class periodtype(
    namedtuple(
        'period', [
            'dictionary_id', 'depth_from', 'depth_to', 'bh', 'borehole_id'])):
    def __new__(
            cls,
            dictionary_id=-1,
            depth_from=-1,
            depth_to=-1,
            bh=None,
            borehole_id=-1):
        return super(
            periodtype,
            cls).__new__(
            cls,
            dictionary_id,
            depth_from,
            depth_to,
            bh,
            borehole_id)


class datatype(
    namedtuple(
        'datatype', [
            'value', 'depth_from', 'depth_to', 'meaning_id', 'bh', 'borehole_id'])):
    def __new__(
            cls,
            value=-1,
            depth_from=-1,
            meaning_id=-1,
            depth_to=-1,
            borehole_id=-1,
            bh=None):
        return super(
            datatype,
            cls).__new__(
            cls,
            value,
            depth_from,
            meaning_id,
            depth_to,
            borehole_id,
            bh)


class SimilaritiesViewsTestCase(django.test.TestCase):
    tests_num = 2
    tests_large_num = 5000
    test_value = 0.5
    test_meaning_name = 'meaning_name'
    test_dict_value = 'dict_value'
    test_section_name = 'section_name'
    test_unit = '%'
    test_borehole_name = 'borehole_name'
    test_lat = 12.34567
    test_lon = 123.45678
    test_depth = 10000
    test_geophysical_depth = 10100
    test_username = 'sweetspot'
    test_password = 'sweetspot'

    test_average = [100, 80, 0]
    a = 200
    step_chart_value = 50

    experiment_num = 1

    borehole_depth = settings.MAX_BOREHOLE_HEIGHT * 100  # in cm
    data_step = 100
    meanings_step = 5
    boreholes_step = 5

    sigma_range = [50 + 0.1 * math.pow(2, p) for p in range(15)]

    def createTestData(self):
        sects = list()
        meanings = list()
        bhs = list()

        for i in range(self.tests_num):
            sects.append(
                MeaningSection.objects.create(
                    name=self.test_section_name +
                    str(i)))

        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningValue.objects.create(name=self.test_meaning_name + str(
                i), unit=self.test_unit + str(i), section=sects[i % self.tests_num]))

        temp = 0
        for i in stratigraphy_list:
            m = MeaningDict.objects.create(id=i,
                                           name=self.test_meaning_name + str(i),
                                           unit='DICT',
                                           section=sects[i % self.tests_num])
            for j in range(1, self.tests_num + 1):
                temp += 1
                MeaningDictValue.objects.create(
                    id=temp,
                    value=self.test_meaning_name +
                    '_value' +
                    str(j) +
                    '_' +
                    str(i),
                    dict_id=m)

        for i in range(self.tests_num):
            bhs.append(
                Borehole.objects.create(
                    name=self.test_borehole_name + str(i),
                    latitude=self.test_lat + i,
                    longitude=self.test_lon + i))

        for i in range(self.tests_num):
            for j in range(self.tests_large_num):
                RealMeasurement.objects.create(value=self.test_value + float(i * j),
                                               meaning=meanings[j % self.tests_num],
                                               borehole=bhs[i],
                                               depth_from=self.test_depth + j * 10 * i,
                                               depth_to=self.test_depth + (i * j) * 10 + 1,
                                               geophysical_depth=self.test_geophysical_depth + j * 100)

    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.request.user = self.user = User.objects.create_user(
            self.test_username, '', self.test_password)

    def test02compareTo(self):
        self.createTestData()
        self.assertDictEqual(views.compareTo(1,
                                             stratigraphy_list[1],
                                             [i for i in range(self.tests_num,
                                                               self.tests_num * 2)]),
                             {self.test_borehole_name + '1': 'NO_COMMON_METRICS'})

        DictionaryMeasurement.objects.create(
            borehole_id=1,
            depth_from=0,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[0], [i for i in range(
            1, self.tests_num + 1)]), {self.test_borehole_name + '1': 'NO_COMMON_METRICS'})

        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=0,
            depth_to=47900,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))
        self.assertDictEqual(views.compareTo(1,
                                             stratigraphy_list[1],
                                             [i for i in range(self.tests_num,
                                                               self.tests_num * 2)]),
                             {self.test_borehole_name + '1': 'NO_COMMON_METRICS'})

        bh = Borehole.objects.create(
            name=self.test_borehole_name + '2',
            latitude=self.test_lat,
            longitude=self.test_lon)
        self.assertDictEqual(views.compareTo(1,
                                             stratigraphy_list[1],
                                             [i for i in range(self.tests_num,
                                                               self.tests_num * 2)]),
                             {self.test_borehole_name + '2': 'NO_MEASUREMENTS',
                              self.test_borehole_name + '1': 'NO_COMMON_METRICS'})
        bh.delete()

        localdata = RealMeasurement.objects.filter(
            borehole_id=1).order_by(
            'meaning', 'depth_from')
        data = RealMeasurement.objects.filter(
            borehole_id=2).order_by(
            'meaning', 'depth_from')
        temp = RealMeasurement.objects.all().order_by('meaning', 'depth_from')
        avgs = calculateAVGs(temp)
        varc = calculateVariances(temp, avgs)
        localperiods = calculatePeriods(
            DictionaryMeasurement.objects.filter(
                borehole_id=1).order_by(
                'dictionary',
                'depth_from'))
        periods = calculatePeriods(
            DictionaryMeasurement.objects.filter(
                borehole_id=2).order_by(
                'dictionary',
                'depth_from'))
        localmetrics = calculateMetrics(localdata, localperiods, varc)
        metrics = calculateMetrics(data, periods, varc)

        dst = 0
        for (m, i) in set(metrics.keys()).intersection(
                set(localmetrics.keys())):
            dst += (metrics[(m, i)] - localmetrics[(m, i)])**2
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[0], [i for i in range(
            1, self.tests_num + 1)]), {self.test_borehole_name + '1': math.sqrt(dst)})
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[0], [i for i in range(
            2, self.tests_num + 1)]), {self.test_borehole_name + '1': 'NO_COMMON_METRICS'})

        dst = 0
        for i in set(periods.keys()).intersection(set(localperiods.keys())):
            if (1, i) in metrics and (1, i) in localmetrics:
                dst += (metrics[(1, i)] - localmetrics[(1, i)])**2
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[0], [i for i in range(
            1, self.tests_num + 1)], [1]), {self.test_borehole_name + '1': math.sqrt(dst)})

    def test021compareTo(self):
        self.createTestData()
        DictionaryMeasurement.objects.create(
            borehole_id=1,
            depth_from=0,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))
        DictionaryMeasurement.objects.create(
            borehole_id=1,
            depth_from=0,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[1]),
            dictionary=MeaningDictValue.objects.get(
                id=3))
        DictionaryMeasurement.objects.create(
            borehole_id=1,
            depth_from=0,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[2]),
            dictionary=MeaningDictValue.objects.get(
                id=5))

        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=0,
            depth_to=250000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))
        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=250000,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))
        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=0,
            depth_to=10000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[1]),
            dictionary=MeaningDictValue.objects.get(
                id=3))
        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=10000,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[1]),
            dictionary=MeaningDictValue.objects.get(
                id=4))
        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=0,
            depth_to=9000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[2]),
            dictionary=MeaningDictValue.objects.get(
                id=5))
        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=9000,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[2]),
            dictionary=MeaningDictValue.objects.get(
                id=6))

        localdata = RealMeasurement.objects.filter(
            borehole_id=1).order_by(
            'meaning', 'depth_from')
        data = RealMeasurement.objects.filter(
            borehole_id=2).order_by(
            'meaning', 'depth_from')
        temp = RealMeasurement.objects.all().order_by('meaning', 'depth_from')
        avgs = calculateAVGs(temp)
        varc = calculateVariances(temp, avgs)
        localperiods = calculatePeriods(
            DictionaryMeasurement.objects.filter(
                borehole_id=1).order_by(
                'dictionary',
                'depth_from'))
        periods = calculatePeriods(
            DictionaryMeasurement.objects.filter(
                borehole_id=2).order_by(
                'dictionary',
                'depth_from'))
        localmetrics = calculateMetrics(localdata, localperiods, varc)
        metrics = calculateMetrics(data, periods, varc)

        dst = 0
        for (m, i) in set(localmetrics.keys()
                          ).intersection(set(metrics.keys())):
            dst += (metrics[(m, i)] - localmetrics[(m, i)])**2

        self.assertDictEqual(views.compareTo(1, stratigraphy_list[0], [i for i in range(
            1, self.tests_num + 1)]), {self.test_borehole_name + '1': math.sqrt(dst)})
        self.assertDictEqual(
            views.compareTo(
                1, stratigraphy_list[1], [3]), {
                self.test_borehole_name + '1': 0})
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[1], [4]), {
                             self.test_borehole_name + '1': 'NO_COMMON_METRICS'})
        self.assertDictEqual(
            views.compareTo(
                1, stratigraphy_list[1], [
                    3, 4]), {
                self.test_borehole_name + '1': 0})
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[2], [5]), {
                             self.test_borehole_name + '1': 'NO_COMMON_METRICS'})
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[2], [5, 6]), {
                             self.test_borehole_name + '1': 'NO_COMMON_METRICS'})
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[2], [6]), {
                             self.test_borehole_name + '1': 'NO_COMMON_METRICS'})

        dst = 0
        for i in set(periods.keys()).intersection(set(localperiods.keys())):
            if (1, i) in metrics and (1, i) in localmetrics:
                dst += (metrics[(1, i)] - localmetrics[(1, i)])**2
        self.assertDictEqual(views.compareTo(1, stratigraphy_list[0], [i for i in range(
            1, self.tests_num + 1)], [1]), {self.test_borehole_name + '1': math.sqrt(dst)})

    def test03calculateAVGs(self):
        data = [
            datatype(
                self.test_value + i,
                i,
                i + 1,
                1) for i in range(
                25000,
                475000)]
        self.assertEqual(calculateAVGs(data),
                         {1: sum(item.value for item in data) / len(data)})

        data = [
            datatype(
                self.test_value *
                i,
                i,
                i +
                1,
                j) for j in range(
                1,
                4) for i in range(
                25000,
                475000)]
        self.assertDictEqual(calculateAVGs(data),
                             {1: sum(item.value for item in data[:450000]) / len(data[:450000]),
                              2: sum(item.value for item in data[450000:900000]) / len(data[450000:900000]),
                              3: sum(item.value for item in data[900000:1350000]) / len(data[900000:1350000])})

    def test05calculateVariances(self):
        data = [
            datatype(
                self.test_value + i,
                i,
                i + 1,
                1) for i in range(
                25000,
                475000)]
        avg = sum(item.value for item in data) / len(data)
        self.assertEqual(calculateVariances(data, {1: avg}), {1: sum(
            [abs(item.value - avg)**2 for item in data]) / (len(data) - 1)})

        data = [
            datatype(
                self.test_value *
                i,
                i,
                i +
                1,
                j) for j in range(
                1,
                4) for i in range(
                25000,
                475000)]
        avgs = {1: sum(item.value for item in data[:450000]) / len(data[:450000]),
                2: sum(item.value for item in data[450000:900000]) / len(data[450000:900000]),
                3: sum(item.value for item in data[900000:1350000]) / len(data[900000:1350000])}
        self.assertDictEqual(calculateVariances(data,
                                                avgs),
                             {1: sum(abs(item.value - avgs[1])**2 for item in data[:450000]) / (len(data[:450000]) - 1),
                              2: sum(abs(item.value - avgs[2])**2 for item in data[450000:900000]) / (len(data[450000:900000]) - 1),
                              3: sum(abs(item.value - avgs[3])**2 for item in data[900000:1350000]) / (len(data[900000:1350000]) - 1)})

    def test06getSimilarities(self):
        self.createTestData()
        self.request.GET = QueryDict(
            'stratigraphy_level=603&epochs=1&epochs=2')
        DictionaryMeasurement.objects.create(
            borehole_id=1,
            depth_from=0,
            depth_to=500000,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))
        DictionaryMeasurement.objects.create(
            borehole_id=2,
            depth_from=0,
            depth_to=47900,
            geophysical_depth=0,
            meaning=MeaningDict.objects.get(
                id=stratigraphy_list[0]),
            dictionary=MeaningDictValue.objects.get(
                id=1))

        self.request.method = 'GET'

        self.assertEqual(len(json.loads(views.similarities(
            self.request, 1).content.decode('utf-8'))), 1)

        self.assertRaises(
            Borehole.DoesNotExist,
            views.similarities,
            self.request,
            3)

    def test07calculatePeriods(self):
        periods = [periodtype(1,
                              self.test_depth + i * 100000,
                              self.test_depth + i * 100000 + 50000) for i in range(self.tests_num)] + [periodtype(2,
                                                                                                                  self.test_depth + i * 100000,
                                                                                                                  self.test_depth + i * 100000 + 50000) for i in range(self.tests_num,
                                                                                                                                                                       self.tests_num * 2)] + [periodtype(3,
                                                                                                                                                                                                          self.test_depth + i * 100000,
                                                                                                                                                                                                          self.test_depth + i * 100000 + 50000) for i in range(self.tests_num * 2,
                                                                                                                                                                                                                                                               self.tests_num * 3)]

        self.assertDictEqual(calculatePeriods(periods),
                             {1: [{'from': self.test_depth,
                                   'to': self.test_depth + 50000},
                                  {'from': self.test_depth + 100000,
                                   'to': self.test_depth + 100000 + 50000}],
                              2: [{'from': self.test_depth + self.tests_num * 100000,
                                   'to': self.test_depth + self.tests_num * 100000 + 50000},
                                  {'from': self.test_depth + (self.tests_num + 1) * 100000,
                                   'to': self.test_depth + (self.tests_num + 1) * 100000 + 50000}],
                              3: [{'from': self.test_depth + 2 * self.tests_num * 100000,
                                   'to': self.test_depth + 2 * self.tests_num * 100000 + 50000},
                                  {'from': self.test_depth + (2 * self.tests_num + 1) * 100000,
                                   'to': self.test_depth + (2 * self.tests_num + 1) * 100000 + 50000}]})

        periods = [periodtype(3,
                              self.test_depth + i * 100000,
                              self.test_depth + i * 100000 + 100000) for i in range(self.tests_num)] + [periodtype(4,
                                                                                                                   self.test_depth + i * 100000,
                                                                                                                   self.test_depth + i * 100000 + 150000) for i in range(self.tests_num,
                                                                                                                                                                         self.tests_num * 2)]

        self.assertDictEqual(calculatePeriods(periods),
                             {3: [{'from': self.test_depth,
                                   'to': self.test_depth + (self.tests_num - 1) * 100000 + 100000}],
                              4: [{'from': self.test_depth + self.tests_num * 100000,
                                   'to': self.test_depth + (2 * self.tests_num - 1) * 100000 + 150000}]})

    def test08calculateMetrics(self):
        periods = {3: [{'from': self.test_depth, 'to': self.test_depth + self.tests_num * 100000}],  # 100m - 2100m
                   4: [{'from': self.test_depth + self.tests_num * 100000, 'to': self.test_depth + (2 * self.tests_num) * 100000 + 50000}]}  # 2100m - 4600m
        variances = {1: 0.5, 2: 0.2, 3: 1}
        avgs = {1: 30, 2: 45, 3: 56}
        vals = [datatype(self.test_value + i,
                         self.test_depth + i * 10000,
                         self.test_depth + i * 10000 + 1,
                         1) for i in range(self.tests_num)] + [datatype(self.test_value + i * 2,
                                                                        self.test_depth + (i + 1) * 100000,
                                                                        self.test_depth + (i + 1) * 100000 + 1,
                                                                        2) for i in range(self.tests_num)] + [datatype(self.test_value + i * 3,
                                                                                                                       self.test_depth + (i + 2) * 10000,
                                                                                                                       self.test_depth + (i + 2) * 10000 + 1,
                                                                                                                       3) for i in range(self.tests_num)]

        self.assertDictEqual(calculateMetrics(vals, periods, variances), {(
            1, 3): 1 / math.sqrt(0.5), (2, 3): 1.5 / math.sqrt(0.2), (3, 3): 2, (2, 4): 2.5 / math.sqrt(0.2)})

        periods = {1: [{'from': self.test_depth, 'to': self.test_depth + 50000},  # 100m - 600m
                       {'from': self.test_depth + 100000, 'to': self.test_depth + 100000 + 50000}],  # 1100m - 1600m
                   2: [{'from': self.test_depth + self.tests_num * 100000, 'to': self.test_depth + self.tests_num * 100000 + 50000},  # 2100m-2600m
                       {'from': self.test_depth + (self.tests_num + 1) * 100000,
                        'to': self.test_depth + (self.tests_num + 1) * 100000 + 50000}],  # 3100m - 3600m
                   3: [{'from': self.test_depth + 2 * self.tests_num * 100000,
                        'to': self.test_depth + 2 * self.tests_num * 100000 + 50000},  # 4100m- 4600m
                       {'from': self.test_depth + (2 * self.tests_num + 1) * 100000,  # 5100m - 5600m
                        'to': self.test_depth + (2 * self.tests_num + 1) * 100000 + 50000}]}
        vals = [datatype(self.test_value + i,
                         self.test_depth + i * 10000,
                         self.test_depth + i * 10000 + 1,
                         1) for i in range(20)] + [datatype(self.test_value + i * 2,
                                                            self.test_depth + (i + 1) * 10000,
                                                            self.test_depth + (i + 1) * 10000 + 1,
                                                            2) for i in range(20)] + [datatype(self.test_value + i * 3,
                                                                                               self.test_depth + (i + 2) * 10000,
                                                                                               self.test_depth + (i + 2) * 10000 + 1,
                                                                                               3) for i in range(20)]

        self.assertDictEqual(calculateMetrics(vals, periods, variances),
                             {(1, 1): 8 / math.sqrt(0.5), (2, 1): 163.5 / 11 / math.sqrt(0.2), (3, 1): 21.2,
                              (2, 2): 38.5 / math.sqrt(0.2), (3, 2): 56})

        self.assertDictEqual(calculateMetrics([], periods, variances), {})

        variances = {1: 0.5, 2: 0.2, 3: 0}
        self.assertDictEqual(calculateMetrics(vals, periods, variances),
                             {(1, 1): 8 / math.sqrt(0.5), (2, 1): 163.5 / 11 / math.sqrt(0.2), (3, 1): 0,
                              (2, 2): 38.5 / math.sqrt(0.2), (3, 2): 0})

        variances = {1: 0, 2: 0.2, 3: 1}
        self.assertDictEqual(calculateMetrics(vals, periods, variances),
                             {(1, 1): 0, (2, 1): 163.5 / 11 / math.sqrt(0.2), (3, 1): 21.2,
                              (2, 2): 38.5 / math.sqrt(0.2), (3, 2): 56})
    '''
    def draw(self, x, y, labels, xlabel, ylabel, title):
        plt.clf()
        handlers = list()
        for (i, d) in enumerate(y):
            handler, = plt.plot(x, d, label = labels[i])
            handlers.append(handler)
        plt.legend(handles = handlers)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.savefig('../doc/inz/img/%s.png' % title)

    def generateData(self, datapattern, epochpattern):
        data = list()
        epochs = dict()

        for m in datapattern:
            data += [datatype(m['generator'](i), i, i + 1, m['meaning_id'], self.test_borehole_name + str(m['borehole_id']), m['borehole_id'])
                         for i in range(m['start'], m['stop'], m['step'])]
        for e in epochpattern:
            tmp = self.borehole_depth / float(e['epochs_num'])
            epochs[e['borehole_id']] = [periodtype(i + 1, i * tmp, (i + 1) * tmp, self.test_borehole_name + str(e['borehole_id']), e['borehole_id'])
                                         for i in range(e['epochs_num'])]

        return (sorted(data, key = lambda x: (x.meaning_id, x.depth_from)), epochs)

    def test21research(self):
        """3 boreholes, each with constant meaning value (100, 80, 0) and one epoch, to make sure the algorithm works correctly"""
        """
        testvalues = sorted([datatype(self.test_average[0], i, i + 1, 1, self.test_borehole_name + '1', 1)
                             for i in range(0, self.borehole_depth, self.data_step)] + \
                            [datatype(self.test_average[1], i, i + 1, 1, self.test_borehole_name + '2', 2)
                             for i in range(0, self.borehole_depth, self.data_step)] + \
                            [datatype(self.test_average[2], i, i + 1, 1, self.test_borehole_name + '3', 3)
                             for i in range(0, self.borehole_depth, self.data_step)],
                            key = lambda x: (x.meaning_id, x.depth_from))

        teststrat = {1 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '1', 1)],
                     2 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '2', 2)],
                     3 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '3', 3)]}
        """
        testvalues, teststrat = self.generateData([(lambda local_i: {'generator' : lambda x: self.test_average[local_i], 'meaning_id' : 1, 'borehole_id' : i + 1,
                                                     'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step})(i) for i in range(3)],
                                                  [{'borehole_id' : i + 1, 'epochs_num' : 1} for i in range(3)])

        res = views.comparision(2, testvalues, teststrat)
        res2 = views.comparision(1, testvalues, teststrat)

        self.assertGreater(res[self.test_borehole_name + '3'], res[self.test_borehole_name + '1'])
        self.assertGreater(res2[self.test_borehole_name + '3'], res[self.test_borehole_name + '3'])
        self.assertEqual(res[self.test_borehole_name + '1'], res2[self.test_borehole_name + '2'])

    def test22research(self):
        """3 boreholes, each with constant meaning affected by sigma incremented in a loop"""
        xdata = self.sigma_range
        ydataAB = [0 for _ in range(len(xdata))]
        ydataCB = [0 for _ in range(len(xdata))]
        errorsdata = [0 for _ in range(len(xdata))]

        for (ind, j) in enumerate(xdata):
            errors = 0
            for _ in range(self.experiment_num):
                """
                testvalues = sorted([datatype(self.test_average[0] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[1] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[2] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth, self.data_step)],
                                    key = lambda x: (x.meaning_id, x.depth_from))
                teststrat = {1 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '1', 1)],
                             2 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '2', 2)],
                             3 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '3', 3)]}
                """
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i] + random.gauss(0, j), 'meaning_id' : m + 1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                              for m in range(5)])(i)
                                            for i in range(3)]

                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                                  [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])

                res = views.comparision(2, testvalues, teststrat)

                ydataAB[ind] += res[self.test_borehole_name + '1']
                ydataCB[ind] += res[self.test_borehole_name + '3']
                if res[self.test_borehole_name + '1'] >= res[self.test_borehole_name + '3']:
                    errors += 1

            errorsdata[ind] = errors * 100 / float(self.experiment_num)
            ydataAB[ind] /= float(self.experiment_num)
            ydataCB[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydataAB, ydataCB], ['A-B distance', 'B-C distance'], 'sigma', 'd', 'research2_1_constant_distance_in_sigma')
        self.draw(xdata, [errorsdata], ['procent blednych obliczen'], 'sigma', 'errors %', 'research2_1_errors')

    def test23research(self):
        """3 boreholes, each with meaning affected by constant sigma, number of epochs incremented in loop"""
        xdata = range(1, 31)
        ydataAB = [0 for i in range(len(xdata))]
        ydataCB = [0 for i in range(len(xdata))]

        sigma = math.sqrt(50)
        for (ind, j) in enumerate(xdata):
            for n in range(self.experiment_num):
                """
                testvalues = sorted([datatype(self.test_average[0] + random.gauss(0, sigma), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[1] + random.gauss(0, sigma), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[2] + random.gauss(0, sigma), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth, self.data_step)],
                                    key = lambda x: (x.meaning_id, x.depth_from))
                teststrat = {1 : [periodtype(i + 1, i * tmp, (i + 1) * tmp, self.test_borehole_name + '1', 1) for i in range(j)],
                             2 : [periodtype(i + 1, i * tmp, (i + 1) * tmp, self.test_borehole_name + '2', 2) for i in range(j)],
                             3 : [periodtype(i + 1, i * tmp, (i + 1) * tmp, self.test_borehole_name + '3', 3) for i in range(j)]}
                """
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i] + random.gauss(0, sigma), 'meaning_id' : m + 1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                              for m in range(5)])(i)
                                            for i in range(3)]
                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                                  [{'borehole_id' : i + 1, 'epochs_num' : j} for i in range(3)])

                res = views.comparision(2, testvalues, teststrat)

                ydataAB[ind] += res[self.test_borehole_name + '1']
                ydataCB[ind] += res[self.test_borehole_name + '3']
            ydataAB[ind] /= float(self.experiment_num)
            ydataCB[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydataAB, ydataCB], ['A-B distance', 'B-C distance'], 'E', 'd', 'research2_2_constant_distance_in_epochs')

    def test24research(self):
        """3 boreholes, each with meaning value as linear function affected by sigma incremented in a loop"""
        xdata = self.sigma_range
        ydataAB = [0 for i in range(len(xdata))]
        ydataCB = [0 for i in range(len(xdata))]
        errorsdata = [0 for i in range(len(xdata))]

        for (ind, j) in enumerate(xdata):
            errors = 0
            for n in range(self.experiment_num):
                """
                testvalues = sorted([datatype(self.test_average[0] + self.a * i + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[1] + self.a * i + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[2] + self.a * i + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth, self.data_step)],
                                    key = lambda x: (x.meaning_id, x.depth_from))
                teststrat = {1 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '1', 1)],
                             2 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '2', 2)],
                             3 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '3', 3)]}
                """
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i] + self.a * x + random.gauss(0, j), 'meaning_id' : m + 1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                              for m in range(5)])(i)
                                            for i in range(3)]
                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                                  [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])

                res = views.comparision(2, testvalues, teststrat)

                ydataAB[ind] += res[self.test_borehole_name + '1']
                ydataCB[ind] += res[self.test_borehole_name + '3']
                if res[self.test_borehole_name + '1'] >= res[self.test_borehole_name + '3']:
                    errors += 1

            ydataAB[ind] /= float(self.experiment_num)
            ydataCB[ind] /= float(self.experiment_num)
            errorsdata[ind] = errors * 100 / float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydataAB, ydataCB], ['A-B distance', 'B-C distance'], 'sigma', 'd', 'research4_linear_distance_in_sigma')
        self.draw(xdata, [errorsdata], ['procent blednych obliczen'], 'sigma', 'errors %', 'research4_errors')

    def test25research(self):
        """3 boreholes, each with meaning value as rectangular function affected by sigma incremented in a loop"""
        xdata = self.sigma_range
        ydataAB = [0 for i in range(len(xdata))]
        ydataCB = [0 for i in range(len(xdata))]
        errorsdata = [0 for i in range(len(xdata))]

        for (ind, j) in enumerate(xdata):
            errors = 0
            for n in range(self.experiment_num):
                """
                testvalues = sorted([datatype(self.test_average[0] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth / 3, self.data_step)] + \
                                    [datatype(self.test_average[0] + self.step_chart_value + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(self.borehole_depth / 3, 2 * self.borehole_depth / 3, self.data_step)] + \
                                    [datatype(self.test_average[0] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(2 * self.borehole_depth / 3, self.borehole_depth, self.data_step)] + \

                                    [datatype(self.test_average[1] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth / 3, self.data_step)] + \
                                    [datatype(self.test_average[1] + self.step_chart_value + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(self.borehole_depth / 3, 2 * self.borehole_depth / 3, self.data_step)] + \
                                    [datatype(self.test_average[1] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(2 * self.borehole_depth / 3, self.borehole_depth, self.data_step)] + \

                                    [datatype(self.test_average[2] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth / 3, self.data_step)] + \
                                    [datatype(self.test_average[2] + self.step_chart_value + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(self.borehole_depth / 3, 2 * self.borehole_depth / 3, self.data_step)] + \
                                    [datatype(self.test_average[2] + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(2 * self.borehole_depth / 3, self.borehole_depth, self.data_step)],

                                    key = lambda x: (x.meaning_id, x.depth_from))
                teststrat = {1 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '1', 1)],
                             2 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '2', 2)],
                             3 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '3', 3)]}
                """
                pattern = [(lambda local_i: [[{'generator' : lambda x: self.test_average[local_i] + random.gauss(0, j), 'meaning_id' : m + 1,
                                               'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth / 3, 'step' : self.data_step},
                                              {'generator' : lambda x: self.test_average[local_i] + self.step_chart_value + random.gauss(0, j),
                                               'meaning_id' : m + 1, 'borehole_id' : i + 1, 'start' : self.borehole_depth / 3,
                                               'stop' : 2 * self.borehole_depth / 3, 'step' : self.data_step},
                                              {'generator' : lambda x: self.test_average[local_i] + random.gauss(0, j), 'meaning_id' :m + 1,
                                               'borehole_id' : i + 1, 'start' : 2 * self.borehole_depth / 3, 'stop' : self.borehole_depth,
                                               'step' : self.data_step}] for m in range(5)])(i)
                           for i in range(3)]

                testvalues, teststrat = self.generateData([m for i in pattern for n in i for m in n], [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])

                res = views.comparision(2, testvalues, teststrat)

                ydataAB[ind] += res[self.test_borehole_name + '1']
                ydataCB[ind] += res[self.test_borehole_name + '3']
                if res[self.test_borehole_name + '1'] >= res[self.test_borehole_name + '3']:
                    errors += 1

            errorsdata[ind] = errors * 100 / float(self.experiment_num)
            ydataAB[ind] /= float(self.experiment_num)
            ydataCB[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydataAB, ydataCB], ['A-B distance', 'B-C distance'], 'sigma', 'd', 'research5_rectangular_distance_in_sigma')
        self.draw(xdata, [errorsdata], ['procent bednych obliczen'], 'sigma', 'errors %', 'research5_errors')

    def test26research(self):
        """3 boreholes, each with 3 meanings each with linear function"""
        xdata = self.sigma_range
        ydataAB = [0 for i in range(len(xdata))]
        ydataCB = [0 for i in range(len(xdata))]
        errorsdata = [0 for i in range(len(xdata))]

        for (ind, j) in enumerate(xdata):
            errors = 0
            for n in range(self.experiment_num):
                """
                testvalues = sorted([datatype(self.test_average[0] + self.a * i + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[0] + self.a * i + random.gauss(0, j), i, i + 1, 2, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[0] + self.a * i + random.gauss(0, j), i, i + 1, 3, self.test_borehole_name + '1', 1)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \

                                    [datatype(self.test_average[1] + self.a * i + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[1] + self.a * i + random.gauss(0, j), i, i + 1, 2, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[1] + self.a * i + random.gauss(0, j), i, i + 1, 3, self.test_borehole_name + '2', 2)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \

                                    [datatype(self.test_average[2] + self.a * i + random.gauss(0, j), i, i + 1, 1, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[2] + self.a * i + random.gauss(0, j), i, i + 1, 2, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth, self.data_step)] + \
                                    [datatype(self.test_average[2] + self.a * i + random.gauss(0, j), i, i + 1, 3, self.test_borehole_name + '3', 3)
                                     for i in range(0, self.borehole_depth, self.data_step)],
                                    key = lambda x: (x.meaning_id, x.depth_from))
                teststrat = {1 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '1', 1)],
                             2 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '2', 2)],
                             3 : [periodtype(1, 0, self.borehole_depth, self.test_borehole_name + '3', 3)]}
                """
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i] + self.a * x + random.gauss(0, j), 'meaning_id' : m + 1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                              for m in range(5)])(i)
                                            for i in range(3)]

                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                            [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])

                res = views.comparision(2, testvalues, teststrat)

                ydataAB[ind] += res[self.test_borehole_name + '1']
                ydataCB[ind] += res[self.test_borehole_name + '3']
                if res[self.test_borehole_name + '1'] >= res[self.test_borehole_name + '3']:
                    errors += 1

            ydataAB[ind] /= float(self.experiment_num)
            ydataCB[ind] /= float(self.experiment_num)
            errorsdata[ind] = errors * 100 / float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydataAB, ydataCB], ['A-B distance', 'B-C distance'], 'sigma', 'd', 'research6_3bhs_linear_distance_in_sigma')
        self.draw(xdata, [errorsdata], ['procent blednych obliczen'], 'sigma', 'errors %', 'research6_errors')

    def test27research(self):
        """3 boreholes, each with 1 meanings each with measurements number incremented"""
        xdata = [self.data_step * 100, self.data_step * 10, self.data_step, self.data_step / 10, self.data_step / 100]
        ydata = [0 for i in range(len(xdata))]
        sigma = 600

        for (ind, j) in enumerate(xdata):
            errors = 0
            for n in range(self.experiment_num):
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i] + self.a * x + random.gauss(0, sigma), 'meaning_id' : m + 1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : j}
                                              for m in range(5)])(i)
                                            for i in range(3)]

                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                            [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])
                t = time.time()
                res = views.comparision(2, testvalues, teststrat)
                t = time.time() - t
                ydata[ind] += t

            ydata[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        xdata = [self.borehole_depth / float(i) for i in xdata]
        self.draw(xdata, [ydata], ['czas dzialania algorytmu'], 'data quantity', 'time', 'research7_linear_time_in_measurements')

    def test28research(self):
        """3 boreholes, each with 1 meanings each with meanings num incremented in loop"""
        xdata = range(1, 51, self.meanings_step)
        ydata = [0 for i in range(len(xdata))]
        sigma = 600

        for (ind, j) in enumerate(xdata):
            errors = 0
            for n in range(self.experiment_num):
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i] + self.a * x + random.gauss(0, sigma), 'meaning_id' : m + 1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                              for m in range(j)])(i)
                                            for i in range(3)]
                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                            [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])
                t = time.time()
                res = views.comparision(2, testvalues, teststrat)
                t = time.time() - t
                ydata[ind] += t

            ydata[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydata], ['czas dzialania algorytmu'], 'meanings number', 'time', 'research8_linear_time_in_meanings')

    def test29research(self):
        """3 boreholes, each with 1 meanings each with """
        xdata = range(3, 53, self.boreholes_step)
        ydata = [0 for i in range(len(xdata))]
        sigma = 600

        for (ind, j) in enumerate(xdata):
            errors = 0
            for n in range(self.experiment_num):
                pattern = [(lambda local_i: [{'generator' : lambda x: self.test_average[local_i % len(self.test_average)] + self.a * x + random.gauss(0, sigma),
                                              'meaning_id' : m + 1, 'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                             for m in range(5)])(i)
                                            for i in range(j)]
                testvalues, teststrat = self.generateData([m for i in pattern for m in i],
                                            [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(j)])
                t = time.time()
                res = views.comparision(2, testvalues, teststrat)
                t = time.time() - t
                ydata[ind] += t

            ydata[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydata], ['czas dzialania algorytmu'], 'boreholes number', 'time', 'research9_linear_time_in_boreholes')

    def test30research(self):
        """3 boreholes, each with meaning value as rectangular function affected by sigma incremented in a loop"""
        xdata = self.sigma_range
        ydataAB = [0 for i in range(len(xdata))]
        ydataCB = [0 for i in range(len(xdata))]

        for (ind, j) in enumerate(xdata):
            for n in range(self.experiment_num):
                pattern = [(lambda local_i: [[{'generator' : lambda x: self.test_average[local_i] + random.gauss(0, j), 'meaning_id' : m+1,
                                              'borehole_id' : i + 1, 'start' : 0, 'stop' : self.borehole_depth / 3, 'step' : self.data_step},
                                             {'generator' : lambda x: self.test_average[local_i] + self.step_chart_value + random.gauss(0, j),
                                              'meaning_id' : m+1, 'borehole_id' : i + 1, 'start' : self.borehole_depth / 3,
                                              'stop' : 2 * self.borehole_depth / 3, 'step' : self.data_step},
                                             {'generator' : lambda x: self.test_average[local_i] + random.gauss(0, j), 'meaning_id' : m+1,
                                              'borehole_id' : i + 1, 'start' : 2 * self.borehole_depth / 3, 'stop' : self.borehole_depth,
                                              'step' : self.data_step}] for m in range(5)])(i)
                                                           for i in [0, 2]]
                testvalues, teststrat = self.generateData([{'generator' : lambda x: self.test_average[1] + random.gauss(0, j), 'meaning_id' : m+1,
                                                             'borehole_id' : 2, 'start' : 0, 'stop' : self.borehole_depth, 'step' : self.data_step}
                                                           for m in range(5)] +
                                                          [m for i in pattern for n in i for m in n],
                                                  [{'borehole_id' : i + 1, 'epochs_num' : 10} for i in range(3)])

                res = views.comparision(2, testvalues, teststrat)

                ydataAB[ind] += res[self.test_borehole_name + '1']
                ydataCB[ind] += res[self.test_borehole_name + '3']
            ydataAB[ind] /= float(self.experiment_num)
            ydataCB[ind] /= float(self.experiment_num)

            print "%.1f%%" % ((ind+1) * 100 / float(len(xdata)))

        self.draw(xdata, [ydataAB, ydataCB], ['A-B distance', 'B-C distance'], 'sigma', 'd', 'research10_2rectangular_1linear_distance_in_sigma')
    '''
