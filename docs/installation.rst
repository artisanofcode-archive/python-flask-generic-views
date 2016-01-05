Installation
============

A minimal install without database support can be performed with the
following:

::

    pip install flask-generic-views


Optional packages
-----------------

To avoid excessive dependencies some of the dependencies are broken out into
setup tools "extra" feature.

You can safely mix multiple of the following in your ``requirements.txt``.

SQLAlchemy
~~~~~~~~~~

To install flask-generic-views with SQLAlchemy support use the following:

::

    pip install flask-generic-views[sqlalchemy]


All
~~~

To install flask-generic-views with all optional dependencies use the
following:

::

    pip install flask-generic-views[all]
