import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "table-football",
    version = "1.0",
    url = 'http://github.com/keizik/table-football',
    license = 'BSD',
    description = "Table Football statistics app.",
    long_description = read('README'),
	
    author = 'Aleksandr Keizik',
    author_email = 'alex.keizik@gmail.com',
    
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools'],
    
    classifiers = [
        'Development Status :: v1',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
) 