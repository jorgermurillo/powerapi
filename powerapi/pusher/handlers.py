# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from powerapi.handler import InitHandler, Handler, StartHandler
from powerapi.report import PowerReport
from powerapi.message import ErrorMessage
from powerapi.message import OKMessage, StartMessage
from powerapi.database import DBError


class PusherStartHandler(StartHandler):
    """
    Handle Start Message
    """

    def initialization(self, state):
        """
        Initialize the output database

        :param powerapi.State state: State of the actor.
        :rtype powerapi.State: the new state of the actor
        """
        try:
            state.database.connect()
        except DBError as error:
            state.socket_interface.send_control(ErrorMessage(error.msg))
            return state

        return state


class PowerHandler(InitHandler):
    """
    Allow to save the PowerReport received.
    """

    def handle(self, msg, state):
        """
        Save the msg in the database

        :param powerapi.PowerReport msg: PowerReport to save.
        :param powerapi.State state: State of the actor.
        """
        if not isinstance(msg, PowerReport):
            return state

        state.buffer.append(msg.serialize())

        return state

class PusherPoisonPillHandler(Handler):
    """
    Set a timeout for the pusher for the timeout_handler. If he didn't
    read any input during the timeout, the actor end.
    """
    def handle(self, msg, state):
        """

        :param powerapi.PoisonPillMessage msg: PoisonPillMessage.
        :param powerapi.pusher.PusherState state: State of the actor.
        :return powerapi.State: new State
        """
        state.timeout_handler = TimeoutKillHandler()
        state.socket_interface.timeout = 2000
        return state

class TimeoutBasicHandler(InitHandler):
    """
    Pusher timeout flush the buffer
    """

    def handle(self, msg, state):
        """
        Flush the buffer in the database
        :param msg: None
        :param state: State of the actor
        :return powerapi.PusherState: new State
        """
        state.database.save_many(state.buffer)
        state.buffer = []
        return state

class TimeoutKillHandler(InitHandler):
    """
    Pusher timeout kill the actor
    """
    def handle(self, msg, state):
        """
        Kill the actor by setting alive to False
        :param msg: None
        :param state: State of the actor
        :return powerapi.PusherState: new State
        """
        state.alive = False
        return state