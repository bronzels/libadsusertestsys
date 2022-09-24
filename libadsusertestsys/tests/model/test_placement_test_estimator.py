# -*- coding: utf-8 -*-
import unittest

from libadsusertestsys.tests.myenv import *
from libadsusertestsys.model.placement_test_estimator import PlacementTestEstimator
from libpycommon.common.mylog import *


class MyclassTest(unittest.TestCase):
    def setUp(self):
        '''
        测试之前的准备工作
        :return:
        '''

    def tearDown(self):
        '''
        测试之后的收尾
        如关闭数据库
        :return:
        '''
        pass

    def test_analysis_confusions(self):
        logger.debug(
            '[\'abc"123"\', \'abc"456"\', \'abc"789"\']:{}'.format(PlacementTestEstimator._analysis_confusions('[\'abc"123"\', \'abc"456"\', \'abc"789"\']')))
        logger.debug(
            '[\'abc"123"\', "abc\'456\'", \'abc"789"\']:{}'.format(PlacementTestEstimator._analysis_confusions('[\'abc"123"\', "abc\'456\'", \'abc"789"\']')))
        logger.debug(
            '["abc\'123\'", "abc\'456\'", \'abc"789"\']:{}'.format(PlacementTestEstimator._analysis_confusions('["abc\'123\'", "abc\'456\'", \'abc"789"\']')))
        logger.debug(
            '[\'abc"123"\', "abc\'456\'", "abc\'789\'"]:{}'.format(PlacementTestEstimator._analysis_confusions('[\'abc"123"\', "abc\'456\'", "abc\'789\'"]')))
        logger.debug(
            '["abc\'123\'", "abc\'456\'", "abc\'789\'"]:{}'.format(PlacementTestEstimator._analysis_confusions('["abc\'123\'", "abc\'456\'", "abc\'789\'"]')))
        logger.debug(
            '[\'abc"123"\', "abc\'456\'", "abc\'789\'"]:{}'.format(PlacementTestEstimator._analysis_confusions('[\'abc"123"\', "abc\'456\'", "abc\'789\'"]')))
        logger.debug(
            '["abc\'123\'", \'abc"456"\', "abc\'789\'"]:{}'.format(PlacementTestEstimator._analysis_confusions('["abc\'123\'", \'abc"456"\', "abc\'789\'"]')))
        logger.debug(
            '["abc\'123\'", "abc\'456\'", \'abc"789"\']:{}'.format(PlacementTestEstimator._analysis_confusions('["abc\'123\'", "abc\'456\'", \'abc"789"\']')))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(MyclassTest('test_analysis_confusions'))
    runner = unittest.TextTestRunner()
    runner.run(suite)
