from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class WeComAppClient:
    corpid: str
    corpsecret: str

    _access_token: str | None = None
    _expires_at: float = 0.0

    def _get_token(self) -> str:
        import requests

        now = time.time()
        if self._access_token and now < self._expires_at - 60:
            return self._access_token

        r = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            params={"corpid": self.corpid, "corpsecret": self.corpsecret},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom gettoken error: {data}")
        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 7200))
        self._expires_at = now + expires_in
        return self._access_token

    def send_markdown(
        self,
        *,
        agentid: int,
        markdown: str,
        touser: str | None = None,
        toparty: str | None = None,
        totag: str | None = None,
    ) -> None:
        import requests

        token = self._get_token()
        payload = {
            "msgtype": "markdown",
            "agentid": agentid,
            "markdown": {"content": markdown},
            "touser": touser or "",
            "toparty": toparty or "",
            "totag": totag or "",
            "safe": 0,
        }
        r = requests.post(
            "https://qyapi.weixin.qq.com/cgi-bin/message/send",
            params={"access_token": token},
            json=payload,
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"WeCom message/send error: {data}")

