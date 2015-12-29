##
# @file web/urls.py
# @brief Django urls file

from django.conf import settings
from django.conf.urls import patterns, include, url

import boreholes.views
import charts.views
import data.views
import images.views
import meanings.views
import measurements.views
import similarities.views
import tables.views
import users.views
import views
import stratigraphy.views
import log.views
import reset.views

urlpatterns = patterns('',
    url(r'^(srvsweetspot/)?ajax/', include(patterns('ajax', 
        url(r'^image/archive/(?P<borehole_id>\d+)', images.views.upload_archive),
        url(r'^image/progress', images.views.getArchiveProgress),
        url(r'^image/cancel', images.views.cancel),
        url(r'^image(/(?P<measurement_id>\d+))?', images.views.image),
        
        url(r'^boreholes(/(?P<borehole_id>\d+))?', boreholes.views.boreholes),
        url(r'^borehole_image/(?P<borehole_id>\d+)/(?P<start_depth_in>\d+)-(?P<stop_depth_in>\d+)/(?P<outimg_width>\d+)-(?P<outimg_height>\d+)',
            images.views.borehole_image),

        url(r'^similarities/(?P<borehole_id>\d+)/', similarities.views.similarities),
        
        url(r'^measurements/intervals/(?P<borehole_id>\d+)/(?P<start_depth>\d+)-(?P<stop_depth>\d+)/(?P<outimg_width>\d+)-(?P<outimg_height>\d+)', 
            measurements.views.intervals),
        url(r'^measurements/export/(?P<borehole_id>\d+)/(?P<depth_from>\d+)-(?P<depth_to>\d+)/(?P<lang>\w+)', measurements.views.export),
        url(r'^measurements/download/(?P<filename>\w+).(?P<ext>\w+)', measurements.views.download),
        url(r'^measurements/archive/(?P<borehole_id>\d+)/(?P<data_col>\d+)/(?P<meaning_id>\d+)/(?P<lang>\w+)', measurements.views.archive),
        url(r'^measurements/(?P<id>\d+)?', measurements.views.measurements),
        
        url(r'^data', data.views.data),
        
        url(r'^tables/(?P<borehole_id>\d+)/', tables.views.tables),
        
        url(r'^stratigraphy/(?P<borehole_id>\d+)/', stratigraphy.views.stratigraphy),
        
        url(r'^users/((?P<command>\w+))?', users.views.users),
        
        url(r'^meanings/sections/((?P<section_id>\w+))?', meanings.views.sections),
        url(r'^meanings/(?P<meaning_id>\d+)?', meanings.views.meanings),
        
        url(r'^charts/(?P<borehole_id>\d+)?', charts.views.charts),
        
        url(r'^log/(?P<line_num>\d+)?', log.views.logs),
        
        url(r'^reset/?', reset.views.reset),

        url(r'(?P<module>\w+)/(?P<function>\w+)/', views.ajax),
    ))),
    url(r'(srvsweetspot/)?^$', views.index, name='index'),
)



