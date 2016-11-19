from math import ceil

import pytest
from flask.ext.wtf import Form
from hypothesis import strategies as st
from hypothesis import example, given
from inflection import camelize, underscore
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import Column
from werkzeug.exceptions import HTTPException

from flask_generic_views import core, sqlalchemy
from flask_generic_views._compat import integer_types, iteritems, iterkeys
from tests.utils import ASCII, DIGITS, SLUG, nondigit

try:
    from unittest.mock import Mock, call, patch
except ImportError:
    from mock import Mock, call, patch


def mock_query(success=True):
    query = Mock()

    query._entities = [Mock(name='mock._entities[0]')]

    if not success:
        query.filter_by.return_value.one.side_effect = NoResultFound

    return query


class TestTouch(object):

    def test_touch(self):
        obj = Mock()

        with patch.object(sqlalchemy, 'getattr', create=True) as m1:
            with patch.object(sqlalchemy, 'inspect') as m2:
                m2.return_value.attrs.keys.return_value = keys = [Mock()]

                sqlalchemy._touch(obj)

        m1.assert_called_once_with(obj, keys[0], None)


class TestSession(object):

    def test_find_session(self):
        extension = Mock()

        with patch.object(sqlalchemy, 'current_app') as m:
            m.extensions = {'sqlalchemy': extension}

            assert sqlalchemy._find_session() == extension.db.session


