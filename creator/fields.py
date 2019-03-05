import random
from django.db import models
import base32_crockford as b32


def kf_id_generator(prefix):
    """
    (Crockford)[http://www.crockford.com/wrmg/base32.html] base 32
    encoded number up to 8 characters left padded with 0 and prefixed with
    a two character value representing the entity type and delimited by
    an underscore
    Ex:
    'PT_0004PEDE'
    'SA_D167JSHP'
    'DM_ZZZZZZZZ'
    'ST_00000000'
    """
    if not len(prefix) == 2:
        raise ValueError('prefix must be of length 2')
    prefix = prefix.upper()

    return '{0}_{1:0>8}'.format(prefix,
                                b32.encode(random.randint(0, 32**8-1)))


class KFIDField(models.CharField):
    """
    A Kids First ID Field
    Stores an char of length 11 that is prefixed with a two character string
    and followed by an underscore and an 8 character Crockford-encoded string.

    Must be 11 characters long
    Must be unique
    Is not editable
    """
    description = 'A Kids First Identifier'

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 11
        kwargs['unique'] = True
        kwargs['editable'] = False
        super().__init__(*args, **kwargs)
