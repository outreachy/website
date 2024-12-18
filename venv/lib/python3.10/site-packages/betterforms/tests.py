import unittest  # NOQA

from unittest import mock

import django
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.db import models
from django.test import TestCase
from django.template.loader import render_to_string
from django.http import QueryDict

from betterforms.changelist import (
    BaseChangeListForm, SearchForm, SortForm, HeaderSet, Header, BoundHeader
)
from betterforms.forms import (
    BetterForm, BetterModelForm, Fieldset, BoundFieldset, flatten_to_tuple,
)


class TestUtils(TestCase):
    def test_flatten(self):
        fields1 = ('a', 'b', 'c')
        self.assertTupleEqual(flatten_to_tuple(fields1), fields1)

        fields2 = ('a', ('b', 'c'), 'd')
        self.assertTupleEqual(flatten_to_tuple(fields2), ('a', 'b', 'c', 'd'))

        fields3 = ('a', ('b', 'c'), 'd', ('e', ('f', 'g', ('h',)), 'i'))
        self.assertTupleEqual(flatten_to_tuple(fields3), ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'))


class TestFieldSets(TestCase):
    def test_basic_fieldset(self):
        fields = ('a', 'b', 'c')
        fieldset = Fieldset('the_name', fields=fields)
        self.assertEqual(fieldset.name, 'the_name')
        self.assertTupleEqual(fields, fieldset.fields)

    def test_nested_fieldset(self):
        fields = ('a', ('b', 'c'), 'd')
        fieldset = Fieldset('the_name', fields=fields)
        self.assertTupleEqual(flatten_to_tuple(fields), fieldset.fields)
        iterated = tuple(iter(fieldset))
        self.assertEqual(iterated[0], 'a')
        self.assertTupleEqual(iterated[1].fields, ('b', 'c'))
        self.assertEqual(iterated[2], 'd')

    def test_named_nested_fieldset(self):
        fields = ('a', ('sub_name', {'fields': ('b', 'c')}), 'd')
        fieldset = Fieldset('the_name', fields=fields)
        self.assertTupleEqual(fieldset.fields, ('a', 'b', 'c', 'd'))
        fieldsets = tuple(iter(fieldset))
        self.assertEqual(fieldsets[0], 'a')
        self.assertTupleEqual(fieldsets[1].fields, ('b', 'c'))
        self.assertEqual(fieldsets[1].name, 'sub_name')
        self.assertEqual(fieldsets[2], 'd')

    def test_deeply_nested_fieldsets(self):
        fields = ('a', ('b', 'c'), 'd', ('e', ('f', 'g', ('h',)), 'i'))
        fieldset = Fieldset('the_name', fields=fields)
        self.assertTupleEqual(flatten_to_tuple(fields), fieldset.fields)

    def test_fieldset_as_row_item(self):
        fields = ('a', Fieldset('sub_name', fields=['b', 'c']))
        fieldset = Fieldset('the_name', fields=fields)
        self.assertTupleEqual(fieldset.fields, ('a', 'b', 'c'))

    def test_nonzero_fieldset(self):
        fieldset1 = Fieldset('the_name', fields=[])
        self.assertFalse(fieldset1)

        fieldset2 = Fieldset('the_name', fields=['a'])
        self.assertTrue(fieldset2)

    def test_assigning_template_name(self):
        fieldset1 = Fieldset('the_name', fields=['a'])
        self.assertIsNone(fieldset1.template_name)
        fieldset2 = Fieldset('the_name', fields=['a'], template_name='some_custom_template.html')
        self.assertEqual(fieldset2.template_name, 'some_custom_template.html')


class TestFieldsetDeclarationSyntax(TestCase):
    def test_admin_style_declaration(self):
        class TestForm(BetterForm):
            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()
            d = forms.CharField()

            class Meta:
                fieldsets = (
                    ('first', {'fields': ('a',)}),
                    ('second', {'fields': ('b', 'c')}),
                    ('third', {'fields': ('d',)}),
                )
        form = TestForm()
        fieldsets = [fieldset for fieldset in form.fieldsets]
        self.assertEqual(fieldsets[0].name, 'first')
        self.assertTupleEqual(fieldsets[0].fieldset.fields, ('a',))
        self.assertEqual(fieldsets[1].name, 'second')
        self.assertTupleEqual(fieldsets[1].fieldset.fields, ('b', 'c'))
        self.assertEqual(fieldsets[2].name, 'third')
        self.assertTupleEqual(fieldsets[2].fieldset.fields, ('d',))
        self.assertIsInstance(fieldsets[0], BoundFieldset)

    def test_bare_fields_style_declaration(self):
        class TestForm(BetterForm):
            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()
            d = forms.CharField()

            class Meta:
                fieldsets = ('a', ('b', 'c'), 'd')
        form = TestForm()
        fieldsets = [fieldset for fieldset in form.fieldsets]
        self.assertEqual(fieldsets[0].field, form.fields['a'])
        self.assertEqual(fieldsets[1].name, '__base_fieldset___1')
        self.assertTupleEqual(fieldsets[1].fieldset.fields, ('b', 'c'))
        self.assertEqual(fieldsets[2].field, form.fields['d'])
        self.assertIsInstance(fieldsets[0], forms.BoundField)
        self.assertIsInstance(fieldsets[1], BoundFieldset)
        self.assertIsInstance(fieldsets[2], forms.BoundField)


class TestBetterForm(TestCase):
    def setUp(self):
        class TestForm(BetterForm):
            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()

            class Meta:
                fieldsets = (
                    ('first', {'fields': ('a', 'b')}),
                    ('second', {'fields': ('c',)}),
                )
        self.TestForm = TestForm

    def test_name_lookups(self):
        form = self.TestForm()
        fieldsets = [fieldset for fieldset in form.fieldsets]
        # field lookups
        self.assertEqual(form['a'].field, fieldsets[0]['a'].field)
        # fieldset lookups
        self.assertEqual(form['first'].fieldset, fieldsets[0].fieldset)
        self.assertEqual(form['second'].fieldset, fieldsets[1].fieldset)

    def test_index_lookups(self):
        form = self.TestForm()
        # field lookups
        self.assertEqual(form['a'].field, form.fieldsets[0][0].field)
        # fieldset lookups
        self.assertEqual(form['first'].fieldset, form.fieldsets[0].fieldset)
        self.assertEqual(form['second'].fieldset, form.fieldsets[1].fieldset)

    def test_field_to_fieldset_name_conflict(self):
        with self.assertRaises(AttributeError):
            class NameConflictForm(self.TestForm):
                class Meta:
                    fieldsets = (
                        ('first', {'fields': ('a', 'b')}),
                        ('first', {'fields': ('c',)}),
                    )

    def test_duplicate_name_in_fieldset(self):
        with self.assertRaises(AttributeError):
            class NameConflictForm(self.TestForm):
                class Meta:
                    fieldsets = (
                        ('first', {'fields': ('a', 'a')}),
                        ('second', {'fields': ('c',)}),
                    )

    def test_field_error(self):
        data = {'a': 'a', 'b': 'b', 'c': 'c'}
        form = self.TestForm(data)
        self.assertTrue(form.is_valid())

        form.field_error('a', 'test')
        self.assertFalse(form.is_valid())

    def test_form_error(self):
        data = {'a': 'a', 'b': 'b', 'c': 'c'}
        form = self.TestForm(data)
        self.assertTrue(form.is_valid())

        form.form_error('test')
        self.assertFalse(form.is_valid())
        self.assertDictEqual(form.errors, {'__all__': [u'test']})

    def test_fieldset_error(self):
        data = {'a': 'a', 'b': 'b', 'c': 'c'}
        form = self.TestForm(data)
        self.assertTrue(form.is_valid())

        self.assertNotIn(form.fieldsets[0].fieldset.error_css_class, form.fieldsets[0].css_classes)

        form.field_error('first', 'test')
        self.assertFalse(form.is_valid())
        fieldsets = [fieldset for fieldset in form.fieldsets]
        self.assertTrue(fieldsets[0].errors)
        self.assertIn(form.fieldsets[0].fieldset.error_css_class, form.fieldsets[0].css_classes)

    def test_fieldset_css_classes(self):
        class TestForm(BetterForm):
            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()

            class Meta:
                fieldsets = (
                    ('first', {'fields': ('a', 'b')}),
                    ('second', {'fields': ('c',), 'css_classes': ['arst', 'tsra']}),
                )
        form = TestForm()
        self.assertIn('arst', form.fieldsets[1].css_classes)
        self.assertIn('tsra', form.fieldsets[1].css_classes)

    def test_fieldset_iteration(self):
        form = self.TestForm()
        self.assertTupleEqual(
            tuple(fieldset.fieldset for fieldset in form),
            tuple(fieldset.fieldset for fieldset in form.fieldsets),
        )

    def test_no_fieldsets(self):
        class TestForm(BetterForm):
            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()

        form = TestForm()
        fields_iter = sorted((field.field for field in form), key=id)
        fields_values = sorted(form.fields.values(), key=id)
        self.assertSequenceEqual(fields_iter, fields_values)


class TestBetterModelForm(TestCase):
    def setUp(self):
        class TestModel(models.Model):
            a = models.CharField(max_length=255)
            b = models.CharField(max_length=255)
            c = models.CharField(max_length=255)
            d = models.CharField(max_length=255)

        self.TestModel = TestModel

    def test_basic_fieldsets(self):
        class TestModelForm(BetterModelForm):
            class Meta:
                model = self.TestModel

                fieldsets = (
                    ('first', {'fields': ('a',)}),
                    ('second', {'fields': ('b', 'c')}),
                    ('third', {'fields': ('d',)}),
                )
        form = TestModelForm()
        fieldsets = [fieldset for fieldset in form.fieldsets]
        self.assertEqual(fieldsets[0].name, 'first')
        self.assertEqual(fieldsets[1].name, 'second')
        self.assertEqual(fieldsets[2].name, 'third')
        self.assertTupleEqual(fieldsets[0].fieldset.fields, ('a',))
        self.assertTupleEqual(fieldsets[1].fieldset.fields, ('b', 'c'))
        self.assertTupleEqual(fieldsets[2].fieldset.fields, ('d',))

    def test_fields_meta_attribute(self):
        class TestModelForm1(BetterModelForm):
            class Meta:
                model = self.TestModel
                fieldsets = (
                    ('first', {'fields': ('a',)}),
                    ('second', {'fields': ('b', 'c')}),
                    ('third', {'fields': ('d',)}),
                )
        self.assertTrue(hasattr(TestModelForm1.Meta, 'fields'))
        self.assertTupleEqual(TestModelForm1.Meta.fields, ('a', 'b', 'c', 'd'))

        class TestModelForm2(BetterModelForm):
            class Meta:
                model = self.TestModel
                fieldsets = (
                    ('first', {'fields': ('a',)}),
                    ('second', {'fields': ('b', 'c')}),
                    ('third', {'fields': ('d',)}),
                )
                fields = ('a', 'b', 'd')

        self.assertTrue(hasattr(TestModelForm2.Meta, 'fields'))
        self.assertTupleEqual(TestModelForm2.Meta.fields, ('a', 'b', 'd'))

        class TestModelForm3(TestModelForm2):
            pass

        self.assertTrue(hasattr(TestModelForm3.Meta, 'fields'))
        self.assertTupleEqual(TestModelForm3.Meta.fields, ('a', 'b', 'd'))

        class TestModelForm4(TestModelForm2):
            class Meta(TestModelForm2.Meta):
                fieldsets = (
                    ('first', {'fields': ('a', 'c')}),
                    ('third', {'fields': ('d',)}),
                )

        self.assertTrue(hasattr(TestModelForm4.Meta, 'fields'))
        self.assertTupleEqual(TestModelForm4.Meta.fields, ('a', 'c', 'd'))


class TestFormRendering(TestCase):
    def setUp(self):
        class TestForm(BetterForm):
            # Set the label_suffix to an empty string for consistent results
            # across Django 1.5 and 1.6.
            label_suffix = ''

            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()

            class Meta:
                fieldsets = (
                    ('first', {'fields': ('a', 'b')}),
                    ('second', {'fields': ('c',)}),
                )
        self.TestForm = TestForm

    def test_non_fieldset_form_rendering(self):
        class TestForm(BetterForm):
            # Set the label_suffix to an empty string for consistent results
            # across Django 1.5 and 1.6.
            label_suffix = ''

            a = forms.CharField()
            b = forms.CharField(required=False)
            c = forms.CharField()

        form = TestForm()
        env = {
            'form': form,
            'no_head': True,
            'fieldset_template_name': 'betterforms/fieldset_as_div.html',
            'field_template_name': 'betterforms/field_as_div.html',
        }
        test = """
            <div class="required a formField">
                <label class="required" for="id_a">A</label>
                <input id="id_a" name="a" required type="text" />
            </div>
            <div class="b formField">
                <label for="id_b">B</label>
                <input id="id_b" name="b" type="text" />
            </div>
            <div class="required c formField">
                <label class="required" for="id_c">C</label>
                <input id="id_c" name="c" required type="text" />
            </div>
            """

        self.assertHTMLEqual(
            render_to_string('betterforms/form_as_fieldsets.html', env),
            test,
        )
        form.field_error('a', 'this is an error message')
        test = """
            <div class="required error a formField">
                <label class="required" for="id_a">A</label>
                <input id="id_a" name="a" required type="text" />
                <ul class="errorlist"><li>this is an error message</li></ul>
            </div>
            <div class="b formField">
                <label for="id_b">B</label>
                <input id="id_b" name="b" type="text" />
            </div>
            <div class="required c formField">
                <label class="required" for="id_c">C</label>
                <input id="id_c" name="c" required type="text" />
            </div>
            """

        self.assertHTMLEqual(
            render_to_string('betterforms/form_as_fieldsets.html', env),
            test,
        )

    def test_include_tag_rendering(self):
        form = self.TestForm()
        env = {
            'form': form,
            'no_head': True,
            'fieldset_template_name': 'betterforms/fieldset_as_div.html',
            'field_template_name': 'betterforms/field_as_div.html',
        }
        test = """
            <fieldset class="formFieldset first">
                <div class="required a formField">
                    <label class="required" for="id_a">A</label>
                    <input id="id_a" name="a" required type="text" />
                </div>
                <div class="required b formField">
                    <label class="required" for="id_b">B</label>
                    <input id="id_b" name="b" required type="text" />
                </div>
            </fieldset>
            <fieldset class="formFieldset second">
                <div class="required c formField">
                    <label class="required" for="id_c">C</label>
                    <input id="id_c" name="c" required type="text" />
                </div>
            </fieldset>
            """

        self.assertHTMLEqual(
            render_to_string('betterforms/form_as_fieldsets.html', env),
            test,
        )
        form.field_error('a', 'this is an error message')
        test = """
            <fieldset class="formFieldset first">
                <div class="required error a formField">
                    <label class="required" for="id_a">A</label>
                    <input id="id_a" name="a" required type="text" />
                    <ul class="errorlist"><li>this is an error message</li></ul>
                </div>
                <div class="required b formField">
                    <label class="required" for="id_b">B</label>
                    <input id="id_b" name="b" required type="text" />
                </div>
            </fieldset>
            <fieldset class="formFieldset second">
                <div class="required c formField">
                    <label class="required" for="id_c">C</label>
                    <input id="id_c" name="c" required type="text" />
                </div>
            </fieldset>
            """

        self.assertHTMLEqual(
            render_to_string('betterforms/form_as_fieldsets.html', env),
            test,
        )

    def test_fields_django_form_required(self):
        class TestForm(forms.Form):
            a = forms.CharField(label='A:')
            b = forms.CharField(label='B:', required=False)

        form = TestForm()

        env = {
            'form': form,
            'no_head': True,
            'fieldset_template_name': 'betterforms/fieldset_as_div.html',
            'field_template_name': 'betterforms/field_as_div.html',
        }
        test = """
            <div class="a formField required">
                <label for="id_a">A:</label>
                <input id="id_a" name="a" required type="text" />
            </div>
            <div class="b formField">
                <label for="id_b">B:</label>
                <input id="id_b" name="b" type="text" />
            </div>
            """

        self.assertHTMLEqual(
            render_to_string('betterforms/form_as_fieldsets.html', env),
            test,
        )

    @unittest.expectedFailure
    def test_form_to_str(self):
        # TODO: how do we test this
        assert False

    @unittest.expectedFailure
    def test_form_as_table(self):
        form = self.TestForm()
        form.as_table()

    @unittest.expectedFailure
    def test_form_as_ul(self):
        form = self.TestForm()
        form.as_ul()

    def test_form_as_p(self):
        form = self.TestForm()
        test = """
            <fieldset class="formFieldset first">
                <p class="required">
                    <label class="required" for="id_a">A</label>
                    <input id="id_a" name="a" required type="text" />
                </p>
                <p class="required">
                    <label class="required" for="id_b">B</label>
                    <input id="id_b" name="b" required type="text" />
                </p>
            </fieldset>
            <fieldset class="formFieldset second">
                <p class="required">
                    <label class="required" for="id_c">C</label>
                    <input id="id_c" name="c" required type="text" />
                </p>
            </fieldset>
            """

        self.assertHTMLEqual(
            form.as_p(),
            test,
        )

        form.field_error('a', 'this is an error')
        test = """
            <fieldset class="formFieldset first">
                <p class="required error">
                    <ul class="errorlist"><li>this is an error</li></ul>
                    <label class="required" for="id_a">A</label>
                    <input id="id_a" name="a" required type="text" />
                </p>
                <p class="required">
                    <label class="required" for="id_b">B</label>
                    <input id="id_b" name="b" required type="text" />
                </p>
            </fieldset>
            <fieldset class="formFieldset second">
                <p class="required">
                    <label class="required" for="id_c">C</label>
                    <input id="id_c" name="c" required type="text" />
                </p>
            </fieldset>
            """
        self.maxDiff=None

        self.assertHTMLEqual(
            form.as_p(),
            test,
        )

    def test_fieldset_legend(self):
        class TestForm(BetterForm):
            a = forms.CharField()
            b = forms.CharField()
            c = forms.CharField()

            label_suffix = ''

            class Meta:
                fieldsets = (
                    Fieldset('first', ('a', 'b'), legend='First Fieldset'),
                    Fieldset('second', ('c',), legend='Second Fieldset'),
                )

        form = TestForm()
        test = """
            <fieldset class="formFieldset first">
                <legend>First Fieldset</legend>
                <p class="required">
                    <label class="required" for="id_a">A</label>
                    <input id="id_a" name="a" required type="text" />
                </p>
                <p class="required">
                    <label class="required" for="id_b">B</label>
                    <input id="id_b" name="b" required type="text" />
                </p>
            </fieldset>
            <fieldset class="formFieldset second">
                <legend>Second Fieldset</legend>
                <p class="required">
                    <label class="required" for="id_c">C</label>
                    <input id="id_c" name="c" required type="text" />
                </p>
            </fieldset>
            """

        self.assertHTMLEqual(
            form.as_p(),
            test,
        )

    def test_css_classes_when_form_has_prefix(self):
        class TestForm(BetterForm):
            name = forms.CharField()
            label_suffix = ''

        form = TestForm(prefix="prefix")
        env = {'form': form, 'no_head': True}
        test = """
            <div class="required prefix-name name formField">
                <label class="required" for="id_prefix-name">Name</label>
                <input type="text" id="id_prefix-name" required name="prefix-name" />
            </div>
            """

        self.assertHTMLEqual(
            render_to_string('betterforms/form_as_fieldsets.html', env),
            test,
        )


class ChangeListModel(models.Model):
    field_a = models.CharField(max_length=255)
    field_b = models.CharField(max_length=255)
    field_c = models.TextField(max_length=255)


class TestChangleListQuerySetAPI(TestCase):
    def setUp(self):
        class TestChangeListForm(BaseChangeListForm):
            model = ChangeListModel
            foo = forms.CharField()
        self.TestChangeListForm = TestChangeListForm

        for i in range(5):
            ChangeListModel.objects.create(field_a=str(i))

    def test_with_model_declared(self):
        form = self.TestChangeListForm({})

        # base_queryset should default to Model.objects.all()
        self.assertTrue(form.base_queryset.count(), 5)

    def test_with_model_declaration_and_provided_queryset(self):
        form = self.TestChangeListForm({'foo': 'arst'}, queryset=ChangeListModel.objects.exclude(field_a='0').exclude(field_a='1'))

        self.assertTrue(form.base_queryset.count(), 3)
        form.full_clean()
        self.assertTrue(form.get_queryset().count(), 3)

    def test_missing_model_and_queryset(self):
        class TestChangeListForm(BaseChangeListForm):
            pass

        with self.assertRaises(AttributeError):
            TestChangeListForm()


class TestSearchFormAPI(TestCase):
    def setUp(self):
        ChangeListModel.objects.create(field_a='foo', field_b='bar', field_c='baz')
        ChangeListModel.objects.create(field_a='bar', field_b='baz')
        ChangeListModel.objects.create(field_a='baz')

    def test_requires_search_fields(self):
        class TheSearchForm(SearchForm):
            model = ChangeListModel

        with self.assertRaises(ImproperlyConfigured):
            TheSearchForm({})

    def test_passing_in_search_fields(self):
        class TheSearchForm(SearchForm):
            model = ChangeListModel

        form = TheSearchForm({}, search_fields=('field_a',))
        self.assertEqual(form.SEARCH_FIELDS, ('field_a',))

        form = TheSearchForm({}, search_fields=('field_a', 'field_b'))
        self.assertEqual(form.SEARCH_FIELDS, ('field_a', 'field_b'))

    def test_setting_search_fields_on_class(self):
        class TheSearchForm(SearchForm):
            SEARCH_FIELDS = ('field_a', 'field_b', 'field_c')
            model = ChangeListModel

        form = TheSearchForm({})
        self.assertEqual(form.SEARCH_FIELDS, ('field_a', 'field_b', 'field_c'))

    def test_overriding_search_fields_set_on_class(self):
        class TheSearchForm(SearchForm):
            SEARCH_FIELDS = ('field_a', 'field_b', 'field_c')
            model = ChangeListModel

        form = TheSearchForm({}, search_fields=('field_a', 'field_c'))
        self.assertEqual(form.SEARCH_FIELDS, ('field_a', 'field_c'))

    def test_searching(self):
        class TheSearchForm(SearchForm):
            SEARCH_FIELDS = ('field_a', 'field_b', 'field_c')
            model = ChangeListModel

        f = TheSearchForm({'q': 'foo'})
        f.full_clean()
        self.assertEqual(f.get_queryset().count(), 1)

        f = TheSearchForm({'q': 'bar'})
        f.full_clean()
        self.assertEqual(f.get_queryset().count(), 2)

        f = TheSearchForm({'q': 'baz'})
        f.full_clean()
        self.assertEqual(f.get_queryset().count(), 3)

    def test_searching_over_limited_fields(self):
        class TheSearchForm(SearchForm):
            SEARCH_FIELDS = ('field_a', 'field_c')
            model = ChangeListModel

        f = TheSearchForm({'q': 'foo'})
        f.full_clean()
        self.assertEqual(f.get_queryset().count(), 1)

        f = TheSearchForm({'q': 'bar'})
        f.full_clean()
        self.assertEqual(f.get_queryset().count(), 1)

        f = TheSearchForm({'q': 'baz'})
        f.full_clean()
        self.assertEqual(f.get_queryset().count(), 2)

    def test_case_insensitive(self):
        class TheSearchForm(SearchForm):
            SEARCH_FIELDS = ('field_a',)
            model = ChangeListModel

        self.assertFalse(TheSearchForm.CASE_SENSITIVE)

        upper_cased = ChangeListModel.objects.create(field_a='TeSt')
        lower_cased = ChangeListModel.objects.create(field_a='test')

        form = TheSearchForm({'q': 'Test'})
        form.full_clean()

        self.assertIn(upper_cased, form.get_queryset())
        self.assertIn(lower_cased, form.get_queryset())

    @unittest.skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3', 'Case Sensitive __contains queries are not supported on sqlite.')
    def test_case_sensitive(self):
        # TODO: make this test run on travis with postgres/mysql to be sure
        # this functionality actually works.
        class TheSearchForm(SearchForm):
            SEARCH_FIELDS = ('field_a', 'field_c')
            CASE_SENSITIVE = True
            model = ChangeListModel

        self.assertTrue(TheSearchForm.CASE_SENSITIVE)

        upper_cased = ChangeListModel.objects.create(field_a='TeSt')
        lower_cased = ChangeListModel.objects.create(field_a='test')

        form = TheSearchForm({'q': 'TeSt'})
        form.full_clean()

        self.assertIn(upper_cased, form.get_queryset())
        self.assertNotIn(lower_cased, form.get_queryset())


class TestHeaderAPI(TestCase):
    def test_header_bare_declaration(self):
        header = Header('field_a')

        self.assertTrue(header.is_sortable)
        self.assertEqual(header.name, 'field_a')
        self.assertEqual(header.column_name, 'field_a')
        self.assertEqual(header.label, 'Field a')

    def test_header_with_label_declaration(self):
        header = Header('field_a', 'Test Label')

        self.assertEqual(header.label, 'Test Label')

    def test_header_with_column_declared(self):
        header = Header('not_a_column', column_name='field_a')

        self.assertEqual(header.name, 'not_a_column')
        self.assertEqual(header.column_name, 'field_a')

    def test_non_sortable_header(self):
        header = Header('field_a', is_sortable=False)

        self.assertFalse(header.is_sortable)


class TestHeaderSetAPI(TestCase):
    def test_header_names_must_be_unique(self):
        HEADERS = (
            Header('field_a'),
            Header('field_a'),
        )
        with self.assertRaises(ImproperlyConfigured):
            HeaderSet(None, HEADERS)

    def test_header_set_declared_as_header_classes(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b', 'Test Label'),
            Header('test_name', 'Test Name', column_name='field_c'),
            Header('created_at', is_sortable=False),
        )
        self.do_header_set_assertions(HEADERS)

    def test_header_set_declared_as_args(self):
        HEADERS = (
            ('field_a',),
            ('field_b', 'Test Label'),
            ('test_name', 'Test Name', 'field_c'),
            ('created_at', None, None, False),
        )
        self.do_header_set_assertions(HEADERS)

    def test_header_set_declared_as_name_and_kwargs(self):
        HEADERS = (
            ('field_a', {}),
            ('field_b', {'label': 'Test Label'}),
            ('test_name', {'label': 'Test Name', 'column_name': 'field_c'}),
            ('created_at', {'is_sortable': False}),
        )
        self.do_header_set_assertions(HEADERS)

    def test_header_set_mixed_declaration_styles(self):
        HEADERS = (
            'field_a',
            ('field_b', 'Test Label'),
            ('test_name', {'label': 'Test Name', 'column_name': 'field_c'}),
            Header('created_at', is_sortable=False),
        )
        self.do_header_set_assertions(HEADERS)

    def test_bad_header_declaration(self):
        HEADERS = (
            {'bad_declaration': 'test'},
            ('field_b', 'Test Label'),
            ('test_name', {'label': 'Test Name', 'column_name': 'field_c'}),
            Header('created_at', is_sortable=False),
        )
        with self.assertRaises(ImproperlyConfigured):
            self.do_header_set_assertions(HEADERS)

    def do_header_set_assertions(self, HEADERS):
        header_set = HeaderSet(None, HEADERS)

        self.assertTrue(len(header_set), 4)
        self.assertSequenceEqual(
            [header.name for header in header_set.headers.values()],
            ('field_a', 'field_b', 'test_name', 'created_at'),
        )
        self.assertSequenceEqual(
            [header.label for header in header_set.headers.values()],
            ('Field a', 'Test Label', 'Test Name', 'Created at'),
        )
        self.assertSequenceEqual(
            [header.column_name for header in header_set.headers.values()],
            ('field_a', 'field_b', 'field_c', None),
        )
        self.assertSequenceEqual(
            [header.is_sortable for header in header_set.headers.values()],
            (True, True, True, False),
        )

    def test_iteration_yields_bound_headers(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b', 'Test Label'),
            Header('test_name', 'Test Name', column_name='field_c'),
            Header('created_at', is_sortable=False),
        )
        form = mock.NonCallableMagicMock(forms.Form)
        form.prefix = None
        header_set = HeaderSet(form, HEADERS)

        self.assertTrue(all((
            isinstance(header, BoundHeader) for header in header_set
        )))

    def test_index_and_key_lookups(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b', 'Test Label'),
            Header('test_name', 'Test Name', column_name='field_c'),
            Header('created_at', is_sortable=False),
        )
        form = mock.NonCallableMagicMock(forms.Form)
        form.prefix = None
        header_set = HeaderSet(form, HEADERS)

        self.assertIsInstance(header_set[0], BoundHeader)
        self.assertEqual(header_set[0].header, HEADERS[0])

        self.assertIsInstance(header_set['field_b'], BoundHeader)
        self.assertEqual(header_set['field_b'].header, HEADERS[1])


class TestBoundHeaderAPI(TestCase):
    def setUp(self):
        self.HEADERS = (
            Header('test_name', 'Test Label', 'column_name', is_sortable=True),
        )
        self.form = mock.NonCallableMagicMock(forms.Form)
        self.form.prefix = None
        self.form.HEADERS = self.HEADERS

    def test_bound_header_pass_through_properties(self):
        header_set = HeaderSet(self.form, self.HEADERS)

        self.assertEqual(header_set[0].header, self.HEADERS[0])
        self.assertEqual(header_set[0].name, self.HEADERS[0].name)
        self.assertEqual(header_set[0].label, self.HEADERS[0].label)
        self.assertEqual(header_set[0].column_name, self.HEADERS[0].column_name)
        self.assertEqual(header_set[0].is_sortable, self.HEADERS[0].is_sortable)

    def test_sort_parameter_no_prefix(self):
        self.assertIsNone(self.form.prefix)
        header = HeaderSet(self.form, self.HEADERS)[0]

        self.assertEqual(header.param, 'sorts')

    def test_sort_parameter_with_prefix(self):
        self.form.prefix = 'test'
        header = HeaderSet(self.form, self.HEADERS)[0]

        self.assertEqual(header.param, 'test-sorts')

    def test_is_active_property_while_not_active(self):
        header = HeaderSet(self.form, self.HEADERS)[0]

        self.assertFalse(header.is_active)
        self.assertFalse(header.is_ascending)
        self.assertFalse(header.is_descending)

    def test_is_active_property_while_active_and_ascending(self):
        self.form.data = {'sorts': '1'}
        self.form.cleaned_data = {'sorts': [1]}
        header = HeaderSet(self.form, self.HEADERS)[0]

        self.assertTrue(header.is_active)
        self.assertTrue(header.is_ascending)
        self.assertFalse(header.is_descending)

    def test_is_active_property_while_active_and_descending(self):
        self.form.data = {'sorts': '-1'}
        self.form.cleaned_data = {'sorts': [-1]}
        header = HeaderSet(self.form, self.HEADERS)[0]

        self.assertTrue(header.is_active)
        self.assertFalse(header.is_ascending)
        self.assertTrue(header.is_descending)

    def test_add_to_sorts_with_no_sorts(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b'),
            Header('field_c'),
        )
        self.form.data = {}
        self.form.cleaned_data = {'sorts': []}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)
        self.assertEqual(header_set['field_a'].add_to_sorts(), [1])
        self.assertEqual(header_set['field_b'].add_to_sorts(), [2])
        self.assertEqual(header_set['field_c'].add_to_sorts(), [3])

    def test_add_to_sorts_with_active_sorts(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b'),
            Header('field_c'),
        )
        self.form.data = {'sorts': '1.-2'}
        self.form.cleaned_data = {'sorts': [1, -2]}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)
        self.assertEqual(header_set['field_a'].add_to_sorts(), [-1, -2])
        self.assertEqual(header_set['field_b'].add_to_sorts(), [2, 1])
        self.assertEqual(header_set['field_c'].add_to_sorts(), [3, 1, -2])

    def test_sort_priority_display(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b'),
            Header('field_c'),
        )
        self.form.data = {'sorts': '-2.1'}
        self.form.cleaned_data = {'sorts': [-2, 1]}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)
        self.assertEqual(header_set['field_a'].priority, 2)
        self.assertEqual(header_set['field_b'].priority, 1)
        self.assertEqual(header_set['field_c'].priority, None)

    def test_css_classes(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b'),
            Header('field_c'),
        )
        self.form.data = {'sorts': '1.-2'}
        self.form.cleaned_data = {'sorts': [1, -2]}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)
        self.assertEqual(header_set['field_a'].css_classes, 'active ascending')
        self.assertEqual(header_set['field_b'].css_classes, 'active descending')
        self.assertEqual(header_set['field_c'].css_classes, '')

    def test_bound_header_querystring_properties(self):
        HEADERS = (
            Header('field_a'),
            Header('field_b'),
            Header('field_c'),
        )
        self.form.data = {'sorts': '1.-2'}
        self.form.cleaned_data = {'sorts': [1, -2]}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)

        self.assertEqual(header_set['field_a'].querystring, 'sorts=-1.-2')
        self.assertEqual(header_set['field_a'].singular_querystring, 'sorts=-1')
        self.assertEqual(header_set['field_a'].remove_querystring, 'sorts=-2')

        self.assertEqual(header_set['field_b'].querystring, 'sorts=2.1')
        self.assertEqual(header_set['field_b'].singular_querystring, 'sorts=2')
        self.assertEqual(header_set['field_b'].remove_querystring, 'sorts=1')

        self.assertEqual(header_set['field_c'].querystring, 'sorts=3.1.-2')
        self.assertEqual(header_set['field_c'].singular_querystring, 'sorts=3')
        self.assertEqual(header_set['field_c'].remove_querystring, 'sorts=1.-2')

    def assertQueryStringEqual(self, a, b, *args, **kwargs):
        """
        We need this because QueryDicts are dicts and key-ordering is not
        guaranteed on Python3. So we just convert query_strings back into
        QueryDicts to compare them.
        """
        self.assertEqual(QueryDict(a), QueryDict(b), *args, **kwargs)

    def test_bound_header_querystring_with_querydict(self):
        HEADERS = (
            Header('field_a'),
        )
        self.form.data = QueryDict('field=value')
        self.form.cleaned_data = {'field': 'value'}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)

        self.assertQueryStringEqual(header_set['field_a'].querystring, 'field=value&sorts=1')
        self.assertQueryStringEqual(header_set['field_a'].singular_querystring, 'field=value&sorts=1')
        self.assertQueryStringEqual(header_set['field_a'].remove_querystring, 'field=value&sorts=')

    def test_bound_header_querystring_with_querydict_overwrites_instead_of_appending(self):
        HEADERS = (
            Header('field_a'),
        )
        self.form.data = QueryDict('field=value&sorts=1')
        self.form.cleaned_data = {'field': 'value', 'sorts': [1]}
        self.form.HEADERS = HEADERS
        header_set = HeaderSet(self.form, HEADERS)

        # It used to output 'field=value&sorts=1&sorts=-1'
        self.assertQueryStringEqual(header_set['field_a'].querystring, 'field=value&sorts=-1')
        self.assertQueryStringEqual(header_set['field_a'].singular_querystring, 'field=value&sorts=-1')
        self.assertQueryStringEqual(header_set['field_a'].remove_querystring, 'field=value&sorts=')


