# -*- coding: utf-8 -*-
from .categories import alias, unique_aliases
from .utils import load

confusables_data = load('confusables.json')


class Found(Exception):
    pass


def is_mixed_script(string, allowed_aliases=['COMMON']):
    """Checks if ``string`` contains mixed-scripts content, excluding script
    blocks aliases in ``allowed_aliases``.

    E.g. ``B. C`` is not considered mixed-scripts by default: it contains characters
    from **Latin** and **Common**, but **Common** is excluded by default.

    >>> confusables.is_mixed_script('Abç')
    False
    >>> confusables.is_mixed_script('ρτ.τ')
    False
    >>> confusables.is_mixed_script('ρτ.τ', allowed_aliases=[])
    True
    >>> confusables.is_mixed_script('Alloτ')
    True

    :param string: A unicode string
    :type string: str
    :param allowed_aliases: Script blocks aliases not to consider.
    :type allowed_aliases: list(str)
    :return: Whether ``string`` is considered mixed-scripts or not.
    :rtype: bool
    """
    allowed_aliases = [a.upper() for a in allowed_aliases]
    cats = unique_aliases(string) - set(allowed_aliases)
    return len(cats) > 1


def is_confusable(string, greedy=False, preferred_aliases=[]):
    """Checks if ``string`` contains characters which might be confusable with
    characters from ``preferred_aliases``.

    If ``greedy=False``, it will only return the first confusable character
    found without looking at the rest of the string, ``greedy=True`` returns
    all of them.

    ``preferred_aliases=[]`` can take an array of unicode block aliases to
    be considered as your 'base' unicode blocks:

    -  considering ``paρa``,

       -  with ``preferred_aliases=['latin']``, the 3rd character ``ρ``
          would be returned because this greek letter can be confused with
          latin ``p``.
       -  with ``preferred_aliases=['greek']``, the 1st character ``p``
          would be returned because this latin letter can be confused with
          greek ``ρ``.
       -  with ``preferred_aliases=[]`` and ``greedy=True``, you'll discover
          the 29 characters that can be confused with ``p``, the 23
          characters that look like ``a``, and the one that looks like ``ρ``
          (which is, of course, *p* aka *LATIN SMALL LETTER P*).

    >>> confusables.is_confusable('paρa', preferred_aliases=['latin'])[0]['character']
    'ρ'
    >>> confusables.is_confusable('paρa', preferred_aliases=['greek'])[0]['character']
    'p'
    >>> confusables.is_confusable('Abç', preferred_aliases=['latin'])
    False
    >>> confusables.is_confusable('AlloΓ', preferred_aliases=['latin'])
    False
    >>> confusables.is_confusable('ρττ', preferred_aliases=['greek'])
    False
    >>> confusables.is_confusable('ρτ.τ', preferred_aliases=['greek', 'common'])
    False
    >>> confusables.is_confusable('ρττp')
    [{'homoglyphs': [{'c': 'p', 'n': 'LATIN SMALL LETTER P'}], 'alias': 'GREEK', 'character': 'ρ'}]

    :param string: A unicode string
    :type string: str
    :param greedy: Don't stop on finding one confusable character - find all of them.
    :type greedy: bool
    :param preferred_aliases: Script blocks aliases which we don't want ``string``'s characters
        to be confused with.
    :type preferred_aliases: list(str)
    :return: False if not confusable, all confusable characters and with what they are confusable
        otherwise.
    :rtype: bool or list
    """
    preferred_aliases = [a.upper() for a in preferred_aliases]
    outputs = []
    checked = set()
    for char in string:
        if char in checked:
            continue
        checked.add(char)
        char_alias = alias(char)
        if char_alias in preferred_aliases:
            # it's safe if the character might be confusable with homoglyphs from other
            # categories than our preferred categories (=aliases)
            continue
        found = confusables_data.get(char, False)
        if found is False:
            continue
        # character λ is considered confusable if λ can be confused with a character from
        # preferred_aliases, e.g. if 'LATIN', 'ρ' is confusable with 'p' from LATIN.
        # if 'LATIN', 'Γ' is not confusable because in all the characters confusable with Γ,
        # none of them is LATIN.
        if preferred_aliases:
            potentially_confusable = []
            try:
                for d in found:
                    aliases = [alias(glyph) for glyph in d['c']]
                    for a in aliases:
                        if a in preferred_aliases:
                            potentially_confusable = found
                            raise Found()
            except Found:
                pass
        else:
            potentially_confusable = found
        if potentially_confusable:  # we found homoglyphs
            output = {
                'character': char,
                'alias': char_alias,
                'homoglyphs': potentially_confusable,
            }
            if not greedy:
                return [output]
            outputs.append(output)

    return outputs or False


def is_dangerous(string, preferred_aliases=[]):
    """Checks if ``string`` can be dangerous, i.e. is it not only mixed-scripts
    but also contains characters from other scripts than the ones in ``preferred_aliases``
    that might be confusable with characters from scripts in ``preferred_aliases``

    For ``preferred_aliases`` examples, see ``is_confusable`` docstring.

    >>> bool(confusables.is_dangerous('Allo'))
    False
    >>> bool(confusables.is_dangerous('AlloΓ', preferred_aliases=['latin']))
    False
    >>> bool(confusables.is_dangerous('Alloρ'))
    True
    >>> bool(confusables.is_dangerous('AlaskaJazz'))
    False
    >>> bool(confusables.is_dangerous('ΑlaskaJazz'))
    True

    :param string: A unicode string
    :type string: str
    :param preferred_aliases: Script blocks aliases which we don't want ``string``'s characters
        to be confused with.
    :type preferred_aliases: list(str)
    :return: Is it dangerous.
    :rtype: bool
    """
    return (
        is_mixed_script(string)
        and bool(is_confusable(string, preferred_aliases=preferred_aliases))
    )
