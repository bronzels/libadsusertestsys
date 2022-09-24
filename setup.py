import setuptools
import os
import requests

from _version import __version__

# 将markdown格式转换为rst格式
def md_to_rst(from_file, to_file):
    r = requests.post(url='http://c.docverter.com/convert',
                      data={'to': 'rst', 'from': 'markdown'},
                      files={'input_files[]': open(from_file, 'rb')})
    if r.ok:
        with open(to_file, "wb") as f:
            f.write(r.content)

md_to_rst("README.md", "README.rst")

if os.path.exists('README.rst'):
    long_description = open('README.rst', encoding="utf-8").read()
else:
    long_description = 'Add a fallback short description here'

if os.path.exists("requirements.txt"):
    install_requires = open("requirements.txt").read().split("\n")
else:
    install_requires = []
print('install_requires:\n{}'.format(install_requires))

setuptools.setup(
    name="libadsusertestsys",
    version=__version__,
    author="Alex Liu",
    license='Copyright © 2021 阿卡索外教 Inc. All Rights Reserved.',
    author_email="alexliu@acadsoc.com",
    python_requires='>=3.7.0',
    description="library with functions and classes for usertestsys service apps",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://www.acadsoc.com/",
    packages=setuptools.find_packages(exclude=["tests", "test_*"]),
    classifiers=(
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=install_requires,
    include_package_data=True
)
