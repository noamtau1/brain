"""
The server agent module provides an interface for the client to communicate with the server.
"""
from furl import furl

from brain.autogen import client_server_pb2, sample_pb2
from brain.utils.common import get_logger
from brain.utils.http import post

logger = get_logger(__name__)


def copy_protobuf(item_a, item_b, attrs):
    for attr in attrs:
        setattr(item_a, attr, getattr(item_b, attr))


class ServerAgent:
    """
    Streams snapshot to the server

    :param host: server hostname
    :param port: server port number
    """

    def __init__(self, host: str, port: int):
        logger.info(f'initializing ServerAgent, {host=}, {port=}')
        self.host = host
        self.port = port
        self.url = furl(scheme='http', host=host, port=port)

    @classmethod
    def construct_snapshot(cls, user: sample_pb2.User, snapshot: sample_pb2.Snapshot):
        """
        Construct a message to the server in client_server format

        :param user: user in sample_pb2.User format
        :param snapshot: snapshot in sample_pb2.Snapshot format
        :return: snapshot in client_server_pb2.Snapshot format, containing the given user and snapshot
        """

        new_snapshot = client_server_pb2.Snapshot()
        copy_protobuf(new_snapshot, snapshot, ['datetime'])
        copy_protobuf(new_snapshot.user, user, ['user_id', 'username', 'birthday', 'gender'])
        copy_protobuf(new_snapshot.pose.translation, snapshot.pose.translation, ['x', 'y', 'z'])
        copy_protobuf(new_snapshot.pose.rotation, snapshot.pose.rotation, ['x', 'y', 'z', 'w'])
        copy_protobuf(new_snapshot.color_image, snapshot.color_image, ['width', 'height', 'data'])
        copy_protobuf(new_snapshot.depth_image, snapshot.depth_image, ['width', 'height'])
        new_snapshot.depth_image.data.extend(snapshot.depth_image.data)
        copy_protobuf(new_snapshot.feelings, snapshot.feelings, ['hunger', 'thirst', 'exhaustion', 'happiness'])
        return new_snapshot

    def send_snapshot(self, user, snapshot):
        """
        Sends a snapshot to the server

        :param user: user in sample_pb2.User format
        :param snapshot: snapshot in sample_pb2.Snapshot format
        """

        new_snapshot = self.construct_snapshot(user, snapshot)
        url = self.url / 'snapshot'
        snapshot_msg = new_snapshot.SerializeToString()
        logger.debug(f'sending snapshot to {url}')
        post(url, snapshot_msg)
