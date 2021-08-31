# Copyright (c) 2018, INRIA
# Copyright (c) 2018, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import logging
import sys

from typing import List, Type

from thespian.actors import ActorSystem, ActorAddress, ActorExitRequest

from powerapi.message import OKMessage, ErrorMessage, StartMessage, EndMessage, PingMessage
from powerapi.actor import InitializationException, Actor
from powerapi.exception import PowerAPIExceptionWithMessage
from powerapi.pusher import PusherActor
from powerapi.puller import PullerActor
from powerapi.dispatcher import DispatcherActor


class ActorCrashedException(PowerAPIExceptionWithMessage):
    """
    Exception raised when an actor crashed and can't be restarted
    """


class actorLogFilter(logging.Filter):
    def filter(self, logrecord):
        return 'actor_name' in logrecord.__dict__


class notActorLogFilter(logging.Filter):
    def filter(self, logrecord):
        return 'actorAddress' not in logrecord.__dict__


LOG_DEF = {
    'version': 1,
    'formatters': {
        'normal': {'format': '%(levelname)s::%(created)s::ROOT::%(message)s'},
        'actor': {'format': '%(levelname)s::%(created)s::%(actor_name)s::%(message)s'}},
    'filters': {
        'isActorLog': {'()': actorLogFilter},
        'notActorLog': {'()': notActorLogFilter}},
    'handlers': {
        'h1': {'class': 'logging.StreamHandler',
               'stream': sys.stdout,
               'formatter': 'normal',
               'filters': ['notActorLog'],
               'level': logging.DEBUG},
        'h2': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'actor',
            'filters': ['isActorLog'],
            'level': logging.DEBUG}
    },
    'loggers': {'': {'handlers': ['h1', 'h2'], 'level': logging.DEBUG}}
}

class Supervisor:

    def __init__(self, verbose_mode: bool):

        if verbose_mode:
            LOG_DEF['handlers']['h1']['level'] = logging.DEBUG
            LOG_DEF['handlers']['h2']['level'] = logging.DEBUG
        else:
            LOG_DEF['handlers']['h1']['level'] = logging.INFO
            LOG_DEF['handlers']['h2']['level'] = logging.INFO

        self.system = ActorSystem(systemBase='multiprocQueueBase', logDefs=LOG_DEF)
        self.pushers = {}
        self.pullers = {}
        self.dispatchers = {}
        self.actors = {}

    def launch(self, actor_cls: Type[Actor], start_message: StartMessage):
        """
        create an actor from a given class and send it a start message.
        :param actor_cls: class used to create the actor
        :param start_message: message used to initialize the actor
        :raise InitializationException: if an error occurs during actor initialiszation process
        """
        name = start_message.name
        address = self.system.createActor(actor_cls)
        answer = self.system.ask(address, start_message)

        if isinstance(answer, OKMessage):
            self._add_actor(address, name, actor_cls)
            return address
        if isinstance(answer, ErrorMessage):
            raise InitializationException(answer.error_message)

    def _add_actor(self, address, name, actor_cls):
        if actor_cls is PusherActor:
            self.pushers[name] = address
        elif actor_cls is PullerActor:
            self.pullers[name] = address
        elif actor_cls is DispatcherActor:
            self.dispatchers[name] = address
        else:
            raise AttributeError('Actor is not a DispatcherActor, PusherActor of PullerActor')
        self.actors[name] = address

    def _wait_actors(self):
        for _ in self.pushers:
            self.system.listen()

    def shutdown(self):
        self.system.shutdown()

    def monitor(self):
        """
        wait for an actor to send an EndMessage or for an actor to crash
        """
        while True:
            msg = self.system.listen(1)
            if msg is None:
                pass
            elif isinstance(msg, EndMessage):
                self._wait_actors()
                return
            else:
                #: todo log ici
                pass
