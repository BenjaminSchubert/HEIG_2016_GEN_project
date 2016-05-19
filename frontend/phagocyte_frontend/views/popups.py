#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from kivy.lang import Builder
from kivy.uix.popup import Popup

from phagocyte_frontend.views import KV_DIRECTORY


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class InfoPopup(Popup):
    """
    Create a popup with a message and a title to be set
    """
    def __init__(self, **kwargs):
        """
        dynamically load popup.kv file
        """
        Builder.load_file(os.path.join(KV_DIRECTORY, "popup.kv"))
        super().__init__(**kwargs)