class TestSingleObjectMixin(object):

    @given(st.booleans(), st.booleans())
    def test_get_model(self, query, model):
        instance = sqlalchemy.SingleObjectMixin()
        if query:
            instance.query = mock_query()

        if model:
            instance.model = Mock()

        cls = instance.get_model()

        if query:
            assert cls == instance.query._entities[0].entity_zero.class_
        elif model:
            assert cls == instance.model
        else:
            assert cls is None

    @given(st.text(), st.lists(st.text(ASCII).filter(bool), unique=True),
           st.integers(), st.booleans())
    @example('pk', ['pk'], 1, True)
    @example('pk', [], 1, True)
    @example('pk', ['id_1', 'id_2'], 1, True)
    @example('pk', ['pk'], 1, False)
    def test_get_object_pk(self, pk_view_arg, fields, pk, success):
        instance = sqlalchemy.SingleObjectMixin()
        instance.pk_view_arg = pk_view_arg
        instance.query = query = mock_query(success)
        instance.get_model = Mock()

        return_value = query.filter_by.return_value.one.return_value

        primary_key = [Column(key=name) for name in fields]

        with patch.object(sqlalchemy, 'inspect') as m1:
            with patch.object(sqlalchemy, 'request') as m2:
                m1.return_value.primary_key = primary_key
                m2.view_args = {pk_view_arg: pk}

                if len(fields) == 1:
                    if not success:
                        with pytest.raises(HTTPException) as excinfo:
                            instance.get_object()

                        assert excinfo.value.code == 404
                    else:
                        assert instance.get_object() == return_value

                    query.filter_by.assert_called_once_with(**{fields[0]: pk})
                else:
                    with pytest.raises(RuntimeError) as excinfo:
                        instance.get_object()

                    if len(fields) > 1:
                        error = ('SingleObjectMixin requires non composite '
                                 'primary key')
                    else:
                        error = ('SingleObjectMixin requires primary key')

                    assert excinfo.value.args[0] == error

            m1.assert_called_once_with(instance.get_model.return_value)
            instance.get_model.assert_called_once_with()

    @given(st.text(ASCII), st.text(ASCII), st.text(ASCII), st.booleans())
    def test_get_object_slug(self, slug_view_arg, slug_field, slug, success):
        instance = sqlalchemy.SingleObjectMixin()
        instance.query = query = mock_query(success)
        instance.slug_view_arg = slug_view_arg

        instance.get_slug_field = Mock(return_value=slug_field)

        return_value = query.filter_by.return_value.one.return_value

        with patch.object(sqlalchemy, 'request') as m:
            m.view_args = {slug_view_arg: slug}

            if not success:
                with pytest.raises(HTTPException) as excinfo:
                    instance.get_object()

                assert excinfo.value.code == 404
            else:
                assert instance.get_object() == return_value

        query.filter_by.assert_called_once_with(**{slug_field: slug})

    @given(st.integers(), st.text(ASCII),
           st.lists(st.text(ASCII).filter(bool), 2, 2, 2, unique=True),
           st.booleans())
    @example(1, 'foobar', ['id', 'slug'], True)
    @example(1, 'foobar', ['id', 'slug'], False)
    def test_get_object(self, pk, slug, fields, query_pk_and_slug):
        instance = sqlalchemy.SingleObjectMixin()
        instance.slug_field = fields[0]
        instance.query_pk_and_slug = query_pk_and_slug

        query = mock_query()

        instance.query = query

        rv = query.filter_by.return_value.one.return_value

        with patch.object(sqlalchemy, 'inspect') as m1:
            with patch.object(sqlalchemy, 'request') as m2:
                m1.return_value.primary_key = [Column(name=fields[1])]
                m2.view_args = {instance.pk_view_arg: pk,
                                instance.slug_view_arg: slug}

                assert instance.get_object() == rv

        if query_pk_and_slug:
            query.filter_by.assert_called_once_with(**{fields[0]: slug,
                                                       fields[1]: pk})
        else:
            query.filter_by.assert_called_once_with(**{fields[1]: pk})

    def test_get_object_neither(self):
        instance = sqlalchemy.SingleObjectMixin()
        instance.query = mock_query()

        with patch.object(sqlalchemy, 'request') as m:
            m.view_args = {}

            with pytest.raises(RuntimeError) as excinfo:
                instance.get_object()

        error = ('SingleObjectMixin must be called with either object pk or '
                 'slug')

        assert excinfo.value.args[0] == error

    @given(st.booleans(), st.booleans())
    def test_get_query(self, model, query):
        instance = sqlalchemy.SingleObjectMixin()
        if model:
            instance.model = Mock()

        if query:
            instance.query = Mock()

        if not model and not query:
            with pytest.raises(NotImplementedError) as excinfo:
                instance.get_query()

            error = ('SingleObjectMixin requires either a definition of '
                     "'query', 'model', or an implementation of 'get_query()'")

            assert excinfo.value.args[0] == error

        elif query:
            assert instance.get_query() == instance.query
        else:
            assert instance.get_query() == instance.model.query

    @given(st.text())
    @example('slug')
    def test_get_slug_field(self, slug):
        instance = sqlalchemy.SingleObjectMixin()
        instance.slug_field = slug

        assert instance.get_slug_field() == slug

    @given(st.booleans(), st.text(SLUG).map(camelize).map(str))
    def test_get_context_object_name(self, name, class_name):
        instance = sqlalchemy.SingleObjectMixin()
        instance.get_model = Mock(return_value=None)

        if name:
            instance.context_object_name = Mock()

        if class_name:
            instance.get_model.return_value = type(class_name, (object,), {})

        result = instance.get_context_object_name()

        if name:
            assert result == instance.context_object_name
        elif class_name:
            assert result == underscore(class_name)
        else:
            assert result is None

    @given(st.booleans(), st.text(), st.dictionaries(st.text(), st.text()))
    @example(True, 'foo', {'foo': 'bar'})
    @example(True, 'bar', {'object': 'baz'})
    @example(True, 'baz', {'object': 'bar', 'baz': 'foo'})
    @example(True, 'foo', {})
    @example(True, '', {})
    @example(True, '', {'object': 'foo bar'})
    @example(False, '', {})
    def test_get_context_data(self, obj, context_object_name, kwargs):
        instance = sqlalchemy.SingleObjectMixin()

        context = kwargs.copy()

        if obj:
            instance.object = Mock()
            context.setdefault('object', instance.object)

            if context_object_name:
                context.setdefault(context_object_name, instance.object)

        with patch.object(core.ContextMixin, 'get_context_data') as m1:
            with patch.object(instance, 'get_context_object_name') as m2:
                m2.return_value = context_object_name or None

                result = instance.get_context_data(**kwargs)

                m1.assert_called_once_with(**context)

                assert result == m1.return_value


