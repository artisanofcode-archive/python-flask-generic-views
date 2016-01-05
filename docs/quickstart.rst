Quick Start
===========

A Minimal Application
---------------------

A minimal Flask-Generic-Views application looks something like this:

.. code-block:: python

    from flask import Flask
    from flask_generic_views import TemplateView, RedirectView

    app = Flask(__name__)

    index = RedirectView('index', url='/home')

    app.add_url_rule('/', view_func=index)

    home = TemplateView('home', template_name='home.html')

    app.add_url_rule('/home', view_func=home)

    if __name__ == '__main__':
        app.run()

Save this as ``app.py``, and create a template for your `home` view to render.

.. code-block:: jinja

    <h1>Hello World</h1>

Save this as ``templates/home.html`` and run the application with your Python
interpreter.

::

    $ python app.py
    * Running on http://127.0.0.1:5000/

If you head to http://127.0.0.1:5000/ now you should see the rendered template.

An SQLAlchemy Application
=========================

.. code-block:: python

    from flask import Flask
    from flask.ext.generic_views.sqlalchemy import (CreateView,
                                                    DeleteView,
                                                    DetailView,
                                                    ListView,
                                                    UpdateView)
    from flask.ext.sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    app.config['SECRET_KEY'] = '5up3r5ekr3t'

    db = SQLAlchemy(app)

    class Post(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))
        body = db.Column(db.Text(120))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # index

    index_view = ListView.as_view('index', model=Post,
                                  ordering=[Post.created_at],
                                  per_page=20)

    app.add_url_rule('/', view_func=index_view)

    # show

    show_view = DetailView.as_view('show', model=Post)

    app.add_url_rule('/<int:pk>', view_func=show_view)

    # new

    new_view = CreateView.as_view('new', model=Post,
                                  fields=('name', 'body'),
                                  success_url='/{id}')

    app.add_url_rule('/new', view_func=new_view)

    # edit

    edit_view = UpdateView.as_view('edit', model=Post,
                                   fields=('name', 'body'),
                                   success_url='/{id}')

    app.add_url_rule('/<int:pk>/edit', view_func=edit_view)

    # delete

    delete_view = DeleteView.as_view('delete', model=Post,
                                     success_url='/')

    app.add_url_rule('/<int:pk>/delete', view_func=delete_view)

    if __name__ == '__main__':
        app.run()