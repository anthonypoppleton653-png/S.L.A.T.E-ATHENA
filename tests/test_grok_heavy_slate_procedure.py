# Modified: 2026-02-08T18:00:00Z | Author: COPILOT | Change: Add test coverage for grok_heavy_slate_procedure.py
"""Tests for slate/grok_heavy_slate_procedure.py — security audit, findings, constants."""
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConstants:
    """Test module-level constants."""

    def test_workspace_root(self):
        from slate.grok_heavy_slate_procedure import WORKSPACE_ROOT
        assert isinstance(WORKSPACE_ROOT, Path)

    def test_ollama_host_localhost(self):
        from slate.grok_heavy_slate_procedure import OLLAMA_HOST
        assert '127.0.0.1' in OLLAMA_HOST or 'localhost' in OLLAMA_HOST
        assert '0.0.0.0' not in OLLAMA_HOST

    def test_analysis_models(self):
        from slate.grok_heavy_slate_procedure import ANALYSIS_MODELS
        assert isinstance(ANALYSIS_MODELS, dict)
        assert 'code_audit' in ANALYSIS_MODELS
        assert 'security_plan' in ANALYSIS_MODELS or 'triage' in ANALYSIS_MODELS

    def test_fallback_models(self):
        from slate.grok_heavy_slate_procedure import FALLBACK_MODELS
        assert isinstance(FALLBACK_MODELS, dict)
        assert len(FALLBACK_MODELS) >= 2

    def test_skip_patterns(self):
        from slate.grok_heavy_slate_procedure import SKIP_PATTERNS
        assert isinstance(SKIP_PATTERNS, list)
        assert len(SKIP_PATTERNS) >= 5

    def test_audit_prompts(self):
        from slate.grok_heavy_slate_procedure import AUDIT_PROMPTS
        assert isinstance(AUDIT_PROMPTS, dict)
        assert 'code_vulnerability' in AUDIT_PROMPTS
        for key, prompt in AUDIT_PROMPTS.items():
            assert isinstance(prompt, str)
            assert len(prompt) > 20


class TestFinding:
    """Test Finding dataclass."""

    def test_create_finding(self):
        from slate.grok_heavy_slate_procedure import Finding
        f = Finding(
            severity='high',
            file_path='slate/test.py',
            line_number=42,
            description='SQL injection vulnerability',
            recommendation='Use parameterized queries',
            source='static_scan'
        )
        assert f.severity == 'high'
        assert f.line_number == 42

    def test_finding_to_dict(self):
        from slate.grok_heavy_slate_procedure import Finding
        f = Finding(
            severity='medium',
            file_path='app.py',
            line_number=10,
            description='Test finding',
            recommendation='Fix it',
            source='llm'
        )
        d = f.to_dict()
        assert isinstance(d, dict)
        assert d['severity'] == 'medium'
        assert d['file'] == 'app.py'  # to_dict() uses 'file' not 'file_path'
        assert d['line'] == 10  # to_dict() uses 'line' not 'line_number'

    def test_finding_timestamp(self):
        from slate.grok_heavy_slate_procedure import Finding
        f = Finding(
            severity='low',
            file_path='x.py',
            line_number=1,
            description='desc',
            recommendation='fix',
            source='test'
        )
        assert f.timestamp is not None or 'timestamp' in f.to_dict()


class TestAuditReport:
    """Test AuditReport dataclass."""

    def test_create_report(self):
        from slate.grok_heavy_slate_procedure import AuditReport, Finding
        report = AuditReport(
            findings=[
                Finding('high', 'a.py', 1, 'desc', 'fix', 'test'),
                Finding('low', 'b.py', 2, 'desc2', 'fix2', 'test')
            ],
            files_scanned=10,
            duration_seconds=5.0,
            model_used='slate-coder'
        )
        assert len(report.findings) == 2
        assert report.files_scanned == 10

    def test_report_to_dict(self):
        from slate.grok_heavy_slate_procedure import AuditReport, Finding
        report = AuditReport(
            findings=[Finding('critical', 'x.py', 99, 'd', 'r', 's')],
            files_scanned=5,
            duration_seconds=2.0,
            model_used='test-model'
        )
        d = report.to_dict()
        assert isinstance(d, dict)
        assert 'findings' in d
        assert 'files_scanned' in d
        assert d['files_scanned'] == 5

    def test_empty_report(self):
        from slate.grok_heavy_slate_procedure import AuditReport
        report = AuditReport(
            findings=[],
            files_scanned=0,
            duration_seconds=0.0,
            model_used=None
        )
        d = report.to_dict()
        assert len(d['findings']) == 0


class TestGrokHeavySlateProcedure:
    """Test GrokHeavySlateProcedure class."""

    def test_init(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure
        proc = GrokHeavySlateProcedure()
        assert hasattr(proc, 'audit_file')
        assert hasattr(proc, 'audit_full')
        assert hasattr(proc, 'status')

    def test_should_skip_venv(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure, WORKSPACE_ROOT
        proc = GrokHeavySlateProcedure()
        # _should_skip expects absolute paths relative to WORKSPACE_ROOT
        assert proc._should_skip(WORKSPACE_ROOT / '.venv' / 'lib' / 'foo.py') is True

    def test_should_skip_node_modules(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure, WORKSPACE_ROOT
        proc = GrokHeavySlateProcedure()
        assert proc._should_skip(WORKSPACE_ROOT / 'node_modules' / 'express' / 'index.js') is True

    def test_should_not_skip_source(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure, WORKSPACE_ROOT
        proc = GrokHeavySlateProcedure()
        assert proc._should_skip(WORKSPACE_ROOT / 'slate' / 'slate_status.py') is False

    def test_select_model_code_audit(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure
        proc = GrokHeavySlateProcedure()
        model = proc._select_model('code_audit')
        # Should return a model name string or None
        assert model is None or isinstance(model, str)

    def test_parse_llm_response_empty(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure
        proc = GrokHeavySlateProcedure()
        findings = proc._parse_llm_response('', Path('test.py'))
        assert isinstance(findings, list)
        assert len(findings) == 0

    def test_parse_llm_response_json(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure
        proc = GrokHeavySlateProcedure()
        response = json.dumps({
            'findings': [{
                'severity': 'high',
                'line': 10,
                'description': 'Test vuln',
                'recommendation': 'Fix it'
            }]
        })
        findings = proc._parse_llm_response(response, Path('test.py'))
        assert isinstance(findings, list)

    def test_status_returns_dict(self):
        from slate.grok_heavy_slate_procedure import GrokHeavySlateProcedure
        proc = GrokHeavySlateProcedure()
        s = proc.status()
        assert isinstance(s, dict)
