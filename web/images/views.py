 ##
# @file web/images/views.py
# @brief The views module for images application, provides services for fetching, creating, modifying and deleting images from database.

from io import BytesIO
import json
import logging
from . import models
from PIL import Image
from boreholes.models import Borehole, _JsonResponse
from django.conf import settings
from django.http import HttpResponse
import images.archiver
from images.common import add_image, calculateImgHeight, imagePosHeight
from meanings.models import MeaningImage
from settings import MEASUREMENT_IMAGE_HEIGHT_PX, MEASUREMENT_IMAGE_WIDTH_PX
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q, F

logger = logging.getLogger('sweetspot.images')

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TEXT = 0x01
BINARY = 0x02

archiver = images.archiver.Archiver()

def image(request, measurement_id=None):
    '''
    The service for getting a list of all existing images or getting particular image
    '''
    if measurement_id is None and "id" in request.GET:
        measurement_id = request.GET["id"]

    if measurement_id is not None:
        img = models.Image.objects.get(id = measurement_id)

        if request.method == 'GET': # get image with id
            response = HttpResponse()
            response['content-type'] = 'image/jpeg'
            response.write(img.imagedata)
            return response
        elif request.method == 'DELETE': # delete image with id
            img.delete()
            logger.info("User %s deleted image" % request.user.username)
            
            return _JsonResponse({'status' : 'ok'})

    if request.method == 'POST': # upload file here
        depth_from = None
        if "depth_from" in request.POST:
            depth_from = request.POST["depth_from"]
        elif "geophysical_depth" in request.POST:
            depth_from = request.POST["geophysical_depth"]
        else:
            depth_from = request.POST["depth"]

        depth_from = float(depth_from) * 100
        depth_to = float(request.POST['depth_to'])*100 if ('depth_to' in request.POST and int(request.POST['depth_to'])*100 > depth_from) \
                                            else depth_from + float(settings.MEASUREMENT_IMAGE_HEIGHT_CM)

        geodepth = None
        if "geophysical_depth" in request.POST:
            geodepth = request.POST["geophysical_depth"]
        elif "depth_from" in request.POST:
            geodepth = request.POST["depth_from"]
        else:
            geodepth = request.POST["depth"]

        geodepth = float(geodepth) * 100
        
        meaning = MeaningImage.objects.get(id = request.POST['meaning']) if 'meaning' in request.POST else None
        ret = None
        imgdata = request.FILES['image_path'].read()
        if Image.open(BytesIO(imgdata)).size == (settings.MEASUREMENT_IMAGE_WIDTH_PX, settings.MEASUREMENT_IMAGE_HEIGHT_PX):
            ret = HttpResponse()
        else:
            ret = HttpResponse(status = 415)
            
        img = add_image(imgdata,
            borehole = Borehole.objects.get(id = request.POST["borehole_id"]),
            depth_from = depth_from,
            depth_to = depth_to,
            geophysical_depth = geodepth, meaning = meaning)            
            
        logger.info("User %s added new photo" % request.user.username)
        
        return ret

    if request.method == 'PUT':
        global archiver

        borehole = Borehole.objects.get(id = json.loads(request.read().decode('utf-8'))["borehole_id"])

        if (archiver.isBusy()):
            return HttpResponse(status=503)

        archiver.startRegeneration(request, borehole)
        logger.info("User %s started photo regeneration" % request.user.username)

        return HttpResponse()

    # get list of images
    
    imgs = models.Image.objects.filter(meaning = None, borehole = Borehole.objects.get(id = request.GET["borehole_id"])).order_by('depth_from')
    imgs = imgs.values_list('id', 'depth_from', 'depth_to', 'geophysical_depth')
        
    if "start_depth" in request.GET:
        imgs = imgs.filter(depth_to__gte = int(request.GET["start_depth"]) * 100)
    if "stop_depth" in request.GET:
        imgs = imgs.filter(depth_from__lte = int(request.GET["stop_depth"]) * 100)

    return _JsonResponse([{ "id" : img[0], "depth_from" : img[1], "depth_to" : img[2], "geophysical_depth" : img[3]} 
                              for img in imgs])