class TestSortFormAPI(TestCase):
    def setUp(self):
        self.abc = ChangeListModel.objects.create(field_a='a', field_b='b', field_c='c')
        self.cab = ChangeListModel.objects.create(field_a='c', field_b='a', field_c='b')
        self.bca = ChangeListModel.objects.create(field_a='b', field_b='c', field_c='a')

        class TestSortForm(SortForm):
            model = ChangeListModel
            HEADERS = (
                Header('field_a'),
                Header('field_b'),
                Header('named_header', column_name='field_c'),
                Header('not_sortable', is_sortable=False),
            )
        self.TestSortForm = TestSortForm

    def test_valid_with_no_sorts(self):
        form = self.TestSortForm({})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_queryset().count(), 3)

    def test_sort_field_cleaning(self):
        self.assertTrue(self.TestSortForm({'sorts': '1.2.3'}).is_valid())
        self.assertTrue(self.TestSortForm({'sorts': '2.3.1'}).is_valid())
        self.assertTrue(self.TestSortForm({'sorts': '3.1.2'}).is_valid())

        # Unsortable Header
        unsortable = self.TestSortForm({'sorts': '1.2.3.4'})
        self.assertFalse(unsortable.is_valid())
        self.assertIn('sorts', unsortable.errors)
        self.assertIn(self.TestSortForm.error_messages['unsortable_header'], unsortable.errors['sorts'])

        # Unknown Header
        unknown = self.TestSortForm({'sorts': '1.2.3.5'})
        self.assertFalse(unknown.is_valid())
        self.assertIn('sorts', unsortable.errors)
        self.assertIn(self.TestSortForm.error_messages['unknown_header'], unsortable.errors['sorts'])

        # Invalid Header
        unknown = self.TestSortForm({'sorts': '1.2.X'})
        self.assertFalse(unknown.is_valid())
        self.assertIn('sorts', unsortable.errors)
        self.assertIn(self.TestSortForm.error_messages['unknown_header'], unsortable.errors['sorts'])

    def test_single_field_sorting(self):
        f = self.TestSortForm({'sorts': '1'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.abc, self.bca, self.cab),
        )

        f = self.TestSortForm({'sorts': '-1'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.cab, self.bca, self.abc),
        )

        f = self.TestSortForm({'sorts': '2'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.cab, self.abc, self.bca),
        )

        f = self.TestSortForm({'sorts': '-2'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.bca, self.abc, self.cab),
        )

        f = self.TestSortForm({'sorts': '3'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.bca, self.cab, self.abc),
        )

        f = self.TestSortForm({'sorts': '-3'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.abc, self.cab, self.bca),
        )

    def test_multi_field_sorting(self):
        self.aac = ChangeListModel.objects.create(field_a='a', field_b='a', field_c='c')

        f = self.TestSortForm({'sorts': '1.2'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.aac, self.abc, self.bca, self.cab),
        )

        f = self.TestSortForm({'sorts': '1.-2'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.abc, self.aac, self.bca, self.cab),
        )

    def test_order_by_override(self):
        self.aac = ChangeListModel.objects.create(field_a='a', field_b='a', field_c='c')
        self.aab = ChangeListModel.objects.create(field_a='a', field_b='a', field_c='b')

        class OverriddenOrderForm(self.TestSortForm):
            def get_order_by(self):
                order_by = super().get_order_by()
                return ['field_a'] + order_by

        f = OverriddenOrderForm({'sorts': '-3.2'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.aac, self.abc, self.aab, self.bca, self.cab),
        )

        f = OverriddenOrderForm({'sorts': '3.2'})
        f.full_clean()
        self.assertSequenceEqual(
            f.get_queryset(),
            (self.aab, self.aac, self.abc, self.bca, self.cab),
        )
