"""
Phagocyte Authentication Server

This server is used for authenticating and dispatching players to their games.

See runserver.py for how to run the server
"""


import os
import sys
from flask import Flask
from flask_jwt import JWT
from flask_script import Manager

from phagocyte_authentication_server.auth import authenticate, identity
from phagocyte_authentication_server.commands import Server
from phagocyte_authentication_server.games import GameManager
from phagocyte_authentication_server.models import db, Base


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


# the Flask application
app = Flask("phagocyte_auth")

# Flask configuration
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.dirname(__file__))

app.config["CONFIG_PATH"] = os.environ.get("PHAGOCYTE_AUTH_SERVER", os.path.join(application_path, "config.cfg"))
app.config.from_pyfile(app.config["CONFIG_PATH"])

# Database setup
db.init_app(app)

with app.app_context():
    Base.metadata.create_all(db.engine)


# authentication
jwt = JWT(app, authenticate, identity)

# games
games = GameManager(app)

# command line options
manager = Manager(app, with_default_commands=False)

manager.add_command("runserver", Server(
    debug=app.config.get("DEBUG", False),
    host=app.config.get("HOST", "127.0.0.1"),
    port=app.config.get("PORT", 8000)
))

# views, json api
from . import views
