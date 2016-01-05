import pytest
from hypothesis import strategies as st
from hypothesis import example, given
from werkzeug.datastructures import CombinedMultiDict, ImmutableMultiDict
from werkzeug.exceptions import HTTPException
from werkzeug.routing import BuildError
from werkzeug.urls import url_encode, url_parse

from flask_generic_views import core
from flask_generic_views._compat import iteritems, iterkeys
from tests.utils import ASCII, SLUG, nondigit

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


class TestView(object):

    @given(st.dictionaries(st.text(SLUG), st.text(), average_size=2))
    def test_init(self, kwargs):
        instance = core.View(**kwargs)

        for k, v in iteritems(kwargs):
            assert getattr(instance, k) == v


class TestContextMixin(object):

    @given(st.dictionaries(st.text(ASCII), st.text()))
    @example({})
    @example({'view': '123'})
    @example({'foo': 'bar'})
    def test_get_context_data(self, kwargs):
        instance = core.ContextMixin()

        context = kwargs.copy()
        context.setdefault('view', instance)

        assert instance.get_context_data(**kwargs) == context


class TestTemplateResponseMixin(object):

    @given(st.text())
    @example('untitled.html')
    @example('')
    def test_get_template_list(self, template_name):
        instance = core.TemplateResponseMixin()
        instance.template_name = template_name or None

        if not template_name:
            with pytest.raises(NotImplementedError) as excinfo:
                instance.get_template_list()

            error = ('TemplateResponseMixin requires either a definition of '
                     "'template_name' or an implementation of "
                     "'get_template_list()'")

            assert excinfo.value.args[0] == error
        else:
            assert instance.get_template_list() == [template_name]

    @given(st.dictionaries(st.text(), st.text()), st.text(),
           st.dictionaries(st.text(ASCII), st.text()))
    @example({}, 'text/html', {})
    @example({'foo': 'bar', 'baz': '123'}, 'text/html', {})
    @example({}, 'text/html', {'mimetype': 'text/plain'})
    def test_create_response(self, context, mimetype, kwargs):
        instance = core.TemplateResponseMixin()
        instance.get_template_list = template_names = Mock()
        instance.mimetype = mimetype
        instance.response_class = response_class = Mock()

        response_kwargs = kwargs.copy()
        response_kwargs.setdefault('mimetype', mimetype)

        with patch.object(core, 'render_template') as m:
            response = instance.create_response(context, **kwargs)

            assert response == response_class.return_value

            m.assert_called_once_with(template_names.return_value, **context)

        response_class.assert_called_once_with(m.return_value,
                                               **response_kwargs)


class TestTemplateView(object):

    @given(st.text(), st.dictionaries(st.text(ASCII), st.text()))
    @example({'foo': 'bar'})
    @example({})
    def test_get(self, kwargs):
        instance = core.TemplateView()
        instance.get_context_data = get_context_data = Mock()
        instance.create_response = create_response = Mock()

        assert instance.get(**kwargs) == create_response.return_value

        get_context_data.assert_called_once_with(**kwargs)

        create_response.called_with(get_context_data.return_value)


class TestRedirectView(object):

    @given(st.dictionaries(st.text(SLUG).filter(nondigit),
                           st.text(SLUG)))
    @example({'foo': 'abc', 'bar': 'def'})
    @example({})
    def test_get_redirect_url_with_url(self, kwargs):
        url = '/'.join('{{{0}}}'.format(k) for k in iterkeys(kwargs))

        instance = core.RedirectView(url=url)

        assert instance.get_redirect_url(**kwargs) == url.format(**kwargs)

    @given(st.text(SLUG + '/').filter(lambda x: '//' not in x), st.text(SLUG),
           st.dictionaries(st.text(SLUG), st.text()),
           st.dictionaries(st.text(), st.text()))
    @example('/foo/bar', 'foobar', {'foo': 'bar'}, {'baz': 'abc'})
    @example('', 'foobar', {'foo': 'bar'}, {'baz': 'abc'})
    def test_get_redirect_url_endpoint(self, url, endpoint, kwargs, qs):
        instance = core.RedirectView(endpoint=endpoint)

        return_value = url_parse(url).replace(query=url_encode(qs)).to_url()

        with patch.object(core, 'url_for') as m:
            if url:
                m.return_value = return_value
            else:
                m.side_effect = BuildError(endpoint, kwargs, 'GET')

            assert instance.get_redirect_url(**kwargs) == (url or None)

            m.assert_called_once_with(endpoint, **kwargs)

    @given(st.text(SLUG + '/'), st.text(SLUG))
    @example('/foo/bar', 'foo_bar')
    def test_get_redircet_url_favors_url(self, url, endpoint):
        instance = core.RedirectView(url=url, endpoint=endpoint)

        assert instance.get_redirect_url() == url

    def test_get_redirect_url_with_neither(self):
        instance = core.RedirectView()

        assert instance.get_redirect_url() is None

    @given(st.text(SLUG + '/'), st.dictionaries(st.text(), st.text()))
    @example('/foo/bar', {'foo': 'abc', 'bar': 'def'})
    def test_get_redirect_url_with_query_string(self, url, qs):
        instance = core.RedirectView(url=url, query_string=True)

        result = url_parse(url).replace(query=url_encode(qs)).to_url()

        with patch.object(core, 'request') as m:
            m.environ = {'QUERY_STRING': url_encode(qs)}

            assert instance.get_redirect_url() == result

    @given(st.text(SLUG + '/'), st.booleans(),
           st.dictionaries(st.text(SLUG), st.text()))
    @example('/foo/bar', True, {'foo': 'abc'})
    @example('/foo/bar', False, {'foo': 'abc'})
    @example('', True, {'foo': 'abc'})
    @example('', False, {'foo': 'abc'})
    def test_dispatch_request(self, url, permanent, kwargs):
        instance = core.RedirectView(permanent=permanent)

        instance.get_redirect_url = Mock(return_value=url or None)

        if url:
            with patch.object(core, 'redirect') as m:
                assert instance.dispatch_request(**kwargs) == m.return_value

                if permanent:
                    m.assert_called_once_with(url, code=301)
                else:
                    m.assert_called_once_with(url)

            instance.get_redirect_url.asset_called_once_with(**kwargs)
        else:
            with pytest.raises(HTTPException) as extinfo:
                instance.dispatch_request(**kwargs)

            response = extinfo.value.get_response()

            assert response.status_code == 410


