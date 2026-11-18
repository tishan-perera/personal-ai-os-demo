import json
import threading
import unittest
import urllib.error
import urllib.request

from atrium.llm import DemoBrain
from atrium.office import Office
from atrium.server import make_server


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.office = Office(brain=DemoBrain())
        self.server = make_server(self.office, "127.0.0.1", 0, quiet=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.base = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def _request(
        self,
        path: str,
        payload: dict | None = None,
        method: str = "GET",
    ) -> tuple[int, dict | str]:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8")
                status = response.status
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            status = exc.code
        if body.startswith("{") or body.startswith("["):
            return status, json.loads(body)
        return status, body

    def test_health_and_desk_are_fictional_demo_mode(self) -> None:
        status, health = self._request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["mode"], "demo")
        self.assertTrue(health["fictional"])
        status, page = self._request("/")
        self.assertEqual(status, 200)
        self.assertIsInstance(page, str)
        self.assertIn("Fictional demo", page)
        self.assertIn("Atrium", page)

    def test_approve_and_reject_over_http(self) -> None:
        status, created = self._request(
            "/api/requests",
            {"text": "Pay the fictional studio rent of 900 dollars"},
            "POST",
        )
        self.assertEqual(status, 200)
        proposal_id = created["proposal"]["id"]
        status, state = self._request("/api/state")
        self.assertEqual(state["world"]["flags"]["studio_rent"], "unpaid")
        status, rejected = self._request(
            f"/api/proposals/{proposal_id}/decision",
            {"decision": "reject", "actor": "owner"},
            "POST",
        )
        self.assertEqual(status, 200)
        self.assertEqual(rejected["proposal"]["status"], "rejected")
        self.assertEqual(rejected["world_flags"]["studio_rent"], "unpaid")
        status, again = self._request(
            f"/api/proposals/{proposal_id}/decision",
            {"decision": "approve", "actor": "owner"},
            "POST",
        )
        self.assertEqual(status, 409)
        self.assertEqual(again["error"]["code"], "not_pending")

    def test_empty_request_and_reset(self) -> None:
        status, error = self._request("/api/requests", {"text": "  "}, "POST")
        self.assertEqual(status, 400)
        self.assertEqual(error["error"]["code"], "empty_request")
        self._request("/api/requests", {"text": "Summarize the fictional inbox"}, "POST")
        status, state = self._request("/api/reset", {}, "POST")
        self.assertEqual(status, 200)
        self.assertEqual(state["turns"], [])
        self.assertEqual(state["proposals"], [])
        self.assertEqual(state["audit"], [])

    def test_unknown_path(self) -> None:
        status, body = self._request("/api/missing")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"]["code"], "not_found")


if __name__ == "__main__":
    unittest.main()
