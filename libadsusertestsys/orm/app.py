from flask import Flask

from libpycommon.common import misc
from libadsusertestsys.mykey.me import package_key_res_path

SERVER_ADDR = misc.get_env('DB_HOST')#'192.168.3.139'
DATABASE = misc.get_env('DB_DATABASE')#'AcadsocDataAnalysisAlgorithm'
USER_ACCOUNT = misc.get_env_encrypted('DB_USER', package_key_res_path)
SECURIT_CODE = misc.get_env_encrypted('DB_PASSWD', package_key_res_path)

def create_app():
    global USER_ACCOUNT, SECURIT_CODE
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pymssql://{}:{}@{}/{}".format(
        USER_ACCOUNT, SECURIT_CODE, SERVER_ADDR, DATABASE)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['JSON_AS_ASCII'] = False
    return app


if __name__ == '__main__':
    pass
