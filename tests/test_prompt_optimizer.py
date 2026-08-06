from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

path = Path(__file__).resolve().parents[1] / "prompt_optimizer.py"
spec = importlib.util.spec_from_file_location("prompt_optimizer_test", path)
optimizer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(optimizer)


class Response:
    def __init__(self, chunks): self.chunks, self.closed = list(chunks), False
    def read(self, _size=-1): return self.chunks.pop(0) if self.chunks else b""
    def close(self): self.closed = True


class Progress:
    def __init__(self): self.values = []
    def update_absolute(self, value, *_args): self.values.append(value)


class OptimizerTests(unittest.TestCase):
    def test_split_sse_reasoning_and_progress(self):
        chunks = [
            b': keep-alive\n\ndata: {"choices":[{"delta":{"reasoning_content":"why "}}]}\n\nda',
            b'ta: {"choices":[{"delta":{"content":"```text\\ndone\\n```","reasoning_details":[{"text":"now"}]}}]}\n\ndata: [DONE]\n\n',
        ]
        progress = Progress()
        with mock.patch.object(optimizer, "urlopen", return_value=Response(chunks)), mock.patch.object(optimizer, "_check_interrupted"):
            result = optimizer.optimize_prompt("idea", "image", "http://localhost/v1", "model", max_tokens=1024, progress=progress)
        self.assertEqual(result, ("done", "why now"))
        self.assertEqual(progress.values[-1], 100)
        self.assertTrue(all(0 <= value <= 100 for value in progress.values))

    def test_non_stream_json(self):
        payload = {"choices": [{"message": {"content": "done", "reasoning": "why"}}]}
        with mock.patch.object(optimizer, "urlopen", return_value=Response([json.dumps(payload).encode()])), mock.patch.object(optimizer, "_check_interrupted"):
            self.assertEqual(optimizer.optimize_prompt("idea", "image", "http://localhost/v1", "model"), ("done", "why"))

    def test_auto_video_retries_once(self):
        calls = []
        def open_request(request, timeout=None):
            calls.append(json.loads(request.data))
            if len(calls) == 1:
                raise HTTPError(request.full_url, 415, "Unsupported", {}, io.BytesIO(b"video_url is not supported"))
            return Response([b'data: {"choices":[{"delta":{"content":"done"}}]}\n\ndata: [DONE]\n\n'])
        media = [{"type": "video", "label": "video", "data_url": "data:video/mp4;base64,AAAA", "sampled_frames": [{"label": "frame", "data_url": "data:image/jpeg;base64,BBBB"}]}]
        with mock.patch.object(optimizer, "urlopen", side_effect=open_request), mock.patch.object(optimizer, "_check_interrupted"):
            self.assertEqual(optimizer.optimize_prompt("idea", "reference", "http://localhost/v1", "model", media_items=media), ("done", ""))
        self.assertEqual(len(calls), 2)

    def test_truncated_stream_fails(self):
        value = b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'
        with mock.patch.object(optimizer, "urlopen", return_value=Response([value])), mock.patch.object(optimizer, "_check_interrupted"):
            with self.assertRaisesRegex(RuntimeError, "stream ended"):
                optimizer.optimize_prompt("idea", "image", "http://localhost/v1", "model")


if __name__ == "__main__":
    unittest.main()
