# -*- coding: utf-8 -*-
"""
Модульные тесты для модуля Контракты
"""
import unittest

import xml.etree.ElementTree as ET


class Result:
    id, code, comment, comment_id, comment_str = None, None, None, None, None

    def __init__(self, xml):
        """ Разбор XML """
        for child in ET.fromstring(xml):
            setattr(self, child.tag, child.text)
        x = str.split(str(self.comment))
        if len(x) > 0:
            self.comment_id = int(x[0])
        if len(x) > 1:
            self.comment_str = x[1]


class FHTest(unittest.TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

    def test_Result(self):
        result = Result("""<?xml version="1.0" encoding="UTF-8"?>
<result>
<id>0</id>
<code>YES</code>
<comment>0 </comment>
</result>
""")
        self.assertEqual(result.id, "0")
        self.assertEqual(result.code, "YES")
        self.assertEqual(result.comment, "0 ")
        self.assertEqual(result.comment_id, 0)
        self.assertEqual(result.comment_str, None)



