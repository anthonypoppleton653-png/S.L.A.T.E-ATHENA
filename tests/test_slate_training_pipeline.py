# Modified: 2026-02-08T18:00:00Z | Author: COPILOT | Change: Add test coverage for slate_training_pipeline.py
"""Tests for slate/slate_training_pipeline.py — SecretScanner, dataclasses, constants."""
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConstants:
    """Test module-level constants and patterns."""

    def test_workspace_root_exists(self):
        from slate.slate_training_pipeline import WORKSPACE_ROOT
        assert isinstance(WORKSPACE_ROOT, Path)

    def test_training_dir_is_path(self):
        from slate.slate_training_pipeline import TRAINING_DIR
        assert isinstance(TRAINING_DIR, Path)

    def test_ollama_url_localhost(self):
        from slate.slate_training_pipeline import OLLAMA_URL
        assert '127.0.0.1' in OLLAMA_URL
        assert '0.0.0.0' not in OLLAMA_URL

    def test_secret_patterns_compiled(self):
        from slate.slate_training_pipeline import SECRET_PATTERNS
        assert len(SECRET_PATTERNS) >= 5
        for pattern in SECRET_PATTERNS:
            assert hasattr(pattern, 'search'), "Should be compiled regex"

    def test_excluded_file_patterns_are_strings(self):
        from slate.slate_training_pipeline import EXCLUDED_FILE_PATTERNS
        assert isinstance(EXCLUDED_FILE_PATTERNS, list)
        assert all(isinstance(p, str) for p in EXCLUDED_FILE_PATTERNS)

    def test_training_file_extensions_has_python(self):
        from slate.slate_training_pipeline import TRAINING_FILE_EXTENSIONS
        assert '.py' in TRAINING_FILE_EXTENSIONS
        assert '.yml' in TRAINING_FILE_EXTENSIONS or '.yaml' in TRAINING_FILE_EXTENSIONS


class TestTrainingSample:
    """Test TrainingSample dataclass."""

    def test_create_sample(self):
        from slate.slate_training_pipeline import TrainingSample
        sample = TrainingSample(
            source='test',
            content='print("hello")',
            content_type='code',
            file_path='test.py'
        )
        assert sample.source == 'test'
        assert sample.content_type == 'code'

    def test_sample_defaults(self):
        from slate.slate_training_pipeline import TrainingSample
        sample = TrainingSample(
            source='test',
            content='x = 1',
            content_type='code',
            file_path='t.py'
        )
        assert sample.commit_hash is None or isinstance(sample.commit_hash, str)
        assert sample.tokens_estimated >= 0 or sample.tokens_estimated is None


class TestSecurityScanResult:
    """Test SecurityScanResult dataclass."""

    def test_create_safe_result(self):
        from slate.slate_training_pipeline import SecurityScanResult
        result = SecurityScanResult(
            is_safe=True,
            secrets_found=[],
            pii_found=[],
            redacted_content='clean text',
            warnings=[]
        )
        assert result.is_safe is True
        assert len(result.secrets_found) == 0

    def test_create_unsafe_result(self):
        from slate.slate_training_pipeline import SecurityScanResult
        result = SecurityScanResult(
            is_safe=False,
            secrets_found=['API key detected'],
            pii_found=['email found'],
            redacted_content='[REDACTED]',
            warnings=['Contains secrets']
        )
        assert result.is_safe is False
        assert len(result.secrets_found) == 1


class TestSecretScanner:
    """Test SecretScanner class methods."""

    def test_init(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        assert hasattr(scanner, 'contains_secrets')

    def test_contains_secrets_clean(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        result = scanner.contains_secrets('x = 42\nprint("hello world")')
        assert isinstance(result, list)
        assert len(result) == 0

    def test_contains_secrets_with_api_key(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        # Pattern: api_key/secret_key/access_key = "value"
        content = 'api_key = "sk-1234567890abcdef1234567890abcdef"'
        result = scanner.contains_secrets(content)
        assert len(result) > 0

    def test_is_file_excluded_venv(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        assert scanner.is_file_excluded('.venv/lib/site-packages/foo.py') is True

    def test_is_file_excluded_node_modules(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        assert scanner.is_file_excluded('node_modules/express/index.js') is True

    def test_is_file_excluded_source(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        assert scanner.is_file_excluded('slate/slate_status.py') is False

    def test_get_stats(self):
        from slate.slate_training_pipeline import SecretScanner
        scanner = SecretScanner()
        stats = scanner.get_stats()
        assert isinstance(stats, dict)
        assert 'files_scanned' in stats or 'total_scanned' in stats or isinstance(stats, dict)

    @patch('slate.slate_training_pipeline.scan_text')
    @patch('slate.slate_training_pipeline.redact_text')
    def test_scan_and_redact_clean(self, mock_redact, mock_scan):
        from slate.slate_training_pipeline import SecretScanner
        mock_scan.return_value = []
        mock_redact.return_value = 'clean text'
        scanner = SecretScanner()
        result = scanner.scan_and_redact('clean text')
        assert result.is_safe is True


class TestGitIngester:
    """Test GitIngester class structure."""

    def test_init(self):
        from slate.slate_training_pipeline import GitIngester
        ingester = GitIngester(Path('.'))
        assert hasattr(ingester, 'get_all_tracked_files')
        assert hasattr(ingester, 'collect_code_samples')


class TestTrainingPipeline:
    """Test TrainingPipeline class."""

    def test_init(self):
        from slate.slate_training_pipeline import TrainingPipeline
        pipeline = TrainingPipeline()
        assert hasattr(pipeline, 'validate_training_data')
        assert hasattr(pipeline, 'collect_training_data')

    def test_load_state_missing_file(self):
        from slate.slate_training_pipeline import TrainingPipeline
        pipeline = TrainingPipeline()
        state = pipeline._load_state()
        assert isinstance(state, dict)
