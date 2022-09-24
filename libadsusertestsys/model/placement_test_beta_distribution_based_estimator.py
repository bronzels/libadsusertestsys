from random import sample
import numpy as np


from libadsusertestsys.model.placement_test_estimator import PlacementTestEstimator
from libadsusertestsys.entity.evaluation_entity import *
from abc import abstractmethod


class PlacementTestBetaDistributionBasedEstimator(PlacementTestEstimator):
    """选择题型的定级测试算子"""
    def __init__(self, test_type, test_orm_entity, prior_alpha, prior_beta,
                 lower_confidence, upper_confidence, min_question_request, max_question_request,
                 max_question_request_bucket, begin_bucket, min_level, max_level, begin_level):
        super().__init__(test_type, test_orm_entity, min_question_request, max_question_request,
                         max_question_request_bucket, begin_bucket, min_level, max_level, begin_level)
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.lower_confidence = lower_confidence
        self.upper_confidence = upper_confidence

    @abstractmethod
    def _form_test_question(self, question):
        pass

    @staticmethod
    def _beta_distribution_statistics(alpha, beta, right_answers, wrong_answers):
        """计算Beta分布后验统计量"""
        mu = (alpha + right_answers) / (alpha + right_answers + beta + wrong_answers)
        var = (alpha + right_answers) * (beta + wrong_answers) / \
              (alpha + right_answers + beta + wrong_answers) ** 2 / (alpha + right_answers + beta + wrong_answers + 1)
        sigma = np.sqrt(var)
        return mu, sigma

    @staticmethod
    def estimate_algorithm(test_type, user_questions_and_answers):
        """测评算子"""
        last_answered_question = user_questions_and_answers[-1]
        user_level = last_answered_question.question.bucket
        user_level_corresponding_questions_and_answers = [
            x for x in user_questions_and_answers if x.question.bucket == user_level]

        right_answers = len([x for x in user_level_corresponding_questions_and_answers if x.is_correct(test_type) == 1])
        wrong_answers = len([x for x in user_level_corresponding_questions_and_answers if x.is_correct(test_type) != 1])

        user_score = round(right_answers / (right_answers + wrong_answers)*100)
        user_level = 'level_' + str(user_level)
        return user_score, user_level

    def _get_next_bucket(self, level):
        """根据当前级别名推导下一级别名"""
        return level + 1 if level < self.max_level else self.max_level

    def _get_previous_bucket(self, level):
        """根据当前级别名推导上一级别名"""
        return level - 1 if level > self.min_level else self.min_level

    def _level_up_or_down(self, mu, sigma, original_level):
        """根据Beta分布后验统计量以及初始等级，依据2std法则评估升降（一）级"""
        if mu - 2 * sigma > self.upper_confidence:
            new_level = self._get_next_bucket(original_level)
        elif mu + 2 * sigma < self.lower_confidence:
            new_level = self._get_previous_bucket(original_level)
        else:
            new_level = original_level
        return new_level

    def _get_next_question_bucket(self, user_questions_and_answers):
        user_actual_level = user_questions_and_answers[-1].question.bucket
        user_actual_level_questions_and_answers = list(filter(lambda q: q.question.bucket == user_actual_level, user_questions_and_answers))
        right_answers = len(list(filter(lambda q: q.is_correct(self.test_type) == 1, user_questions_and_answers)))
        wrong_answers = len(user_actual_level_questions_and_answers) - right_answers
        mean, std = self._beta_distribution_statistics(
            self.prior_alpha, self.prior_beta, right_answers, wrong_answers)
        next_question_bucket = self._level_up_or_down(mean, std, user_actual_level)
        return next_question_bucket

    def _get_next_available_questions(self, user_questions_and_answers, question_rev_id):
        """根据答题数利用beta分布评估当前的等级，然后再获取当前等级对应的题库"""
        user_answered_questions = [x for x in user_questions_and_answers if x.answer is not None]
        if len(user_questions_and_answers) == 0:  # 如果尚未答题，则从BEGIN_BUCKET开始取题
            if self.test_type == TestType.VOCAB_ESTIMATION:
                return [x for x in self.questions_by_rev_bucket[question_rev_id][self.begin_bucket]]
            else:
                return [x for x in self.questions_by_rev_bucket[question_rev_id][self.begin_level]]
        else:
            answered_question_ids = [x.question.question_id for x in user_answered_questions]
            next_question_bucket = self._get_next_question_bucket(user_answered_questions)
            available_questions = [x for x in self.questions_by_rev_bucket[question_rev_id][next_question_bucket]
                                   if x.question_id not in answered_question_ids]
            return available_questions

    def get_next_question(self, user_questions_and_answers, question_rev_id):
        """获取下一题"""
        available_questions = self._get_next_available_questions(user_questions_and_answers, question_rev_id)
        if len(available_questions) == 0:
            return None  # 如果没有可用试题或者答题数达到预设定上限则返回None
        else:
            next_question = sample(available_questions, 1)[0]
            next_question = next_question.instantiate_test_question()
            return next_question

    def estimate_rate_of_beaten(self, scores, bucket, estimated_score):
        """评估打败人数"""
        base_rate = self._get_base_rate_of_beaten(bucket)
        additional_rate = len([x for x in scores if x.score <= estimated_score]) / len(scores) \
            if len(scores) != 0 else 0

        rate_gap = self._get_rate_gap()
        rate_of_beaten = base_rate + additional_rate * rate_gap
        return float(rate_of_beaten) if rate_of_beaten < 1 else 0.99

    def _get_rate_gap(self):
        #level_numbers = self.max_level - (self.min_level + 1)
        level_numbers = self.max_level - self.min_level + 1
        return round(1 / level_numbers, 1)

    def _get_base_rate_of_beaten(self, level):
        """测评等级映射打败人数比例"""
        rate_gap = self._get_rate_gap()
        gaps = level - self.min_level + 1
        return rate_gap * gaps
