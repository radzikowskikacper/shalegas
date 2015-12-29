##
# @file web/version/models.py
# @brief Version model. It stores database version, database connecting strings and application version.

from django.db import connection

from .version_gen import *

def getVersionString():
    """version string, for displaying in client"""
    return str(major) + "." + str(minor) + "." + str(compilation)

def getDBName():
    """database name"""
    return DB_NAME

def getDBUser():
    """database user"""
    return DB_USER

def getDBPassword():
    """database password"""
    return DB_PASSWORD

def _versionFromRow(row):
    """helping function - parse row to return the correct version"""
    ver = 'unknown'
    try:
        ver = str(row[0].split(',')[0])
    except:
        pass
    return ver

def getDBVersionString():
    """database version"""
    cursor = connection.cursor()
    cursor.execute("select version();")
    row = cursor.fetchone()
    return _versionFromRow(row)