class TestFormMixin(object):

    def test_get_data(self):
        instance = core.FormMixin()
        instance.data = Mock()

        assert instance.get_data() == instance.data.copy.return_value

    def test_get_prefix(self):
        instance = core.FormMixin()
        instance.prefix = Mock()

        assert instance.get_prefix() == instance.prefix

    @given(st.dictionaries(st.text(), st.text(), ImmutableMultiDict),
           st.dictionaries(st.text(), st.text(), ImmutableMultiDict))
    def test_get_formdata(self, form, files):
        instance = core.FormMixin()

        data = CombinedMultiDict([form, files])

        with patch.object(core, 'request') as m:
            m.form = form
            m.files = files

            assert instance.get_formdata() == data

    @given(st.sampled_from(['GET', 'HEAD', 'POST', 'PUT']))
    def test_get_form_kwargs(self, method):
        instance = core.FormMixin()
        instance.get_data = Mock()
        instance.get_prefix = Mock()
        instance.get_formdata = Mock()

        with patch.object(core, 'request') as m:
            m.method = method

            kwargs = {'data': instance.get_data.return_value,
                      'prefix': instance.get_prefix.return_value}

            if method in ('POST', 'PUT'):
                kwargs['formdata'] = instance.get_formdata.return_value

            assert instance.get_form_kwargs() == kwargs

    def test_get_form_class(self):
        instance = core.FormMixin()
        instance.form_class = Mock()

        assert instance.get_form_class() == instance.form_class

        instance = core.FormMixin()
        with pytest.raises(NotImplementedError) as excinfo:
            instance.get_form_class()

        error = ("FormMixin requires either a definition of 'form_class' or "
                 "an implementation of 'get_form_class()'")

        assert excinfo.value.args[0] == error

    @given(st.dictionaries(st.text(SLUG), st.text()))
    def test_get_form(self, kwargs):
        instance = core.FormMixin()
        instance.get_form_kwargs = lambda: kwargs
        instance.form_class = Mock()

        assert instance.get_form() == instance.form_class.return_value

        instance.form_class.assert_called_once_with(**kwargs)

    def test_get_success_url(self):
        instance = core.FormMixin()
        instance.success_url = Mock()
        assert instance.get_success_url() == instance.success_url

        instance = core.FormMixin()
        with pytest.raises(NotImplementedError) as excinfo:
            instance.get_success_url()

        error = ("FormMixin requires either a definition of 'success_url' "
                 "or an implementation of 'get_success_url()'")

        assert excinfo.value.args[0] == error

    def test_form_valid(self):
        instance = core.FormMixin()
        instance.get_success_url = Mock()

        with patch.object(core, 'redirect') as m:
            assert instance.form_valid(None) == m.return_value

            m.asset_called_once_with(instance.get_success_url.return_value)

    def test_form_invalid(self):
        instance = core.FormMixin()
        instance.get_context_data = get_context_data = Mock()
        instance.create_response = render = Mock()

        form = Mock()

        assert instance.form_invalid(form) == render.return_value

        get_context_data.assert_called_once_with(form=form)
        render.assert_called_once_with(get_context_data.return_value)

    @given(kwargs=st.dictionaries(st.text(SLUG), st.text()))
    def test_get_context_data(self, kwargs):
        instance = core.FormMixin()
        instance.get_form = Mock()

        context = kwargs.copy()
        context.setdefault('form', instance.get_form.return_value)

        with patch.object(core.ContextMixin, 'get_context_data') as m:
            assert instance.get_context_data(**kwargs) == m.return_value

            m.assert_called_once_with(**context)


class TestProcessFormView(object):

    def test_get(self):
        instance = core.ProcessFormView()
        instance.get_context_data = get_context_data = Mock()
        instance.create_response = render = Mock()

        assert instance.get() == render.return_value

        render.assert_called_once_with(get_context_data.return_value)

    @given(st.booleans())
    def test_post(self, valid):
        form = Mock()
        form.validate.return_value = valid

        instance = core.ProcessFormView()
        instance.get_form = lambda: form
        instance.form_valid = Mock()
        instance.form_invalid = Mock()

        if valid:
            assert instance.post() == instance.form_valid.return_value
            instance.form_valid.called_once_wtih(form)
            instance.form_invalid.assert_not_called()
        else:
            assert instance.post() == instance.form_invalid.return_value
            instance.form_invalid.called_once_wtih(form)
            instance.form_valid.assert_not_called()

    @given(st.dictionaries(st.text(SLUG), st.text()))
    @example({'bar': 'baz'})
    def test_put(self, kwargs):
        instance = core.ProcessFormView()
        instance.post = Mock()

        assert instance.put(**kwargs) == instance.post.return_value

        instance.post.assert_called_once_with(**kwargs)
