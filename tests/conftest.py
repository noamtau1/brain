import gzip
import os
import struct
import sys

import docker
import pymongo
import pytest

from brain import tests_path as _tests_path
from brain.autogen import mind_pb2
from brain.utils.consts import *
from .data_generators import gen_user, gen_snapshot_for_client
from .utils import wait_for_address

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_resources_path = _tests_path / 'resources'
_sample_path = _resources_path / 'tests_sample.mind.gz'


@pytest.fixture(scope='session')
def tests_path():
    return _tests_path


@pytest.fixture(scope='session')
def resources_path():
    return _resources_path


def write_sample(user, snapshots, path):
    # given a user and snapshot, write it to sample file in mind.gz format
    file_path = str(path / 'sample.mind.gz')
    user_raw = user.SerializeToString()
    snapshots_raw = [snapshot.SerializeToString() for snapshot in snapshots]
    with gzip.open(file_path, 'wb') as file:
        file.write(struct.pack('I', len(user_raw)) + user_raw)
        for snapshot_raw in snapshots_raw:
            file.write(struct.pack('I', len(snapshot_raw)) + snapshot_raw)

    return file_path


@pytest.fixture
def random_sample(tmp_path):
    # generate random sample and write it to file
    user = gen_user(mind_pb2.User())
    snapshots = [gen_snapshot_for_client() for _ in range(5)]
    file_path = write_sample(user, snapshots, tmp_path)
    return user, snapshots, file_path


@pytest.fixture(scope='session', autouse=True)
def run_containers():
    # run required docker containers (mongodb, rabbitmq) before all tests
    client = docker.from_env()
    mongo_container = client.containers.run('mongo:latest', detach=True, ports={f'{DB_PORT}/tcp': DB_PORT},
                                            network='host')
    rabbit_container = client.containers.run('rabbitmq:latest', detach=True, ports={f'{MQ_PORT}/tcp': MQ_PORT},
                                             network='host')
    wait_for_address(DB_HOST, DB_PORT, timeout=15.0)
    wait_for_address(MQ_HOST, MQ_PORT, timeout=15.0)
    yield
    mongo_container.stop()
    rabbit_container.stop()


@pytest.fixture(scope='session', autouse=True)
def database(run_containers):
    # database connection
    conn = pymongo.MongoClient(DB_URL)
    conn.drop_database(DB_NAME)
    db = conn.brain
    yield db
    conn.drop_database(DB_NAME)
    conn.close()
