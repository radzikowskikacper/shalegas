# coding=utf-8
"""integrity testing for sweetspot server and sweetspot client (web application)"""

import sys, re, six, paramiko
import unittest
import splinter, time
from splinter import Browser
import time, psycopg2, base64
from PIL import Image as Im
from io import BytesIO

#naming for tests
TEST_BOREHOLE_NAME = "test_borehole_name"
TEST_BOREHOLE_DESC = "test_description"
TEST_BOREHOLE_LAT = 12.34567
TEST_BOREHOLE_LON = 123.45678
TEST_USERNAME = "sweetspot"
TEST_PASSWORD = "sweetspot"
TEST_PASSWORD_BAD = "bad_password"

TEST_USER_NAME = "test_user_name"
TEST_USER_FNAME = "test_user_first_name"
TEST_USER_LNAME = "test_user_last_name"

TEST_SECTION_NAME = 'test_section_name'
TEST_MEANING_NAME = 'test_meaning_name'
TEST_UNIT = 'test_unit'
TEST_DICT_VALUE = 'test_dict_value'

TEST_LONG_NAME = """test_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_name
                                            test_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_name
                                            test_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_nametest_long_name
                                            """

TEST_VALUE = 3
TEST_DEPTH_FROM = 100
TEST_DRILLING_DEPTH = 90

dbuser = ''
dbname = ''
dbpassword = ''
users_num = -1
sections_num = -1
meanings_num = -1
boreholes_num = -1
demo = False
mock_id = 9999999
web_addr = None
ssh_port = 22

#number of objects to insert into DB
test_num = 2

sshc = None

def queryDB(queries):
    if not demo:      
	con = None
	try:
	    con = psycopg2.connect("host=127.0.0.1 dbname=%s password=%s user=%s" % (dbname, dbpassword, dbuser))
	    cur = con.cursor()

	    for query in queries:
		cur.execute(query)

	    con.commit();

	except psycopg2.DatabaseError as e:
	    print('Error %s' % e)

	finally:
	    if con:
		con.close()
    else:
	global sshc
	#if not sshc:
	#    sshc = paramiko.SSHClient()
	   # sshc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    #sshc.connect(www_addr, port = ssh_port, username = 'sweetspot', password = 'VirtualBoxAntakya227')
	for i, q in enumerate(queries):
	    queries[i] = q.replace('$', '\$')
	std_stdin, ssh_stdout, ssh_stderr = sshc.exec_command('psql -d sweetspot -c "%s"' % ';'.join(queries))
	
def cleanDB():
    queryDB(["""DELETE FROM values_realmeasurement WHERE meaning_id >= %d""" % mock_id,
             'DELETE FROM dictionaries_dictionarymeasurement WHERE meaning_id >= %d' % mock_id,
             '''DELETE FROM dictionaries_dictionarymeasurement WHERE measurement_ptr_id IN
                 (SELECT id FROM measurements_measurement WHERE borehole_id >= %d)''' % mock_id,
             '''DELETE FROM images_image WHERE measurement_ptr_id IN 
                 (SELECT id FROM measurements_measurement WHERE borehole_id >= %d)''' % mock_id,
             'DELETE FROM measurements_measurement WHERE borehole_id >= %d' % mock_id,
             "DELETE FROM boreholes_borehole WHERE name LIKE '%s%%'" % TEST_BOREHOLE_NAME,
               """DELETE FROM meanings_meaningdictvalue WHERE dict_id_id IN
                   (SELECT id FROM meanings_meaningvalue WHERE name LIKE '%s%%')""" % TEST_MEANING_NAME,
               """DELETE FROM meanings_meaningdict WHERE meaningvalue_ptr_id IN
                   (SELECT id FROM meanings_meaningvalue WHERE name LIKE '%s%%')""" % TEST_MEANING_NAME,
               """DELETE FROM meanings_meaningimage WHERE meaningvalue_ptr_id IN
                   (SELECT id FROM meanings_meaningvalue WHERE name LIKE '%s%%')""" % TEST_MEANING_NAME,
               "DELETE FROM meanings_meaningvalue WHERE name LIKE '%s%%'" % TEST_MEANING_NAME,
               "DELETE FROM meanings_meaningsection WHERE  name LIKE '%s%%'" % TEST_SECTION_NAME,
               """DELETE FROM auth_user_groups WHERE user_id IN 
                   (SELECT id FROM auth_user WHERE username LIKE '%s%%')""" % TEST_USER_NAME,
               "DELETE FROM auth_user WHERE username LIKE '%s%%'" % TEST_USER_NAME])

