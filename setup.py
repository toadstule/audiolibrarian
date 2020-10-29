import glob
import os
from distutils.core import setup

VERSION = '0.7.0'

SCRIPTS = glob.glob(os.path.join('scripts', '*'))

setup(
    name='audiolibrarian',
    version=VERSION,
    packages=['audiolibrarian'],
    url='https://bitbucket.org/toadstule/jib-audio/',
    license='GNU General Public License v3.0',
    author='Steve Jibson',
    author_email='steve@jibson.com',
    description='Audio library utilities',
    scripts=SCRIPTS,
    install_requires=[line.strip() for line in open("requirements_base.txt")]
)
