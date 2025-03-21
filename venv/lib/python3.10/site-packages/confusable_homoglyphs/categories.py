# -*- coding: utf-8 -*-
from .utils import load

categories_data = load('categories.json')


def aliases_categories(chr):
    """Retrieves the script block alias and unicode category for a unicode character.

    >>> categories.aliases_categories('A')
    ('LATIN', 'L')
    >>> categories.aliases_categories('τ')
    ('GREEK', 'L')
    >>> categories.aliases_categories('-')
    ('COMMON', 'Pd')

    :param chr: A unicode character
    :type chr: str
    :return: The script block alias and unicode category for a unicode character.
    :rtype: (str, str)
    """
    le = 0
    r = len(categories_data['code_points_ranges']) - 1
    c = ord(chr)

    # binary search
    while r >= le:
        m = (le + r) // 2
        if c < categories_data['code_points_ranges'][m][0]:
            r = m - 1
        elif c > categories_data['code_points_ranges'][m][1]:
            le = m + 1
        else:
            return (
                categories_data['iso_15924_aliases'][categories_data['code_points_ranges'][m][2]],
                categories_data['categories'][categories_data['code_points_ranges'][m][3]])
    return 'Unknown', 'Zzzz'


def alias(chr):
    """Retrieves the script block alias for a unicode character.

    >>> categories.alias('A')
    'LATIN'
    >>> categories.alias('τ')
    'GREEK'
    >>> categories.alias('-')
    'COMMON'

    :param chr: A unicode character
    :type chr: str
    :return: The script block alias.
    :rtype: str
    """
    a, _ = aliases_categories(chr)
    return a


def category(chr):
    """Retrieves the unicode category for a unicode character.

    >>> categories.category('A')
    'L'
    >>> categories.category('τ')
    'L'
    >>> categories.category('-')
    'Pd'

    :param chr: A unicode character
    :type chr: str
    :return: The unicode category for a unicode character.
    :rtype: str
    """
    _, a = aliases_categories(chr)
    return a


def unique_aliases(string):
    """Retrieves all unique script block aliases used in a unicode string.

    >>> categories.unique_aliases('ABC')
    {'LATIN'}
    >>> categories.unique_aliases('ρAτ-')
    {'GREEK', 'LATIN', 'COMMON'}

    :param string: A unicode character
    :type string: str
    :return: A set of the script block aliases used in a unicode string.
    :rtype: (str, str)
    """
    cats = [alias(c) for c in string]
    return set(cats)
