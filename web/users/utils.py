## @file web/users/utils.py
# @brief Utility functions module for users.views services

from django.contrib.auth.models import User
from boreholes.models import _JsonResponse


class BadUsername(Exception):
    def __init__(self):
        Exception.__init__(self, 'bad_username')
class IncorrectPassword(Exception):
    def __init__(self):
        Exception.__init__(self, 'incorrect_password')
class UsersDuplicate(Exception):
    def __init__(self):
        Exception.__init__(self, 'user_exists')
class PasswordMismatch(Exception):
    def __init__(self):
        Exception.__init__(self, 'password_mismatch')

def getUsers(uid=None):
    '''
    The function gets all existing users or particular user by id.
    '''
    def createElement(obj):
        temp = {attr : str(getattr(obj, attr)) for attr in ("id", "username", "first_name", "last_name")}
        temp['readwrite'] = obj.groups.filter(name='editors').exists()
        return temp
    
    users = createElement(User.objects.get(id = uid)) if uid else [createElement(u) for u in User.objects.all()]

    return _JsonResponse(users)