class TestBaseDetailView(object):

    def test_get(self):
        instance = sqlalchemy.BaseDetailView()
        instance.get_object = get_object = Mock()
        instance.get_context_data = get_context_data = Mock()
        instance.create_response = render = Mock()

        assert instance.get() == render.return_value
        assert instance.object == get_object.return_value

        render.assert_called_once_with(get_context_data.return_value)

        get_context_data.assert_called_once_with()


class TestSingleObjectTemplateResponseMixin(object):

    @given(st.text(ASCII), st.text(ASCII), st.text(ASCII))
    def test_format_template_name(self, blueprint, name, suffix):
        instance = sqlalchemy.SingleObjectTemplateResponseMixin()
        instance.template_name_suffix = suffix

        with patch.object(sqlalchemy, 'request') as m:
            m.blueprint = blueprint or None

            if blueprint:
                prefix = blueprint + '/'
            else:
                prefix = ''

            expected = '{0}{1}{2}.html'.format(prefix, name, suffix)

            assert instance._format_template_name(name) == expected

    @given(st.text(), st.text(SLUG).map(camelize).map(str), st.text(SLUG),
           st.text())
    @example('', '', '', '')
    @example('foo.html', '', '', '')
    @example('',  'FooBar', '', '')
    @example('', '', 'foo', '')
    @example('', '', 'foo', 'bar')
    def test_get_template_list(self, template_name, class_name, field, value):
        model = class_name and type(class_name, (object,), {}) or None

        instance = sqlalchemy.SingleObjectTemplateResponseMixin()
        instance.template_name_field = field or None
        instance._format_template_name = fmt = Mock()
        instance.get_model = get_model = Mock(return_value=model)

        if field and value:
            instance.object = Mock()
            setattr(instance.object, field, value or None)

        p1 = patch.object(core.TemplateResponseMixin, 'get_template_list')

        with p1 as m1:
            if not template_name:
                m1.side_effect = NotImplementedError

                names = []

                if field and value:
                    names.append(value)

                if class_name:
                    names.append(fmt.return_value)

                if names:
                    assert instance.get_template_list() == names

                    if class_name:
                        fmt.assert_called_once_with(underscore(class_name))
                else:
                    with pytest.raises(NotImplementedError):
                        instance.get_template_list()

                get_model.assert_called_once_with()

            else:
                assert instance.get_template_list() == m1.return_value


