import ast
import os
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "taivas_control_center.py"
SOURCE = ENTRYPOINT.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_node(name):
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"Function {name} was not found")


def _function_source(name):
    return ast.get_source_segment(SOURCE, _function_node(name))


class _Context:
    def __init__(self, url="", headers=None):
        self.url = url
        self.headers = {} if headers is None else headers


class _Streamlit:
    def __init__(self, context):
        self.context = context


class _NoContextStreamlit:
    pass


class _BrokenContextStreamlit:
    @property
    def context(self):
        raise RuntimeError("No request context")


def _detector():
    namespace = {
        "os": os,
        "urlparse": urlparse,
        "st": _NoContextStreamlit(),
    }
    node = _function_node("detect_runtime_environment")
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(ENTRYPOINT), "exec"), namespace)
    return namespace["detect_runtime_environment"]


class RuntimeEnvironmentMetadataTests(unittest.TestCase):
    def test_explicit_streamlit_cloud_override(self):
        self.assertEqual(
            _detector()(
                {"TAIVAS_RUNTIME_ENV": "streamlit_cloud"},
                _NoContextStreamlit(),
            ),
            "streamlit_cloud",
        )

    def test_explicit_local_override(self):
        self.assertEqual(
            _detector()(
                {"TAIVAS_RUNTIME_ENV": "local"},
                _NoContextStreamlit(),
            ),
            "local",
        )

    def test_explicit_deployed_override(self):
        self.assertEqual(
            _detector()(
                {"TAIVAS_RUNTIME_ENV": "deployed"},
                _NoContextStreamlit(),
            ),
            "deployed",
        )

    def test_invalid_override_continues_to_url_detection(self):
        self.assertEqual(
            _detector()(
                {"TAIVAS_RUNTIME_ENV": "unverified-value"},
                _Streamlit(
                    _Context(url="https://example-taivas.streamlit.app/")
                ),
            ),
            "streamlit_cloud",
        )

    def test_streamlit_cloud_url(self):
        self.assertEqual(
            _detector()(
                {},
                _Streamlit(
                    _Context(url="https://example-taivas.streamlit.app/")
                ),
            ),
            "streamlit_cloud",
        )

    def test_localhost_url(self):
        self.assertEqual(
            _detector()(
                {},
                _Streamlit(_Context(url="http://localhost:8501/")),
            ),
            "local",
        )

    def test_streamlit_cloud_host_header(self):
        self.assertEqual(
            _detector()(
                {},
                _Streamlit(
                    _Context(
                        headers={
                            "Host": "example-taivas.streamlit.app",
                        }
                    )
                ),
            ),
            "streamlit_cloud",
        )

    def test_missing_or_broken_context_falls_back_to_local(self):
        detector = _detector()
        self.assertEqual(detector({}, _NoContextStreamlit()), "local")
        self.assertEqual(detector({}, _BrokenContextStreamlit()), "local")

    def test_audit_runtime_uses_detector_and_preserves_other_fields(self):
        audit_source = _function_source("build_audit_trail_record")
        self.assertIn(
            '"environment": detect_runtime_environment()',
            audit_source,
        )
        self.assertNotIn(
            '"environment": TAIVAS_RUNTIME_CONFIG["environment"]',
            audit_source,
        )
        self.assertIn(
            '"audit_backend": TAIVAS_RUNTIME_CONFIG["audit_backend"]',
            audit_source,
        )
        self.assertIn(
            'bool(TAIVAS_RUNTIME_CONFIG["audit_log_path"])',
            audit_source,
        )


if __name__ == "__main__":
    unittest.main()
