# -*- coding: utf-8 -*-

import hashlib
import time
import datetime

def get_unsubscribe_hash(user):
    first_name = user.first_name
    last_name = user.last_name
    birthdate_utc = ''
    if user.birth_date:
        birthdate_utc = time.mktime(user.get_profile().birth_date.timetuple())
    hash_str = first_name + last_name + str(birthdate_utc)
    return hashlib.md5(hash_str.encode('utf-16')).hexdigest()