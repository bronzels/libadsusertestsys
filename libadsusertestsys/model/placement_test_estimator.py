from libadsusertestsys.common.utils import replace_all
from libadsusertestsys.dao.evaluation_dao import *
from libadsusertestsys.entity.evaluation_entity import *
from libadsusertestsys.orm.config import l_question_rev_id
from abc import abstractmethod
import re

import libpycommon.common.mylog as mylog

class PlacementTestEstimator:
    def __init__(self, test_type, test_orm_entity, min_question_request, max_question_request, max_question_request_bucket,
                 begin_bucket, min_level, max_level, begin_level):
        self.test_type = test_type
        self.test_orm_entity = test_orm_entity

        self.min_question_request = min_question_request
        self.max_question_request = max_question_request
        self.max_question_request_bucket = max_question_request_bucket
        self.begin_bucket = begin_bucket
        self.min_level = min_level
        self.max_level = max_level
        self.begin_level = begin_level

        self.questions_by_rev_bucket = {}
        self.load_evaluation_questions()

    @staticmethod
    def _analysis_confusions(str_confusions):
        to_eval = '{}'.format(str_confusions)
        return eval(to_eval)

    @abstractmethod
    def _form_test_question(self, question):
        pass

    def load_evaluation_questions(self):
        """一次性导入题库"""
        questions_count = 0
        mylog.logger.debug("loading {} test questions! min level {}, max level {} begin level {}".format(
            self.test_type, self.min_level, self.max_level, self.begin_level))
        all_questions = get_placement_test_questions_by_test_type_and_level_interval(
            self.test_orm_entity, self.min_level, self.max_level, l_question_rev_id)  # 返回列表
        for question in all_questions:
            if "option_type" not in question.__dict__.keys():
                question.option_type = ConfusionsType.Text.value
            test_question = self._form_test_question(question)

            if test_question.question_rev_id in self.questions_by_rev_bucket:
                rev_bucket_questions = self.questions_by_rev_bucket[test_question.question_rev_id]
            else:
                rev_bucket_questions = {}
                self.questions_by_rev_bucket[test_question.question_rev_id] = rev_bucket_questions

            if test_question.bucket in rev_bucket_questions:
                bucket_questions = rev_bucket_questions[test_question.bucket]  # 初始为空字典
            else:
                bucket_questions = []
                self.questions_by_rev_bucket[test_question.question_rev_id][test_question.bucket] = bucket_questions
            bucket_questions.append(test_question)

            questions_count += 1
        mylog.logger.debug("{} test question loaded! {} questions available".format(self.test_type, questions_count))
        mylog.logger.debug("questions_by_rev_bucket:{}".format(self.questions_by_rev_bucket))
