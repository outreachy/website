# -*- coding: utf-8 -*-
import json
import os
from urllib.request import urlopen

PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))


def u(x):
    return x


def get(url, timeout=None):
    return urlopen(url, timeout=timeout).read().decode('utf-8').split('\n')


def path(filename):
    """Returns a file path relative to the data directory.

    This is the package directory by default, or the env variable
    CONFUSABLE_DATA if set.

    :return: A file path string.
    :rtype: str
    """
    data_dir = os.environ.get("CONFUSABLE_DATA", PACKAGE_DIR)
    return os.path.join(data_dir, filename)


def load(filename):
    """Loads a JSON data file.

    :return: A dict.
    :rtype: dict
    """
    with open(path(filename), 'r') as file:
        return json.load(file)


def dump(filename, data):
    with open(path(filename), 'w+') as file:
        return json.dump(data, file)


def delete(filename):
    """Deletes a JSON data file if it exists.
    """
    try:
        os.remove(path(filename))
    except OSError:
        pass
