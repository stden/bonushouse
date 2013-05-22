# -*- coding: utf-8 -*-

import hashlib
import time

def get_unsubscribe_hash(user):
    first_name = user.first_name
    last_name = user.last_name
    birthdate_utc = ''
    if user.get_profile().birth_date:
        try:
            birthdate_utc = time.mktime(user.get_profile().birth_date.timetuple())
        except ValueError:
            birthdate_utc = ''
    hash_str = first_name + last_name + str(birthdate_utc)
    return hashlib.md5(hash_str.encode('utf-16')).hexdigest()