# -*- coding: utf-8 -*-
"""
Модульные тесты для модуля Контракты
"""
import unittest
from django.contrib.auth.models import User

from contracts.utils import can_restructure_contract, Result, restructure_contract_1


class FHTest(unittest.TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

    def test_Result(self):
        result = Result("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                        "<result>\n"
                        "<id>0</id>\n"
                        "<code>YES</code>\n"
                        "<comment>0 </comment>\n"
                        "</result>\n")
        self.assertEqual(result.id, "0")
        self.assertEqual(result.code, "YES")
        self.assertEqual(result.comment, "0 ")
        self.assertEqual(result.comment_id, 0)
        self.assertEqual(result.comment_str, None)

    def check_contract(self):
        ERROR = 'Данный договор нельзя перевести через интернет-сайт, обратитесь за информацией в отдел продаж 610-06-06'
        self.assertIsNone(can_restructure_contract("13/12121201"))
        self.assertIsNone(can_restructure_contract("M13/12121201"))
        self.assertIsNone(can_restructure_contract("MB13/12121201"))
        self.assertIsNone(can_restructure_contract("MB13/12121201"))
        self.assertEqual(can_restructure_contract("К13/12121201"), ERROR)
        self.assertEqual(can_restructure_contract("Г13/12121201"), ERROR)
        self.assertEqual(can_restructure_contract("A13/12121201"), ERROR)
        self.assertEqual(can_restructure_contract("Z13/12121201"), ERROR)
        self.assertEqual(can_restructure_contract("sasdfasdf/sdfsdf"), ERROR)

    def restructure_contract_1_test_1(self):
        response = {'bd': ['1980.05.18'], 'sdate': ['2013.07.02'], 'sname': ['990.00'], 'src_id': ['9794377'],
                    'edate': ['\xf1\xe5\xf0\xe3\xe5\xe9'],
                    'src_club': ['FH \xed\xe0 \xcc\xe5\xe1\xe5\xeb\xfc\xed\xee\xe9'],
                    'passport': ['990.00'], 'activity': ['0\r\n?status=2'], 'dognumber': ['MB62/1307024'],
                    '?status': ['1'],
                    'debt': ['0.00'], 'type': ['10 \xe4\xed\xe5\xe9'], 'email': ['\xee\xf0\xe5\xf5\xee\xe2']}
        user = User()
        passport = u'0202 194723'
        res = restructure_contract_1(response, 'MB62/1307024', user, passport)
        self.assertEqual("Договор не найден или неверные данные!", res)

    def restructure_contract_1_test_2(self):
        response = {'bd': ['1980.05.18'], 'sdate': ['2013.07.02'], 'sname': ['990.00'], 'src_id': ['9794377'],
                    'edate': ['\xf1\xe5\xf0\xe3\xe5\xe9'],
                    'src_club': ['FH \xed\xe0 \xcc\xe5\xe1\xe5\xeb\xfc\xed\xee\xe9'],
                    'passport': ['990.00'], 'activity': ['0\r\n?status=2'], 'dognumber': ['MB62/1307024'],
                    '?status': ['1'],
                    'debt': ['0.00'], 'type': ['10 \xe4\xed\xe5\xe9'], 'email': ['\xee\xf0\xe5\xf5\xee\xe2']}
        user = User()
        passport = u'990.00'
        res = restructure_contract_1(response, 'MB62/1307024', user, passport)
        self.assertEqual(u"Договор не найден или неверные данные!", res)





