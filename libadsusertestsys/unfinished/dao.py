from libpycommon.common import mylog
from libadsusertestsys.orm.user_test_sys_orm import *
from libadsusertestsys.entity.evaluation_entity import TestType
from sqlalchemy import or_
from libadsusertestsys.entity.evaluation_entity import ConfusionsType, EntityTestQuestionAndAnswer
from libadsusertestsys.unfinished.entity import UnfinishedTest
def get_test_unfinished(test_orientation_value, test_type, user_id, estimator):
    orm_entity = estimator.test_orm_entity
    orm_test_results_unfinished = TestResult.query \
        .filter(test_user_id=user_id, test_orientation=test_orientation_value) \
        .filter(TestResult.score.is_(None)) \
        .order_by(TestResult.id.desc()).limit(1)
    if orm_test_results_unfinished is None:
        return None, None, None

    orm_test_result_unfinished = orm_test_results_unfinished[0].openid

    if test_type == TestType.SPEAKING_EVALUATION:
        test_question_and_answers_unfinished = SpeakingTestQuestionAndAnswer.query\
        .filter(test_result_id = orm_test_result_unfinished.id).all()
    else:
        test_question_and_answers_unfinished = TestQuestionAndAnswer.query\
            .filter(test_result_id=orm_test_result_unfinished.id).all()

    if test_question_and_answers_unfinished is None:
        mylog.logger.error(
            'no unfinished questions per test result, id:{}, test_user_id:{}, test_orientation:{}, create_time:{}',
            orm_test_result_unfinished.id, orm_test_result_unfinished.test_user_id, orm_test_result_unfinished.test_orientation,
            orm_test_result_unfinished.create_time)
        return None, None, None

    queston_and_answer_all_unfinished = []
    queston_and_answer_unfinished = {}
    for orm_question_and_answer in test_question_and_answers_unfinished:
        orm_test_questions = orm_entity.query.filter(orm_entity.id == orm_question_and_answer.test_question_id).all()
        if orm_test_questions is None:
            mylog.logger.error(
                'no question details per test question index, id:{}, test_user_id:{}, test_answer:{}, test_question_id:{}, create_time:{}',
                orm_question_and_answer.id, orm_question_and_answer.test_user_id, orm_question_and_answer.test_answer,
                orm_question_and_answer.test_question_id, orm_question_and_answer.create_time)
            continue
        orm_test_question = orm_test_questions[0]
        if "option_type" not in orm_test_question.__dict__.keys():
            orm_test_question.option_type = ConfusionsType.Text.value
        test_question = estimator._form_test_question(orm_test_question)
        if test_type == TestType.SPEAKING_EVALUATION:
            question_and_answer = EntityTestQuestionAndAnswer(test_question, orm_question_and_answer.test_answer)
        else:
            question_and_answer = EntityTestQuestionAndAnswer(test_question,
                                                              {'category': orm_question_and_answer.category,
                                                               'test_user_audio_path': orm_question_and_answer.test_user_audio_path,
                                                               'is_nonsense': orm_question_and_answer.is_nonsense,
                                                               'accuracy_score': orm_question_and_answer.accuracy_score,
                                                               'standard_score': orm_question_and_answer.standard_score,
                                                               'fluency_score': orm_question_and_answer.fluency_score,
                                                               'integrity_score': orm_question_and_answer.integrity_score,
                                                               'total_score': orm_question_and_answer.total_score}
                                                              )

        if orm_question_and_answer.test_answer is not None:
            question_and_answer.m_correct = question_and_answer.is_correct(test_type)
        queston_and_answer_all_unfinished.append(question_and_answer)
        queston_and_answer_unfinished[question_and_answer.question.bucket] = question_and_answer
    is_last_question_answered = test_question_and_answers_unfinished[-1].test_answer is not None
    return UnfinishedTest(orm_test_result_unfinished.id, len(queston_and_answer_all_unfinished), is_last_question_answered), queston_and_answer_unfinished, queston_and_answer_all_unfinished
