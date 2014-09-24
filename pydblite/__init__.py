from __future__ import print_function
"""PyDbLite"""
# this is a namespace package
import pkg_resources
pkg_resources.declare_namespace(__name__)
from .pydblite import Base  # NOQA
from . import pydblite
__version__ = pydblite.version
