#!/usr/bin/env python3
"""
多电工挂牌 E2E 测试（同工单两条 active 挂牌 + 分步解牌 + 送电审批）。

前提：
  - 后端已启动（默认 http://127.0.0.1:5050）
  - MySQL 可从本机访问（Docker 映射时默认端口 3307）

说明：
  - 「第二人并入免审批工单」依赖 OPC/MQTT 中 active_tag_count>0 且 device_signal_points 有配置，
    环境差异大；本脚本用**数据库插入第二条挂牌**模拟第二电工，覆盖核心业务规则。
  - 连接参数可用环境变量：E2E_DB_HOST / E2E_DB_PORT / E2E_DB_USER / E2E_DB_PASSWORD / E2E_DB_NAME

用法: python tools/e2e_multi_electrician_tag_test.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pymysql

BASE = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:5050").rstrip("/")
PWD = "123456"

DB = {
    "host": os.environ.get("E2E_DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("E2E_DB_PORT", "3307")),
    "user": os.environ.get("E2E_DB_USER", "root"),
    "password": os.environ.get("E2E_DB_PASSWORD", "hxy19990606"),
    "database": os.environ.get("E2E_DB_NAME", "power_control"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def req(
    method: str,
    path: str,
    session_cookie: str | None = None,
    body: dict | None = None,
) -> tuple[int, dict | list | str, str | None]:
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
        with urlopen(r, timeout=90) as resp:
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

    sess = None
    if cookie and "session=" in cookie:
        sess = cookie.split(";")[0].strip()

    try:
        parsed: dict | list = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = raw

    return sc, parsed, sess


def login(username: str) -> str:
    sc, body, sess = req("POST", "/api/login", body={"username": username, "password": PWD})
    if sc != 200 or not sess:
        raise RuntimeError(f"登录失败 {username}: {sc} {body}")
    return sess


def register(username: str, role: str, realname: str) -> None:
    sc, body, _ = req(
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


def insert_second_electrician_tag(application_id: int, device_id: str, e2_id: int, e2_name: str) -> None:
    """为同工单插入第二电工的有效挂牌（模拟现场第二人挂牌/并入工单后的记录）。"""
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO device_tag_records
                    (device_id, application_id, electrician_id, electrician_name, tag_status, tag_time)
                VALUES (%s, %s, %s, %s, 'active', NOW())
                """,
                (device_id, application_id, e2_id, e2_name),
            )
        conn.commit()
    finally:
        conn.close()


