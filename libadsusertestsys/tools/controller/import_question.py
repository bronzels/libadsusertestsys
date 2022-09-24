from libadsusertestsys.orm.user_test_sys_orm import TestQuestion
from libadsusertestsys.dao.evaluation_dao import save_test_question

SOURCE_DIR = 'source/{}/{}'


def import_test_question(test_type, test_orientation, func_get_all_evaluation_test_questions):
    max_vocab_question_id = func_get_all_evaluation_test_questions(test_orientation)[-1].id
    for i in range(1, max_vocab_question_id+1):
        test_question = TestQuestion(
            test_type=test_type,
            test_orientation=test_orientation,
            subject_question_id=i
        )
        save_test_question(test_question)
