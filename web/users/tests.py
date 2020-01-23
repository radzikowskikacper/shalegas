##
# @file web/users/tests.py
# @brief Unit tests for users services

import six

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User, Group
from django.db import DataError
from django.http import HttpRequest, QueryDict
import django.test
import json
from django.utils.importlib import import_module
from users.views import UsersDuplicate, PasswordMismatch

from . import views


class UsersViewTestCase(django.test.TestCase):
    '''
    Main test case for testing users
    '''

    test_username = 'sweetspot'
    test_first_name = 'sweet'
    test_last_name = 'spot'
    test_long_name = "long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name \
                        long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name \
                        long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name"

    test_password = 'sweetspot'
    test_new_password = 'sweetspot_new'

    test_description = 'test_description'

    test_users_num = 3

    def createTestUsers(self):
        '''
        inserts $self.test_users_num users into DB
        naming: test_name = self.test_name + str(i), for i e {0...$self.test_num - 1}
                test_lat = self.test_lat + i
        '''
        for i in range(self.test_users_num):
            user = User.objects.create_user(
                self.test_username + str(i), '', self.test_password + str(i))
            user.first_name = self.test_first_name + str(i)
            user.last_name = self.test_last_name + str(i)
            user.save()

    # before every test create a user, and prepare Httpself.request
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.user = User.objects.create_user(
            self.test_username, '', self.test_password)
        self.user.groups.add(Group.objects.create(name='editors'))
        self.user.groups.add(Group.objects.create(name='viewers'))
        self.request = HttpRequest()
        self.engine = import_module(settings.SESSION_ENGINE)
        self.session_key = None

    def login(self, user, passw, userobj=None):
        '''
        loggin in as a pair (user, passw)
        '''
        params = {'login': user, 'password': passw}

        self.request.read = lambda: json.dumps(params).encode()
        self.request.method = 'POST'
        self.request.session = self.engine.SessionStore(self.session_key)
        if userobj:
            self.request.user = userobj
        return views.users(self.request, 'login')

    def logout(self, request):
        self.request.method = 'POST'
        self.request.session = self.engine.SessionStore(self.session_key)
        self.request.user = self.user
        views.users(self.request, command='logout')

    def test01logout(self):
        self.logout(self.request)

        self.assertFalse(self.request.user.is_authenticated())

    def test02login(self):
        # first make sure noone is logged in
        self.logout(self.request)

        self.assertFalse(self.request.user.is_authenticated())

        # bad login self.request
        params = {'login': self.test_username}

        self.request.read = lambda: json.dumps(params).encode()
        self.request.method = 'POST'
        self.request.session = self.engine.SessionStore(self.session_key)
        self.request.user = self.user
        self.assertRaises(KeyError, views.users, self.request, 'login')

        # incorrect login
        self.assertRaises(
            views.BadUsername,
            self.login,
            'a',
            self.test_password,
            AnonymousUser())
        self.assertFalse(self.request.user.is_authenticated())

        self.assertRaises(
            views.BadUsername,
            self.login,
            self.test_username,
            'b')
        self.assertFalse(self.request.user.is_authenticated())

        self.assertRaises(views.BadUsername, self.login, 123, 123)
        self.assertFalse(self.request.user.is_authenticated())

        resp = self.login(self.test_username, self.test_password)

        self.assertTrue(self.user.is_authenticated())
        self.assertEqual(
            json.loads(
                resp.content.decode('utf-8'))['username'],
            self.test_username)

    def test03getUsers(self):
        # create some users
        self.createTestUsers()

        # get users using views.getUsers
        users = json.loads(views.getUsers().content.decode('utf-8'))
        # users' number should be $self.test_users_num + 1 (sweetspot,
        # sweetspot)
        self.assertEqual(len(users), self.test_users_num + 1)

        # test each user
        for i in range(self.test_users_num):
            u = users[i + 1]
            self.assertEqual(u['username'], self.test_username + str(i))
            self.assertEqual(u['first_name'], self.test_first_name + str(i))
            self.assertEqual(u['last_name'], self.test_last_name + str(i))
            self.assertFalse(u['readwrite'])

        self.request.method = 'GET'
        self.request.user = self.user
        # get all users, enough to test the amount
        users = json.loads(views.users(self.request).content.decode('utf-8'))
        self.assertEqual(len(users), self.test_users_num + 1)

        # get last inserted user by id
        user = json.loads(
            views.users(
                self.request,
                self.test_users_num +
                1).content.decode('utf-8'))
        # test his properties
        self.assertEqual(user['username'],
                         self.test_username + str(self.test_users_num - 1))
        self.assertEqual(user['first_name'],
                         self.test_first_name + str(self.test_users_num - 1))
        self.assertEqual(user['last_name'],
                         self.test_last_name + str(self.test_users_num - 1))

        self.assertDictEqual(
            json.loads(
                views.users(
                    self.request,
                    1).content.decode('utf-8')),
            {
                'username': 'sweetspot',
                'id': six.text_type(1),
                'last_name': '',
                'first_name': '',
                'readwrite': True})

        # try to get nonexisting user
        self.assertRaises(
            User.DoesNotExist,
            views.users,
            self.request,
            self.test_users_num + 2)

    def test04passwordChange(self):
        self.createTestUsers()

        # first log out
        self.logout(self.request)
        self.assertFalse(self.request.user.is_authenticated())

        # prepare password change self.request
        self.request.method = 'PUT'
        self.request.session = self.engine.SessionStore(self.session_key)
        params = {'new_password': self.test_new_password}
        self.request.read = lambda: json.dumps(params)

        # log user in
        self.login(self.test_username + '0', self.test_password + '0')
        self.assertTrue(self.request.user.is_authenticated())

        self.request.method = 'PUT'
        self.assertRaises(User.DoesNotExist, views.users, self.request, 5)
        #self.assertEqual(res.content, 'no_user')

        # as there is no field 'old_password', bad self.request should be
        # returned
        self.request.read = lambda: json.dumps(params).encode()
        self.assertRaises(KeyError, views.users, self.request, 2)

        params['old_password'] = self.test_password + '_different'
        self.assertRaises(
            views.IncorrectPassword,
            views.users,
            self.request,
            2)

        # old one is correct now
        params['old_password'] = self.test_password + '0'
        res = views.users(self.request, 2)

        # so password should be changed
        self.assertTrue(
            check_password(
                self.test_new_password,
                User.objects.get(
                    id=2).password))

    def test05personalDataChange(self):
        # first log out
        self.logout(self.request)
        self.assertFalse(self.request.user.is_authenticated())

        # prepare password change self.request
        self.request.method = 'PUT'
        self.request.session = self.engine.SessionStore(self.session_key)
        params = {
            'first_name': self.test_first_name,
            'last_name': self.test_long_name,
            'description': self.test_description}
        self.request.read = lambda: json.dumps(params)

        # log user in
        self.login(self.test_username, self.test_password, AnonymousUser())
        self.assertTrue(self.request.user.is_authenticated())
        self.request.method = 'PUT'
        self.request.read = lambda: json.dumps(params).encode()

        self.assertRaises(DataError, views.users, self.request, 1)

        params['last_name'] = self.test_last_name + '_modified'
        res = json.loads(views.users(self.request, 1).content.decode('utf-8'))

        self.assertEqual(res['first_name'], self.test_first_name)
        self.assertEqual(res['last_name'], self.test_last_name + '_modified')

        self.assertFalse(
            self.request.user.groups.filter(
                name='editors').exists())

        params['readwrite'] = True
        views.users(self.request, 1)
        self.assertTrue(
            self.request.user.groups.filter(
                name='editors').exists())

        params = {}
        views.users(self.request, 1)
        self.assertFalse(
            self.request.user.groups.filter(
                name='editors').exists())

    def test05userDelete(self):
        self.createTestUsers()
        self.request.method = 'DELETE'
        self.request.user = self.user
        # delete nonexisting user
        self.assertRaises(User.DoesNotExist, views.users, self.request, 5)

        # total amount of users should still be self.test_users_num + 1
        # (sweetspot, sweetspot)
        self.assertEqual(len(User.objects.all()), self.test_users_num + 1)

        # delete user with id=4
        res = views.users(self.request, 4)
        # server should return 200 OK
        self.assertEqual(res.status_code, 200)
        # amount of users should be self.test_users_num
        self.assertEqual(len(User.objects.all()), self.test_users_num)

    def test06addUser(self):
        self.request.method = 'POST'
        self.request.user = self.user

        errortab = [TypeError, TypeError] + [KeyError for i in range(20)]
        for j, i in enumerate(['a', '5', {}, {'login': 5}, {'password': 2}, {'fname': 'a'}, {'lname': 'b'},
                               {'login': 'test_login', 'password': 'test_password'},
                               {'login': 'test_login', 'fname': 'test_fname'},
                               {'login': 'test_login', 'lname': 'test_lname'},
                               {'fname': 'test_fname', 'lname': 'test_lname'},
                               {'fname': 'test_fname', 'password': 'test_password'},
                               {'password': 'test_password', 'lname': 'test_lname'},
                               {'login': 'test_login', 'password': 'test_password', 'fname': 'test_fname'},
                               {'login': 'test_login', 'password': 'test_password', 'lname': 'test_lname'},
                               {'login': 'test_login', 'fname': 'test_fname', 'lname': 'test_lname'},
                               {'password': 'test_password', 'lname': 'test_lname', 'fname': 'test_fname'}]):

            self.request.read = lambda: json.dumps(i).encode()
            self.assertRaises(errortab[j], views.users, self.request)

        self.request.read = lambda: json.dumps(
            {
                'login': 'test_login',
                'password': 'test_password',
                'fname': 'test_fname',
                'lname': 'test_lname',
                'password_test': 'test_password1'}).encode()
        self.assertRaises(PasswordMismatch, views.users, self.request)

        self.request.read = lambda: json.dumps(
            {
                'login': 'test_login',
                'password': 'test_password',
                'fname': 'test_fname',
                'lname': 'test_lname',
                'password_test': 'test_password'}).encode()
        self.assertEqual(views.users(self.request).status_code, 200)
        self.assertEqual(len(User.objects.filter(username='test_login')), 1)

        self.assertRaises(UsersDuplicate, views.users, self.request)
