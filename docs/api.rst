API
===

Core
----

.. module:: flask_generic_views.core

View logic is often repetitive, there are standard patterns we repeat over
again both within and across projects, and reimplementing the same patterns
can be a bore.

These views take some of those patterns and abstract them so you can create
views for common tasks quickly without having to write too much code.

Tasks such as rendering a template or redirecting to a new url can be performed
by passing parameters at instantiation without defining additional classes.

Views
~~~~~

.. autoclass:: View
   :members:
   :show-inheritance:

.. autoclass:: MethodView
   :members:
   :show-inheritance:

.. autoclass:: TemplateView
   :members:
   :show-inheritance:

.. autoclass:: RedirectView
   :members:
   :show-inheritance:

   .. attribute:: url
      :annotation: = None

      String containing the URL to redirect to or None to raise a
      :exc:`~werkzeug.exceptions.Gone` exception.

   .. attribute:: endpoint
      :annotation: = None

      The name of the endpoint to redirect to. URL generation will be done
      using the same keyword arguments as are passed in for this view.

   .. attribute:: permanent
      :annotation: = False

      Whether the redirect should be permanent. The only difference here is
      the HTTP status code returned. When True, then the redirect will use
      status code 301. When False, then the redirect will use status code 302.

   .. attribute:: query_string
      :annotation: = False

      Whether to pass along the query string to the new location. When True,
      then the query string is appended to the URL. When False, then the query
      string is discarded.

.. autoclass:: FormView
   :members:
   :show-inheritance:

Helpers
~~~~~~~

.. autoclass:: ContextMixin
   :members:
   :show-inheritance:

.. autoclass:: TemplateResponseMixin
   :members:
   :show-inheritance:
   :exclude-members: response_class

   .. attribute:: mimetype
      :annotation:  = None

      The mime type type to use for the response. The mimetype is passed as a
      keyword argument to :attr:`response_class`.

   .. attribute:: response_class
      :annotation:  = flask.Response

      The :class:`~werkzeug.wrappers.Response` class to be returned by
      :meth:`create_response`.

   .. attribute:: template_name
      :annotation: = None

      The string containing the full name of the template to use. Not defining
      :attr:`template_name` will cause the default implementation of
      :meth:`get_template_names` to raise a :exc:`NotImplementedError`
      exception.

.. autoclass:: FormMixin
   :members:
   :show-inheritance:

   .. attribute:: data
      :annotation: = {}

      A dictionary containing initial data for the form.

   .. attribute:: form_class
      :annotation: = None

      The form class to instantiate.

   .. attribute:: success_url
      :annotation: = None

      The URL to redirect to when the form is successfully processed.

   .. attribute:: prefix
      :annotation: = ''

      The prefix for the generated form.

.. autoclass:: ProcessFormView
   :members:
   :show-inheritance:

.. autoclass:: BaseFormView
   :members:
   :show-inheritance:

SQLAlchemy
----------

.. module:: flask_generic_views.sqlalchemy

Views logic often relates to retrieving and persisting data in a database,
these views cover some of the most common patterns for working with models
using the SQLAlchemy_ library.

Tasks such as displaying, listing, creating, updating, and deleting objects
can be performed by passing parameters at instantiation without defining
additional classes.

Views
~~~~~

.. autoclass:: DetailView
   :members:
   :show-inheritance:

.. autoclass:: ListView
   :members:
   :show-inheritance:

.. autoclass:: CreateView
   :members:
   :show-inheritance:

   .. attribute:: template_name_suffix
      :annotation: = '_form'

      The suffix to use when generating a template name from the model class

.. autoclass:: UpdateView
   :members:
   :show-inheritance:

   .. attribute:: template_name_suffix
      :annotation: = '_form'

      The suffix to use when generating a template name from the model class

.. autoclass:: DeleteView
   :members:
   :show-inheritance:

   .. attribute:: template_name_suffix
      :annotation: = '_delete'

      The suffix to use when generating a template name from the model class

Helpers
~~~~~~~


