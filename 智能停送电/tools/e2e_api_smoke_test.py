#!/usr/bin/env python3
"""
端到端 API 冒烟测试：需本机已启动后端（默认 http://127.0.0.1:5050）。
用法: python tools/e2e_api_smoke_test.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:5050").rstrip("/")
PWD = "123456"


def req(
    method: str,
    path: str,
    session_cookie: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict | list | str, str | None, str | None]:
    url = f"{BASE}{path}"
    data = None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    if session_cookie:
        headers["Cookie"] = session_cookie
    r = Request(url, data=data, headers=headers, method=method)
    cookie = None
    try:
        with urlopen(r, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            sc = resp.status
            cookie = resp.headers.get("Set-Cookie")
    except HTTPError as e:
        sc = e.code
        raw = e.read().decode("utf-8", errors="replace")
        cookie = e.headers.get("Set-Cookie")
    except URLError as e:
        print(f"FAIL: 无法连接 {BASE}: {e}", file=sys.stderr)
        sys.exit(2)

    # Flask session cookie from login
    sess = None
    if cookie and "session=" in cookie:
        sess = cookie.split(";")[0].strip()

    try:
        parsed: dict | list = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = raw

    return sc, parsed, sess, cookie


def login(username: str) -> str:
    sc, body, sess, _ = req("POST", "/api/login", body={"username": username, "password": PWD})
    if sc != 200 or not sess:
        raise RuntimeError(f"登录失败 {username}: {sc} {body}")
    return sess


def register(username: str, role: str, realname: str) -> None:
    sc, body, _, _ = req(
        "POST",
        "/api/register",
        body={"username": username, "password": PWD, "role": role, "realname": realname},
    )
    if sc not in (200, 400):
        raise RuntimeError(f"注册异常 {username}: {sc} {body}")
    if sc == 400 and isinstance(body, dict) and "已存在" in str(body.get("msg", "")):
        return
    if sc != 200:
        raise RuntimeError(f"注册失败 {username}: {body}")


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    u_e = f"test_e_{suffix}"
    u_d = f"test_d_{suffix}"
    u_u = f"test_u_{suffix}"
    u_a = f"test_a_{suffix}"

    results: list[tuple[str, bool, str]] = []

    def ok(name: str, cond: bool, detail: str = "") -> None:
        results.append((name, cond, detail))

    print(f"BASE: {BASE}")
    for u, role, rn in [
        (u_e, "electrician", "测试电工"),
        (u_d, "dispatcher", "测试调度"),
        (u_u, "user", "测试普通"),
        (u_a, "admin", "测试管理"),
    ]:
        register(u, role, rn)
        print(f"  用户就绪: {u} ({role})")

    # --- 电工 + 调度：完整工单 ---
    s_e = login(u_e)
    s_d = login(u_d)

    sc, devices, _s, _ = req("GET", "/api/devices", session_cookie=s_e)
    ok("GET /api/devices (电工)", sc == 200 and isinstance(devices, list), f"status={sc}")
    if not isinstance(devices, list) or not devices:
        print("FAIL: 无设备列表", file=sys.stderr)
        return 1

    # 依次尝试多台设备，直到没有「未完工单」冲突（开发库常有历史工单占住首条设备）
    dev_candidates = []
    for d in devices:
        did = d.get("device_id") or d.get("deviceId")
        if did:
            dev_candidates.append(did)

    body = None
    sc = 0
    dev_used = None
    for dev_id in dev_candidates[:40]:
        sc, body, _s, _ = req(
            "POST",
            "/api/power-apply",
            session_cookie=s_e,
            body={
                "deviceIds": [dev_id],
                "reason": "E2E 冒烟测试停电",
                "power_off_time": "2026-04-01 08:00",
                "power_on_time": "2026-04-01 18:00",
            },
        )
        if sc == 200 and isinstance(body, dict):
            created = body.get("created") or []
            if isinstance(created, list) and len(created) > 0:
                dev_used = dev_id
                break
    ok(
        "POST /api/power-apply",
        sc == 200 and dev_used is not None,
        f"device={dev_used} {str(body)[:160] if body else ''}",
    )
    app_id = None
    if isinstance(body, dict):
        apps = body.get("created") or body.get("applications") or body.get("applications_created")
        if isinstance(apps, list) and apps:
            app_id = apps[0].get("id")
        if app_id is None:
            app_id = body.get("id")
    ok("解析工单 id", app_id is not None, f"id={app_id}")
    if not app_id:
        print("FAIL: 无工单 id", file=sys.stderr)
        return 1

    sc, body, _, _ = req(
        "POST",
        "/api/power-off-approve",
        session_cookie=s_d,
        body={"id": app_id, "action": "approve", "comment": "同意"},
    )
    ok("POST /api/power-off-approve", sc == 200, str(body)[:120])

    sc, body, _, _ = req(
        "POST",
        "/api/electrician-verify",
        session_cookie=s_e,
        body={"id": app_id, "safety_measures": "措施已确认", "comment": "验电完成"},
    )
    ok("POST /api/electrician-verify", sc == 200, str(body)[:120])

    sc, body, _, _ = req(
        "POST",
        "/api/repair-operation",
        session_cookie=s_e,
        body={"id": app_id, "operation": "start", "comment": "开始检修"},
    )
    ok("POST /api/repair-operation start", sc == 200, str(body)[:120])

    sc, body, _, _ = req(
        "POST",
        "/api/repair-operation",
        session_cookie=s_e,
        body={"id": app_id, "operation": "end", "comment": "检修结束"},
    )
    ok("POST /api/repair-operation end", sc == 200, str(body)[:120])

    sc, body, _, _ = req(
        "POST",
        "/api/power-on-apply",
        session_cookie=s_e,
        body={
            "id": app_id,
            "comment": "申请送电",
            "power_on_time": "2026-04-01 18:00",
        },
    )
    ok("POST /api/power-on-apply", sc == 200, str(body)[:200])

    sc, body, _, _ = req(
        "POST",
        "/api/power-on-approve",
        session_cookie=s_d,
        body={"id": app_id, "approved": True, "comment": "同意送电"},
    )
    ok("POST /api/power-on-approve", sc == 200, str(body)[:120])

    # --- 其它只读 ---
    sc, body, _, _ = req("GET", f"/api/application/{app_id}", session_cookie=s_e)
    ok("GET /api/application/<id>", sc == 200, "")

    sc, body, _, _ = req("GET", "/api/notifications", session_cookie=s_e)
    ok("GET /api/notifications", sc == 200, "")

    sc, body, _, _ = req("GET", "/api/device-status", session_cookie=s_e)
    ok("GET /api/device-status", sc == 200, "")

    sc, body, _, _ = req("POST", "/api/device-control", session_cookie=s_e, body={})
    ok("POST /api/device-control 已停用(410)", sc == 410, "")

    # --- 普通用户：仅申请（换一台设备避免冲突）---
    s_u = login(u_u)
    u_body = None
    u_sc = 0
    u_dev = None
    for dev_id in dev_candidates[:40]:
        if dev_id == dev_used:
            continue
        u_sc, u_body, _, _ = req(
            "POST",
            "/api/power-apply",
            session_cookie=s_u,
            body={
                "deviceIds": [dev_id],
                "reason": "E2E 用户申请",
                "power_off_time": "2026-04-01 09:00",
            },
        )
        if u_sc == 200 and isinstance(u_body, dict) and (u_body.get("created") or u_body.get("joined")):
            u_dev = dev_id
            break
    ok(
        "普通用户 POST /api/power-apply",
        u_sc == 200 and u_dev is not None,
        f"dev={u_dev} {str(u_body)[:100] if u_body else ''}",
    )

    # --- 管理：用户列表 ---
    s_a = login(u_a)
    sc, body, _, _ = req("GET", "/api/users", session_cookie=s_a)
    ok("GET /api/users (admin)", sc == 200, "")

    sc, body, _, _ = req("GET", "/api/permission-options", session_cookie=s_a)
    ok("GET /api/permission-options", sc == 200, "")

    sc, body, _, _ = req("GET", "/api/system/metrics", session_cookie=s_a)
    ok("GET /api/system/metrics", sc == 200, "")

    sc, body, _, _ = req("GET", "/api/approval-history", session_cookie=s_d)
    ok("GET /api/approval-history", sc == 200, "")

    sc, body, _, _ = req("GET", "/api/completed-applications-history", session_cookie=s_d)
    ok("GET /api/completed-applications-history", sc == 200, "")

    sc, body, _, _ = req("GET", "/", session_cookie=None)
    ok("GET / 首页", sc == 200, "")

    # --- 补充：仅管理员导出、检修批次列表 ---
    sc, csv_body, _, _ = req("GET", "/api/export/applications", session_cookie=s_a)
    ok(
        "GET /api/export/applications (CSV, admin)",
        sc == 200 and isinstance(csv_body, str) and "ID" in csv_body[:200],
        f"len={len(csv_body) if isinstance(csv_body, str) else 0}",
    )

    sc, body, _, _ = req("GET", "/api/maintenance-batches", session_cookie=s_a)
    ok("GET /api/maintenance-batches (admin)", sc == 200, "")

    print("\n--- 结果汇总 ---")
    failed = 0
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        if not passed:
            failed += 1
        line = f"[{mark}] {name}"
        if detail:
            line += f" {detail}"
        print(line)

    print(f"\n合计: {len(results) - failed}/{len(results)} 通过")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
