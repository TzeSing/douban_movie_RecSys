# -*- coding: utf-8 -*-

"""
recsys.utils
~~~~~~~~~~~~

Helper utilities and decorators.

:copyright: (c) 2020 by TzeSing.
:license: Apache2, see LICENSE for more details.
"""

from flask import flash


def flash_errors(form, category="warning"):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text} - {error}", category)