## @brief test-cases for integrity
class TestIntegrity(unittest.TestCase):
    browser = ''
    browser2 = ''

    @classmethod
    def setUpClass(cls):
	global users_num
	global sections_num
	global meanings_num
	global boreholes_num
	
	if not demo:
	    con = None
	    try:
		con = psycopg2.connect("host=127.0.0.1 dbname=%s password=%s user=%s" % (dbname, dbpassword, dbuser))
		cur = con.cursor()

		query = 'SELECT COUNT(*) FROM auth_user'
		cur.execute(query)
		users_num = cur.fetchone()[0]

		query = 'SELECT COUNT(*) FROM meanings_meaningsection'
		cur.execute(query)
		sections_num = cur.fetchone()[0]

		query = 'SELECT COUNT(*) FROM meanings_meaningvalue'
		cur.execute(query)
		meanings_num = cur.fetchone()[0] - 4

		query = 'SELECT COUNT(*) FROM boreholes_borehole'
		cur.execute(query)
		boreholes_num = cur.fetchone()[0]
		con.commit();

	    except psycopg2.DatabaseError as e:
		print('Error %s' % e)

	    finally:
		if con:
		    con.close()
	else:
	    global sshc
	    #if not sshc:
	    sshc = paramiko.SSHClient()
	    sshc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	    sshc.connect(www_addr, port = ssh_port, username = 'sweetspot', password = 'VirtualBoxAntakya227')
	    std_stdin, ssh_stdout, ssh_stderr = sshc.exec_command('psql -d sweetspot -c "%s"' % 'SELECT COUNT(*) FROM auth_user')
	    users_num = int(ssh_stdout.read().split('\n')[2])
	    
	    std_stdin, ssh_stdout, ssh_stderr = sshc.exec_command('psql -d sweetspot -c "%s"' % 'SELECT COUNT(*) FROM meanings_meaningsection')
	    sections_num = int(ssh_stdout.read().split('\n')[2])
	    
	    std_stdin, ssh_stdout, ssh_stderr = sshc.exec_command('psql -d sweetspot -c "%s"' % 'SELECT COUNT(*) FROM meanings_meaningvalue')
	    meanings_num = int(ssh_stdout.read().split('\n')[2]) - 4
	    
	    std_stdin, ssh_stdout, ssh_stderr = sshc.exec_command('psql -d sweetspot -c "%s"' % 'SELECT COUNT(*) FROM boreholes_borehole')
	    boreholes_num = int(ssh_stdout.read().split('\n')[2])
	    
    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        cleanDB()

        try:
	    for br in [self.browser, self.browser2]:
		br.find_by_css('[ng-click="ok()"]').first.click()
		br.find_by_css('[ng-click="cancel()"]').first.click()
        except:
            pass
        
        for br in [self.browser, self.browser2]:
            self.clickMenuLink('#a_lang_en', browser=br)
            if not len(br.find_by_css('[ng-if="!logged"]')) and self.getWhenReadyCss('[ng-if="logged"]', browser=br).first.text != "Logged as " + TEST_USERNAME:
                self.clickMenuLink('[ng-click="logout()"]', browser=br)
                self.assertCondition(lambda : br.find_by_css('[ng-if="!logged"]').first.text == "Not logged")
                
            if len(br.find_by_css('[ng-if="!logged"]')):
                self.loginUser(TEST_USERNAME, TEST_PASSWORD, browser=br)
                self.assertCondition(lambda : br.find_by_css('[ng-if="logged"]').first.text == "Logged as " + TEST_USERNAME)
                br.reload()
                self.clickMenuLink('#a_lang_en', browser=br)
                self.assertCondition(lambda : len(br.find_by_css('[ng-if="logged"]')) == 1)
                self.assertCondition(lambda : br.find_by_css('[ng-if="logged"]').first.text == "Logged as " + TEST_USERNAME)
        
    def tearDown(self):
        pass

    def clickMenuLink(self, ident, interval=0.1, maxTime=5, browser=None):
        if not browser:
            browser = self.browser
            
        counter = 0
        link = None 
        
        while counter < maxTime:
            try:
                browser.find_by_css(ident).first.click()
                return
            except:
                time.sleep(interval)
                counter += interval
             
        link = browser.find_by_css(ident)
        self.assertGreaterEqual(len(link), 1, "Cannot find link with ident='{css}' in {brow}".
                         format(css=ident, brow = 'browser' if browser == self.browser else 'browser2'))   
        link.first.click()

    #simulates user's action on login
    def loginUser(self, user_name=None, password_str=None, browser = None):
        browser = browser or self.browser
        
        self.clickMenuLink('[ng-click="loginWindow()"]', browser = browser)

        browser.fill('user',user_name)
        browser.fill('password', password_str)

        #send login request
        self.clickMenuLink('[ng-click="ok()"]', browser = browser)

    def addMeaning(self, **kwargs):
        self.getWhenReadyCss('input[name=meaning_name]')

        if 'name' in kwargs:
	    if 'modif' in  kwargs:
		self.assertCondition(lambda: self.browser.find_by_name('meaning_name').value != '')
            self.browser.fill('meaning_name', kwargs['name'])
        if 'section' in kwargs:
	    def sect_condition(name):
	      for opt in self.browser.find_by_name('meaning_section').first.find_by_tag('option'):
		  if name == opt.text:
		      self.browser.select('meaning_section', opt.value)
		      return name
	    self.assertCondition(lambda: sect_condition(kwargs['section']) == kwargs['section'])

        self.assertCondition(lambda: len(self.browser.find_by_css("[ng-change='updateMeaning();']")) == 3)        
        if 'unit' in kwargs:
            self.assertCondition(lambda: self.browser.find_by_name('meaning_name').value != '')
            self.browser.choose("meaningtype", "normal")
            self.assertCondition(lambda: len(self.browser.find_by_name("meaning_unit")) == 1)
            self.browser.fill('meaning_unit', kwargs['unit'])
        elif 'dictvals' in kwargs:
            self.browser.choose("meaningtype", "dict")
            self.assertCondition(lambda: len(self.browser.find_by_css('[data-description="dict_vals"]')) == 1)
            for val in kwargs['dictvals']:
                self.browser.fill('meaning_dict_value', val)
                self.browser.find_by_css("[ng-click='addValue(newValue);']").first.click()
        else:
            self.browser.choose("meaningtype", "pict")

    def getWhenReadyCss(self, css, interval=0.1, maxTime=1, browser=None):
        if not browser:
            browser = self.browser

        counter = 0
        element = []
        while (len(element) == 0 and counter < maxTime):
            element = browser.find_by_css(css)
            time.sleep(interval)
            counter += interval

        self.assertTrue(len(element) > 0, "Element with css %s not found" % css)
        return element

    def getWhenReadyId(self, id, interval=0.1, maxTime=1, browser=None):
        if not browser:
            browser = self.browser

        counter = 0
        element = []
        while len(element) == 0 and counter < maxTime:
            element = browser.find_by_id(id)
            time.sleep(interval)
            counter += interval

        self.assertTrue(len(element) > 0, "Element with id %s not found" % id)
        return element

    def assertBoreholeListItems(self, itemsExpected, interval=0.5, maxTime=6, browser=None):
        if not browser:
            browser = self.browser

        counter = 0
        itemsFound = 0
        while itemsFound != itemsExpected and counter < maxTime:
            itemsFound = len(browser.find_by_css('table > tbody > tr'))
            time.sleep(interval)
            counter += interval

        self.assertTrue(itemsFound == itemsExpected, "Borehole list items failure. Expected: %d, Found: %d" % (itemsExpected, itemsFound))

    def assertCondition(self, functor, interval=0.1, maxTime=10):
        counter = 0
        
        while counter < maxTime:
            try:
		if functor():
		    return
	    except:
		pass
	    finally:
		time.sleep(interval)
		counter += interval
            
        self.assertTrue(functor())



    def test01AnyAnswer(self):
        """tests if the application is loaded"""
        self.assertTrue(len(self.browser.html) > 0)

    def test02ProperTitleAndLogo(self):
        """tests if the web page title and logo is correct"""
        title = self.browser.title
        if not isinstance(title, str):
            title = title.decode()
            
        self.assertEqual(title, 'SweetSpot')
        self.assertEqual(len(self.browser.find_by_id('logo')), 1 )

    def test03LoginLogout(self):
        #to be sure that user is not logged in
        self.clickMenuLink('[ng-click="logout()"]')
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")

        self.loginUser(TEST_USERNAME, TEST_PASSWORD)
        self.assertEqual(self.browser.find_by_css('[ng-if="logged"]').first.text, "Logged as " + TEST_USERNAME)
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="logged"]').first.text == "Logged as " + TEST_USERNAME)
        
        self.clickMenuLink('[ng-click="logout()"]')
        self.assertCondition(lambda : len(self.browser.find_by_css('[ng-if="!logged"]')))
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")

        self.loginUser(TEST_USERNAME, TEST_PASSWORD_BAD)
        self.assertEquals(self.getWhenReadyCss('.modal-body p', interval=0.3, maxTime=3).first.value,
                          'User or password is incorrect')
        self.clickMenuLink('[ng-click="ok()"]')
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")

        self.loginUser(TEST_USERNAME, TEST_PASSWORD)
        self.assertEqual(self.browser.find_by_css('[ng-if="logged"]').first.text, "Logged as " + TEST_USERNAME)
        
        self.loginUser(TEST_USERNAME, TEST_PASSWORD, self.browser2)
        self.assertEqual(self.browser2.find_by_css('[ng-if="logged"]').first.text, "Logged as " + TEST_USERNAME)
        
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.browser2.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser2)
	  
	for brow in [self.browser, self.browser2]:
	    self.getWhenReadyCss('[ng-if="logged"]', browser = brow)
	    self.assertCondition(lambda: self.browser.find_by_css('[ng-if="logged"]').first.text == "Logged as " + TEST_USERNAME)

    def test04TabTranslations(self):
        """test if translations works"""

        self.clickMenuLink('#a_lang_en')
        self.assertEqual(self.getWhenReadyId("menuData").first.text, "Data" )
        self.assertEqual(self.browser.find_by_id("menuManagement").first.text, "Management" )
        self.assertEqual(self.browser.find_by_id("menuAbout").first.text, "About" )

        self.clickMenuLink('#a_lang_pl')
        self.assertCondition(lambda : self.getWhenReadyId("menuData").first.text == "Dane" )
        self.assertEqual(self.browser.find_by_id("menuManagement").first.text, u"Zarządzanie" )
        self.assertEqual(self.browser.find_by_id("menuAbout").first.text, "O systemie" )

    def test05About(self):
        self.clickMenuLink('#aAbout')

        server_time = self.getWhenReadyId('server_time_val').first.text
        self.assertTrue(len(server_time) > 0)
        self.assertTrue(len(self.browser.find_by_id('server_version_val').first.text) > 0)
        self.assertTrue(len(self.browser.find_by_id('db_version_val').first.text) > 0)
        self.assertTrue(len(self.browser.find_by_id('client_version_val').first.text) > 0)

        server_time_after = server_time
        counter = 0
        while server_time_after == server_time and counter < 10:
            server_time_after = self.browser.find_by_id('server_time_val').first.text
            time.sleep(1)
            counter += 1

        self.assertNotEqual(server_time, server_time_after)
    
    def test06NewBoreholeUpdate(self):
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('#aBoreholes', self.browser2)

        for i in range(test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == boreholes_num + i)
            self.clickMenuLink('[ng-click="toggleBoreholeAdding();"]')
            self.getWhenReadyCss('.new_bh_name').fill(TEST_BOREHOLE_NAME + str(i))
            self.browser.find_by_css('.new_bh_latitude input').fill(str(TEST_BOREHOLE_LAT + i))
            self.browser.find_by_css('.new_bh_longitude input').fill(str(TEST_BOREHOLE_LON + i))
            self.browser.find_by_css('textarea.new_bh_description').fill(TEST_BOREHOLE_DESC + str(i))

            #send newBorehole request
            self.clickMenuLink('[ng-click="addBorehole(newBorehole)"]')

        self.assertBoreholeListItems(boreholes_num + test_num)
        self.assertBoreholeListItems(boreholes_num + test_num, browser = self.browser2)

        found = 0
        bholes = self.browser.find_by_css('table > tbody > tr > td')
        for i in range(0, len(bholes), 7):
            if self.browser.find_by_css('table > tbody > tr > td')[i].value in [TEST_BOREHOLE_NAME + str(j) for j in range(test_num)]:
                found = found + 1
                self.assertCondition(lambda : self.browser.find_by_css('table > tbody > tr > td')[i + 5].value in [TEST_BOREHOLE_DESC + str(j) for j in range(test_num)])
        self.assertEqual(found, test_num)
    
    def test07DeleteBoreholeUpdate(self):
        queryDB(["""INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)])])
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('#aBoreholes', self.browser2)
        self.browser.reload()
        self.clickMenuLink('#a_lang_en')

        for i in range(mock_id, mock_id + test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css('tbody tr')) == boreholes_num + test_num + mock_id - i)
            self.clickMenuLink('tbody tr[data-id="{}"] .remove-borehole-btn'.format(i))

        for b in [self.browser, self.browser2]:
            self.assertBoreholeListItems(boreholes_num, browser=b)
            for i in range(mock_id, mock_id + test_num):
                self.assertCondition(lambda : len(b.find_by_css('[data-id="%d"]' % i)) == 0)

    def test08ModifyBoreholeUpdate(self):
        queryDB(["""INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)])])

        self.clickMenuLink('#aBoreholes')
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('tr[data-id="%d"] td button[ss-modify]' % mock_id)

        #modify field
        self.getWhenReadyCss('input.new_bh_name').first.fill(TEST_BOREHOLE_NAME + '_modified')

        #click OK to save
        self.clickMenuLink("[ng-click='modifyBorehole(borehole_copy)']")

	def temp(brow):
            found = 0
            bholes = brow.find_by_css('table > tbody > tr > td')
            for i in range(0, len(bholes), 7):
                if bholes[i].value == TEST_BOREHOLE_NAME + '_modified':
                    found = found + 1
            return found

        for brow in [self.browser, self.browser2]:
            self.assertBoreholeListItems(boreholes_num + test_num, browser=brow)
            self.assertCondition(lambda: temp(brow) == 1)

        self.assertEqual(self.browser.find_by_css('[data-id="%d"] td' % mock_id)[0].value, TEST_BOREHOLE_NAME + '_modified')
        for i in range(mock_id+1, mock_id + test_num):
            self.assertEqual(len(self.browser.find_by_css('[data-id="%d"]' % i)), 1)

    def test09Map(self):
        btnmap = self.browser.find_by_css('[href="#/map"]')
        self.assertGreater(len(btnmap), 0)

        btnmap.first.click()

    def test10userProfile(self):
        #navigate to profile tab
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('[data-page="Settings"]')
        usname_field = self.getWhenReadyId('username')
        self.assertCondition(lambda : len(usname_field) == 1)
        self.assertCondition(lambda : usname_field.first.value == 'sweetspot')

    def test11managementList(self):
        queryDB(["INSERT INTO auth_user VALUES " +
                       ",".join(["""({id}, '{password}', '2014-05-06 15:51:56.493655+02', '0', '{login}', '{fname}',
                                   '{lname}', 'test@gmail.com', '0', '1', '2014-05-06 15:51:56.493655+02')"""
                                                             .format(id=i + mock_id,
                                                             login=TEST_USER_NAME + str(i),
                                                             fname=TEST_USER_FNAME + str(i),
                                                             lname=TEST_USER_LNAME + str(i),
                                                             password=TEST_PASSWORD + str(i))
                                                             for i in range(test_num)])])

        self.clickMenuLink('#aManagement')
        self.assertCondition(lambda : len(self.browser.find_by_css('#management-table > tbody > tr')) == users_num + test_num)
	
        self.clickMenuLink('[data-id="%d"]' % mock_id)
        self.assertCondition(lambda : self.browser.find_by_id('username').first.value == TEST_USER_NAME + str(0))

    def test12deleteUser(self):
        queryDB(["INSERT INTO auth_user VALUES " +
                       ",".join(["""({id}, '{password}', '2014-05-06 15:51:56.493655+02', '0', '{login}', '{fname}',
                                   '{lname}', 'test@gmail.com', '0', '1', '2014-05-06 15:51:56.493655+02')"""
                                                             .format(id=i + mock_id,
                                                             login=TEST_USER_NAME + str(i),
                                                             fname=TEST_USER_FNAME + str(i),
                                                             lname=TEST_USER_LNAME + str(i),
                                                             password=TEST_PASSWORD + str(i))
                                                             for i in range(test_num)])])
        # navigate to users list
        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[data-id="%d"]' % mock_id)
	self.assertCondition(lambda: self.browser.find_by_css('input[name=new_first_name]').value == TEST_USER_FNAME + '0')
        self.clickMenuLink('#delete-user-btn')

        # confirm
        self.clickMenuLink('[ng-click="ok()"]')

        # go back to user list
        self.clickMenuLink('#aManagement')

        # check if the users count is as assumed
        self.assertCondition(lambda : len(self.browser.find_by_css('#management-table > tbody > tr'))
                             == users_num + test_num - 1)

    def test13modifyPersonalData(self):
        queryDB(["INSERT INTO auth_user VALUES " +
                       ",".join(["""({id}, '{password}', '2014-05-06 15:51:56.493655+02', '0', '{login}', '{fname}',
                                   '{lname}', 'test@gmail.com', '0', '1', '2014-05-06 15:51:56.493655+02')"""
                                                             .format(id=i + mock_id,
                                                             login=TEST_USER_NAME + str(i),
                                                             fname=TEST_USER_FNAME + str(i),
                                                             lname=TEST_USER_LNAME + str(i),
                                                             password='pbkdf2_sha256$15000$52JbpISi3vg4$jphqFOfhztWlS5tXdvKt5gcrpwONY72V6FcAUynzUog=')
                                                             for i in range(test_num)]),
                 "INSERT INTO auth_user_groups VALUES " +
                        ",".join(["(%d, %d, %d)" % (i + mock_id, mock_id + i, 2) for i in range(2)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(1)])])

        # navigate to users list
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aManagement')
        self.clickMenuLink('tr[data-id="%d"]' % (mock_id + 1))
        self.clickMenuLink('#modify-user-btn')

        self.getWhenReadyCss('input[name=new_first_name]')
	self.assertCondition(lambda: self.browser.find_by_css('input[name=new_first_name]').value == TEST_USER_FNAME + '1')
        self.browser.fill('new_first_name', TEST_USER_FNAME + '_modified')
        self.getWhenReadyCss('input[type=checkbox]').click()
        self.clickMenuLink('#save-personal-data-btn')

        self.assertCondition(lambda : self.browser.find_by_name('new_first_name').value == TEST_USER_FNAME + '_modified')

        self.clickMenuLink('#aManagement')

        self.assertCondition(lambda : self.browser.find_by_css('[data-id="%d"] td' % (mock_id + 1))[1].value == TEST_USER_FNAME + '_modified')
        self.assertCondition(lambda : len(self.browser.find_by_css('#management-table > tbody > tr')) == users_num + test_num)

        for i in [0]:#range(test_num):
            self.clickMenuLink('[data-id="%d"]' % (mock_id + i))
	    self.assertCondition(lambda: self.browser.find_by_css('input[name=new_first_name]').value == TEST_USER_FNAME + '0')
            self.clickMenuLink('#delete-user-btn')
            self.assertCondition(lambda: len(self.browser.find_by_css('[ng-click="ok()"]')) == 1)
            self.clickMenuLink('[ng-click="ok()"]')
            self.assertCondition(lambda: len(self.browser.find_by_css('[ng-click="ok()"]')) == 0)
            self.clickMenuLink('#aManagement')

        self.assertCondition(lambda : len(self.browser.find_by_css('#management-table > tbody > tr')) == users_num + 1)
        
        self.clickMenuLink('[ng-click="logout()"]')
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")
        self.loginUser(TEST_USER_NAME+'1', TEST_PASSWORD)        
        time.sleep(15)
        self.assertCondition(lambda: self.browser.find_by_css('[ng-if="logged"]').first.text == "Logged as " + TEST_USER_NAME+'1')
        self.browser.reload()
        self.clickMenuLink('#a_lang_en')
        self.assertEqual(self.browser.find_by_css('[ng-if="logged"]').first.text, "Logged as " + TEST_USER_NAME+'1')

        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('#a_lang_en')

        self.clickMenuLink('tbody tr[data-id="{}"] .remove-borehole-btn'.format(mock_id))

        self.assertCondition(lambda : len(self.browser.find_by_css('tbody tr')) == boreholes_num)

        self.clickMenuLink('[ng-click="logout()"]')
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")

    def test14addSection(self):
        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.sections"]')

        def addSection(name):
            self.clickMenuLink('[ng-click="toggleAddition();"]')
            self.getWhenReadyCss('input[name=sect_name]')
            self.browser.fill('sect_name', name)
            self.clickMenuLink('[ng-click="addSection(newSection);"]')
        """
        for i in ['', TEST_LONG_NAME]:
            addSection(i)
            self.assertEquals(self.browser.find_by_css('.modal-body').first.find_by_tag('p').first.value, 'Browser sent incorrect request' if i == '' else 'field_name_too_long')
            self.clickMenuLink('[ng-click="ok()"]')
            time.sleep(0.3)
            self.clickMenuLink('[ng-click="toggleAddition();"]')
        """
        for i in range(test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                             == sections_num + i);
            addSection(TEST_SECTION_NAME + str(i))

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                             == sections_num + test_num);
        addSection(TEST_SECTION_NAME + str(0))
        self.assertCondition(lambda : self.browser.find_by_css('.modal-body').first.find_by_tag('p').first.value
                             == 'section_exists')
        self.clickMenuLink('[ng-click="ok()"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                             == sections_num + test_num);
        for i in range(test_num):
            self.assertEqual(len(self.browser.find_by_css('[data-id="%s"]' % (TEST_SECTION_NAME + str(i)))), 1)

    def test15modifySection(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i)) for i in range(test_num)])])

        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.sections"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == sections_num + test_num)

        self.clickMenuLink('[data-id="%s"] td' % (TEST_SECTION_NAME + str(0)))

        self.clickMenuLink('[ng-click="toggleSectionEdit();"]')

        self.assertCondition(lambda : self.browser.find_by_css('.modal-body').first.find_by_tag('p').first.value
                             == 'Modification may result in lack of translation')
        self.clickMenuLink('[ng-click="ok()"]')

        self.getWhenReadyCss('input[name=sect_name]')
        self.browser.fill('sect_name', TEST_SECTION_NAME + '_modified')
        self.clickMenuLink('[ng-click="modifySection(name)"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == sections_num + test_num)
        for i in range(1, test_num):
            self.assertEqual(len(self.browser.find_by_css('[data-id="%s"]' % (TEST_SECTION_NAME + str(i)))), 1)
        self.assertEqual(len(self.browser.find_by_css('[data-id="%s"]' % (TEST_SECTION_NAME + '_modified'))), 1)

    def test16deleteSection(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i)) for i in range(test_num)])])

        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.sections"]')

        for i in range(test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == sections_num + test_num - i)
            self.clickMenuLink("[data-id='%s'] td button" % (TEST_SECTION_NAME + str(i)))
            
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == sections_num);
        for i in range(test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css("[data-id='%s']" % (TEST_SECTION_NAME + str(i))))
                                 == 0)

    def test17addMeaning(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i)) for i in range(test_num)])])

        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.meanings"]')

        for i in range(test_num):
            for j in range(test_num):
                self.getWhenReadyCss('[ng-if="!additionForm"]')
                self.clickMenuLink('[ng-click="toggleAddition();"]')
                self.addMeaning(**{'name' : TEST_MEANING_NAME + str(j), 'section' : TEST_SECTION_NAME + str(i),
                              'unit' : '' if j else TEST_UNIT + str(j)})
                self.clickMenuLink('[ng-click="addMeaning(newMeaning);"]')

        self.getWhenReadyCss('[ng-if="!additionForm"]')
        self.clickMenuLink('[ng-click="toggleAddition();"]')

        self.addMeaning(**{'name' : TEST_MEANING_NAME + str(0), 'section' : TEST_SECTION_NAME + str(0), 'unit' : ''})
        self.clickMenuLink('[ng-click="addMeaning(newMeaning);"]')
        self.assertCondition(lambda : self.browser.find_by_css('.modal-body').first.find_by_tag('p').first.value 
                             == 'Meaning already exists')
        self.clickMenuLink('[ng-click="ok()"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                        == meanings_num + sections_num + (test_num + 1) * test_num);
                        
        sects = self.browser.find_by_css('table > tbody > tr > td')
        found = 0
        for i in range(0, len(sects), 3):
            if sects[i].value in [TEST_MEANING_NAME + str(j) for j in range(test_num)]:
                found = found + 1
                self.assertTrue(sects[i + 1].value in [TEST_UNIT + str(0), ''])
        self.assertEqual(found, test_num * test_num)

    def test18addDictMeaning(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i)) for i in range(test_num)])])

        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.meanings"]')

        for i in range(test_num):
            for j in range(test_num):
                self.getWhenReadyCss('[ng-if="!additionForm"]')
                self.clickMenuLink('[ng-click="toggleAddition();"]')

                self.addMeaning(**{'name' : TEST_MEANING_NAME + str(j), 'section' : TEST_SECTION_NAME + str(i),
                              'dictvals' : [TEST_DICT_VALUE]})
                self.clickMenuLink('[ng-click="addMeaning(newMeaning);"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                         == meanings_num + sections_num + (test_num + 1) * test_num)
        
        sects = self.browser.find_by_css('table > tbody > tr > td')
        found = 0
        for i in range(0, len(sects), 3):
            if sects[i].value in [TEST_MEANING_NAME + str(j) for j in range(test_num)]:
                found = found + 1
                self.assertEquals(sects[i + 1].value, 'Dictionary')
        self.assertEqual(found, test_num * test_num)
    
    def test19modifyMeaning(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', 'DICT', '{sec}')".format(id = i + mock_id + test_num,
                                                                        name = TEST_MEANING_NAME + str(i),
                                                                        sec = TEST_SECTION_NAME + str(1))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdict VALUES " + ",".join(["(%d)" % (i + mock_id + test_num)
                                                                        for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdictvalue(dict_id_id, value) VALUES " +
                 ",".join(["({did}, '{val}')".format(did = i + mock_id + test_num, val = TEST_DICT_VALUE + str(j))
                           for j in range(test_num) for i in range(test_num)])])
        self.browser.reload()
        self.clickMenuLink('#a_lang_en')
        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.meanings"]')

        self.clickMenuLink("[data-id='%d'] td" % (mock_id + test_num))
        self.clickMenuLink('[ng-click="toggleMeaningEdit();"]')
        self.getWhenReadyCss('[ng-if="editMode"]')
        self.addMeaning(**{'unit' : TEST_UNIT + '_modified', 'modif' : True})
        self.clickMenuLink('[ng-click="modifyMeaning(meaning)"]')

        self.getWhenReadyCss('[ng-if="!additionForm"]')

        found = 0
        fields = self.browser.find_by_css('table > tbody > tr > td')
        for i in range(1, len(fields), 3):
            if fields[i].value == TEST_UNIT + '_modified':
                found = 1
        self.assertEqual(found, 1)

        self.clickMenuLink("[data-id='%d'] td" % mock_id)
        self.clickMenuLink('[ng-click="toggleMeaningEdit();"]')
        self.getWhenReadyCss('[ng-if="editMode"]')
        self.addMeaning(**{'name' : TEST_MEANING_NAME + '_modified', 'dictvals' : [TEST_DICT_VALUE], 'modif' : True})
        self.clickMenuLink('[ng-click="modifyMeaning(meaning)"]')
        
        self.getWhenReadyCss('[ng-if="!additionForm"]')

        def meaning_cond(name):
	    fields = self.browser.find_by_css('table > tbody > tr > td')	  
	    for i in range(0, len(fields), 3):
		if fields[i].value == name:
		    self.assertEqual(fields[i + 1].value, 'Dictionary')
		    return 1
        self.assertCondition(lambda: meaning_cond(TEST_MEANING_NAME + '_modified'), 1)
        
        self.clickMenuLink("[data-id='%d'] td" % (mock_id + 1))
        self.clickMenuLink('[ng-click="toggleMeaningEdit();"]')
        self.getWhenReadyCss('[ng-if="editMode"]')
        self.addMeaning(**{'name' : TEST_MEANING_NAME + 'TEST', 'modif' : True})
        self.clickMenuLink('[ng-click="modifyMeaning(meaning)"]')
        
        self.getWhenReadyCss('[ng-if="!additionForm"]')

        found = 0
        fields = self.browser.find_by_css('table > tbody > tr > td')
        for i in range(0, len(fields), 3):
            if fields[i].value == TEST_MEANING_NAME + 'TEST':
                found = 1
                self.assertEqual(fields[i + 1].value, 'Picture')
        self.assertEqual(found, 1)

    def test20deleteMeaning(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', 'DICT', '{sec}')".format(id = i + mock_id + test_num,
                                                                        name = TEST_MEANING_NAME + str(i),
                                                                        sec = TEST_SECTION_NAME + str(1))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', 'PICT', '{sec}')".format(id = i + mock_id + test_num*2,
                                                                        name = TEST_MEANING_NAME + str(i + test_num),
                                                                        sec = TEST_SECTION_NAME + str(1))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdict VALUES " + ",".join(["(%d)" % (i + mock_id + test_num)
                                                                        for i in range(test_num)]),
                 "INSERT INTO meanings_meaningIMAGE VALUES " + ",".join(["(%d)" % (i + mock_id + test_num*2)
                                                                        for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdictvalue(dict_id_id, value) VALUES " +
                 ",".join(["({did}, '{val}')".format(did = i + mock_id + test_num, val = TEST_DICT_VALUE + str(j))
                           for j in range(test_num) for i in range(test_num)])])

        self.browser.reload()
        self.clickMenuLink('#a_lang_en')
        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.meanings"]')

        for i in range(mock_id, mock_id + 3 * test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                          == meanings_num + sections_num + 2 + 3 * test_num + mock_id - i);
            self.clickMenuLink("[data-id='%d'] td button" % i)
            
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == 
                             meanings_num + sections_num + test_num)

    def test21addValue(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)])])
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.measurements"]')
        self.clickMenuLink('[ng-model="filters.mon"]')
        
        for i in range(test_num):
            self.assertCondition(lambda : self.browser.find_by_css('[ng-model="newValue.depth_from"]').first.value == '')
            self.browser.find_by_css('[ng-model="newValue.depth_from"]').first.fill(TEST_DRILLING_DEPTH + i)
            self.assertCondition(lambda : len(self.browser.find_by_name('new_meaning').first.find_by_tag('option')) > 5)            
            for opt in self.browser.find_by_name('new_meaning').first.find_by_tag('option'):
                if (TEST_MEANING_NAME + '0') == opt.text:
                    opt.click()
                    break
            self.browser.find_by_css('[ng-model="newValue.value"]').first.fill(TEST_VALUE + i)


            self.clickMenuLink('[ng-click="addValue(newValue);"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == test_num)

        self.clickMenuLink('[ng-model="filters.mon"]')        
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == 0)
        
        self.clickMenuLink('[ng-model="filters.mon"]')
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == test_num)

        vals = self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"] > td')
        found = 0
        for i in range(2, len(vals), 6):
            if vals[i].value == TEST_MEANING_NAME + '0':
                found = found + 1
                self.assertTrue(vals[i + 1].value in [str(TEST_VALUE), str(TEST_VALUE + 1)])
                self.assertTrue(vals[i - 2].value in [str(TEST_DRILLING_DEPTH), str(TEST_DRILLING_DEPTH + 1)])
                self.assertEqual(vals[i + 2].value, TEST_UNIT + '0')
        self.assertEqual(found, test_num)

        self.clickMenuLink('[ng-model="filters.mon"]')
        self.clickMenuLink("input[id='%s']" % (TEST_SECTION_NAME + '0'))

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == test_num)
        
        self.clickMenuLink("input[id='%s']" % (TEST_SECTION_NAME + '0'))
        self.clickMenuLink("div[data-id='%s'] > div" % (TEST_SECTION_NAME + '0'))
        self.clickMenuLink("input[data-id='%d']" % mock_id)

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == test_num)

        self.clickMenuLink('[ng-model="filters.mon"]')
        
        self.browser.evaluate_script("window.scrollTo(0, 0);")
        self.getWhenReadyCss('[ng-click="setImageDepth()"]')[1].click()
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == 0)
        
        self.clickMenuLink("[ng-click='zoomOut();']")
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == test_num)
        
        for i in range(3):
            self.clickMenuLink('[ng-click="setImageDepth()"]')
            
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in real_measurements | limitTo:limit"]'))
                              == test_num)

    def test22deleteValue(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, {a}, {df}, {dt}, {dd})'.format(a = mock_id, id = i + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + mock_id, val = TEST_VALUE, mid = mock_id)
                            for i in range(test_num)])])

        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.measurements"]')
        self.clickMenuLink('[ng-model="filters.mon"]')
        
        for i in range(mock_id, mock_id + test_num):
            self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) - 3 == test_num + mock_id - i)
            self.clickMenuLink("[data-id='%d'] td button" % i)
            
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) - 3 == 0)

    def test23addDictionary(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', 'DICT', '{sec}')".format(id = i + mock_id + test_num,
                                                                        name = TEST_MEANING_NAME + str(i),
                                                                        sec = TEST_SECTION_NAME + str(1))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdict VALUES " + ",".join(["(%d)" % (i + mock_id + test_num)
                                                                        for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdictvalue(dict_id_id, value) VALUES " +
                 ",".join(["({did}, '{val}')".format(did = i + mock_id + test_num, val = TEST_DICT_VALUE + str(j))
                           for j in range(test_num) for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)])])
    
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.measurements"]')
        self.clickMenuLink('[ng-model="filters.mon"]')

        self.assertCondition(lambda : len(self.browser.find_by_name('new_dict_meaning').first.find_by_tag('option')) >= test_num)
        
        for i in range(test_num):
            self.assertCondition(lambda : self.browser.find_by_css('[ng-model="newDictionary.depth_from"]').first.value == '')
            self.browser.find_by_css('[ng-model="newDictionary.depth_from"]').first.fill(TEST_DRILLING_DEPTH + i)

            for opt in self.browser.find_by_name('new_dict_meaning').first.find_by_tag('option'):
                if (TEST_MEANING_NAME + '0') == opt.text:
                    opt.click()
                    break
                
            self.assertCondition(lambda : len(self.browser.find_by_name('new_dict_value').first.find_by_tag('option')) == test_num + 1)
            for opt in self.browser.find_by_name('new_dict_value').first.find_by_tag('option'):
                if (TEST_DICT_VALUE + str(i)) == opt.text:
                    opt.click()
                    break

            self.clickMenuLink('[ng-click="addDictionary(newDictionary);"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]'))
                              == test_num)
        
        vals = self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"] > td')
        found = 0
        for i in range(2, len(vals), 6):
            if vals[i].value == TEST_MEANING_NAME + '0':
                found = found + 1
                self.assertTrue(vals[i + 1].value in [TEST_DICT_VALUE + '0', TEST_DICT_VALUE + '1'])
                self.assertTrue(vals[i - 2].value in [str(TEST_DRILLING_DEPTH), str(TEST_DRILLING_DEPTH + 1)])
                self.assertEqual(vals[i + 2].value, 'Dictionary')
        self.assertEqual(found, test_num)
        
        self.clickMenuLink('[ng-model="filters.mon"]')
        self.clickMenuLink("input[id='%s']" % (TEST_SECTION_NAME + '1'))

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]'))
                              == test_num)

        self.clickMenuLink("input[id='%s']" % (TEST_SECTION_NAME + '1'))
        self.clickMenuLink("div[data-id='%s'] > div" % (TEST_SECTION_NAME + '1'))
        self.clickMenuLink("input[data-id='%d']" % (mock_id + test_num))

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]'))
                              == test_num)

        self.clickMenuLink('[ng-model="filters.mon"]')

        self.browser.evaluate_script("window.scrollTo(0, 0);")
        self.getWhenReadyCss('[ng-click="setImageDepth()"]')[1].click()
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]'))
                              == 0)
        
        self.clickMenuLink("[ng-click='zoomOut();']")
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]'))
                              == test_num)
        
        for i in range(3):
            self.clickMenuLink('[ng-click="setImageDepth()"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]'))
                              == test_num)

    def test24deleteDictionary(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', 'DICT', '{sec}')".format(id = i + mock_id + test_num,
                                                                        name = TEST_MEANING_NAME + str(i),
                                                                        sec = TEST_SECTION_NAME + str(1))
                           for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdict VALUES " + ",".join(["(%d)" % (i + mock_id + test_num)
                                                                        for i in range(test_num)]),
                 "INSERT INTO meanings_meaningdictvalue(id, dict_id_id, value) VALUES " +
                 ",".join(["({id}, {did}, '{val}')".format(id = mock_id + 2 * j + i, did = i + mock_id + test_num, val = TEST_DICT_VALUE + str(j))
                           for j in range(test_num) for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, {a}, {df}, {dt}, {dd})'.format(a = mock_id, id = i + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO dictionaries_dictionarymeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + mock_id, val = i + mock_id, mid = mock_id + test_num)
                            for i in range(test_num)])])
        
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.measurements"]')
        self.clickMenuLink('[ng-model="filters.mon"]')
        
        for i in range(mock_id, mock_id + test_num):            
            self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]')) == test_num + mock_id - i, maxTime=2)
            self.clickMenuLink("tr[data-id='%d'] td button" % i)
        self.assertCondition(lambda : len(self.browser.find_by_css('table tr[ng-repeat="v in dictionary_measurements | limitTo:limit"]')) == 0)

    def test25csvModal(self):
        queryDB(["""INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)])
                 ])
        
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.importexport"]')
        self.getWhenReadyCss('button[ng-click="showCsvModal(borehole_id, archive.path)"]').click()
        
        self.clickMenuLink('[ng-click="cancel()"]')

    def test26similarities(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, {a}, {df}, {dt}, {dd})'.format(a = mock_id, id = i + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + mock_id, val = TEST_VALUE + i, mid = mock_id)
                            for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, 10000000, {df}, {dt}, {dd})'.format(id = i + test_num + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + test_num + mock_id, val = TEST_VALUE + i, mid = mock_id)
                            for i in range(test_num)])])
    
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.similarity"]')
        self.clickMenuLink('[ng-model="filters.mon"]')

        self.assertCondition(lambda: len(self.browser.find_by_tag('select').first.find_by_tag('option')) > 1)
        self.browser.find_by_tag('select').first.find_by_tag('option')[1].click()

        self.assertCondition(lambda: len(self.browser.find_by_css("div[ng-repeat='d in dictvals'] > input[type='checkbox']")) > 1)
        self.browser.find_by_css("div[ng-repeat='d in dictvals'] > input[type='checkbox']")[1].click()
        
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr[ng-repeat="(n, s) in similarities"]')) >= 1)
    
    def test27addUser(self):
        queryDB(["""INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(1)])])

        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aManagement')
        self.clickMenuLink('button[ng-click="toggleUserAddition();"]')
        
        self.getWhenReadyCss('[ng-model="user.login"]').fill(TEST_USER_NAME + '1')
        self.getWhenReadyCss('[ng-model="user.fname"]').fill(TEST_USER_FNAME + '2')
        self.getWhenReadyCss('[ng-model="user.lname"]').fill(TEST_USER_LNAME + '3')
        self.getWhenReadyCss('[ng-model="user.password"]').fill(TEST_PASSWORD + '4')
        self.getWhenReadyCss('[ng-model="user.password_test"]').fill(TEST_PASSWORD + '4')
        self.clickMenuLink('button[ng-click="addUser(newUser)"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr')) == users_num + 1)
        cells = self.browser.find_by_css('table > tbody > tr > td')
        found = 0

        for i in range(0, len(cells), 4):
            if cells[i].value == TEST_USER_NAME + '1':
                found = 1
                self.assertEqual(cells[i + 1].value, TEST_USER_FNAME + '2')
                self.assertEqual(cells[i + 2].value, TEST_USER_LNAME + '3')
        self.assertEqual(found, 1)

        self.clickMenuLink('[ng-click="logout()"]')
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")
        self.loginUser(TEST_USER_NAME+'1', TEST_PASSWORD+'4')        
        self.assertCondition(lambda: self.browser.find_by_css('[ng-if="logged"]').first.text == "Logged as " + TEST_USER_NAME+'1')
        self.browser.reload()
        self.clickMenuLink('#a_lang_en')
        self.assertEqual(self.browser.find_by_css('[ng-if="logged"]').first.text, "Logged as " + TEST_USER_NAME+'1')

        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('#a_lang_en')

        self.clickMenuLink('tbody tr[data-id="{}"] .remove-borehole-btn'.format(mock_id))

        self.assertCondition(lambda : self.browser.find_by_css('.modal-body').first.find_by_tag('p').first.value
                             == 'No permissions to modify data')
        self.clickMenuLink('[ng-click="ok()"]')

        self.clickMenuLink('[ng-click="logout()"]')
        self.assertCondition(lambda : self.browser.find_by_css('[ng-if="!logged"]').first.text == "Not logged")

    def test28help(self):
        self.browser.reload()
        self.clickMenuLink('[ui-sref="help-state"]')
        self.assertCondition(lambda : len(self.browser.find_by_css('ul > li')) > 0)

    def test29tableView(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, {a}, {df}, {dt}, {dd})'.format(a = mock_id, id = i + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + mock_id, val = TEST_VALUE + i, mid = mock_id)
                            for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, 10000000, {df}, {dt}, {dd})'.format(id = i + test_num + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + test_num + mock_id, val = TEST_VALUE + i, mid = mock_id)
                            for i in range(test_num)])])

        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.tables"]')
        
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) == 0)
        
        self.clickMenuLink('[ng-model="filters.mon"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) > 0)

        self.clickMenuLink('[ng-model="filters.mon"]')
        self.clickMenuLink("div[data-id='%s'] > div" % (TEST_SECTION_NAME + '0'))
        self.clickMenuLink("input[data-id='%d']" % mock_id)

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) > 1)
        j = 0
        for i in self.browser.find_by_css('table > thead > tr > th'):
            self.assertTrue(i.value in ['Depth', '{} [{}]'.format(TEST_MEANING_NAME + '0', TEST_UNIT + '0')])
            j += 1
        self.assertEqual(j, 2)
    
    def test30addStratigraphy(self):
        queryDB(["""INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)])])
        
        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aBoreholes')
        self.clickMenuLink('tr[data-id="%d"] td' % mock_id)
        self.clickMenuLink('[ui-sref="borehole-details-state.stratigraphy"]')
        
        for i in range(test_num):
            self.assertCondition(lambda : self.browser.find_by_css('[ng-model="newDictionary.depth_from"]').first.value == '')
            self.browser.find_by_css('[ng-model="newDictionary.depth_from"]').first.fill(TEST_DRILLING_DEPTH + i)
            self.browser.find_by_css('[ng-model="newDictionary.depth_to"]').first.fill(TEST_DRILLING_DEPTH + i)

            for j in range(4):
                self.assertCondition(lambda : len(self.browser.find_by_tag('select')[j].find_by_tag('option')) > 0)
                self.browser.find_by_tag('select')[j].find_by_tag('option')[1].click()
            
            self.clickMenuLink("[ng-click='addStratigraphy(newDictionary);']")
            self.assertCondition(lambda : len(self.browser.find_by_css('table >tbody >tr')) == i + 2)
            
        index = 0
        for i in self.browser.find_by_css('table > tbody > tr'):
            if not index:
                continue
            self.assertCondition(lambda : i.find_by_css('td').value == ("%d" % TEST_DRILLING_DEPTH + index))
            index += 1

    def test31addPictMeaning(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i)) for i in range(test_num)])])

        self.clickMenuLink('#aManagement')
        self.clickMenuLink('[ui-sref="management-state.meanings"]')

        for i in range(test_num):
            for j in range(test_num):
                self.getWhenReadyCss('[ng-if="!additionForm"]')
                self.clickMenuLink('[ng-click="toggleAddition();"]')
                self.addMeaning(**{'name' : TEST_MEANING_NAME + str(j), 'section' : TEST_SECTION_NAME + str(i)})
                self.clickMenuLink('[ng-click="addMeaning(newMeaning);"]')

        self.getWhenReadyCss('[ng-if="!additionForm"]')
        self.clickMenuLink('[ng-click="toggleAddition();"]')

        self.addMeaning(**{'name' : TEST_MEANING_NAME + str(0), 'section' : TEST_SECTION_NAME + str(0)})
        self.clickMenuLink('[ng-click="addMeaning(newMeaning);"]')
        self.assertCondition(lambda : self.browser.find_by_css('.modal-body').first.find_by_tag('p').first.value 
                             == 'Meaning already exists')
        self.clickMenuLink('[ng-click="ok()"]')

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr'))
                        == meanings_num + sections_num + (test_num + 1) * test_num);
                        
        sects = self.browser.find_by_css('table > tbody > tr > td')
        found = 0
        for i in range(0, len(sects), 3):
            if sects[i].value in [TEST_MEANING_NAME + str(j) for j in range(test_num)]:
                found = found + 1
                self.assertCondition(lambda : sects[i + 1].value == 'Picture')
        self.assertEqual(found, test_num * test_num)

    def test32dataView(self):
        queryDB(["INSERT INTO meanings_meaningsection VALUES "  + ",".join(["('%s')" % (TEST_SECTION_NAME + str(i))
                                                                            for i in range(test_num)]),
                 "INSERT INTO meanings_meaningvalue VALUES " +
                 ",".join(["({id}, '{name}', '{unit}', '{sec}')".format(id = i + mock_id, name = TEST_MEANING_NAME + str(i),
                                                                        unit = TEST_UNIT + str(i),
                                                                        sec = TEST_SECTION_NAME + str(0))
                           for i in range(test_num)]),
                 """INSERT INTO boreholes_borehole(id, name, latitude, longitude, description)
                    VALUES """ + ','.join(["({id}, '{name}', {lat}, {lon}, '{desc}')"
                                           .format(id = i + mock_id, name = TEST_BOREHOLE_NAME + str(i),
                                                   lat = TEST_BOREHOLE_LAT + float(i), lon = TEST_BOREHOLE_LON + float(i),
                                                   desc = TEST_BOREHOLE_DESC + str(i))
                                           for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, {a}, {df}, {dt}, {dd})'.format(a = mock_id, id = i + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + mock_id, val = TEST_VALUE + i, mid = mock_id)
                            for i in range(test_num)]),
                 """INSERT INTO measurements_measurement VALUES """
                 + ','.join(['({id}, 10000000, {df}, {dt}, {dd})'.format(id = i + test_num + mock_id, df = TEST_DEPTH_FROM + i,
                                                                     dt = TEST_DEPTH_FROM + 1 + i,
                                                                     dd = TEST_DRILLING_DEPTH + i)
                             for i in range(test_num)]),
                 """INSERT INTO values_realmeasurement VALUES """
                 + ','.join(['({mptr}, {val}, {mid})'.format(mptr = i + test_num + mock_id, val = TEST_VALUE + i, mid = mock_id)
                            for i in range(test_num)])])

        self.browser.reload()
        self.clickMenuLink('#a_lang_en', browser=self.browser)
        self.clickMenuLink('#aData')
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) == 0)
        
        self.clickMenuLink("div[data-id='%s'] > div" % (TEST_SECTION_NAME + '0'))
        self.clickMenuLink("input[data-id='%d']" % mock_id)

        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) > 1)

        self.clickMenuLink("input[data-id='%d']" % mock_id)
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) == 0)

        self.clickMenuLink("div[data-id='%s'] > div > input" % (TEST_SECTION_NAME + '0'))
        self.assertCondition(lambda : len(self.browser.find_by_css('table > tbody > tr > td')) > 1)

    
        
if __name__ == "__main__":
    www_browser = 'firefox'
    www_addr = '127.0.0.1'
    www_port = '9000'

    if len(sys.argv) >= 7:
        www_browser = sys.argv[1]
        www_addr = sys.argv[2]
        www_port = sys.argv[3]
        dbuser = sys.argv[4]
        dbname = sys.argv[5]
        dbpassword = sys.argv[6]
	if len(sys.argv) == 8:
	    demo = True
	    ssh_port = int(sys.argv[7])

    browser, browser2 = Browser(www_browser), Browser(www_browser)
    browser.driver.maximize_window()
    browser2.driver.maximize_window()

    browser.visit('http://' + www_addr + ':' + www_port)
    browser2.visit('http://' + www_addr + ':' + www_port)
    #the order is changed, the last is top window, so the operations are visible
    TestIntegrity.browser = browser2
    TestIntegrity.browser2 = browser
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIntegrity))

    try:
        unittest.TextTestRunner(verbosity=3).run(suite)
    finally:
        cleanDB()
        if demo:
	    sshc.close()

    browser.quit()
    browser2.quit()
