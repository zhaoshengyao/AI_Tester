# -*- coding: utf-8 -*-
"""pytest conftest for IPD API automation (project_key=ipd).

Reads:
  - projects/ipd/.env (BASE_URL/API_BASE_URL/TEST_USERNAME/TEST_PASSWORD/API_CLIENT_ID)
  - projects/ipd/system.yaml (auth 6 items: login_path=/prod-api/auth/login, camel fields
    clientId + grantType, AES-256-ECB key=client_id_full 32B, tenantId=000000, captchaOff)

Fixtures
========
ipd_config(dict):    merged config from system.yaml + .env
api_base_url(str):   "http://192.168.2.97:6090/prod-api"
encrypt_password(pw): returns AES-256-ECB + pkcs7 + hex (lower) as IPD login expects
login_token(dict):   {"access_token": str, "token_type": str, "expires_in": int, "raw": dict}
                      Raises AssertionError if login fails (blocks downstream tests).
authed_session(requests.Session):   pre-configured Session with Authorization/tenantId/clientId.
                                    Automatically retries login once on 401 token expiry.
known_ids(dict):    stable ids from the实测 baseline: project_id_circuit, etc.
safe_str(v):        helper for optional fields (None -> "").
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

REPO_ROOT = Path(__file__).resolve().parents[3]   # AITestDemo/
IPD_ROOT = REPO_ROOT / "projects" / "ipd"
DOTENV = IPD_ROOT / ".env"
SYSTEM_YAML = IPD_ROOT / "system.yaml"


# ---------------------------------------------------------------------------
# Config loading (no PyYAML dependency required - parse the subset we need manually)
# ---------------------------------------------------------------------------

def _load_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    # Also apply to os.environ for processes that read from there
    for k, v in env.items():
        os.environ.setdefault(k, v)
    return env


def _load_system_yaml_auth(path: Path) -> dict[str, Any]:
    """Parse auth+auth.config blocks from system.yaml manually (no pyyaml dependency).

    YAML hierarchy we support:
        auth:
          type: oauth2
          config:
            grant_type: password
            grant_type_field: "grantType"
            client_id: "..."          # <- 32 hex
            client_id_field: "clientId"
            login_path: "/prod-api/auth/login"
            password_encryption: "aes-256-ecb"   # may have trailing comments
            password_encryption_key_source: "client_id_full"
            extra_fields:
              tenantId: "000000"

    Returns flat dict with keys matching the fixture expectations:
      grant_type, grant_type_field, client_id, client_id_field, login_path,
      password_encryption, password_encryption_key_source,
      extra_fields: {tenantId}
    """
    txt = path.read_text(encoding="utf-8")
    auth: dict[str, Any] = {"extra_fields": {}}

    # ---------- helpers ----------
    def _clean_value(raw_val: str) -> str:
        """Strip yaml comments and outer quotes."""
        val = raw_val.strip()
        if "#" in val:
            in_single = in_double = False
            cut_at = -1
            for i, ch in enumerate(val):
                if ch == "'" and not in_double:
                    in_single = not in_single
                elif ch == '"' and not in_single:
                    in_double = not in_double
                elif ch == "#" and not in_single and not in_double:
                    cut_at = i
                    break
            if cut_at >= 0:
                val = val[:cut_at].strip()
        return val.strip().strip('"').strip("'").strip()

    lines = txt.splitlines()
    i = 0
    # locate `auth:` line
    auth_indent = -1
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            indent = len(raw) - len(raw.lstrip())
            if stripped.startswith("auth:"):
                auth_indent = indent
                break
        i += 1
    if auth_indent < 0:
        return auth
    i += 1
    # locate `config:` child of auth (indent == auth_indent + 2, typically)
    config_indent = -1
    config_start = -1
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent <= auth_indent:
            # out of auth block already without finding config: give up
            return auth
        if stripped.startswith("config:"):
            config_indent = indent
            config_start = i + 1
            break
        i += 1
    if config_start < 0:
        return auth
    # iterate inside config block until indent <= config_indent
    in_extra = False
    i = config_start
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent <= config_indent:
            break
        if ":" in stripped:
            key, val = stripped.split(":", 1)
            key, val = key.strip(), _clean_value(val)
            if key == "extra_fields" and (val == "" or val == "{}"):
                in_extra = True
                i += 1
                continue
            if in_extra and key in ("tenantId",):
                auth["extra_fields"][key] = val
                i += 1
                continue
            if key in {
                "grant_type", "grant_type_field", "client_id", "client_id_field",
                "login_path", "password_encryption", "password_encryption_key_source",
                "token_field", "token_type", "username_field", "password_field",
            }:
                auth[key] = val
        i += 1
    return auth


@pytest.fixture(scope="session")
def ipd_config() -> dict[str, Any]:
    env = _load_dotenv(DOTENV)
    auth = _load_system_yaml_auth(SYSTEM_YAML)
    return {
        "base_url": env.get("BASE_URL") or "http://192.168.2.97:6090",
        "api_base_url": env.get("API_BASE_URL") or "http://192.168.2.97:6090/prod-api",
        "username": env.get("TEST_USERNAME") or env.get("API_USERNAME") or "赵经理",
        "password": env.get("TEST_PASSWORD") or env.get("API_PASSWORD") or "123456",
        "client_id": env.get("API_CLIENT_ID") or auth.get("client_id") or "e5cd7e4891bf95d1d19206ce24a7b32e",
        "auth": auth,
    }


@pytest.fixture(scope="session")
def api_base_url(ipd_config) -> str:
    return ipd_config["api_base_url"]


# ---------------------------------------------------------------------------
# AES-256-ECB password encryption (hex-encoded ciphertext, lowercase)
# ---------------------------------------------------------------------------

def _encrypt_aes_256_ecb_hex(plaintext: str, key_str: str) -> str:
    """IPD 实际密码加密方式（验证通过）：
    key 来源于 client_id 字符串的 **UTF-8 原始字节**，即对于 32 字符的 hex ASCII client_id，
    str.encode('utf-8') 得到 32 字节（= 256 bits），正好是 AES-256 的 key 长度。

    **特别注意**：此处不要对 client_id 做 hex→bytes 解码，否则 32 hex chars 只得到 16 字节
    （= AES-128，长度不够直接报错或登录"密码错误"）。
    """
    key_bytes = key_str.encode("utf-8")
    if len(key_bytes) != 32:
        # Fallback: 如果不是 32 字符 ASCII（比如未来 client_id 缩短），按字节补 0x00 或截断
        if len(key_bytes) < 32:
            key_bytes = key_bytes + b"\x00" * (32 - len(key_bytes))
        else:
            key_bytes = key_bytes[:32]
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    padded = pad(plaintext.encode("utf-8"), AES.block_size, style="pkcs7")
    ct = cipher.encrypt(padded)
    return ct.hex().lower()


@pytest.fixture(scope="session")
def encrypt_password(ipd_config):
    key_source = ipd_config["auth"].get("password_encryption_key_source", "client_id_full")
    if key_source == "client_id_full":
        key = ipd_config["client_id"]
    else:
        key = ipd_config["client_id"]
    assert ipd_config["auth"].get("password_encryption", "").lower() == "aes-256-ecb", (
        f"Only aes-256-ecb supported in IPD fixture; got {ipd_config['auth'].get('password_encryption')}"
    )

    def _enc(pw: str) -> str:
        return _encrypt_aes_256_ecb_hex(pw, key)

    return _enc


# ---------------------------------------------------------------------------
# Login + authed session (session-scoped, auto refresh on 401)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def login_token(ipd_config, encrypt_password, api_base_url) -> dict[str, Any]:
    auth = ipd_config["auth"]
    payload = {
        auth.get("client_id_field", "clientId"): ipd_config["client_id"],
        auth.get("grant_type_field", "grantType"): auth.get("grant_type", "password"),
        "username": ipd_config["username"],
        "password": encrypt_password(ipd_config["password"]),
    }
    for k, v in (auth.get("extra_fields") or {}).items():
        payload.setdefault(k, v)

    login_path = auth.get("login_path", "/auth/login")
    # system.yaml login_path is "/prod-api/auth/login" but urljoin with api_base_url already
    # contains /prod-api. Strip /prod-api prefix if present to avoid double prefix.
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")

    resp = requests.post(url, json=payload, timeout=15)
    assert resp.status_code == 200, f"Login HTTP {resp.status_code}: {resp.text[:500]}"
    body = resp.json()
    code = body.get("code")
    assert code == 200, f"Login business code={code}; msg={body.get('msg')}; {resp.text[:500]}"
    data = body.get("data") or {}
    access_token = data.get("access_token")
    assert access_token and isinstance(access_token, str) and len(access_token) > 200, (
        f"Login token missing or too short: {data}"
    )
    return {
        "access_token": access_token,
        "token_type": data.get("token_type", "Bearer"),
        "expires_in": data.get("expires_in"),
        "login_payload_keys": sorted(payload.keys()),  # for debugging 6 param naming
        "raw": body,
    }


class _AuthedSession(requests.Session):
    """requests.Session with Authorization header + retry-once on 401."""

    def __init__(self, token: str, client_id: str, tenant_id: str, refresh_factory):
        super().__init__()
        self.headers.update({
            "Authorization": f"Bearer {token}",
            "clientid": client_id,
            "tenant-id": tenant_id,
            "Content-Type": "application/json",
        })
        self._client_id = client_id
        self._tenant_id = tenant_id
        self._refresh = refresh_factory
        self._retried_on_401 = False

    def request(self, method, url, **kwargs):  # type: ignore[override]
        r = super().request(method, url, **kwargs)
        if r.status_code in (401, 403) and not self._retried_on_401:
            # refresh once
            self._retried_on_401 = True
            new_token = self._refresh()
            self.headers["Authorization"] = f"Bearer {new_token}"
            r = super().request(method, url, **kwargs)
        return r


@pytest.fixture(scope="session")
def authed_session(ipd_config, login_token, encrypt_password, api_base_url):
    tenant_id = (ipd_config["auth"].get("extra_fields") or {}).get("tenantId", "000000")

    def _refresh() -> str:
        # re-login with same credentials; re-use login_token fixture logic
        auth = ipd_config["auth"]
        payload = {
            auth.get("client_id_field", "clientId"): ipd_config["client_id"],
            auth.get("grant_type_field", "grantType"): auth.get("grant_type", "password"),
            "username": ipd_config["username"],
            "password": encrypt_password(ipd_config["password"]),
        }
        for k, v in (auth.get("extra_fields") or {}).items():
            payload.setdefault(k, v)
        login_path = auth.get("login_path", "/auth/login")
        if login_path.startswith("/prod-api/"):
            login_path = login_path[len("/prod-api"):]
        url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
        body = requests.post(url, json=payload, timeout=15).json()
        assert body.get("code") == 200, f"refresh login failed: {body}"
        return body["data"]["access_token"]

    sess = _AuthedSession(
        token=login_token["access_token"],
        client_id=ipd_config["client_id"],
        tenant_id=tenant_id,
        refresh_factory=_refresh,
    )
    return sess


@pytest.fixture(scope="session")
def known_ids() -> dict[str, str]:
    """Stable ids captured from实测 baseline for the 5 projects / riskRule/1 etc."""
    return {
        # project ids
        "project_circuit": "2086985374914007042",   # 回路监控箱设备 hardware/closed
        "project_gateway": "2086985374914007041",   # 智能网关设备 hardware/inProgress
        "project_lock": "2085617546210209793",      # 智能蓝牙门锁 hardware/inProgress
        "project_doc": "2086985374914007043",       # 智慧文档管理系统 software/approved
        "project_compliance": "2086985374914007044", # 智慧合规系统 software/inProgress
        "risk_rule_budget_warn_id": "1",            # BUDGET_WARN
        "wf_category_idmp": "2099000000000000001",  # IDMP 审批分类 id（R10 过滤验证，实际执行时若错再调整）
    }


@pytest.fixture(scope="session")
def safe_str():
    def _safe(v: Any, default: str = "") -> str:
        return default if v is None else str(v)
    return _safe


# =========================================================
# 赵老板角色（全局老板视角，只读权限）fixtures （复用现有加密算法，
# 账号 = 赵老板/密码=123456；与 .env 的赵经理账号隔离）
# =========================================================

BOSS_USERNAME = "赵老板"
BOSS_PASSWORD = "123456"


def _do_login_request(
    username: str, password_plain: str, ipd_config: dict, encrypt_password, api_base_url: str
) -> dict:
    """通用：对任意 username/password 发登录请求。返回完整响应 body。"""
    auth = ipd_config["auth"]
    payload = {
        auth.get("client_id_field", "clientId"): ipd_config["client_id"],
        auth.get("grant_type_field", "grantType"): auth.get("grant_type", "password"),
        "username": username,
        "password": encrypt_password(password_plain),
    }
    for k, v in (auth.get("extra_fields") or {}).items():
        payload.setdefault(k, v)

    login_path = auth.get("login_path", "/auth/login")
    if login_path.startswith("/prod-api/"):
        login_path = login_path[len("/prod-api"):]
    url = api_base_url.rstrip("/") + "/" + login_path.lstrip("/")
    r = requests.post(url, json=payload, timeout=15)
    assert r.status_code == 200, f"[{username}] 登录 HTTP={r.status_code} body={r.text[:500]}"
    body = r.json()
    assert body.get("code") == 200, f"[{username}] 登录业务 code={body.get('code')} msg={body.get('msg')} body={r.text[:500]}"
    data = body.get("data") or {}
    access_token = data.get("access_token")
    assert access_token and isinstance(access_token, str) and len(access_token) > 200, f"[{username}] token 缺失/太短 data={data}"
    return {"access_token": access_token, "token_type": data.get("token_type", "Bearer"),
            "expires_in": data.get("expires_in"), "user": data.get("user") or {}, "raw": body}


@pytest.fixture(scope="session")
def boss_login_token(ipd_config, encrypt_password, api_base_url) -> dict:
    """赵老板角色登录 token（session 级 scope，与 authed_session 互不影响）。"""
    return _do_login_request(BOSS_USERNAME, BOSS_PASSWORD, ipd_config, encrypt_password, api_base_url)


@pytest.fixture(scope="session")
def boss_authed_session(ipd_config, boss_login_token, encrypt_password, api_base_url):
    """赵老板角色的 requests Session（带 401 自动刷新）。"""
    tenant_id = (ipd_config["auth"].get("extra_fields") or {}).get("tenantId", "000000")

    def _refresh() -> str:
        data = _do_login_request(BOSS_USERNAME, BOSS_PASSWORD, ipd_config, encrypt_password, api_base_url)
        return data["access_token"]

    return _AuthedSession(
        token=boss_login_token["access_token"],
        client_id=ipd_config["client_id"],
        tenant_id=tenant_id,
        refresh_factory=_refresh,
    )
