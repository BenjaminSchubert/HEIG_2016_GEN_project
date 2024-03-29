"""
Package containing all the screens used in the application
"""

from abc import ABCMeta
from configparser import ConfigParser, Error
from functools import partial
import os
from kivy import Logger

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from phagocyte_frontend.network.authentication import Client
from phagocyte_frontend.views import resource_path
from phagocyte_frontend.views.popups import InfoPopup


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class AutoLoadableScreen(Screen):
    """
    Auto load screen from it's name

    :param kwargs: additional keyword arguments
    """
    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        Builder.load_file(os.path.join(resource_path(), "screens/{name}.kv").format(name=self.screen_name))
        super(Screen, self).__init__(**kwargs)
        self.name = self.screen_name


class PhagocyteScreenManager(ScreenManager):
    """
    Screen manager for the application

    :param config_parser: config parser used to get information
    :param kwargs: additional keyword arguments
    """
    info_popup = InfoPopup()

    def __init__(self, config_parser: ConfigParser, **kwargs):
        super().__init__(**kwargs)
        self.config_parser = config_parser
        self.callback = None

        self.client = Client(self.config_parser.get("Server", "host"), self.config_parser.get("Server", "port"))

    # noinspection PyUnusedLocal
    def main_screen(self, *args, **kwargs):
        """
        set the current screen to the lobby main screen
        """
        self.current = self.screen_names[0]

    def warn(self, msg: str, title: str="Info", callback: callable=None):
        """
        Open a warn popup

        :param msg: content of the popup
        :param title: title of the popup
        :param callback: callback to call when the popup is dismissed
        """
        self.info_popup.msg = msg
        self.info_popup.title = title
        self.callback = partial(self.callback_handler, callback)
        self.info_popup.bind(on_dismiss=self.callback)
        self.info_popup.open()

    def callback_handler(self, callback: callable, *args):
        """
        call the callback given in parameter if not None, and removes it from the event on which it was bound

        :param callback: callback to call when the event is fired
        :param args: arguments to pass to the callback
        """
        if callback is not None:
            callback(*args)
        self.info_popup.unbind(on_dismiss=self.callback)
