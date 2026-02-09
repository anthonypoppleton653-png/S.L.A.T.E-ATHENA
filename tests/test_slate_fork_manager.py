# tests/test_slate_fork_manager.py

import pytest
from pathlib import Path
from slate.slate_fork_manager import ForkConfig, SLATE_UPSTREAM, PROTECTED_FILES, REQUIRED_FILES

def test_fork_config_initialization():
    config = ForkConfig("test_user", "test@example.com")
    assert config.user_name == "test_user"
    assert config.user_email == "test@example.com"
    assert config.upstream_url == SLATE_UPSTREAM
    assert config.fork_source == "upstream"

def test_fork_config_to_dict_and_from_dict():
    config = ForkConfig("test_user", "test@example.com")
    config_dict = config.to_dict()
    new_config = ForkConfig.from_dict(config_dict)
    assert new_config.user_name == config.user_name
    assert new_config.user_email == config.user_email

def test_protected_files_and_required_files():
    assert Path(PROTECTED_FILES[0]).is_dir()  # Check if the protected files path is a directory
    assert REQUIRED_FILES  # Check if required files list is not empty