import datetime

def timestamp():
    """ Used in SQL Alchemy models to ensure we refresh timestamp when new models initialised"""
    return datetime.datetime.utcnow()