def borehole_image(request, borehole_id, start_depth_in, stop_depth_in, outimg_width, outimg_height):
    """
    Create image for borehole with geophysical depth from  start_depth [cm] to stop_depth [cm]. Whole image is included, the image is not cut.
    The output has required outimg_height in pixels.
    """
    if int(stop_depth_in) < int(start_depth_in):
        raise Exception("stop_depth should be bigger than start_depth")

    depthRange = int(stop_depth_in) - int(start_depth_in)

    image_height_cm = int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
    start_depth = int(start_depth_in) * image_height_cm
    stop_depth = int(stop_depth_in) * image_height_cm
    outimg_height = int(outimg_height)
    outimg_width = int(outimg_width)

    imgheight = calculateImgHeight(depthRange)

    if depthRange != 1:
        imgs = models.Image.objects.filter(borehole = borehole_id, depth_to__gte=start_depth, depth_from__lte=stop_depth)
        imgs = imgs.extra(where=['depth_to - depth_from=%d' % (imgheight * image_height_cm)]).order_by('depth_from')
    else:
        imgs = models.Image.objects.filter(borehole = borehole_id)
        imgs = imgs.filter(Q(depth_from__range=(start_depth, stop_depth)) | Q(depth_to__range=(start_depth, stop_depth)))#depth_from=start_depth, depth_to=stop_depth)
        imgs = imgs.filter(depth_to=F('depth_from') + int(settings.MEASUREMENT_IMAGE_HEIGHT_CM))
    #print len(imgs)
    response = HttpResponse()
    response['content-type'] = 'image/jpeg'
    
    if depthRange != 1 or outimg_width != 0 and outimg_height != 0:
        outimg = Image.new("RGBA", (int(settings.MEASUREMENT_IMAGE_WIDTH_PX), int(imagePosHeight(stop_depth - start_depth) / imgheight)))
        for img in imgs:
            if img.depth_to != img.depth_from + image_height_cm*imgheight:
                logger.warning('image: bad height in [cm] for id={img_id}, from={depth_from}, to={depth_to}, height={height}'.format(img_id=img.id,
                                                                                                                                     depth_from=img.depth_from,
                                                                                                                                     depth_to=img.depth_to,
                                                                                                                                     height=image_height_cm
                                                                                                                                 ))
            imgdata = Image.open(BytesIO(img.imagedata))

            if imgdata.size != (settings.MEASUREMENT_IMAGE_WIDTH_PX, settings.MEASUREMENT_IMAGE_HEIGHT_PX):
                imgdata = imgdata.resize((settings.MEASUREMENT_IMAGE_WIDTH_PX, settings.MEASUREMENT_IMAGE_HEIGHT_PX), resample = Image.ANTIALIAS)
            outimg.paste(imgdata, (0, int(imagePosHeight(img.depth_from - start_depth) / imgheight)))
        outimg = outimg.resize((outimg_width, outimg_height), resample=Image.ANTIALIAS)
    else:
        outimg = Image.open(BytesIO(imgs[0].imagedata))

    outimg.save(response, format="JPEG")

    return response

def upload_archive(request, borehole_id):
    if request.method == 'POST':
        global archiver
    
        borehole = Borehole.objects.get(id = borehole_id)
    
        if (archiver.isBusy()):
            return HttpResponse(status=503)
    
        data = request.FILES['archive']
        if not isinstance(data, InMemoryUploadedFile):
            file = BytesIO(open(data.temporary_file_path(), 'rb').read())
        else:
            file = BytesIO(data.read())

        archiver.startUpload(request, file, borehole)

        return HttpResponse()

def getArchiveProgress(request):
    ret = {'status' : archiver.status, 'progress' :
           int(float(archiver.progress) / float(archiver.max) * 100) if archiver.max else 0}
    return _JsonResponse(ret)

def cancel(request):
    archiver.interrupted = True
    logger.info("User %s canceled processing photos" % request.user.username)

    return HttpResponse()