.. data:: session

    A proxy to the current SQLAlchemy session provided by Flask-SQLAlchemy.


.. autoclass:: SingleObjectMixin
   :members:
   :show-inheritance:

   .. attribute:: object

      The the object used by the view.

   .. attribute:: model
      :annotation: =  None

      The :class:`~flask_sqlalchemy.Model` class used to retrieve the object
      used by this view.

      This property is a shorthand, ``model = Post`` and ``query = Post.query``
      are functionally identical.


   .. attribute:: query
      :annotation: =  None

      The :class:`~sqlalchemy.orm.query.Query`  instance used to retrieve the
      object used by this view.

   .. attribute:: slug_field
      :annotation: =  'slug'

      The name of model field that contains the slug

   .. attribute:: context_object_name
      :annotation: =  None

      The name of the context variable name to store the :attr:`object` in.

   .. attribute:: slug_view_arg
      :annotation: =  'slug'

      The name of the view keyword argument that contains the slug.

   .. attribute:: pk_view_arg
      :annotation: =  'pk'

      The name of the view keyword argument that contains the primary-key.

   .. attribute:: query_pk_and_slug
      :annotation: =  False

      When True :meth:`get_object` will filter the query by both primary-key
      and slug when available.

.. autoclass:: BaseDetailView
   :members:
   :show-inheritance:

.. autoclass:: SingleObjectTemplateResponseMixin
   :members:
   :show-inheritance:

.. autoclass:: MultipleObjectMixin
   :members:
   :show-inheritance:
   :exclude-members: pagination_class


   .. attribute:: object_list

      The final :class:`~sqlalchemy.orm.query.Query` instance used by the view.

   .. attribute:: error_out
      :annotation: = False

      Wether to raise a :exc:`~werkzeug.exceptions.NotFound` exception when no
      results are found.

   .. attribute:: query
      :annotation: = None

      The base :class:`~sqlalchemy.orm.query.Query` instance used by this view.

   .. attribute:: model
      :annotation: = None

      The :class:`~flask_sqlalchemy.Model` class used to retrieve the object
      used by this view.

      This property is a shorthand, ``model = Post`` and ``query = Post.query``
      are functionally identical.

   .. attribute:: per_page
      :annotation: = None

      The number of results to return per page, when None pagination will be
      disabled.

   .. attribute:: context_object_name
      :annotation: = None

      The name of the context variable name to store the :attr:`object_list`
      in.

   .. attribute:: pagination_class
      :annotation: = flask_sqlalchemy.Pagination

      The :class:`~flask_sqlalchemy.Pagination` class to be returned by
      :meth:`get_pagination`.

   .. attribute:: page_arg
      :annotation: = 'page'

      The name of the view / query-string keyword argument that contains the
      page number.

   .. attribute:: order_by
      :annotation: = None

      A :class:`tuple` of criteria to pass to pass to the query
      :meth:`~sqlalchemy.orm.query.Query.order_by` method.


.. autoclass:: BaseListView
   :members:
   :show-inheritance:

.. autoclass:: MultipleObjectTemplateResponseMixin
   :members:
   :show-inheritance:

   .. attribute:: template_name_suffix
      :annotation: = '_list'

      The suffix to use when generating a template name from the model class

.. autoclass:: ModelFormMixin
   :members:
   :show-inheritance:

   .. attribute:: fields
      :annotation: = None

      A :class:`tuple` of :class:`str` mapping to the names of column
      attribute on the :attr:`model`, these will be added as form fields on the
      automatically generated form.

.. autoclass:: BaseCreateView
   :members:
   :show-inheritance:

.. autoclass:: BaseUpdateView
   :members:
   :show-inheritance:

.. autoclass:: DeletionMixin
   :members:
   :show-inheritance:

   .. attribute:: success_url
      :annotation: = None

      The URL to redirect to after deletion.

.. autoclass:: BaseDeleteView
   :members:
   :show-inheritance:

.. _SQLAlchemy: http://www.sqlalchemy.org/