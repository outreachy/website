import copy

from django import forms
from django.forms.utils import pretty_name
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db.models import Q
from collections import OrderedDict
from functools import reduce
from django.utils.http import urlencode

from .forms import BetterForm


def construct_querystring(data, **kwargs):
    params = copy.copy(data)

    # We can't call update here because QueryDict extends rather than replaces.
    for key, value in kwargs.items():
        params[key] = value

    if hasattr(params, 'urlencode'):
        return params.urlencode()
    else:
        return urlencode(params)


class IterDict(OrderedDict):
    """
    Extension of djangos built in sorted dictionary class which iterates
    through the values rather than keys.
    """
    def __iter__(self):
        for key in super().__iter__():
            yield self[key]


class BaseChangeListForm(BetterForm):
    """
    Base class for all ``ChangeListForms``.
    """
    def __init__(self, *args, **kwargs):
        """
        Takes an option named argument ``queryset`` as the base queryset used in
        the ``get_queryset`` method.
        """
        try:
            self.base_queryset = kwargs.pop('queryset', None)
            if self.base_queryset is None:
                self.base_queryset = self.model.objects.all()
        except AttributeError:
            raise AttributeError('`ChangeListForm`s must be instantiated with a\
                                 queryset, or have a `model` attribute set on\
                                 them')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        """
        If the form was initialized with a queryset, this method returns that
        queryset.  Otherwise it returns ``Model.objects.all()`` for whatever
        model was defined for the form.
        """
        return self.base_queryset


class SearchForm(BaseChangeListForm):
    SEARCH_FIELDS = None
    CASE_SENSITIVE = False
    q = forms.CharField(label="Search", required=False)

    def __init__(self, *args, **kwargs):
        self.SEARCH_FIELDS = kwargs.pop('search_fields', self.SEARCH_FIELDS)
        super().__init__(*args, **kwargs)

        if self.SEARCH_FIELDS is None:
            raise ImproperlyConfigured('`SearchForm`s must be instantiated with an\
                                       iterable of fields to search over, or have \
                                       a `SEARCH_FIELDS` attribute set on them.')

    def get_queryset(self):
        """
        Constructs an '__contains' or '__icontains' filter across all of the
        fields listed in ``SEARCH_FIELDS``.
        """
        qs = super().get_queryset()

        # Do Searching
        q = self.cleaned_data.get('q', '').strip()
        if q:
            args = []
            for field in self.SEARCH_FIELDS:
                if self.CASE_SENSITIVE:
                    kwarg = {field + '__contains': q}
                else:
                    kwarg = {field + '__icontains': q}
                args.append(Q(**kwarg))
            if len(args) > 1:
                qs = qs.filter(reduce(lambda x, y: x | y, args))
            elif len(args) == 1:
                qs = qs.filter(args[0])

        return qs


class BoundHeader:
    def __init__(self, form, header):
        self.form = form
        self.header = header
        self.sorts = getattr(form, 'cleaned_data', {}).get('sorts', [])
        self.param = "{0}-sorts".format(form.prefix or '').strip('-')

    @property
    def name(self):
        return self.header.name

    @property
    def label(self):
        return self.header.label

    @property
    def column_name(self):
        return self.header.column_name

    @property
    def is_sortable(self):
        return self.header.is_sortable

    @property
    def _index(self):
        return self.form.HEADERS.index(self.header)

    @property
    def _sort_index(self):
        """
        1-indexed value for what number represents this header in the sorts
        querystring parameter.
        """
        return self._index + 1

    @property
    def is_active(self):
        """
        Returns whether this header is currently being used for sorting.
        """
        return self._sort_index in map(abs, self.sorts)

    @property
    def is_ascending(self):
        """
        Returns whether this header is currently being used for sorting in
        ascending order.
        """
        return self.is_active and self._sort_index in self.sorts

    @property
    def is_descending(self):
        """
        Returns whether this header is currently being used for sorting in
        descending order.
        """
        return self.is_active and self._sort_index not in self.sorts

    @property
    def css_classes(self):
        """
        String suitable to be used for the `class` attribute for an HTML
        element.  Denotes whether this header is active in the sorts, and the
        order in which it is being used.
        """
        classes = []
        if self.is_active:
            classes.append('active')
            if self.is_ascending:
                classes.append('ascending')
            elif self.is_descending:
                classes.append('descending')
        return ' '.join(classes)

    def add_to_sorts(self):
        """
        Compute the sorts that should be used when we're clicked on. If we're
        currently in the sorts, we'll be set as the first sort [ascending].
        Unless we're already at the front then we'll be inverted.
        """
        if self.sorts and abs(self.sorts[0]) == self._sort_index:
            return [-1 * self.sorts[0]] + self.sorts[1:]
        else:
            return [self._sort_index] + list(filter(lambda x: abs(x) != self._sort_index, self.sorts))

    @property
    def priority(self):
        if self.is_active:
            return list(map(abs, self.sorts)).index(self._sort_index) + 1

    @property
    def querystring(self):
        return construct_querystring(self.form.data, **{self.param: '.'.join(map(str, self.add_to_sorts()))})

    @property
    def singular_querystring(self):
        if self.is_active and abs(self.sorts[0]) == self._sort_index:
            value = -1 * self._sort_index
        else:
            value = self._sort_index
        return construct_querystring(self.form.data, **{self.param: str(value)})

    @property
    def remove_querystring(self):
        return construct_querystring(self.form.data, **{self.param: '.'.join(map(str, self.add_to_sorts()[1:]))})


