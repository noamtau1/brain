"""
The parsers agent provides an interface for the server to construct messages to can be sent to the parsers over the MQ.
It should provide only `construct_parsers_message` as its interface.
"""

import numpy as np

from brain import data_path
from brain.autogen import server_parsers_pb2, client_server_pb2
from brain.utils.common import normalize_path, get_logger

logger = get_logger(__name__)


def copy_protobuf(item_a, item_b, attrs):
    for attr in attrs:
        setattr(item_a, attr, getattr(item_b, attr))


def handle_color_image(snapshot, data):
    # save color image blob as raw file to disk
    path = normalize_path(snapshot.path)
    image_file = str(path / 'color_image.raw')
    with open(image_file, 'wb') as writer:
        writer.write(data)
    snapshot.color_image.file_name = image_file


def handle_depth_image(snapshot, data):
    # save depth image blob as raw file to disk
    path = normalize_path(snapshot.path)
    image_file = 'depth_image.raw'
    image_file_path = str(path / image_file)
    array = np.array(data).astype(np.float)
    np.save(image_file_path, array)
    snapshot.depth_image.file_name = image_file + '.npy'


def construct_parsers_message(snapshot: client_server_pb2.Snapshot, snapshot_uuid: int) -> server_parsers_pb2.Snapshot:
    """
    Construct a message to the parsers.

    The main change being done at this point, is to save blobs such as color and depth image to the disk,
    and provide a path to the file on disk instead of the actual data being stored as part of the message so far.

    :param snapshot: snapshot in client_server_pb2.Snapshot format.
    :param snapshot_uuid: uuid of the snapshot.
    :return: the constructed message in server_parsers_pb2.Snapshot format.
    """

    logger.debug(f'constructing message for parsers')
    parsers_snapshot = server_parsers_pb2.Snapshot()
    parsers_snapshot.uuid = snapshot_uuid
    copy_protobuf(parsers_snapshot, snapshot, ['datetime'])
    copy_protobuf(parsers_snapshot.user, snapshot.user, ['user_id', 'username', 'birthday', 'gender'])
    copy_protobuf(parsers_snapshot.pose.translation, snapshot.pose.translation, ['x', 'y', 'z'])
    copy_protobuf(parsers_snapshot.pose.rotation, snapshot.pose.rotation, ['x', 'y', 'z', 'w'])
    copy_protobuf(parsers_snapshot.color_image, snapshot.color_image, ['width', 'height'])
    copy_protobuf(parsers_snapshot.depth_image, snapshot.depth_image, ['width', 'height'])
    copy_protobuf(parsers_snapshot.feelings, snapshot.feelings, ['hunger', 'thirst', 'exhaustion', 'happiness'])

    # before saving blobs to the disk, we must find a directory to saves file to.
    # we will use the <data-path>/<user-id>/<snapshot-id>/ directory (and create it if not exists).
    base_path = data_path
    user_id = parsers_snapshot.user.user_id
    user_dir = base_path / str(user_id)
    if not user_dir.exists():
        user_dir.mkdir()
    snapshot_dir = user_dir / str(parsers_snapshot.uuid)
    if not snapshot_dir.exists():
        snapshot_dir.mkdir()

    # provide base path as part of the message, and certain results will contains file name.
    parsers_snapshot.path = str(snapshot_dir)

    if parsers_snapshot.color_image:
        handle_color_image(parsers_snapshot, snapshot.color_image.data)
    if parsers_snapshot.depth_image:
        handle_depth_image(parsers_snapshot, snapshot.depth_image.data)
    return parsers_snapshot
