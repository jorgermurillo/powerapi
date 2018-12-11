import multiprocessing


import setproctitle
import pytest
import zmq
from mock import Mock, patch

from smartwatts.message import UnknowMessageTypeException, PoisonPillMessage
from smartwatts.actor import Actor
from smartwatts.handler import PoisonPillMessageHandler


class DummyActor(Actor):

    def setup(self):
        self.add_handler(PoisonPillMessage, PoisonPillMessageHandler())


ACTOR_NAME = 'dummy_actor'
VERBOSE_MODE = False
PULL_SOCKET_ADDRESS = 'ipc://@' + ACTOR_NAME


@pytest.fixture()
def dummy_actor():
    """ Return a dummy actor"""
    actor = DummyActor(name=ACTOR_NAME, verbose=VERBOSE_MODE)
    return actor


@pytest.fixture()
def initialized_dummy_actor(dummy_actor):
    dummy_actor.setup()
    return dummy_actor


def test_actor_initialisation(dummy_actor):
    """ test actor attributes initialization"""
    assert dummy_actor.state.alive is True
    assert dummy_actor.pull_socket_address == PULL_SOCKET_ADDRESS
    assert dummy_actor.name == ACTOR_NAME


def test_communication_setup(dummy_actor):
    """
    test if zmq context and sockets are correctly initialized and if the proc
    title is correctly set after the run function was call
    """

    dummy_actor._communication_setup()

    assert isinstance(dummy_actor.context, zmq.Context)
    assert isinstance(dummy_actor.pull_socket, zmq.Socket)
    assert dummy_actor.pull_socket.closed is False
    assert dummy_actor.pull_socket.get(zmq.TYPE) == zmq.PULL
    assert (dummy_actor.pull_socket.get(zmq.LAST_ENDPOINT).decode("utf-8") ==
            PULL_SOCKET_ADDRESS)
    assert setproctitle.getproctitle() == ACTOR_NAME
    dummy_actor._kill_process()


def test_get_handler_unknow_message_type(initialized_dummy_actor):
    """test to handle a message with no handle bind to its type

    must raise an UnknowMessageTypeException

    """
    with pytest.raises(UnknowMessageTypeException):
        initialized_dummy_actor.get_corresponding_handler('toto')


def test_get_handler(initialized_dummy_actor):
    """ Test to get the predefined handler for PoisonPillMessage type
    """
    print(initialized_dummy_actor.handlers)
    handler = initialized_dummy_actor.get_corresponding_handler(
        PoisonPillMessage())
    assert isinstance(handler, PoisonPillMessageHandler)

def test_behaviour_change(initialized_dummy_actor):
    """ Test if the actor behaviour could be change during the current
    behaviour function execution
    """

    buzzer = Mock()

    def next_behaviour(actor):
        """ call the buzzer and set the alive flag to False"""
        buzzer.buzz()
        actor.state.alive = False

    def init_behaviour(actor):
        actor.state.behaviour = next_behaviour

    initialized_dummy_actor.state.behaviour = init_behaviour

    initialized_dummy_actor.run()

    assert len(buzzer.mock_calls) == 1
