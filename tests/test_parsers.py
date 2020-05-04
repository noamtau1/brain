import json
import os

import numpy as np
import pytest

import brain.parsers
from brain.autogen import parsers_pb2
from brain.parsers import run_parser, invoke_parser
from tests.data_generators import gen_server_snapshot
from tests.sample_generator import gen_random_user, gen_random_snapshot
from tests.utils import protobuf2dict, json2pb

MQ_URL = 'rabbitmq://127.0.0.1:5672'


@pytest.fixture
def parsers_snapshot(tmp_path):
    snapshot = gen_server_snapshot(tmp_path)
    data = snapshot.SerializeToString()
    return snapshot, data


def verify_result_header(result, snapshot):
    assert result['uuid'] == str(snapshot.uuid)  # TODO: this is workaround, solve the problem
    assert result['datetime'] == str(snapshot.datetime)
    assert result['user'] == protobuf2dict(snapshot.user)


def verify_pose(result, snapshot):
    assert result == protobuf2dict(snapshot.pose)


def verify_color_image(result, snapshot):
    # TODO: read image from file and compare
    assert os.path.isfile(result)


def verify_depth_image(result, snapshot):
    # TODO: read image from file and compare
    assert os.path.isfile(result)


def verify_feelings(result, snapshot):
    assert result == protobuf2dict(snapshot.feelings)


def test_pose(parsers_snapshot):
    snapshot, data = parsers_snapshot
    result = run_parser('pose', data)
    verify_result_header(result, snapshot)
    verify_pose(result['result'], snapshot)


def test_color_image(parsers_snapshot):
    # TODO: read image from file and compare
    snapshot, data = parsers_snapshot
    result = run_parser('color-image', data)
    verify_result_header(result, snapshot)
    verify_color_image(result['result'], snapshot)


def test_depth_image(parsers_snapshot):
    # TODO: read image from file and compare
    snapshot, data = parsers_snapshot
    result = run_parser('depth-image', data)
    verify_result_header(result, snapshot)
    verify_color_image(result['result'], snapshot)


def test_feelings(parsers_snapshot):
    snapshot, data = parsers_snapshot
    result = run_parser('feelings', data)
    verify_result_header(result, snapshot)
    verify_feelings(result['result'], snapshot)


class MockMQAgent:
    snapshot = None
    result = None

    def __init__(self, url):
        pass

    def consume_snapshots(self, callback, topic):
        callback(self.__class__.snapshot)

    def publish_result(self, result, topic):
        self.__class__.result = result

    @classmethod
    def clear(cls):
        cls.snapshot = cls.result = None


@pytest.fixture
def mock_mq_agent(monkeypatch):
    yield monkeypatch.setattr(brain.parsers.parsers, 'MQAgent', MockMQAgent)
    MockMQAgent.clear()


@pytest.mark.parametrize('parser', ['pose', 'color-image', 'depth-image', 'feelings'])
def test_invoke_parser(parser, mock_mq_agent, parsers_snapshot):
    snapshot, data = parsers_snapshot
    MockMQAgent.snapshot = data
    invoke_parser(parser, MQ_URL)
    result = MockMQAgent.result
    result = json.loads(result)
    verify_result_header(result, snapshot)
    result = result['result']
    if parser == 'pose':
        verify_pose(result, snapshot)
    elif parser == 'color-image':
        verify_color_image(result, snapshot)
    elif parser == 'depth-image':
        verify_depth_image(result, snapshot)
    else:
        verify_feelings(result, snapshot)


def test_mq_agent():
    assert False


def test_cli():
    assert False


@pytest.fixture
def random_snapshot(tmp_path):
    user = gen_random_user()
    snapshot = gen_random_snapshot()
    snapshot['user'] = user
    data = snapshot['color_image'].pop('data')
    with open(str(tmp_path / 'color_image.raw'), 'wb') as file:
        file.write(data)
    snapshot['color_image']['path'] = str(tmp_path / 'color_image.raw')
    data = snapshot['depth_image'].pop('data')
    array = np.array(data).astype(np.float)
    np.save(str(tmp_path / 'depth_image'), array)
    snapshot['depth_image']['path'] = str(tmp_path / 'depth_image.npy')
    snapshot_obj = parsers_pb2.Snapshot()
    data = json2pb(snapshot, snapshot_obj, serialize=True)
    return snapshot, data


def test_all_parsers(random_snapshot):
    pass
