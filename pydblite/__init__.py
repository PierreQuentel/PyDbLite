from __future__ import print_function
"""PyDbLite"""
# this is a namespace package
import pkg_resources
from . import pydblite
from .pydblite import Base  # NOQA
pkg_resources.declare_namespace(__name__)
__version__ = pydblite.version
