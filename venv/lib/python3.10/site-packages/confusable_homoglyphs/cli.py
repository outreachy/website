# -*- coding: utf-8 -*-
import re
import sys
from collections import defaultdict

from . import confusables
from .utils import dump, get, u

try:
    import click
except ImportError:
    print('Install this package with the [cli] extras to enable the CLI.')
    raise


@click.group()
def cli():
    pass


@cli.command()
@click.argument("file", nargs=-1, type=click.File("r"))
def check(file):
    """
    Check whether the contents of a file are dangerous.

    A string is considered dangerous if it is mixed script and contains
    confusable homoglyphs.

    Return 0 if no dangerous content has been found, 2 otherwise.
    """
    safe = True
    for f in file:
        for lin in f.readlines():
            if confusables.is_dangerous(lin):
                print(lin)
                safe = False
    if not safe:
        sys.exit(2)


@cli.command()
def update():
    """
    Update the homoglyph data files from https://www.unicode.org
    """
    generate_categories()
    generate_confusables()


def generate_categories():
    """Generates the categories JSON data file from the unicode specification.

    :return: True for success, raises otherwise.
    :rtype: bool
    """
    # inspired by https://gist.github.com/anonymous/2204527
    code_points_ranges = []
    iso_15924_aliases = []
    categories = []

    match = re.compile(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\W+(\w+)\s*#\s*(\w+)',
                       re.UNICODE)

    url = 'ftp://ftp.unicode.org/Public/UNIDATA/Scripts.txt'
    file = get(url)
    for line in file:
        p = re.findall(match, line)
        if p:
            code_point_range_from, code_point_range_to, alias, category = p[0]
            alias = u(alias.upper())
            category = u(category)
            if alias not in iso_15924_aliases:
                iso_15924_aliases.append(alias)
            if category not in categories:
                categories.append(category)
            code_points_ranges.append((
                int(code_point_range_from, 16),
                int(code_point_range_to or code_point_range_from, 16),
                iso_15924_aliases.index(alias), categories.index(category))
            )
    code_points_ranges.sort()

    categories_data = {
        'iso_15924_aliases': iso_15924_aliases,
        'categories': categories,
        'code_points_ranges': code_points_ranges,
    }

    dump('categories.json', categories_data)


def generate_confusables():
    """Generates the confusables JSON data file from the unicode specification.

    :return: True for success, raises otherwise.
    :rtype: bool
    """
    url = 'ftp://ftp.unicode.org/Public/security/latest/confusables.txt'
    file = get(url)
    confusables_matrix = defaultdict(list)
    match = re.compile(r'[0-9A-F ]+\s+;\s*[0-9A-F ]+\s+;\s*\w+\s*#'
                       r'\*?\s*\( (.+) → (.+) \) (.+) → (.+)\t#',
                       re.UNICODE)
    for line in file:
        p = re.findall(match, line)
        if p:
            char1, char2, name1, name2 = p[0]
            confusables_matrix[char1].append({
                'c': char2,
                'n': name2,
            })
            confusables_matrix[char2].append({
                'c': char1,
                'n': name1,
            })

    dump('confusables.json', dict(confusables_matrix))


if __name__ == "__main__":
    cli()
