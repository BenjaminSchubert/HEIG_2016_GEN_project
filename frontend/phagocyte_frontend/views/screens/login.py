"""
Screen for the login of the user
"""

from phagocyte_frontend.exceptions import CredentialsException
from phagocyte_frontend.views.screens import AutoLoadableScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class LoginScreen(AutoLoadableScreen):
    """
    The login screen
    """
    screen_name = "login"

    def user_login(self):
        """
        connects the specified user with his name and password
        """
        self.loginButton.disabled = True

        try:
            self.manager.client.login(self.username.text, self.password.text)
        except CredentialsException as e:
            self.manager.warn(str(e), title="Error")
        except ConnectionError:
            self.manager.warn("Could not connect to the server", title="Error")
        else:
            self.manager.warn("Welcome back", callback=self.manager.main_screen)

        self.loginButton.disabled = False
