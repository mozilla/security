#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages
# Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ipquery',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='1.0.0',

    description='Web application to allow SAML authenticated users to search'
                'multiple AWS accounts for instances by IP',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/mozilla/nmap-differential-scan'
        '/tree/master/ipquery',

    # Author details
    author='Gene Wood',
    author_email='gene_wood@cementhorizon.com',

    # Choose your license
    license='MPL 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: System :: Systems Administration',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7'

    ],

    # What does your project relate to?
    keywords='aws ec2 saml okta',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    install_requires=['ip2instance>=1.2.0', 
                      'PyYAML>=3.11', 
                      'Flask>=0.10.1',
                      'Flask-Bootstrap>=3.3.2.1',
                      'Flask-Cache>=0.13.1',
                      'Flask-Login>=0.2.11',
                      'Flask-WTF>=0.11',
                      'pysaml2>=2.4.0'],

    include_package_data=True,
    package_data={
                  'templates': 'ipquery/templates/*'
    },

    data_files=[],

    entry_points={
        'console_scripts': [
            'run_ipquery_server = ipquery:main'
        ]
    },
)
