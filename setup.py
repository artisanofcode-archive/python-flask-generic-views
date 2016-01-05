"""
Flask-Generic-Views
===================

Flask-Generic-Views is a set of generic class-based views for the Flask
microframework inspired by the ones in Django.

.. code:: python

    from flask import Flask
    from flask.ext.generic_views import TemplateView

    app = Flask(__name__)

    index_view = TemplateView.as_view('index', template_file='index.html')

    app.add_url_rule('/', index_view)

    if __name__ == '__main__':
        app.run()

Database Support
----------------

Currently Flask-Generic-Views supports use of Models created with SQLAlchemy.

Installation
------------

To install the basic views:

.. code:: bash

    $ pip install flask-generic-views

To install optional SQLAlchemy support:

.. code:: bash

    $ pip install flask-generic-views[sqlalchemy]

To install all optional packages:

.. code:: bash

    $ pip install flask-generic-views[all]

Links
-----

* `Documentation <https://flask-generic-views.readthedocs.org/>`_
* `GitHub <https://github.com/artisanofcode/flask-generic-views>`_
"""

import ast
import re

from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('flask_generic_views/__init__.py', 'rb') as f:
    version = f.read().decode('utf-8')
    version = str(ast.literal_eval(_version_re.search(version).group(1)))


extras_require = {
    'sqlalchemy':  ['flask-sqlalchemy>=2.1', 'wtforms-sqlalchemy>=0.1'],
}

extras_require['all'] = sum(extras_require.values(), [])

setup(
    name='Flask-Generic-Views',
    version=version,
    url='http://github.com/artisanofcode/flask-generic-views',
    license='BSD',
    author='Daniel Knell',
    author_email='contact@danielknell.co.uk',
    description='A set of generic class-based views for flask',
    long_description=__doc__,
    packages=['flask_generic_views'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'flask>=0.10',
        'flask-wtf>=0.12',
        'inflection>=0.3.1',
    ],
    extras_require=extras_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
