from datetime import datetime

from flask import Flask
from flask.ext.generic_views import RedirectView, TemplateView
from flask.ext.generic_views.sqlalchemy import (CreateView, DeleteView,
                                                DetailView, ListView,
                                                UpdateView)
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

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

index_view = ListView.as_view('index', model=Post, ordering=[Post.created_at],
                              per_page=20)

app.add_url_rule('/', view_func=index_view)

# show

show_view = DetailView.as_view('show', model=Post)

app.add_url_rule('/<int:pk>', view_func=show_view)

# new

new_view = CreateView.as_view('new', model=Post, fields=('name', 'body'),
                              success_url='/{id}')

app.add_url_rule('/new', view_func=new_view)

# edit

edit_view = UpdateView.as_view('edit', model=Post, fields=('name', 'body'),
                               success_url='/{id}')

app.add_url_rule('/<int:pk>/edit', view_func=edit_view)

# delete

delete_view = DeleteView.as_view('delete', model=Post, success_url='/')

app.add_url_rule('/<int:pk>/delete', view_func=delete_view)

# about

about_view = TemplateView.as_view('about', template_name='about.html')

app.add_url_rule('/about', view_func=about_view)

# contact

contact_view = RedirectView.as_view('contact', endpoint='index')

app.add_url_rule('/redirect', view_func=contact_view)


@app.before_first_request
def init_stuff():
    try:
        db.create_all()
    except OperationalError as e:
        app.logger.error(e)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
