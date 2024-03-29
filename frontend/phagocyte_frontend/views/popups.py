"""
Popups used through the application
"""

import os

from kivy.lang import Builder
from kivy.uix.popup import Popup

from phagocyte_frontend.views import resource_path


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class InfoPopup(Popup):
    """
    Create a popup with a message and a title to be set

    :param kwargs: additional keyword arguments
    """
    def __init__(self, **kwargs):
        Builder.load_file(os.path.join(resource_path(), "popup.kv"))
        super().__init__(**kwargs)
