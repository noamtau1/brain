"""
The server module contains the main logic of the server, which is, receive incoming snapshots, construct message
to the parsers, and send them via the MQ.
"""

import threading
from typing import Callable

from brain.utils.common import get_logger
from .client_agent import snapshot_handler, run
from .mq_agent import MQAgent
from .parsers_agent import construct_parsers_message
from ..autogen import client_server_pb2

logger = get_logger(__name__)
publish_fn = None  # type: Callable


def construct_publish(mq_url: str) -> callable:
    """
    Construct a `publish` function that publishes a given snapshot to the MQ.

    :param mq_url: address of the MQ.
    :return: the publish function.
    """

    logger.info(f'constructing publish function: {mq_url=}')
    mq_agent = MQAgent(mq_url)

    def _publish(snapshot):
        mq_agent.publish_snapshot(snapshot)

    return _publish


snapshot_lock = threading.Lock()
snapshot_counter = 0


def generate_snapshot_uuid():
    global snapshot_counter
    with snapshot_lock:
        uuid = snapshot_counter
        snapshot_counter += 1
    return uuid


@snapshot_handler
def handle_snapshot(snapshot: client_server_pb2.Snapshot):
    """
    Handle an incoming snapshot: sends is to the provided publish function.

    :param snapshot: the snapshot object, in client_server_pb2.Snapshot format.
    """

    snapshot_uuid = generate_snapshot_uuid()
    logger.info(f'handling new snapshot, user_id={snapshot.user.user_id}, {snapshot_uuid=}')
    parsers_msg = construct_parsers_message(snapshot, snapshot_uuid)
    logger.debug(f'publishing snapshot to rabbitmq')
    publish_fn(parsers_msg)


def init_publish(publish):
    global publish_fn
    publish_fn = publish


def run_server(host: str, port: int, publish: callable):
    """
    Run the server with a given publish function.

    :param host: server hostname.
    :param port: server port number.
    :param publish: publish function.
    """

    logger.info(f'running server: {host=}, {port=}, {publish=}')
    init_publish(publish)
    run(host, port)
