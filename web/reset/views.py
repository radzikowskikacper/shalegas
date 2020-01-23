import json
import settings
import logging
import os
import datetime

from boreholes.models import _JsonResponse
from django.http.response import HttpResponse
from reset.models import TooManyDumpFiles
import version.models


logger = logging.getLogger('sweetspot.reset')

DUMPS_DIRNAME = 'reset/dumps'

if not os.path.isdir(DUMPS_DIRNAME):
    os.makedirs(DUMPS_DIRNAME)


def getDumpFiles():
    return [os.path.splitext(f)[0] for f in os.listdir(
        DUMPS_DIRNAME) if os.path.isfile(os.path.join(DUMPS_DIRNAME, f))]


def prepareDumpName():
    fname = fname_format = "SweetSpot_%s" % datetime.datetime.now().strftime(
        "%Y-%m-%d_%H:%M:%S")
    i = 1

    while os.path.isfile('%s/%s' % (DUMPS_DIRNAME, fname + ".sql")):
        fname = "%s (%d)" % (fname_format, i)
        i += 1
    return "%s/%s.sql" % (DUMPS_DIRNAME, fname)


def reset(request):
    if request.method == 'GET':
        return _JsonResponse(getDumpFiles())

    elif request.method == 'PUT':
        fname = json.loads(request.read().decode())
        if fname and os.path.isfile('%s/%s.sql' % (DUMPS_DIRNAME, fname)):
            logger.info(
                "User %s started restoring database %s.sql ..." %
                (request.user.username, fname))

            os.system(
                "PGPASSWORD='%s' pg_restore -U %s -d %s --clean < %s/%s.sql" %
                (version.models.getDBPassword(),
                 version.models.getDBUser(),
                 version.models.getDBName(),
                 DUMPS_DIRNAME,
                 fname))
            logger.info("Database %s.sql was successfully restored..." % fname)
            return HttpResponse()

    elif request.method == 'POST':
        if len(getDumpFiles()) < settings.MAX_DUMP_FILES:
            os.system(
                "PGPASSWORD='%s' pg_dump -U %s -Fc %s > %s" %
                (version.models.getDBPassword(),
                 version.models.getDBUser(),
                 version.models.getDBName(),
                 prepareDumpName()))
            return HttpResponse()
        else:
            raise TooManyDumpFiles

    elif request.method == 'DELETE':
        fname = json.loads(request.read().decode())
        if fname and os.path.isfile('%s/%s.sql' % (DUMPS_DIRNAME, fname)):
            os.remove('%s/%s.sql' % (DUMPS_DIRNAME, fname))
            return HttpResponse()
