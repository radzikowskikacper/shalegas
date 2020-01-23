##
# @file web/images/tests.py
# @brief Unit tests for images services

import django.test
import json
from .models import Image
from boreholes.models import Borehole
import django.core.management
from django.core.exceptions import ValidationError
from django.conf import settings
from io import BytesIO
from PIL import Image as Im
import zipfile as zf
import time
import images.archiver
from images.archiver import ProgressStatus
from django.http import HttpRequest, QueryDict
from measurements.models import MeasurementsDuplicated
from copy import copy
from meanings.models import MeaningImage, MeaningSection
from django.contrib.auth.models import User, AnonymousUser
from . import views


# #inserts 1 image into DB, using views.new (like AJAX request)
# def createTestImage(name=None, imagepath=None):
#     params = {}

#     if name:
#         params['name'] = name
#     if imagepath:
#         params['image'] = imagepath

#     request = RequestStr(method = 'POST', POST = params)

#     return views.image(request)

# main testcase
class ImageViewTestCase(django.test.TransactionTestCase):
    # example data for test objects
    test_name = "test_borehole"
    test_image = '/tmp/image{}.jpg'

    # number of objects to insert into DB
    test_num = 5
    # number of objects to insert into DB just for 1st borehole
    test_bh1_num = 3

    test_username = 'sweetspot'
    test_password = 'sweetspot'

    def setUp(self):
        self.req = HttpRequest()
        self.user = self.req.user = User.objects.create_user(
            self.test_username, '', self.test_password)
        django.core.management.call_command('flush', interactive=False)

        self.bh1 = Borehole.objects.create(
            id=1, name="bh1", latitude=0, longitude=0, description="")
        for i in range(self.test_bh1_num):
            self.img[i] = Image.objects.create(
                borehole=self.bh1,
                depth_from=i * 100,
                depth_to=(
                    i + 1) * 100,
                geophysical_depth=0,
                imagedata=self.imgw.getvalue())

        self.bh2 = Borehole.objects.create(
            id=2, name="bh2", latitude=10, longitude=10, description="")
        for i in range(self.test_num - self.test_bh1_num):
            Image.objects.create(
                borehole=self.bh2,
                depth_from=i * 100,
                depth_to=i * 100 + 100,
                geophysical_depth=0,
                imagedata=self.imgb.getvalue())

        MeaningImage.objects.create(
            name='meaning',
            id=10,
            section=MeaningSection.objects.create(
                name='section'),
            unit='unit')

    @classmethod
    def setUpClass(self):
        self.imgw = BytesIO()
        Im.new(
            "RGB",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX),
            "white").save(
            self.imgw,
            format="JPEG")

        self.imgsize = BytesIO()
        Im.new("RGB",
               (int(settings.MEASUREMENT_IMAGE_WIDTH_PX / 2),
                int(settings.MEASUREMENT_IMAGE_HEIGHT_PX / 2)),
               "white").save(self.imgsize,
                             format="JPEG")

        self.imgb = BytesIO()
        Im.new(
            "RGB",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX),
            "black").save(
            self.imgb,
            format="JPEG")

        self.imgbig = BytesIO()
        Im.new(
            "RGB",
            (settings.MEASUREMENT_IMAGE_WIDTH_PX +
             100,
             settings.MEASUREMENT_IMAGE_HEIGHT_PX +
             100),
            "white").save(
            self.imgbig,
            format="JPEG")

        self.img = [None for i in range(self.test_bh1_num)]

    # def insertNumObjects(self):
    #     for i in range(self.test_num):
    #         createTestImage(self.test_name + str(i), str(self.test_image).format(i))

    def test02GetBh(self):
        self.req.method = 'GET'
        self.req.GET = copy(QueryDict('borehole_id=%d' % self.bh1.id))
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        img_lst = json.loads(res.content.decode('utf-8'))
        self.assertTrue(isinstance(img_lst, list))
        self.assertEqual(len(img_lst), 3)

        self.req.GET['start_depth'] = 2
        res = views.image(self.req)
        self.assertListEqual(json.loads(res.content.decode('utf-8')), [
            {'id': 2, 'depth_from': 100, 'depth_to': 200, 'geophysical_depth': 0},
            {'id': 3, 'depth_from': 200, 'depth_to': 300, 'geophysical_depth': 0}])

        self.req.GET['start_depth'] = 4
        res = views.image(self.req)
        self.assertListEqual(json.loads(res.content.decode('utf-8')), [])

        del self.req.GET['start_depth']
        self.req.GET['stop_depth'] = 2
        res = views.image(self.req)
        self.assertListEqual(json.loads(res.content.decode('utf-8')),
                             [{'id': 1,
                               'depth_from': 0,
                               'depth_to': 100,
                               'geophysical_depth': 0},
                              {'id': 2,
                               'depth_from': 100,
                               'depth_to': 200,
                               'geophysical_depth': 0},
                              {'id': 3,
                               'depth_from': 200,
                               'depth_to': 300,
                               'geophysical_depth': 0}])

        self.req.GET['stop_depth'] = 1
        res = views.image(self.req)
        self.assertListEqual(json.loads(res.content.decode('utf-8')),
                             [{'id': 1,
                               'depth_from': 0,
                               'depth_to': 100,
                               'geophysical_depth': 0},
                              {'id': 2,
                               'depth_from': 100,
                               'depth_to': 200,
                               'geophysical_depth': 0}])

    def test03GetImage(self):
        self.req.method = 'GET'
        res = views.image(self.req, self.img[0].id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, self.imgw.getvalue())
        self.assertNotEqual(res.content, self.imgb.getvalue())

        # Alternative method
    def test04GetImageAlter(self):
        self.req.method = 'GET'
        self.req.GET = QueryDict('id=%d' % self.img[0].id)
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, self.imgw.getvalue())

    def test05deleteImage(self):
        self.req.method = 'DELETE'
        res = views.image(self.req, self.img[1].id)
        self.assertEqual(res.status_code, 200)
        stat = json.loads(res.content.decode('utf-8'))
        self.assertTrue("status" in stat)
        self.assertEqual(stat["status"], "ok")

        self.req.method = 'GET'
        self.req.GET = QueryDict('borehole_id=%d' % self.bh1.id)
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        img_lst = json.loads(res.content.decode('utf-8'))
        self.assertTrue(isinstance(img_lst, list))
        self.assertEqual(len(img_lst), 2)

    def test06UploadImage1(self):
        self.req.method = 'POST'
        self.req.POST = QueryDict(
            'borehole_id=%d&depth_from=900&geophysical_depth=900' %
            self.bh1.id)
        self.req.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)

        # without 'dept_from'
        self.req.method = 'POST'
        self.req.POST = QueryDict(
            'borehole_id=%d&geophysical_depth=1000' %
            self.bh1.id)
        self.req.FILES = dict(image_path=BytesIO(self.imgsize.getvalue()))
        res = views.image(self.req)
        self.assertEqual(res.status_code, 415)
        # without 'geophysical_depth'

        self.req.POST = QueryDict(
            'borehole_id=%d&depth_from=1100' %
            self.bh1.id)
        self.req.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)

        # duplicate
        self.req.POST = QueryDict(
            'borehole_id=%d&depth_from=1100' %
            self.bh1.id)
        self.req.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        self.assertRaises(MeasurementsDuplicated, views.image, self.req)

        self.req.method = 'GET'
        self.req.GET = QueryDict('borehole_id=%d' % self.bh1.id)
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        img_lst = json.loads(res.content.decode('utf-8'))
        self.assertTrue(isinstance(img_lst, list))
        self.assertEqual(len(img_lst), 6)
        self.assertEqual(img_lst[0]['depth_from'], 0)
        self.assertEqual(img_lst[1]['depth_from'], 100)
        self.assertEqual(img_lst[2]['depth_from'], 200)
        self.assertEqual(img_lst[3]['depth_from'], 90000)
        self.assertEqual(img_lst[4]['depth_from'], 100000)
        self.assertEqual(img_lst[5]['depth_from'], 110000)

        self.req.method = 'POST'
        self.req.POST = QueryDict(
            'borehole_id=%d&depth_from=9000&geophysical_depth=900&meaning=10' %
            self.bh1.id)
        self.req.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(Image.objects.exclude(meaning=None)), 1)

        # res = views.image(RequestStr(method = 'GET', GET = dict(borehole_id=self.bh1.id), POST={}, FILES={}))
        # self.assertEqual(res.status_code, 200)
        # img_lst = json.loads(res.content)
        # self.assertTrue(isinstance(img_lst, list))
        # self.assertEqual(len(img_lst), 4)
        # self.assertEqual(img_lst[0]['depth_from'], 0)
        # self.assertEqual(img_lst[1]['depth_from'], 100)
        # self.assertEqual(img_lst[2]['depth_from'], 200)
        # self.assertEqual(img_lst[3]['depth_from'], 90000)

    def test06UploadImage2(self):
        self.req.method = 'POST'
        self.req.POST = QueryDict('borehole_id=%d&depth=900' % self.bh1.id)
        self.req.FILES = dict(image_path=BytesIO(self.imgw.getvalue()))
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)

        self.req.method = 'GET'
        self.req.GET = QueryDict('borehole_id=%d' % self.bh1.id)
        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        img_lst = json.loads(res.content.decode('utf-8'))
        self.assertTrue(isinstance(img_lst, list))
        self.assertEqual(len(img_lst), 4)

    def test07imagePositionHeight(self):
        image_height_px = int(settings.MEASUREMENT_IMAGE_HEIGHT_PX)
        image_height_cm = int(settings.MEASUREMENT_IMAGE_HEIGHT_CM)

        self.assertEqual(views.imagePosHeight(0), 0)
        self.assertEqual(
            views.imagePosHeight(image_height_cm),
            image_height_px)
        self.assertEqual(
            views.imagePosHeight(
                2 * image_height_cm),
            2 * image_height_px)
        self.assertEqual(
            views.imagePosHeight(
                3 * image_height_cm),
            3 * image_height_px)

    def test08UploadArchive(self):
        self.req.method = 'POST'
        self.assertRaises(Borehole.DoesNotExist,
                          views.upload_archive, self.req, -99)

        arch = BytesIO()
        with zf.ZipFile(arch, 'w') as tmp:
            tmp.writestr('123456.jpg', self.imgw.getvalue())
            #tmp.writestr('dir/1.jpg', self.imgw.getvalue())
        arch.seek(0)

        self.req.FILES = dict(archive=arch)
        res = views.upload_archive(self.req, self.bh1.id)
        self.assertEqual(res.status_code, 200)
        res = views.upload_archive(self.req, self.bh1.id)
        self.assertEqual(res.status_code, 503)
        images.archiver.Archiver().worker.join()

    def test09UploadArchive(self):
        arch = BytesIO()
        with zf.ZipFile(arch, 'w') as tmp:
            tmp.writestr('123456.jpg', self.imgw.getvalue())

        arch.seek(0)

        self.req.method = 'POST'
        self.req.FILES = dict(archive=arch)
        res = views.upload_archive(self.req, self.bh1.id)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(images.archiver.Archiver().isBusy())
        images.archiver.Archiver().worker.join()
        self.assertFalse(images.archiver.Archiver().isBusy())

    def test10BoreholeImage(self):
        # borehole_image(request, borehole_id, start_depth_in, stop_depth_in, outimg_width, outimg_height):
        # start_depth > stop_depth, shouldn't be successfull

        self.req.method = 'GET'
        self.assertRaises(
            Exception,
            views.borehole_image,
            self.req,
            self.bh1.id,
            3,
            0,
            settings.MEASUREMENT_IMAGE_WIDTH_PX,
            3 *
            settings.MEASUREMENT_IMAGE_HEIGHT_PX)

        # image is too big

        img_size = (
            settings.MEASUREMENT_IMAGE_WIDTH_PX,
            settings.MEASUREMENT_IMAGE_HEIGHT_PX)
        Image.objects.create(
            borehole=self.bh1,
            depth_from=0,
            depth_to=500000,
            geophysical_depth=0,
            imagedata=self.imgw.getvalue())
        res = views.borehole_image(
            self.req,
            self.bh1.id,
            0,
            5000,
            settings.MEASUREMENT_IMAGE_WIDTH_PX,
            settings.MEASUREMENT_IMAGE_HEIGHT_PX)
        self.assertEqual(res.status_code, 200)
        img = Im.open(BytesIO(res.content))
        self.assertEqual(img.size, img_size)
        colors = img.getcolors()
        self.assertEqual(len(colors), 1)
        self.assertEqual(
            colors, [
                (img_size[0] * img_size[1], (255, 255, 255))])

        # get image from where there are measurements
        img_size = (
            settings.MEASUREMENT_IMAGE_WIDTH_PX,
            3 * settings.MEASUREMENT_IMAGE_HEIGHT_PX)
        res = views.borehole_image(
            self.req, self.bh1.id, 0, 3, img_size[0], img_size[1])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['content-type'], 'image/jpeg')

        img = Im.open(BytesIO(res.content))
        self.assertEqual(img.size, img_size)
        colors = img.getcolors()
        self.assertEqual(len(colors), 1)
        self.assertEqual(
            colors, [
                (img_size[0] * img_size[1], (255, 255, 255))])

        # get image where there is not measurements - should be all black
        img_size = (
            settings.MEASUREMENT_IMAGE_WIDTH_PX,
            settings.MEASUREMENT_IMAGE_HEIGHT_PX)
        res = views.borehole_image(
            self.req, self.bh1.id, 5, 6, img_size[0], img_size[1])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['content-type'], 'image/jpeg')

        img = Im.open(BytesIO(res.content))
        self.assertEqual(img.size, img_size)
        colors = img.getcolors()
        self.assertEqual(len(colors), 1)
        self.assertEqual(colors, [(img_size[0] * img_size[1], (0, 0, 0))])

    def test11BoreholeImageLarge(self):
        """test the time to generate large borehole image. The database with 3 images, but the output size is 1000"""
        #print("test commented  -- it is too long")
        Image.objects.create(
            borehole=self.bh1,
            depth_from=500,
            depth_to=10500,
            geophysical_depth=0,
            imagedata=self.imgsize.getvalue())
        self.req.method = 'GET'
        t0 = time.time()
        img_size = (100, 100)

        res = views.borehole_image(
            self.req,
            self.bh1.id,
            0,
            1000,
            img_size[0],
            img_size[1])

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['content-type'], 'image/jpeg')

        img = Im.open(BytesIO(res.content))
        self.assertEqual(img.size, img_size)
        print ("large img gen takes " + str(time.time() - t0) + " seconds")

        res = views.borehole_image(self.req, self.bh1.id, 2, 3, 0, 0)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['content-type'], 'image/jpeg')

        img = Im.open(BytesIO(res.content))
        self.assertGreater(img.size[0], 0)
        self.assertGreater(img.size[1], 0)

    def test12Archiver(self):
        archiver = images.archiver.Archiver()

        self.assertEqual(archiver.isBusy(), False)

        archOk = BytesIO()
        with zf.ZipFile(archOk, 'w') as tmp:
            tmp.writestr('1234.jpg', self.imgw.getvalue())
        archOk.seek(0)

        archTooBig = BytesIO()
        with zf.ZipFile(archTooBig, 'w') as tmp:
            tmp.writestr('23456.jpg', self.imgbig.getvalue())
        archTooBig.seek(0)

        archDupl = BytesIO()
        with zf.ZipFile(archDupl, 'w') as tmp:
            tmp.writestr('1.jpg', self.imgw.getvalue())
            tmp.writestr('1.jpg', self.imgb.getvalue())
        archDupl.seek(0)

        self.req.method = 'POST'
        self.req.FILES = dict(archive=archDupl)
        self.assertFalse(archiver.isBusy())
        archiver._reset()
        archiver.doUpload(self.req, self.bh1)
        self.assertEqual(archiver.status, ProgressStatus.DUPLICATE_ERR)

        self.req.FILES = dict(archive=archOk)
        self.assertFalse(archiver.isBusy())
        archiver._reset()
        archiver.doUpload(self.req, self.bh1)
        self.assertEqual(archiver.status, ProgressStatus.FINISHED)
        self.assertEqual(int(float(archiver.progress) /
                             float(archiver.max) * 100), 100)

        archiver._reset()
        self.assertEqual(archiver.status, ProgressStatus.OK)
        self.assertEqual(archiver.progress, 0)
        self.assertEqual(archiver.interrupted, False)

        archOk.seek(0)
        self.assertFalse(archiver.isBusy())
        archiver._reset()
        archiver.doUpload(self.req, self.bh1)
        self.assertEqual(archiver.status, ProgressStatus.INTEGRITY_ERR)

        self.req.FILES = dict(archive=archTooBig)
        archiver._reset()
        archiver.doUpload(self.req, self.bh2)
        self.assertEqual(archiver.status, ProgressStatus.FINISHED)

        self.req.FILES = dict(archive=archOk)
        archiver._reset()
        archiver.interrupted = True
        archiver.doUpload(self.req, self.bh1)
        self.assertEqual(archiver.status, ProgressStatus.OK)

        del self.req.FILES['archive']
        archiver._reset()
        archiver.doUpload(self.req, self.bh1)
        self.assertEqual(archiver.status, ProgressStatus.NO_ARCHIVE)

    def test13largeArchiveProcessing(self):
        print('Archive of 5000 large photos - commented')
        '''
        Image.objects.all().delete()
        archiver = images.archiver.Archiver()

        archMultiple = BytesIO()
        with zf.ZipFile(archMultiple, 'w') as temp:
            for i in range(settings.MAX_BOREHOLE_HEIGHT):
                temp.writestr(str(i) + '.jpg', self.imgw.getvalue())
        archMultiple.seek(0)

        archiver._reset()

        print '(line 305) Archive with %d photos' % settings.MAX_BOREHOLE_HEIGHT
        t0 = time.time()

        archiver.doUpload(RequestStr(method = 'POST', GET = {}, POST = {}, FILES=dict(archive = archMultiple)), self.bh1)
        print time.time() - t0, 'sec'

        self.assertEqual(len(Image.objects.all()), settings.MAX_BOREHOLE_HEIGHT + settings.MAX_BOREHOLE_HEIGHT // 10
                         + settings.MAX_BOREHOLE_HEIGHT // 100 + settings.MAX_BOREHOLE_HEIGHT // 1000 + 1)
        self.assertEqual(archiver.max, len(Image.objects.all()))
        self.assertEqual(len(Image.objects.extra(where=['depth_to - depth_from=1000'])), settings.MAX_BOREHOLE_HEIGHT // 10)
        self.assertEqual(len(Image.objects.extra(where=['depth_to - depth_from=10000'])), settings.MAX_BOREHOLE_HEIGHT // 100)
        self.assertEqual(len(Image.objects.extra(where=['depth_to - depth_from=100000'])), settings.MAX_BOREHOLE_HEIGHT // 1000)
        self.assertEqual(len(Image.objects.extra(where=['depth_to - depth_from=%d' % (settings.MAX_BOREHOLE_HEIGHT
                                                                                      * settings.MEASUREMENT_IMAGE_HEIGHT_CM)])),
                         1)
        '''

    def test14incompleteArchiveProcessing(self):
        Image.objects.all().delete()
        archiver = images.archiver.Archiver()
        archiver._reset()
        self.assertEqual(archiver.max, 0)

        archIncomplete = BytesIO()
        with zf.ZipFile(archIncomplete, 'w') as temp:
            for i in [
                    890,
                    892,
                    897,
                    903,
                    904,
                    905,
                    906,
                    908,
                    909,
                    910,
                    1004,
                    1100,
                    1299]:
                temp.writestr(str(i) + '.jpg', self.imgw.getvalue())
        archIncomplete.seek(0)

        self.req.method = 'POST'
        self.req.FILES = dict(archive=archIncomplete)
        archiver.doUpload(self.req, self.bh1)
        self.assertEqual(len(Image.objects.all()), 27)
        self.assertEqual(len(Image.objects.extra(
            where=['depth_to - depth_from=1000'])), 6)
        self.assertEqual(len(Image.objects.extra(
            where=['depth_to - depth_from=10000'])), 5)
        self.assertEqual(len(Image.objects.extra(
            where=['depth_to - depth_from=100000'])), 2)
        self.assertEqual(
            len(
                Image.objects.extra(
                    where=[
                        'depth_to - depth_from=%d' %
                        (settings.MAX_BOREHOLE_HEIGHT *
                         settings.MEASUREMENT_IMAGE_HEIGHT_CM)])),
            1)

    def test15calculateImgHeight(self):
        for i in range(0, 11):
            self.assertEqual(views.calculateImgHeight(i), 1)
        for i in range(11, 100):
            self.assertEqual(views.calculateImgHeight(i), 10)
        for i in range(101, 1001):
            self.assertEqual(views.calculateImgHeight(i), 100)
        for i in range(1001, settings.MAX_BOREHOLE_HEIGHT):
            self.assertEqual(views.calculateImgHeight(i), 1000)
        self.assertLessEqual(
            views.calculateImgHeight(
                settings.MAX_BOREHOLE_HEIGHT),
            settings.MAX_BOREHOLE_HEIGHT)

    def test16calculateHelpersNumber(self):
        archiver = images.archiver.Archiver()

        self.assertEqual(archiver.calculateHelpersNumber(
            [890, 892, 897, 903, 904, 905, 906, 908, 909, 910, 1004, 1100, 1299]), 14)

        self.assertEqual(
            archiver.calculateHelpersNumber(
                [
                    i for i in range(
                        settings.MAX_BOREHOLE_HEIGHT)]),
            settings.MAX_BOREHOLE_HEIGHT //
            10 +
            settings.MAX_BOREHOLE_HEIGHT //
            100 +
            settings.MAX_BOREHOLE_HEIGHT //
            1000 +
            1)

        self.assertEqual(archiver.calculateHelpersNumber([]), 0)

    def test17doRegenerate(self):
        Image.objects.all().delete()

        archiver = images.archiver.Archiver()

        archIncomplete = BytesIO()
        with zf.ZipFile(archIncomplete, 'w') as temp:
            for i in [
                    890,
                    892,
                    897,
                    903,
                    904,
                    905,
                    906,
                    908,
                    909,
                    910,
                    1004,
                    1100,
                    1299]:
                temp.writestr(str(i) + '.jpg', self.imgw.getvalue())
        archIncomplete.seek(0)

        self.req.method = 'POST'
        self.req.FILES = dict(archive=archIncomplete)
        archiver.doUpload(self.req, self.bh1)

        Image.objects.extra(where=['depth_to - depth_from>1000']).delete()
        Image.objects.create(
            borehole=self.bh1,
            depth_from=135000,
            depth_to=135100,
            geophysical_depth=135000,
            imagedata=self.imgb.getvalue())
        self.assertEqual(len(Image.objects.filter(borehole=self.bh1)), 20)

        archiver._reset()
        archiver.doRegenerate(self.req, self.bh1)
        self.assertEqual(archiver.status, ProgressStatus.FINISHED)
        self.assertEqual(archiver.max, 22)
        self.assertEqual(len(Image.objects.filter(borehole=self.bh1)), 30)
        self.assertEqual(len(Image.objects.extra(
            where=['depth_to - depth_from=1000'])), 7)
        self.assertEqual(len(Image.objects.extra(
            where=['depth_to - depth_from=10000'])), 6)
        self.assertEqual(len(Image.objects.extra(
            where=['depth_to - depth_from=100000'])), 2)
        self.assertEqual(
            len(
                Image.objects.extra(
                    where=[
                        'depth_to - depth_from=%d' %
                        (settings.MAX_BOREHOLE_HEIGHT *
                         settings.MEASUREMENT_IMAGE_HEIGHT_CM)])),
            1)

        archiver._reset()
        archiver.doRegenerate(self.req, self.bh2)
        self.assertEqual(archiver.status, ProgressStatus.FINISHED)
        self.assertEqual(archiver.max, 0)
        self.assertEqual(len(Image.objects.filter(borehole=self.bh2)), 0)

    def test18regenerationRequest(self):
        archiver = images.archiver.Archiver()
        self.req.method = 'PUT'

        self.req.read = lambda: json.dumps({'borehole_id': 3}).encode()
        self.assertRaises(Borehole.DoesNotExist, views.image, self.req)

        self.req.read = lambda: json.dumps(
            {'borehole_id': self.bh1.id}).encode()

        res = views.image(self.req)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(archiver.isBusy())
        res = views.image(self.req)
        self.assertEqual(res.status_code, 503)
        archiver.worker.join()
        self.assertEqual(len(Image.objects.filter(borehole=self.bh1)), 7)

    def test19regenerationInterrupt(self):
        archiver = images.archiver.Archiver()
        self.req.method = 'PUT'
        self.req.read = lambda: json.dumps(
            {'borehole_id': self.bh1.id}).encode()

        views.image(self.req)
        self.assertTrue(archiver.isBusy())
        archiver.interrupted = True
        archiver.worker.join()
        self.assertNotEqual(len(Image.objects.filter(borehole=self.bh1)), 7)

    def test20getArchiveProgress(self):
        archiver = images.archiver.Archiver()

        archiver.status = ProgressStatus.DUPLICATE_ERR
        archiver.progress = 10
        archiver.max = 0
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.DUPLICATE_ERR, 'progress': 0})

        archiver.status = ProgressStatus.BAD_SIZE_ERR
        archiver.progress = 1
        archiver.max = 1
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.BAD_SIZE_ERR, 'progress': 100})

        archiver.status = ProgressStatus.BAD_SIZE_ERR
        archiver.progress = -1
        archiver.max = 1
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.BAD_SIZE_ERR, 'progress': -100})

        archiver.status = ProgressStatus.BAD_SIZE_ERR
        archiver.progress = 0
        archiver.max = 1
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.BAD_SIZE_ERR, 'progress': 0})

        archiver.status = ProgressStatus.BAD_SIZE_ERR
        archiver.progress = 1
        archiver.max = -1
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.BAD_SIZE_ERR, 'progress': -100})

        archiver.status = ProgressStatus.BAD_SIZE_ERR
        archiver.progress = -1
        archiver.max = -1
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.BAD_SIZE_ERR, 'progress': 100})

        archiver.status = ProgressStatus.FINISHED
        archiver.progress = 0
        archiver.max = -1
        self.assertDictEqual(json.loads(views.getArchiveProgress(self.req).content.decode(
            'utf-8')), {'status': ProgressStatus.FINISHED, 'progress': 0})

    def test21cancel(self):
        archiver = images.archiver.Archiver()
        archiver._reset()

        self.assertFalse(archiver.interrupted)
        self.assertEqual(views.cancel(self.req).status_code, 200)
        self.assertTrue(archiver.interrupted)
