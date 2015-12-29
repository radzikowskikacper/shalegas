##
# @file web/users/views.py
# @brief The view for application users, provides services for login and logout.

import json, logging

from django.contrib.auth import authenticate
import django.contrib.auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User, Group
from django.db import IntegrityError, transaction, DataError
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import ensure_csrf_cookie
from images.views import _JsonResponse
from users.utils import BadUsername, getUsers, PasswordMismatch, \
    UsersDuplicate, IncorrectPassword


logger = logging.getLogger('sweetspot.users')

@ensure_csrf_cookie
def users(request, command=None):
    '''
    The main service method for getting all users, particular user, adding, modifying and deleting a user
    '''
    if command == 'login':
        if request.method == 'POST':
            params = json.loads(request.read().decode('utf-8'))

            user = params['login']
            password = params['password']

            with transaction.atomic():
                user = authenticate(username=user, password=password)

                if user is not None:
                    if user.is_active:
                        django.contrib.auth.login(request, user)
                        logger.info("User %s logged in" % request.user.username)
                        return _JsonResponse({'username' : user.username})

            raise BadUsername
    else:
        if not command:
            if request.method == 'GET':
                return getUsers()
            
            elif request.method == 'POST':
                params = json.loads(request.read().decode('utf-8'))
                
                with transaction.atomic():
                    if params['password'] != params['password_test']:
                        raise PasswordMismatch
                    
                    try:
                        user = User.objects.create_user(params['login'], password = params['password'], first_name = params['fname'], last_name = params['lname'])
                        user.groups.add(Group.objects.get(name='viewers'))
                        logger.info("User %s added new user" % request.user.username)
                        
                        return getUsers()
                    except IntegrityError:
                        raise UsersDuplicate

        elif command == 'logout':
            if request.method == 'POST':
                django.contrib.auth.logout(request)
                logger.info("User %s logged out" % request.user.username)
                
                return HttpResponse()
    
        else:
            if request.method == 'GET':
                return getUsers(command)
        
            elif request.method == 'DELETE':
                with transaction.atomic():
                    user = User.objects.get(id=command)
                    user.delete()
                    logger.info("User %s deleted user" % request.user.username)
    
                    return HttpResponse()
    
            elif request.method == 'PUT':
                user = User.objects.get(id=command)
    
                params = json.loads(request.read().decode('utf-8'))
    
                if 'new_password' in params:
                    new_password = params['new_password']
    
                    with transaction.atomic():
                        if check_password(params['old_password'], user.password):
                            user.set_password(new_password)
                            user.save()
                            logger.info("User %s modified user" % request.user.username)
                            
                            return getUsers(user.id)
                        else:
                            raise IncorrectPassword
    
                else:
                    with transaction.atomic():
                        if 'first_name' in params:
                            user.first_name = params['first_name']
                        if 'last_name' in params:
                            user.last_name = params['last_name']
                        if 'readwrite' in params and params['readwrite']:
                            user.groups.add(Group.objects.get(name='editors'))
                        else:
                            user.groups.remove(Group.objects.get(name='editors'))
                                
                        user.save()
                        logger.info("User %s modified user" % request.user.username)
                        
                        return getUsers(user.id)