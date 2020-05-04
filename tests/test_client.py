import gzip
import struct

import pytest
import brain.client.server_agent

from brain.autogen import reader_pb2, protocol_pb2
from brain.client import upload_sample
from tests.sample_generator import gen_random_user, gen_random_snapshot
from tests.data_generators import gen_user, gen_snapshot
from tests.utils import json2pb

HOST = '127.0.0.1'
PORT = 8000


def _write_sample(user, snapshots, path):
    file_path = str(path / 'sample.mind.gz')

    user_msg = json2pb(user, reader_pb2.User(), serialize=True)
    snapshots_msg = []
    for snapshot in snapshots:
        snapshot_msg = json2pb(snapshot, reader_pb2.Snapshot(), serialize=True)
        snapshots_msg.append(snapshot_msg)

    with open(file_path, 'wb') as writer:
        writer.write(struct.pack('I', len(user_msg)) + user_msg)
        for snapshot_msg in snapshots_msg:
            writer.write(struct.pack('I', len(snapshot_msg)) + snapshot_msg)

    return file_path


@pytest.fixture
def random_sample(tmp_path):
    user = gen_random_user()
    snapshots = [gen_random_snapshot() for _ in range(5)]
    file_path = _write_sample(user, snapshots, tmp_path)
    return user, snapshots, file_path


@pytest.fixture
def mock_server(monkeypatch):
    calls = []

    def mock_post(url, data):
        calls.append((url, data))
        return 200

    monkeypatch.setattr(brain.client.server_agent, 'post', mock_post)
    return calls


def write_sample(user, snapshots, path):
    file_path = str(path / 'sample.mind.gz')
    user_raw = user.SerializeToString()
    snapshots_raw = [snapshot.SerializeToString() for snapshot in snapshots]
    with gzip.open(file_path, 'wb') as file:
        file.write(struct.pack('I', len(user_raw)) + user_raw)
        for snapshot_raw in snapshots_raw:
            file.write(struct.pack('I', len(snapshot_raw)) + snapshot_raw)

    return file_path


@pytest.fixture
def new_random_sample(tmp_path):
    user = gen_user(reader_pb2.User())
    snapshots = [gen_snapshot(reader_pb2.Snapshot(), 'file', tmp_path=tmp_path) for _ in range(5)]
    file_path = write_sample(user, snapshots, tmp_path)
    return user, snapshots, file_path


def test_client_new(new_random_sample, mock_server):
    user, snapshots, file_path = new_random_sample
    upload_sample(HOST, PORT, file_path)
    calls = mock_server
    assert len(calls) == len(snapshots)
    for call, snapshot in zip(calls, snapshots):
        url, data = call
        result = protocol_pb2.Snapshot()
        result.ParseFromString(data)
        assert result.datetime == snapshot.datetime
        assert str(result.user) == str(user)
        assert str(result.pose) == str(snapshot.pose)
        assert str(result.color_image) == str(snapshot.color_image)
        assert str(result.depth_image) == str(snapshot.depth_image)
        assert str(result.feelings) == str(snapshot.feelings)

        # expected = protocol_pb2.Snapshot()
        # json2pb(user, expected.user)
        # json2pb(snapshot, expected)
        # data_snapshot = protocol_pb2.Snapshot()
        # data_snapshot.ParseFromString(data)
        # assert data_snapshot == expected


def test_client(random_sample, mock_server):
    user, snapshots, file_path = random_sample
    upload_sample(HOST, PORT, file_path)
    calls = mock_server
    assert len(calls) == len(snapshots)
    for call, snapshot in zip(calls, snapshots):
        url, data = call
        expected = protocol_pb2.Snapshot()
        json2pb(user, expected.user)
        json2pb(snapshot, expected)
        data_snapshot = protocol_pb2.Snapshot()
        data_snapshot.ParseFromString(data)
        assert data_snapshot == expected
