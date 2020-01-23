##
# @file web/images/archiver.py
# @brief Module for handling photo archives and image regeneration

from django.conf import settings
from django.db import transaction
from io import BytesIO, StringIO
import logging
from os.path import basename, splitext
import threading
from . import models
from PIL import Image
from images.common import add_image, BadImageSizeException, imagePosHeight
from measurements.models import MeasurementsDuplicated
import zipfile as zf

logger = logging.getLogger('sweetspot.images')


class UserInterruptException(Exception):
    pass


class ProgressStatus:
    OK = 'Ok'
    DUPLICATE_ERR = 'Archive has duplicated file names'
    BAD_SIZE_ERR = "Size {} {}".format(
        settings.MEASUREMENT_IMAGE_WIDTH_PX,
        settings.MEASUREMENT_IMAGE_HEIGHT_PX)
    INTEGRITY_ERR = 'Duplicated photo for one or more depth'
    FINISHED = 'Finished'
    NO_ARCHIVE = 'no_archive'


class Archiver(object):
    '''
    Archiver class manages process of uploading archive to server.
    '''
    _instance = None
    status = ProgressStatus.OK
    progress = 0
    max = 0
    interrupted = False
    worker = None

    def __new__(cls, *args, **kwargs):
        '''
        Singleton
        '''
        if not cls._instance:
            cls._instance = super(Archiver, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def startUpload(self, request, file, borehole):
        self._reset()
        self.worker = threading.Thread(
            target=self.doUpload, args=(
                request, borehole, file))
        self.worker.start()

    def startRegeneration(self, request, borehole):
        self._reset()
        self.worker = threading.Thread(
            target=self.doRegenerate, args=(
                request, borehole,))
        self.worker.start()

    def _reset(self):
        self.status = ProgressStatus.OK
        self.progress = 0
        self.max = 0
        self.interrupted = False

    def isBusy(self):
        return (self.worker is not None and self.worker.isAlive())

    def calculateHelpersNumber(self, depths_list):
        count = 0
        last = None
        for depth in depths_list:
            temp = depth
            if last is not None:
                for i in range(1, 4):
                    if last // 10**i * 10**i < temp // 10**i * 10**i:
                        count += 1
                    else:
                        break
            else:
                count += 3
            last = temp
        if count:
            count += 1
        return count

    def generateHelperPhotos(self, base_photos, borehole):
        img_num = len(base_photos)
        first10 = base_photos[0].depth_from // 1000 * 1000 if img_num else 0
        first100 = first10 // 10000 * 10000
        first1000 = first10 // 100000 * 100000
        max10 = first10 + 10 * int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
        max100 = first100 + 100 * int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
        max1000 = first1000 + 1000 * int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
        out10 = Image.new(
            "RGBA",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX * 10))
        out100 = Image.new(
            "RGBA",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX * 10))
        out1000 = Image.new(
            "RGBA",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX * 10))
        helper_tab = [10, 100, 1000]
        #print first10, first100, first1000
        #print max10, max100, max1000

        for i, photo in enumerate(base_photos):
            if (self.interrupted):
                raise UserInterruptException

            photodata = Image.open(BytesIO(photo.imagedata))
            if photodata.size != (
                    settings.MEASUREMENT_IMAGE_WIDTH_PX,
                    settings.MEASUREMENT_IMAGE_HEIGHT_PX):
                photodata = photodata.resize(
                    (settings.MEASUREMENT_IMAGE_WIDTH_PX,
                     settings.MEASUREMENT_IMAGE_HEIGHT_PX),
                    resample=Image.ANTIALIAS)
            out10.paste(
                photodata, (0, imagePosHeight(
                    photo.depth_from - first10)))

            counter = i + 1
            for index, j in enumerate(helper_tab):
                if counter >= img_num or base_photos[counter].depth_from // j * j >= locals()[
                        'max%d' % j]:
                    t = BytesIO()
                    locals()[
                        'out%d' %
                        j].resize(
                        (settings.MEASUREMENT_IMAGE_WIDTH_PX,
                         settings.MEASUREMENT_IMAGE_HEIGHT_PX),
                        resample=Image.ANTIALIAS).save(
                        t,
                        format='JPEG')
                    t.seek(0)
                    if index < len(helper_tab) - 1:
                        locals()['out%d' % helper_tab[index + 1]].paste(Image.open(BytesIO(t.read())), (0, int(
                            imagePosHeight(locals()['first%d' % j] - locals()['first%d' % helper_tab[index + 1]]) / j)))
                        t.seek(0)
                    add_image(
                        t.read(),
                        borehole=borehole,
                        depth_from=locals()[
                            'first%d' %
                            j],
                        depth_to=locals()[
                            'max%d' %
                            j],
                        geophysical_depth=locals()[
                            'first%d' %
                            j])
                    self.progress += 1

                    if counter < img_num:
                        if j == 10:
                            first10 = base_photos[counter].depth_from // (
                                100 * j) * (100 * j)
                            max10 = locals()[
                                'first%d' % j] + int(settings.MEASUREMENT_IMAGE_HEIGHT_CM) * j
                            out10 = Image.new(
                                "RGBA",
                                (settings.MEASUREMENT_IMAGE_WIDTH_PX,
                                 settings.MEASUREMENT_IMAGE_HEIGHT_PX * 10))
                        elif j == 100:
                            first100 = base_photos[counter].depth_from // (
                                100 * j) * (100 * j)
                            max100 = locals()[
                                'first%d' % j] + int(settings.MEASUREMENT_IMAGE_HEIGHT_CM) * j
                            out100 = Image.new(
                                "RGBA",
                                (settings.MEASUREMENT_IMAGE_WIDTH_PX,
                                 settings.MEASUREMENT_IMAGE_HEIGHT_PX * 10))
                        elif j == 1000:
                            first1000 = base_photos[counter].depth_from // (
                                100 * j) * (100 * j)
                            max1000 = locals()[
                                'first%d' % j] + int(settings.MEASUREMENT_IMAGE_HEIGHT_CM) * j
                            out1000 = Image.new(
                                "RGBA",
                                (settings.MEASUREMENT_IMAGE_WIDTH_PX,
                                 settings.MEASUREMENT_IMAGE_HEIGHT_PX * 10))
                else:
                    break

        added_photos = models.Image.objects.filter(
            borehole=borehole, meaning=None).extra(
            where=['depth_to - depth_from=100000']).order_by('depth_from')

        if not len(added_photos):
            return

        outfull = Image.new(
            "RGBA",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX * (
                 settings.MAX_BOREHOLE_HEIGHT // 1000)))

        for img in added_photos:
            outfull.paste(Image.open(BytesIO(img.imagedata)), (0, int(
                imagePosHeight(img.depth_from) / 2 / (settings.MAX_BOREHOLE_HEIGHT // 10))))

        t = BytesIO()
        outfull.resize(
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX),
            resample=Image.ANTIALIAS).save(
            t,
            format='JPEG')
        t.seek(0)
        add_image(
            t.read(),
            borehole=borehole,
            depth_from=0,
            depth_to=settings.MAX_BOREHOLE_HEIGHT *
            settings.MEASUREMENT_IMAGE_HEIGHT_CM,
            geophysical_depth=0)
        self.progress += 1

    def doRegenerate(self, request, borehole):
        try:
            imgs = models.Image.objects.filter(borehole=borehole, meaning=None)
            self.max = temp = len(
                imgs.extra(
                    where=['depth_to - depth_from>100']))
            imgs = imgs.order_by('depth_from')
            self.max += self.calculateHelpersNumber(
                [
                    img.depth_from /
                    settings.MEASUREMENT_IMAGE_HEIGHT_CM for img in imgs.extra(
                        where=['depth_to - depth_from=100'])])

            with transaction.atomic():
                imgs.extra(where=['depth_to - depth_from>100']).delete()
                self.progress += temp
                self.generateHelperPhotos(imgs, borehole)
                logger.info(
                    "User %s regenerated photos" %
                    request.user.username)

            self.status = ProgressStatus.FINISHED

        except UserInterruptException as e:
            logger.info('archive upload interrupted by user')

    def doUpload(self, request, borehole, file):
        if 'archive' not in request.FILES:
            logger.warning('No archive selected')
            self.status = ProgressStatus.NO_ARCHIVE
            return

        logger.info("User %s uploaded archive" % request.user.username)

        data = file  # request.FILES['archive']

#        if True:#not isinstance(data, InMemoryUploadedFile):
 #           data = BytesIO(file)
        #    print 'big;'
        # else:
        #    print 'small'
        #    print data
        #    print 'small1'
        #    with open('temp.dat', 'wb+') as destination:
        #        destination.write(data)
        #    data = 'temp.dat'

        #destination = open('temp.dat', 'wb+')
        #data = BytesIO(open(data.temporary_file_path(), 'rb').read())

        # for chunk in data.chunks():
        #    destination.write(chunk)
        # destination.close()
        # data

        # data = BytesIO(open(data.temporary_file_path(), 'rb').read())  # path = default_storage.save('temp.dat', ContentFile(data.read()))
        #data = os.path.join(settings.MEDIA_ROOT, path)

        with zf.ZipFile(data, 'r') as arch:
            jpgs_paths = [img for img in arch.namelist() if splitext(img)[
                1] == '.jpg']
            # and splitext(basename(img))[0].replace(',', '.').isdigit()]
            if len(jpgs_paths) > len(set([basename(i) for i in jpgs_paths])):
                self.status = ProgressStatus.DUPLICATE_ERR
                return

            try:
                self.max = len(jpgs_paths) + self.calculateHelpersNumber(
                    [float(splitext(basename(path))[0].replace(',', '.')) for path in jpgs_paths])
                added_imgs = []
                with transaction.atomic():
                    for path in jpgs_paths:
                        if (self.interrupted):
                            raise UserInterruptException

                        start_depth = float(splitext(basename(path))[0].replace(
                            ',', '.')) * int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)
                        #print start_depth
                        added_imgs.append(
                            add_image(
                                arch.open(path).read(),
                                borehole=borehole,
                                depth_from=start_depth,
                                depth_to=start_depth + int(
                                    settings.MEASUREMENT_IMAGE_HEIGHT_CM),
                                geophysical_depth=start_depth))

                        self.progress += 1
                    self.generateHelperPhotos(
                        sorted(
                            added_imgs,
                            key=lambda x: x.depth_from),
                        borehole)
                    logger.info(
                        "User %s processed photo archive" %
                        request.user.username)

                self.status = ProgressStatus.FINISHED

            except MeasurementsDuplicated as e:
                logger.error(
                    'upload_archive exception: integrity error, ' + str(e))
                self.status = ProgressStatus.INTEGRITY_ERR
            except UserInterruptException as e:
                logger.info('archive upload interrupted by user')
