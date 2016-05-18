#!/usr/bin/env python3

"""
Game server implementation
"""

import json
import json.decoder
import logging
import random
import sys

from rainbow_logging_handler import RainbowLoggingHandler
import requests
from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import DatagramProtocol

from phagocyte_game_server.events import Event


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def create_logger(name, port, debug):
    logger = logging.getLogger(name + ":" + str(port))
    handler = RainbowLoggingHandler(sys.stderr, color_process=("yellow", None, True))

    formatter = logging.Formatter("[%(asctime)s] %(name)s:%(process)d %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO if not debug else logging.DEBUG)

    return logger


class AuthenticationError(Exception):
    """
    Exception raised when authentication failed

    :param msg: information about the error
    """
    def __init__(self, msg):
        self.msg = msg


def random_color():
    """
    get a new random color in hexadecimal

    :return: new hexadecimal color
    """
    return "#%06x" % random.randint(0, 0xFFFFFF)


def register(port, auth_host, auth_port, name, capacity):
    """
    registers the game server against the authentication server

    :param port: port of the game server
    :param auth_host: address of the authentication server
    :param auth_port: port of the authentication server
    :param name: name of the game server
    :param capacity: max capacity of the game server
    """
    r = requests.post(
        "http://{}:{}/games/server".format(auth_host, auth_port),
        json={"port": port, "name": name, "capacity": capacity}
    )

    if r.status_code != requests.codes.ok:
        logging.fatal("Couldn't contact authentication server. exiting")
        exit(2)


class GameProtocol(DatagramProtocol):
    """
    Implementation of the Game protocol for Phagocytes

    :param auth_host: host address of the authentication server
    :param auth_port: port of the authentication server
    :param capacity: max capacity of the server
    """
    clients = dict()
    max_x = 2000
    max_y = 2000

    def __init__(self, auth_host, auth_port, capacity, logger):
        self.auth_host = auth_host
        self.auth_port = auth_port
        self.max_capacity = capacity
        self.logger = logger
        self.url = "http://{}:{}".format(self.auth_host, self.auth_port)

    def random_position(self):
        """
        Returns a random position

        :return: tuple of X,Y position
        """
        return random.randint(0, self.max_x), random.randint(0, self.max_y)

    def authenticate(self, token):
        """
        tries to authenticate the user against the authentication server

        :param token: token given by the user
        :raise AuthenticationError: if authentication failed
        :return: name and color of the user as returned by the authentication server
        """
        r = requests.post(self.url + "/validate", json=dict(token=token))
        if r.status_code == requests.codes.ok:
            return r.json()["username"], r.json()["color"]

        raise AuthenticationError(r.json())

    def register(self, data, addr):
        """
        register a new player on the game server

        :param data: data got from the client
        :param addr: client address
        :return:  message to send to the user
        """
        if data.get("event") != Event.TOKEN:
            self.logger.warning("User from {addr} not registered tried to gain access".format(addr=addr))
            return dict(event=Event.ERROR, error="Client not registered")

        elif data.get("token") is None:
            color = random_color()
            name = data.get("name")
            log_name = "with name {name}".format(name=name) if name is not None else "with no name"
            self.logger.debug("Registering new user {name}".format(name=log_name))
        else:
            try:
                name, color = self.authenticate(data.get("token"))
            except AuthenticationError as e:
                self.logger.warning("User from {addr} tried to register with invalid token".format(addr=addr))
                e.msg["event"] = Event.ERROR
                return e.msg
            else:
                self.logger.debug("Registered new user {name}".format(name=name))

        position = dict(position=self.random_position(), color=color, name=name)
        self.clients[addr] = position
        data = dict(event=Event.GAME_INFO, name=name, max_x=self.max_x, max_y=self.max_y)
        data.update(position)
        return data

    def datagramReceived(self, datagram, addr):
        """
        function called every time a new datagram is received.
        This will dispatch it to the correct handler

        :param datagram: datagram received from the client
        :param addr: client address
        """
        try:
            data = json.loads(datagram.decode("utf8"))
        except json.decoder.JSONDecodeError:
            self.logger.warning("Invalid json received : '{json}'".format(json=datagram.decode("utf-8")))
        else:
            if self.clients.get(addr) is None:
                ret = self.register(data, addr)
            else:
                logging.error("Received invalid action: {json}".format(json=data))
                return

            self.transport.write(json.dumps(ret).encode("utf8"), addr)


def runserver(port, auth_host, auth_port, name, capacity, debug):
    """
    launches the game server

    :param port: port on which to listen
    :param auth_host: hostname of the authentication server to which to refer
    :param auth_port: port of the authentication server to which to refer
    :param name: name of the game server
    :param capacity: capacity of the game server
    :param debug: whether to turn on debugging or not
    """
    logger = create_logger(name, port, debug)

    try:
        reactor.listenUDP(port, GameProtocol(auth_host, auth_port, capacity, logger))
    except CannotListenError as e:
        if isinstance(e.socketError, PermissionError):
            logger.error("Permission denied. Do you have the right to open port {} ?".format(port))
        elif isinstance(e.socketError, OSError):
            logger.error("Couldn't listen on port {}. Port is already used.".format(port))
        else:
            raise e.socketError
    else:
        logger.info("server launched")
        register(port, auth_host, auth_port, name, capacity)
        reactor.run()
