## @file web/similarities/calculations.py
# @brief Calculations module for similarities.views

from collections import defaultdict
import math

from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement
from meanings.models import MeaningValue, MeaningDict, MeaningDictValue
from values.models import RealMeasurement


def calculateAVGs(vals):
    curmeaning, num = 0, 0
    ret = defaultdict(float)
    
    for i in vals:
        if not curmeaning:
            curmeaning = i.meaning_id
            
        ret[i.meaning_id] += i.value
        if curmeaning != i.meaning_id:
            ret[curmeaning] /= num
            curmeaning = i.meaning_id
            num = 1
        else:
            num += 1
    if num:
        ret[curmeaning] /= num
    
    return ret

def calculateVariances(vals, avgs):
    ret = defaultdict(float)
    curmeaning = 0
    num = 0
    
    for i in vals:
        if not curmeaning:
            curmeaning = i.meaning_id
            
        ret[i.meaning_id] += (i.value - avgs[i.meaning_id])**2
        if curmeaning != i.meaning_id:
            ret[curmeaning] /= num - 1 if num > 1 else num
            curmeaning = i.meaning_id
            num = 1
        else:
            num += 1    
    if num:
        ret[curmeaning] /= num - 1 if num > 1 else num

    return ret

def calculatePeriods(periodslist):
    periods = defaultdict(list)

    for p in periodslist:
        if not len(periods[p.dictionary_id]) or periods[p.dictionary_id][-1]['to'] < p.depth_from:
            periods[p.dictionary_id].append({'from' : p.depth_from, 'to' : p.depth_to})
        else:
            periods[p.dictionary_id][-1]['to'] = p.depth_to

    return periods
     
def calculateMetrics(vals, periods, variances):
    ret = defaultdict(float)

    for p in periods:
        lastmeaning, num = None, 0

        for v in vals:
            if lastmeaning != v.meaning_id:
                if lastmeaning and num:
                    if variances[lastmeaning]:
                        ret[(lastmeaning, p)] = abs(ret[(lastmeaning, p)] / num) / math.sqrt(variances[lastmeaning])
                    else:
                        ret[(lastmeaning, p)] = 0
                    
                ptable = iter(periods[p])
                piter = next(ptable)
                lastmeaning = v.meaning_id
                num = 0

            try:            
                while v.depth_from > piter['to']:
                    piter = next(ptable)
            except StopIteration:
                continue
            
            if v.depth_from <= piter['to'] and v.depth_to >= piter['from']:
                ret[(v.meaning_id, p)] += v.value
                num += 1
 
        if lastmeaning and num:
            if variances[lastmeaning]:
                ret[(lastmeaning, p)] = abs(ret[(lastmeaning, p)] / num) / math.sqrt(variances[lastmeaning])
            else:
                ret[(lastmeaning, p)] = 0
        
    return ret

def comparision(borehole_id, vals, strats):
    data = defaultdict(list)
    
    avgs = calculateAVGs(vals)
    variances = calculateVariances(vals, avgs)                  
    for d in vals:
        data[d.borehole_id].append(d)
        
    localmetrics = calculateMetrics(data[borehole_id], calculatePeriods(strats[borehole_id]), variances)
    
    ret = dict()
    for d in data:
        if d == borehole_id:
            continue

        metrics = calculateMetrics(data[d], calculatePeriods(strats[d]), variances)
        dst = 0
        metricsfound = False

        for (m, i) in set(metrics.keys()).intersection(set(localmetrics.keys())):
            metricsfound = True
            dst += (metrics[(m, i)] - localmetrics[(m, i)])**2
            
        ret[data[d][0].bh] = math.sqrt(dst) if metricsfound else 'NO_COMMON_METRICS'
        
    for b in Borehole.objects.exclude(id = borehole_id):
        if not b.name in ret:
            ret[b.name] = 'NO_MEASUREMENTS'
            
    return ret
            
def compareTo(borehole_id, stratigraphy_level, epochs, meanings = None):
    Borehole.objects.get(id = int(borehole_id))
    stratigraphy = defaultdict(list)

    vals = RealMeasurement.objects.extra({'bh' : 'SELECT name FROM boreholes_borehole WHERE id=measurements_measurement.borehole_id'}).all()
    if meanings:
        meanings = [int(m) for m in meanings]
        vals = vals.filter(meaning__in = MeaningValue.objects.filter(id__in = meanings).exclude(unit__in = ['DICT', 'PICT']))
    else:
        meanings = [m.id for m in MeaningValue.objects.exclude(unit__in = ['DICT', 'PICT'])]
    vals = vals.order_by('meaning', 'depth_from')
    
    dict = MeaningDict.objects.get(id = int(stratigraphy_level))
    dictvalues = MeaningDictValue.objects.filter(dict_id = dict)
    if epochs:
        dictvalues = dictvalues.filter(id__in = epochs)

    for d in DictionaryMeasurement.objects.extra({'bh' : 'SELECT name FROM boreholes_borehole WHERE id=measurements_measurement.borehole_id'}).\
        filter(meaning = dict, dictionary__in = dictvalues).order_by('dictionary', 'depth_from'):
        stratigraphy[d.borehole_id].append(d)
        
    return comparision(int(borehole_id), list(vals), stratigraphy)