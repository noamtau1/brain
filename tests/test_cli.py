import pytest
from click.testing import CliRunner

import brain.cli.api_agent
from brain.cli.__main__ import cli
from brain.utils.consts import *


@pytest.fixture
def mock_get(monkeypatch):
    def fake_get(url):
        return url

    monkeypatch.setattr(brain.cli.api_agent, 'get', fake_get)


def test_get_users(mock_get):
    runner = CliRunner()
    result = runner.invoke(cli, ['get-users'])
    assert result.exit_code == 0
    assert furl(result.stdout.rstrip('\n')) == API_FURL / 'users'


def test_get_user(mock_get):
    runner = CliRunner()
    user_id = '1'
    result = runner.invoke(cli, ['get-user', user_id])
    assert result.exit_code == 0, result.exception
    assert furl(result.stdout.rstrip('\n')) == API_FURL / 'users' / user_id


def test_get_snapshots(mock_get):
    runner = CliRunner()
    user_id = '1'
    result = runner.invoke(cli, ['get-snapshots', user_id])
    assert result.exit_code == 0, result.exception
    assert furl(result.stdout.rstrip('\n')) == API_FURL / 'users' / user_id / 'snapshots'


def test_get_snapshot(mock_get):
    runner = CliRunner()
    user_id = '1'
    snapshot_id = '2'
    result = runner.invoke(cli, ['get-snapshot', user_id, snapshot_id])
    assert result.exit_code == 0, result.exception
    assert furl(result.stdout.rstrip('\n')) == API_FURL / 'users' / user_id / 'snapshots' / snapshot_id


@pytest.mark.parametrize('result_name', ['pose', 'color_image', 'depth_image', 'feelings'])
@pytest.mark.parametrize('with_save', [False, True])
def test_get_result(tmp_path, mock_get, result_name, with_save):
    runner = CliRunner()
    user_id = '1'
    snapshot_id = '2'
    path = tmp_path / 'result.txt'
    save_args = [] if not with_save else ['-s', str(path)]
    args = ['get-result', *save_args, user_id, snapshot_id, result_name]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.exception
    if with_save:
        assert path.exists(), f'result was not saved to {str(path)}'
        with open(str(path), 'r') as file:
            data = file.read()
    else:
        data = result.stdout.rstrip('\n')

    assert furl(data) == API_FURL / 'users' / user_id / 'snapshots' / snapshot_id / result_name
