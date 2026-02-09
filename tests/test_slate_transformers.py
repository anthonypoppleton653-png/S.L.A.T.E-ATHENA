# test_slate_transformers.py

import pytest
from slate.slate_transformers import SlateTransformerPipeline, PIPELINE_MODELS, SECURITY_LABELS, COMMIT_INTENT_LABELS

@pytest.fixture
def pipeline():
    return SlateTransformerPipeline()

def test_pipeline_init(pipeline):
    assert hasattr(pipeline, '_pipelines')
    assert hasattr(pipeline, '_load_times')
    assert hasattr(pipeline, '_torch_available')

def test_pipeline_models():
    assert "text-classification" in PIPELINE_MODELS
    assert PIPELINE_MODELS["text-classification"]["model"] == "microsoft/codebert-base"
    assert PIPELINE_MODELS["text-classification"]["gpu"] == 1

def test_security_labels_and_commit_intent_labels():
    assert len(SECURITY_LABELS) > 0
    assert len(COMMIT_INTENT_LABELS) > 0
    assert "SQL injection vulnerability" in SECURITY_LABELS
    assert "bug fix" in COMMIT_INTENT_LABELS

def test_pipeline_methods(pipeline):
    # Test if methods are present
    assert hasattr(pipeline, 'classify_text')
    assert hasattr(pipeline, 'extract_embeddings')
    assert hasattr(pipeline, 'security_scan')
    assert hasattr(pipeline, 'benchmark')
    assert hasattr(pipeline, 'batch_classify_file')