class TestMultipleObjectMixin(object):

    @given(st.booleans(), st.booleans())
    def test_get_model(self, query, model):
        instance = sqlalchemy.MultipleObjectMixin()

        if query:
            instance.query = mock_query()

        if model:
            instance.model = Mock()

        cls = instance.get_model()

        if query:
            assert cls == instance.query._entities[0].entity_zero.class_
        elif model:
            assert cls == instance.model
        else:
            assert cls is None

    @given(st.booleans(), st.booleans(), st.integers(0, 10))
    @example(True, False, 0)
    @example(False, True, 0)
    @example(True, True, 0)
    @example(True, False, 10)
    @example(False, True, 10)
    @example(True, True, 10)
    @example(False, False, 0)
    def test_get_query(self, model, query, order_by):
        order_by = [Mock() for x in range(order_by)]

        instance = sqlalchemy.MultipleObjectMixin()
        instance.get_order_by = Mock(return_value=order_by)

        if query:
            instance.query = Mock()

        if model:
            instance.model = Mock()

        if not model and not query:
            with pytest.raises(NotImplementedError) as excinfo:
                instance.get_query()

            error = ('MultipleObjectMixin requires either a definition of '
                     "'query', 'model', or an implementation of 'get_query()'")

            assert excinfo.value.args[0] == error
        else:
            result = instance.get_query()

            if query:
                expected = instance.query
            else:
                expected = instance.model.query

            if order_by:
                expected.order_by.assert_called_once_with(*order_by)
                expected = expected.order_by.return_value

            assert result == expected

    def test_get_order_by(self):
        instance = sqlalchemy.MultipleObjectMixin()
        instance.order_by = Mock()

        assert instance.get_order_by() == instance.order_by

    def test_get_error_out(self):
        instance = sqlalchemy.MultipleObjectMixin()
        instance.error_out = Mock()

        assert instance.get_error_out() == instance.error_out

    def test_get_pagination(self):
        instance = sqlalchemy.MultipleObjectMixin()
        instance.pagination_class = Mock()
        query = Mock()
        page = Mock()
        per_page = Mock()
        total = Mock()
        items = Mock()

        result = instance.get_pagination(
            query, page, per_page, total, items)

        assert result == instance.pagination_class.return_value

        instance.pagination_class.assert_called_once_with(query, page,
                                                          per_page, total,
                                                          items)

    @given(st.text().filter(bool),
           st.one_of(st.none(), st.integers(), st.text(DIGITS).filter(bool),
                     st.text()),
           st.one_of(st.none(), st.integers(), st.text(DIGITS).filter(bool),
                     st.text()),
           st.booleans())
    @example('page', 1, None, False)
    @example('page', None, 2, False)
    @example('page', '3', '4', False)
    @example('page', 'five', None, False)
    @example('page', 6, 'sevent', False)
    @example('page', 'eight', None, True)
    @example('page', None, 'nine', True)
    @example('page', -10, None, True)
    @example('page', None, '-11', False)
    def test_get_page(self, page_arg, view_arg_value, arg_value, error_out):
        instance = sqlalchemy.MultipleObjectMixin()
        instance.page_arg = page_arg

        with patch.object(sqlalchemy, 'request') as m1:
            if view_arg_value is not None:
                m1.view_args = {page_arg: view_arg_value}
            else:
                m1.view_args = {}

            if arg_value is not None:
                m1.args = {page_arg: arg_value}
            else:
                m1.args = {}

            if view_arg_value is not None:
                expected = view_arg_value
            elif arg_value is not None:
                expected = arg_value
            else:
                expected = 1

            try:
                expected = int(expected)
            except ValueError:
                pass

            print(repr(expected))

            if error_out and (not isinstance(expected, integer_types) or
                              expected < 1):
                with pytest.raises(HTTPException) as excinfo:
                    instance.get_page(error_out)

                assert excinfo.value.code == 404
            else:
                if not isinstance(expected, integer_types) or expected < 1:
                    expected = 1

                assert instance.get_page(error_out) == expected

    def test_get_per_page(self):
        instance = sqlalchemy.MultipleObjectMixin()
        instance.per_page = Mock()

        assert instance.get_per_page() == instance.per_page

    @given(st.booleans(), st.text(SLUG).map(camelize).map(str))
    def test_get_context_object_name(self, name, class_name):
        instance = sqlalchemy.MultipleObjectMixin()
        instance.get_model = Mock(return_value=None)

        if name:
            instance.context_object_name = Mock()

        if class_name:
            instance.get_model.return_value = type(class_name, (object,), {})

        result = instance.get_context_object_name()

        if name:
            assert result == instance.context_object_name
        elif class_name:
            assert result == '{0}_list'.format(underscore(class_name))
        else:
            assert result is None

    @given(st.integers(1), st.integers(1, 100), st.integers(0),
           st.booleans())
    def test_apply_pagination(self, page, per_page, total, error_out):
        pages = int(ceil(total / float(per_page)))  # number of pages
        count = max(min(total - per_page * (page - 1), per_page), 0)

        instance = sqlalchemy.MultipleObjectMixin()
        instance.get_page = Mock(return_value=page)
        instance.get_pagination = Mock()

        pagination = instance.get_pagination.return_value
        pagination.pages = pages

        items = [object() for v in range(count)]

        object_list = mock_query()
        object_list_limit = object_list.limit
        object_list_offset = object_list_limit.return_value.offset
        object_list_all = object_list_offset.return_value.all
        object_list_order_by = object_list.order_by
        object_list_count = object_list_order_by.return_value.count

        object_list_all.return_value = items
        object_list_count.return_value = total

        offset = (page - 1) * per_page

        if count == 0 and page != 1 and error_out:
            with pytest.raises(HTTPException) as excinfo:
                instance.apply_pagination(object_list, per_page, error_out)

            assert excinfo.value.code == 404
        else:
            result = instance.apply_pagination(
                object_list, per_page, error_out)

            assert result == (pagination, pagination.items, pages > 1)

            instance.get_pagination.assert_called_once_with(object_list, page,
                                                            per_page, total,
                                                            items)

        object_list_limit.assert_called_once_with(per_page)
        object_list_offset.assert_called_once_with(offset)
        object_list_all.assert_called_once_with()

        instance.get_page.assert_called_once_with(error_out)

        if object_list_count.called:
            object_list_order_by.assert_called_once_with(None)

    @given(st.integers(0), st.booleans(), st.text(SLUG),
           st.dictionaries(st.text(SLUG), st.text()))
    def test_get_context_data(self, per_page, error_out, name, kwargs):
        paginated = [Mock(), Mock(), Mock()]

        instance = sqlalchemy.MultipleObjectMixin()
        instance.object_list = query = mock_query()
        instance.apply_pagination = pagination = Mock(return_value=paginated)
        instance.get_context_object_name = Mock(return_value=name or None)
        instance.get_per_page = Mock(return_value=per_page)
        instance.get_error_out = Mock(return_value=error_out)

        context = kwargs.copy()

        if per_page > 0:
            context.setdefault('pagination', paginated[0])
            context.setdefault('object_list', paginated[1])
            context.setdefault('is_paginated', paginated[2])
            if name:
                context.setdefault(name, paginated[1])
        else:
            context.setdefault('pagination', None)
            context.setdefault('object_list', query.all.return_value)
            context.setdefault('is_paginated', False)
            if name:
                context.setdefault(name, query.all.return_value)

        with patch.object(core.ContextMixin, 'get_context_data') as m:
            assert instance.get_context_data(**kwargs) == m.return_value

            m.assert_called_once_with(**context)

            if per_page > 0:
                pagination.assert_called_once_with(query, per_page, error_out)

        instance.get_context_object_name.assert_called_once_with()


