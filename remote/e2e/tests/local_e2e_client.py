"""HTTP helpers for the loopback end-to-end browser and gateway flows."""

from __future__ import annotations

import http.client
import json
from urllib.parse import parse_qs, urlencode, urlsplit


class LocalE2EClient:
    def _request(self, path: str, *, cookie: str = ""):
        connection = http.client.HTTPConnection("127.0.0.1", self.web_port, timeout=4)
        headers = {"Cookie": cookie} if cookie else {}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read()
        result = response.status, response.getheaders(), body
        connection.close()
        return result

    def _post_command(self, command: dict, *, cookie: str):
        return self._post_gateway("/api/remote/v1/commands", command, cookie=cookie)

    def _post_challenge(self, target: dict, typed_req: str, *, cookie: str):
        return self._post_gateway("/api/remote/v1/challenges", {"target": target, "typedReq": typed_req},
                                  cookie=cookie)

    def _post_gateway(self, path: str, payload: dict, *, cookie: str):
        connection = http.client.HTTPConnection("127.0.0.1", self.gateway_port, timeout=4)
        body = json.dumps(payload).encode()
        connection.request("POST", path, body=body, headers={
            "Cookie": cookie,
            "Content-Type": "application/json",
            "Origin": f"http://127.0.0.1:{self.web_port}",
            "X-Flow-Request": "1",
        })
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def _sign_in(self, login: str) -> tuple[int, str]:
        status, headers, _ = self._request("/api/auth/login")
        self.assertEqual(status, 302)
        state_cookie = next(value.split(";", 1)[0] for name, value in headers if name.lower() == "set-cookie"
                            and value.startswith("flow_oauth_state="))
        authorize_url = next(value for name, value in headers if name.lower() == "location")
        parsed = urlsplit(authorize_url)
        query = parse_qs(parsed.query)
        provider_path = parsed.path + "?" + urlencode({
            "client_id": query["client_id"][0], "redirect_uri": query["redirect_uri"][0],
            "state": query["state"][0], "login": login,
        })
        provider = http.client.HTTPConnection("127.0.0.1", self.provider.server_address[1], timeout=3)
        provider.request("GET", provider_path)
        authorized = provider.getresponse()
        redirect = authorized.getheader("Location")
        authorized.read()
        provider.close()
        callback = urlsplit(redirect)
        status, headers, _ = self._request(callback.path + "?" + callback.query, cookie=state_cookie)
        session = next((value.split(";", 1)[0] for name, value in headers if name.lower() == "set-cookie"
                        and value.startswith("flow_session=")), "")
        return status, session
