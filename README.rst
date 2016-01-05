Flask-Generic-Views
===================

An extension to Flask that provides a set of generic  class based views. It
aims to simplify applications by providing a set of well tested base classes
and pluggable views for common tasks.

For more information check the Documentation_.

Example
-------

.. code:: python

    from flask import Flask
    from flask_generic_views import TemplateView, RedirectView

    app = Flask(__name__)

    index = RedirectView('index', url='/home')

    app.add_url_rule('/', view_func=index)

    home = TemplateView('home', template_name='home.html')

    app.add_url_rule('/home', view_func=home)

    if __name__ == '__main__':
        app.run()

Install
-------

To install Flask-Generic-Views via pip:

::

    pip install flask-generic-views

Source
------

To install from source:

::

    git clone git://github.com/artisanofcode/flask-generic-views.git
    cd flask-generic-views
    python setup.py develop


History
-------

See `CHANGES <CHANGES>`_

Licence
-------

This project is licensed under the `MIT licence`_.

Meta
----

This project uses `Semantic Versioning`_.

.. _Documentation: http://flask-generic-views.readthedocs.org/
.. _Semantic Versioning: http://semver.org/
.. _MIT Licence: http://dan.mit-license.org/