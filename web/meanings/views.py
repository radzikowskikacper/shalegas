##
# @file web/meanings/views.py
# @brief Module with services for meanings and sections management

import json
import logging

from django.db import IntegrityError, transaction
from .models import *

logger = logging.getLogger('sweetspot.meanings')


def sections(request, section_id=None):
    if not section_id:
        if request.method == 'GET':
            return getSections()

        elif request.method == 'POST':
            params = json.loads(request.read().decode('utf-8'))
            name = params['name']

            with transaction.atomic():
                if not MeaningSection.objects.filter(name=name).exists():
                    MeaningSection.objects.create(name=name)
                    logger.info(
                        "User %s added new section" %
                        request.user.username)

                    return getSections()
                else:
                    raise SectionsDuplicated

    else:
        if request.method == 'PUT':
            params = json.loads(request.read().decode('utf-8'))

            with transaction.atomic():
                sect = MeaningSection.objects.get(name=section_id)

                if MeaningSection.objects.filter(name=params['name']).exists():
                    raise SectionsDuplicated

                sect.name = params['name']
                sect.save()

                sect_old = MeaningSection.objects.get(name=section_id)
                for val in MeaningValue.objects.filter(section=sect_old):
                    val.section = sect
                    val.save()

                sect_old.delete()
                logger.info("User %s modified section" % request.user.username)

                return getSections()

        elif request.method == 'DELETE':
            with transaction.atomic():
                MeaningSection.objects.get(name=section_id).delete()
                logger.info("User %s deleted section" % request.user.username)

                return getSections()


def meanings(request, meaning_id=None):
    if not meaning_id:
        if request.method == 'GET':
            return getMeanings(**request.GET)

        elif request.method == 'POST':
            params = json.loads(request.read().decode('utf-8'))
            name = params['name']
            sect = params['section']

            with transaction.atomic():
                if not MeaningValue.objects.filter(
                        name=name, section=sect).exists():
                    if params['type'] == 'normal':
                        MeaningValue.objects.create(
                            name=name,
                            unit=params['unit'],
                            section=MeaningSection.objects.get(
                                name=sect))
                    elif params['type'] == 'pict':
                        MeaningImage.objects.create(
                            name=name,
                            unit='PICT',
                            section=MeaningSection.objects.get(
                                name=sect))
                    elif params['type'] == 'dict':
                        d = MeaningDict.objects.create(
                            name=name, section=MeaningSection.objects.get(
                                name=sect), unit='DICT')

                        for val in params['dictvals']:
                            MeaningDictValue.objects.create(
                                value=val, dict_id=d)
                    else:
                        raise KeyError()
                    logger.info(
                        "User %s added new meaning" %
                        request.user.username)

                    return getMeanings()
                else:
                    raise MeaningsDuplicated

    else:
        if request.method == 'GET':
            return getMeanings(**{'mid': meaning_id})

        elif request.method == 'PUT':
            params = json.loads(request.read().decode('utf-8'))

            with transaction.atomic():
                meaning = None
                try:
                    try:
                        meaning = MeaningDict.objects.get(id=meaning_id)
                    except MeaningDict.DoesNotExist:
                        meaning = MeaningImage.objects.get(id=meaning_id)
                except MeaningImage.DoesNotExist:
                    meaning = MeaningValue.objects.get(id=meaning_id)

                if params['type'] == 'dict':
                    if meaning.unit != 'DICT':
                        sect = meaning.section
                        name = meaning.name
                        meaning.delete()
                        meaning = MeaningDict.objects.create(
                            name=name, section=sect, unit='DICT')

                    MeaningDictValue.objects.filter(value__in=set([v[0] for v in MeaningDictValue.objects.filter(
                        dict_id=meaning).values_list('value')]).difference(set(params['dictvals']))).delete()

                    for val in set(params['dictvals']).difference(set(
                            [v[0] for v in MeaningDictValue.objects.filter(dict_id=meaning).values_list('value')])):
                        MeaningDictValue.objects.create(
                            dict_id=meaning, value=val)

                else:
                    meaning = MeaningValue.objects.get(id=meaning_id)
                    name = meaning.name
                    sect = meaning.section

                    if params['type'] == 'pict':
                        if meaning.unit != 'PICT':
                            meaning.delete()
                            meaning = MeaningImage.objects.create(
                                name=name, section=sect, unit="PICT")

                    elif params['type'] == 'normal':
                        if meaning.unit in ['PICT', 'DICT']:
                            meaning.delete()
                            meaning = MeaningValue.objects.create(
                                name=name, section=sect)
                        meaning.unit = params['unit']
                        meaning.save()

                if 'name' in params:
                    meaning.name = params['name']

                if 'section' in params:
                    meaning.section = MeaningSection.objects.get(
                        name=params['section'])

                try:
                    meaning.save()
                except IntegrityError:
                    raise MeaningsDuplicated

                logger.info("User %s modified meaning" % request.user.username)

                return getMeanings()

        elif request.method == 'DELETE':
            with transaction.atomic():
                MeaningValue.objects.get(id=meaning_id).delete()
                logger.info("User %s deleted meaning" % request.user.username)
                return getMeanings()
