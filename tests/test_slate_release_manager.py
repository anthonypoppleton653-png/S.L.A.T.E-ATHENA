# test/test_slate_release_manager.py

import pytest
from pathlib import Path
from slate.slate_release_manager import ReleaseManager, ReleaseChannel

@pytest.fixture
def release_manager():
    return ReleaseManager()

def test_get_pyproject_version(release_manager):
    version = release_manager.get_pyproject_version()
    assert isinstance(version, str)

def test_get_git_tag(release_manager):
    tag = release_manager.get_git_tag()
    if tag is not None:
        assert isinstance(tag, str)
    else:
        assert tag is None

def test_get_git_sha(release_manager):
    sha = release_manager.get_git_sha()
    assert isinstance(sha, str)

def test_release_channels():
    channels = [ReleaseChannel.STABLE, ReleaseChannel.BETA, ReleaseChannel.NIGHTLY]
    for channel in channels:
        assert hasattr(ReleaseChannel, channel)
        assert getattr(ReleaseChannel, channel) == channel