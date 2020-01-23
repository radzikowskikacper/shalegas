from initlog import LOG_FILE_NAME
from django.http import HttpResponse
import os


def logs(request, line_num):
    if request.method == 'GET':
        line_num = max(10, int(line_num))
        with open('%s/%s' % (os.environ['SWEETSPOT_LOG_DIR'], LOG_FILE_NAME), "r") as f:
            lines = f.readlines()[-line_num:]
            return HttpResponse(lines, content_type='text/plain')
