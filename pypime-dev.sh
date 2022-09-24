#!/bin/bash
repo_name='libadsusertestsys'
echo repo_name:${repo_name}
rev=`cat _version.py |awk -F \' '{print \$2}'`
echo rev:${rev}
files="/e/pypirepo/${repo_name}-${rev}*"
echo files:${files}
if ls ${files}  1> /dev/null 2>&1; then
rm -f ${files}
fi

python setup.py sdist bdist_wheel
twine upload --repository-url http://localhost:9090 --username pypiadmin --password pypiadmin123 dist/*

rm -rf build
rm -rf dist