def fetch_tag_count_for_app(application_id: int) -> int:
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS c FROM device_tag_records
                WHERE application_id = %s AND tag_status = 'active'
                """,
                (application_id,),
            )
            row = cur.fetchone()
            return int(row["c"] if row else 0)
    finally:
        conn.close()


def main() -> int:
    suffix = uuid.uuid4().hex[:8]
    u1 = f"multi_e1_{suffix}"
    u2 = f"multi_e2_{suffix}"
    ud = f"multi_d_{suffix}"

    print(f"BASE: {BASE}")
    print(f"DB: {DB['host']}:{DB['port']}/{DB['database']}")

    try:
        pymysql.connect(**DB).close()
    except Exception as e:
        print(f"FAIL: 无法连接 MySQL（请检查 E2E_DB_* 与 Docker 端口）: {e}", file=sys.stderr)
        return 2

    register(u1, "electrician", "多挂电工甲")
    register(u2, "electrician", "多挂电工乙")
    register(ud, "dispatcher", "多挂调度")

    s1 = login(u1)
    s2 = login(u2)
    sd = login(ud)

    sc, devices, _ = req("GET", "/api/devices", session_cookie=s1)
    if sc != 200 or not isinstance(devices, list) or not devices:
        print(f"FAIL: 无法获取设备列表: {sc}", file=sys.stderr)
        return 1

    candidates = [d.get("device_id") or d.get("deviceId") for d in devices if d.get("device_id") or d.get("deviceId")]

    created = None
    dev_used = None
    for did in candidates[:50]:
        sc, body, _ = req(
            "POST",
            "/api/power-apply",
            session_cookie=s1,
            body={
                "deviceIds": [did],
                "reason": "多电工挂牌 E2E",
                "power_off_time": "2026-04-01 08:00",
                "power_on_time": "2026-04-01 18:00",
            },
        )
        if sc == 200 and isinstance(body, dict):
            cr = body.get("created") or []
            if isinstance(cr, list) and cr:
                created = cr[0]
                dev_used = did
                break

    if not created or not dev_used:
        print("FAIL: 无法找到可提交停电申请的设备（均被未完工单占用）", file=sys.stderr)
        return 1

    app_id = created["id"]
    print(f"工单 #{app_id} 设备 {dev_used}")

    sc, body, _ = req(
        "POST",
        "/api/power-off-approve",
        session_cookie=sd,
        body={"id": app_id, "action": "approve", "comment": "同意停电"},
    )
    if sc != 200:
        print(f"FAIL: 停电审批: {sc} {body}", file=sys.stderr)
        return 1

    for step in (
        ("POST", "/api/electrician-verify", {"id": app_id, "safety_measures": "已确认", "comment": "验电"}),
        ("POST", "/api/repair-operation", {"id": app_id, "operation": "start", "comment": "开工"}),
        ("POST", "/api/repair-operation", {"id": app_id, "operation": "end", "comment": "完工"}),
    ):
        sc, body, _ = req(step[0], step[1], session_cookie=s1, body=step[2])
        if sc != 200:
            print(f"FAIL: {step[1]} -> {sc} {body}", file=sys.stderr)
            return 1

    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (u2,))
            row = cur.fetchone()
            e2_id = row["id"] if row else None
        if not e2_id:
            print("FAIL: 找不到用户 u2 id", file=sys.stderr)
            return 1
    finally:
        conn.close()

    # 此时甲有一条验电产生的挂牌；再插入乙的挂牌（同工单）
    insert_second_electrician_tag(app_id, dev_used, e2_id, "多挂电工乙")

    ntags = fetch_tag_count_for_app(app_id)
    if ntags < 2:
        print(f"FAIL: 期望至少 2 条 active 挂牌，实际 {ntags}", file=sys.stderr)
        return 1
    print(f"数据库确认：工单 #{app_id} 上 active 挂牌数 = {ntags}")

    sc, detail, _ = req("GET", f"/api/application/{app_id}", session_cookie=s1)
    if sc != 200 or not isinstance(detail, dict):
        print(f"FAIL: 详情: {sc}", file=sys.stderr)
        return 1
    app_payload = detail.get("application") if isinstance(detail.get("application"), dict) else detail
    ac = int(app_payload.get("active_tag_count") or 0)
    if ac < 2:
        print(f"FAIL: 详情 active_tag_count 期望>=2，实际 {ac}", file=sys.stderr)
        return 1

    # 甲先申请送电：应只解本人牌，且不进入送电审批（仍有乙的牌）
    sc, po1, _ = req(
        "POST",
        "/api/power-on-apply",
        session_cookie=s1,
        body={"id": app_id, "comment": "甲解牌", "power_on_time": "2026-04-01 18:00"},
    )
    if sc != 200:
        print(f"FAIL: 甲送电申请 HTTP {sc} {po1}", file=sys.stderr)
        return 1
    if not isinstance(po1, dict):
        print(f"FAIL: 甲送电申请响应异常", file=sys.stderr)
        return 1
    ready1 = po1.get("power_on_ready")
    if ready1 is not False:
        print(f"FAIL: 甲送电后应 power_on_ready=false，实际 {po1}", file=sys.stderr)
        return 1

    sc, st, _ = req("GET", f"/api/application/{app_id}", session_cookie=s1)
    st_app = st.get("application") if isinstance(st.get("application"), dict) else st
    if sc != 200 or not isinstance(st, dict) or st_app.get("status") != "repair_completed":
        print(f"FAIL: 仍有挂牌时应保持 repair_completed，实际 {st_app.get('status')}", file=sys.stderr)
        return 1

    # 乙再申请：应进入送电审批
    sc, po2, _ = req(
        "POST",
        "/api/power-on-apply",
        session_cookie=s2,
        body={"id": app_id, "comment": "乙解牌", "power_on_time": "2026-04-01 18:00"},
    )
    if sc != 200 or not isinstance(po2, dict):
        print(f"FAIL: 乙送电申请 {sc} {po2}", file=sys.stderr)
        return 1
    if po2.get("power_on_ready") is not True:
        print(f"FAIL: 乙送电后应 power_on_ready=true，实际 {po2}", file=sys.stderr)
        return 1

    # 乙可能无权查看非本人申请，用调度会话拉状态
    sc, st, _ = req("GET", f"/api/application/{app_id}", session_cookie=sd)
    st_app = st.get("application") if isinstance(st.get("application"), dict) else st
    if st_app.get("status") != "power_on_applied":
        print(f"FAIL: 应进入 power_on_applied，实际 {st_app.get('status')}", file=sys.stderr)
        return 1

    sc, body, _ = req(
        "POST",
        "/api/power-on-approve",
        session_cookie=sd,
        body={"id": app_id, "approved": True, "comment": "同意送电"},
    )
    if sc != 200:
        print(f"FAIL: 送电审批 {sc} {body}", file=sys.stderr)
        return 1

    sc, st, _ = req("GET", f"/api/application/{app_id}", session_cookie=s1)
    st_app = st.get("application") if isinstance(st.get("application"), dict) else st
    if st_app.get("status") != "completed":
        print(f"FAIL: 最终应 completed，实际 {st_app.get('status')}", file=sys.stderr)
        return 1

    print("PASS: 多电工挂牌 — 分步解牌、送电审批、工单闭环均符合预期。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