class Header:
    BoundClass = BoundHeader
    column_name = None

    def __init__(self, name, label=None, column_name=False, is_sortable=True):
        self.name = name
        self.label = label or pretty_name(name)
        if is_sortable:
            self.column_name = column_name or name
        self.is_sortable = is_sortable


def is_header_kwargs(header):
    try:
        if not len(header) == 2:
            return False
    except AttributeError:
        return False
    try:
        return all((
            isinstance(header[0], str),
            isinstance(header[1], dict),
        ))
    except (IndexError, KeyError):
        return False


class HeaderSet:
    HeaderClass = Header

    def __init__(self, form, headers):
        self.form = form
        self.headers = OrderedDict()
        if headers is None:
            return
        for header in headers:
            if isinstance(header, Header):
                self.headers[header.name] = header
            elif isinstance(header, str):
                self.headers[header] = self.HeaderClass(header)
            elif is_header_kwargs(header):
                header_name, header_kwargs = header
                self.headers[header_name] = self.HeaderClass(header_name, **header_kwargs)
            elif len(header):
                try:
                    header_name = header[0]
                    header_args = header[1:]
                    self.headers[header_name] = self.HeaderClass(header_name, *header_args)
                except KeyError:
                    raise ImproperlyConfigured('Unknown format in header declaration: `{0}`'.format(repr(header)))
            else:
                raise ImproperlyConfigured('Unknown format in header declaration: `{0}`'.format(repr(header)))
        if not len(self) == len(headers):
            raise ImproperlyConfigured('Header names must be unique')

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        for header in self.headers.values():
            yield self.HeaderClass.BoundClass(self.form, header)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.HeaderClass.BoundClass(self.form, list(self.headers.values())[key])
        else:
            return self.HeaderClass.BoundClass(self.form, self.headers[key])


class SortFormBase(BetterForm):
    """
    A base class for writing your own SortForm. This form handles everything
    except applying the sorts to the queryset, which is convenient if you
    aren't working within the ChangeListForm paradigm.

    Usage::

        class MyForm(SortFormBase):
            HEADERS = (
                Header('name', label='Name'),
            )

            # fields ...

            def get_results(self):
                queryset = # ...
                queryset = self.apply_sorting(queryset)
                return queryset
    """
    HeaderSetClass = HeaderSet
    error_messages = {
        'unknown_header': 'Invalid sort parameter',
        'unsortable_header': 'Invalid sort parameter',
    }
    HEADERS = None
    sorts = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = self.HeaderSetClass(self, self.HEADERS)

    def clean_sorts(self):
        cleaned_data = self.cleaned_data
        sorts = list(filter(bool, cleaned_data.get('sorts', '').split('.')))
        if not sorts:
            return []
        # Ensure that the sort parameter does not contain non-numeric sort indexes
        if not all([sort.strip('-').isdigit() for sort in sorts]):
            raise ValidationError(self.error_messages['unknown_header'])
        sorts = [int(sort) for sort in sorts]
        # Ensure that all of our sort parameters are in range of our header values
        if any([abs(sort) > len(self.HEADERS) for sort in sorts]):
            raise ValidationError(self.error_messages['unknown_header'])
        # Ensure not un-sortable fields are being sorted by
        if not all(self.HEADERS[abs(i) - 1].is_sortable for i in sorts):
            raise ValidationError(self.error_messages['unsortable_header'])

        return sorts

    def get_order_by(self):
        # Do Sorting
        sorts = self.cleaned_data.get('sorts', [])
        order_by = []
        for sort in sorts:
            param = self.headers[abs(sort) - 1].column_name
            if sort < 0:
                param = '-' + param
            order_by.append(param)
        return order_by

    def apply_sorting(self, qs):
        order_by = self.get_order_by()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs


class SortForm(BaseChangeListForm, SortFormBase):
    def get_queryset(self):
        """
        Returns an ordered queryset, sorted based on the values submitted in
        the sort parameter.
        """
        qs = super().get_queryset()
        return self.apply_sorting(qs)
