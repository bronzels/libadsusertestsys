from libadsusertestsys.orm.user_test_sys_orm import *

if __name__ == '__main__':
    results = TestResultLast.query.filter_by(test_user_id=14)
    for result in results:
        print(result.__dict__)