class TestBaseListView(object):

    def test_get(self):
        instance = sqlalchemy.BaseListView()
        instance.get_query = get_query = Mock()
        instance.get_context_data = get_context_data = Mock()
        instance.create_response = render = Mock()

        assert instance.get() == render.return_value
        assert instance.object_list == get_query.return_value

        render.assert_called_once_with(get_context_data.return_value)


class TestMultipleObjectTemplateResponseMixin(object):

    @given(st.text(ASCII), st.text(ASCII), st.text(ASCII))
    def test_format_template_name(self, blueprint, name, suffix):
        instance = sqlalchemy.MultipleObjectTemplateResponseMixin()
        instance.template_name_suffix = suffix

        with patch.object(sqlalchemy, 'request') as m:
            m.blueprint = blueprint or None

            if blueprint:
                prefix = blueprint + '/'
            else:
                prefix = ''

            expected = '{0}{1}{2}.html'.format(prefix, name, suffix)

            assert instance._format_template_name(name) == expected

    @given(st.text(), st.text(SLUG).map(camelize).map(str))
    @example('', '')
    @example('foo.html', '')
    @example('',  'FooBar')
    def test_get_template_list(self, template_name, class_name):
        model = class_name and type(class_name, (object,), {}) or None

        instance = sqlalchemy.MultipleObjectTemplateResponseMixin()
        instance._format_template_name = fmt = Mock()
        instance.get_model = get_model = Mock(return_value=model)

        p1 = patch.object(core.TemplateResponseMixin, 'get_template_list')

        with p1 as m1:
            if not template_name:
                m1.side_effect = NotImplementedError

                names = []

                if class_name:
                    names.append(fmt.return_value)

                if names:
                    assert instance.get_template_list() == names

                    if class_name:
                        fmt.assert_called_once_with(underscore(class_name))
                else:
                    with pytest.raises(NotImplementedError):
                        instance.get_template_list()

                get_model.assert_called_once_with()

            else:
                assert instance.get_template_list() == m1.return_value


