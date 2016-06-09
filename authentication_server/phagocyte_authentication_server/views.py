#!/usr/bin/python3

"""
Various views for the Phagocyte authentication server
"""

import json

import uuid

import jwt
import sqlalchemy.exc
from flask import request, jsonify, make_response
from flask_jwt import jwt_required, current_identity

from phagocyte_authentication_server import app
from phagocyte_authentication_server.auth import identity
from phagocyte_authentication_server.models import User, db


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


@app.route("/register", methods=["POST"])
def create_user():
    """
    Creates a new user with the data given in parameter
    """
    data = request.get_json()
    user = User(username=data["username"], password=data["password"])
    try:
        db.session.add(user)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return make_response(jsonify(error="user with the same name already exists"), 409)


@app.route("/validate", methods=["POST"])
def validate_token():
    """
    Validates the token and send back the user's name and color
    """
    token = request.get_json()["token"]
    try:
        user = identity(app.extensions["jwt"].jwt_decode_callback(token))
    except jwt.exceptions.ExpiredSignatureError:
        return (jsonify(error="signature expired"), 403)
    return jsonify(user.as_dict)


@app.route("/games", methods=["GET"])
def games():
    """
    Get the list of all games available
    """
    return jsonify(app.games.games)


@app.route("/games", methods=["POST"])
def create_game():
    """ Creates a new game """
    try:
        app.games.create_game(request.get_json())
    except KeyError as e:
        return make_response(jsonify(error=str(e)), 400)

    return "", 200


@app.route("/games/server", methods=["POST"])
def register_server():
    """
    Registers a new game server

    :return: 200 OK
    """
    # FIXME : check that there are no name clashes
    app.games.add_game(request.json["ip"], request.json["port"], request.json["name"], request.json["capacity"])
    return "", 200


@app.route("/games/manager", methods=["POST"])
def register_manager():
    """
    Registers a new game manager

    :return: token for authentication and information on which server to create if needed
    """
    token = str(uuid.uuid4())
    data = {"token": token}
    app.games.add_manager(token=token, **request.json)
    if len(app.games.games) < 1:
        data["create"] = True
        data["name"] = "Main"
        data["capacity"] = 200
    return jsonify(data)


@app.route("/games/manager", methods=["DELETE"])
def delete_manager():
    """
    Removes a game manager from the list

    :return: 200 OK if ok
    """
    app.games.remove_manager(request.get_json()["token"])
    return "", 200


@app.route("/account/parameters", methods=["POST"])
@jwt_required()
def change_account_parameters():
    """
    Changes the account parameters.

    :return: 200 OK
    """
    received = json.loads(request.get_json())

    if "color" in received:
        current_identity.color = received["color"]

    if "name" in request.json:
        current_identity.name = received["name"]

    return "", 200


@app.route("/account/parameters", methods=["GET"])
@jwt_required()
def get_account_parameters():
    """
    Gets the accounts parameters.

    :return: the account info as json.
    """
    return jsonify(current_identity.as_dict)
