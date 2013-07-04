# -*- coding: utf-8 -*-
"""
Модульные тесты для модуля Контракты
"""
import unittest

from contracts.utils import can_restructure_contract, Result


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