class TestModelFormMixin(object):

    @given(st.booleans(), st.lists(st.text(SLUG).filter(bool)))
    @example(True, ['foo', 'bar'])
    @example(True, [])
    @example(False, ['foo', 'bar'])
    @example(False, [])
    def test_get_form_class(self, form_class, fields):
        instance = sqlalchemy.ModelFormMixin()
        instance.get_model = Mock()
        instance.fields = fields or None
        if form_class:
            instance.form_class = Mock()

        with patch.object(sqlalchemy, 'model_form') as m:
            if form_class and fields:
                with pytest.raises(RuntimeError) as excinfo:
                    instance.get_form_class()

                error = ('ModelFormMixin requires either a definition of '
                         "'fields' or 'form_class', not both")

                assert excinfo.value.args[0] == error
            elif not form_class and not fields:
                with pytest.raises(RuntimeError) as excinfo:
                    instance.get_form_class()

                error = ("ModelFormMixin requires a definition of 'fields' "
                         "when 'form_class' is not defined")

                assert excinfo.value.args[0] == error
            elif form_class:
                assert instance.get_form_class() == instance.form_class
            else:
                assert instance.get_form_class() == m.return_value

                m.assert_called_once_with(instance.get_model.return_value,
                                          sqlalchemy.session, Form,
                                          instance.fields)

    @given(st.booleans(), st.dictionaries(st.text(SLUG), st.text()))
    @example(True, {'foo': 'abc', 'bar': 'def'})
    @example(False, {'foo': 'abc', 'bar': 'def'})
    def test_get_form_kwargs(self, obj, kwargs):
        instance = sqlalchemy.ModelFormMixin()
        expected = kwargs.copy()

        if obj:
            instance.object = Mock()
            expected['obj'] = instance.object

        with patch.object(core.FormMixin, 'get_form_kwargs') as m:
            m.return_value = kwargs

            assert instance.get_form_kwargs() == expected

            m.assert_called_once_with()

    @given(st.dictionaries(st.text(SLUG).filter(nondigit),
                           st.text(SLUG)))
    @example({'foo': 'abc', 'bar': 'def'})
    @example({})
    def test_get_success_url(self, kwargs):
        success_url = '/'.join('{{{0}}}'.format(k) for k in iterkeys(kwargs))

        instance = sqlalchemy.ModelFormMixin()
        instance.success_url = success_url or None
        instance.object = type('foo', (object,), {})()

        for k, v in iteritems(kwargs):
            setattr(instance.object, k, v)

        if not success_url:
            with pytest.raises(NotImplementedError) as excinfo:
                instance.get_success_url()

            error = ('ModelFormMixin requires either a definition of '
                     "'success_url' or an implementation of "
                     "'get_success_url()'")

            assert excinfo.value.args[0] == error
        else:
            assert instance.get_success_url() == success_url.format(**kwargs)

    @given(st.booleans())
    def test_form_valid(self, existing):
        instance = sqlalchemy.ModelFormMixin()
        if existing:
            instance.object = obj = Mock()
        instance.model = Mock()

        form = Mock()

        mocks = Mock()
        with patch.object(sqlalchemy, 'session') as m1:
            with patch.object(sqlalchemy.FormMixin, 'form_valid') as m2:
                with patch.object(sqlalchemy, '_touch') as m3:

                    mocks.attach_mock(m1, 'session')
                    mocks.attach_mock(form, 'form')
                    mocks.attach_mock(m3, 'touch')

                    assert instance.form_valid(form) == m2.return_value

                    m2.assert_called_once_with(form)

                    calls = [call.form.populate_obj(instance.object),
                             call.session.commit(),
                             call.touch(instance.object)]

                    if not existing:
                        assert instance.object == instance.model.return_value

                        calls.insert(0, call.session.add(instance.object))
                    else:
                        assert instance.object == obj

                    mocks.assert_has_calls(calls)


class TestBaseCreateView(object):

    @given(st.dictionaries(st.text(SLUG), st.text()))
    @example({'bar': 'baz'})
    def test_get(self, kwargs):
        instance = sqlalchemy.BaseCreateView()

        with patch.object(core.ProcessFormView, 'get') as m:
            assert instance.get(**kwargs) == m.return_value

            m.assert_called_once_with(**kwargs)

    @given(st.dictionaries(st.text(SLUG), st.text()))
    @example(['foo'], {'bar': 'baz'})
    def test_post(self, kwargs):
        instance = sqlalchemy.BaseCreateView()

        with patch.object(core.ProcessFormView, 'post') as m:
            assert instance.post(**kwargs) == m.return_value

            m.assert_called_once_with(**kwargs)


class TestBaseUpdateView(object):

    @given(st.dictionaries(st.text(SLUG), st.text()))
    @example({'bar': 'baz'})
    def test_get(self, kwargs):
        instance = sqlalchemy.BaseUpdateView()
        instance.get_object = Mock()

        with patch.object(core.ProcessFormView, 'get') as m:
            assert instance.get(**kwargs) == m.return_value
            assert instance.object == instance.get_object.return_value

            m.assert_called_once_with(**kwargs)

    @given(st.dictionaries(st.text(SLUG), st.text()))
    @example({'bar': 'baz'})
    def test_post(self, kwargs):
        instance = sqlalchemy.BaseUpdateView()
        instance.get_object = Mock()

        with patch.object(core.ProcessFormView, 'post') as m:
            assert instance.post(**kwargs) == m.return_value
            assert instance.object == instance.get_object.return_value

            m.assert_called_once_with(**kwargs)


class TestDeletionMixin(object):

    def test_delete(self):
        instance = sqlalchemy.DeletionMixin()
        instance.get_object = get_object = Mock()
        instance.get_success_url = get_success_url = Mock()

        mocks = Mock()

        with patch.object(sqlalchemy, 'session') as m1:
            with patch.object(sqlalchemy, 'redirect') as m2:
                with patch.object(sqlalchemy, '_touch') as m3:
                    mocks.attach_mock(m1, 'session')
                    mocks.attach_mock(m3, 'touch')

                    assert instance.delete() == m2.return_value
                    assert instance.object == get_object.return_value

                    calls = [call.session.delete(instance.object),
                             call.session.commit(),
                             call.touch(instance.object)]

                    mocks.assert_has_calls(calls)

                    m2.assert_called_once_with(get_success_url.return_value)

    @given(st.dictionaries(st.text(SLUG), st.text()))
    @example({'bar': 'baz'})
    def test_post(self, kwargs):
        instance = sqlalchemy.DeletionMixin()
        instance.delete = Mock()

        assert instance.post(**kwargs) == instance.delete.return_value

        instance.delete.assert_called_once_with(**kwargs)

    @given(st.dictionaries(st.text(SLUG).filter(nondigit),
                           st.text(SLUG)))
    @example({'foo': 'abc', 'bar': 'def'})
    @example({})
    def test_get_success_url(self, kwargs):
        success_url = '/'.join('{{{0}}}'.format(k) for k in iterkeys(kwargs))

        instance = sqlalchemy.DeletionMixin()
        instance.success_url = success_url or None
        instance.object = type('foo', (object,), {})()

        for k, v in iteritems(kwargs):
            setattr(instance.object, k, v)

        if not success_url:
            with pytest.raises(NotImplementedError) as excinfo:
                instance.get_success_url()

            error = ('DeletionMixin requires either a definition of '
                     "'success_url' or an implementation of "
                     "'get_success_url()'")

            assert excinfo.value.args[0] == error
        else:
            assert instance.get_success_url() == success_url.format(**kwargs)
