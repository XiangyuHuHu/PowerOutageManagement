#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPC UA 测试脚本
用于单独测试 OPC UA 连接和信号读取。

默认读取你当前截图中的 4 个点位：
- AB.PLC1.AB.Online.刮板机带电
- AB.PLC1.AB.Online.刮板机挂锁测试1
- AB.PLC1.AB.Online.刮板机挂锁测试2
- AB.PLC1.AB.Online.刮板机挂锁测试3

带电信号约定：
- 1 = 带电
- 0 = 不带电
"""

import argparse
import os
import sys
import time

try:
    from opcua import Client
except ImportError:
    print("未安装 opcua 库，请先执行：pip install opcua")
    sys.exit(1)


DEFAULT_ITEM_IDS = [
    "AB.PLC1.AB.Online.刮板机带电",
    "AB.PLC1.AB.Online.刮板机挂锁测试1",
    "AB.PLC1.AB.Online.刮板机挂锁测试2",
    "AB.PLC1.AB.Online.刮板机挂锁测试3",
]


def to_nodeid(item_or_nodeid: str, default_ns: int) -> str:
    """将 item id 转成 OPC UA node id。"""
    value = item_or_nodeid.strip()
    if value.startswith("ns="):
        return value
    # KepServer 常见映射：ns=2;s=<ItemId>
    return f"ns={default_ns};s={value}"


def value_to_binary(value):
    """尽量把值解释为 0/1。"""
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if value != 0 else 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "on", "yes", "y"}:
            return 1
        if normalized in {"0", "false", "off", "no", "n"}:
            return 0
        try:
            return 1 if float(normalized) != 0 else 0
        except Exception:
            return None
    return None


def read_once(client: Client, nodeids):
    print("\n" + "=" * 70)
    print("OPC UA 信号读取结果")
    print("=" * 70)

    for nodeid in nodeids:
        try:
            node = client.get_node(nodeid)
            data_value = node.get_data_value()
            raw_value = data_value.Value.Value
            ts = data_value.SourceTimestamp or data_value.ServerTimestamp
            quality = str(data_value.StatusCode)

            binary = value_to_binary(raw_value)
            power_hint = ""
            if "带电" in nodeid:
                if binary == 1:
                    power_hint = " => 带电"
                elif binary == 0:
                    power_hint = " => 不带电"
                else:
                    power_hint = " => 无法识别带电状态"

            print(f"\nNodeId   : {nodeid}")
            print(f"Value    : {raw_value}{power_hint}")
            print(f"Timestamp: {ts}")
            print(f"Quality  : {quality}")
        except Exception as e:
            print(f"\nNodeId   : {nodeid}")
            print(f"读取失败 : {e}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="OPC UA 信号读取测试")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="持续读取（默认单次读取）",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="持续读取时的刷新间隔（秒）",
    )
    args = parser.parse_args()

    endpoint = os.environ.get("OPCUA_ENDPOINT", "opc.tcp://127.0.0.1:49320")
    username = os.environ.get("OPCUA_USERNAME")
    password = os.environ.get("OPCUA_PASSWORD")
    default_ns = int(os.environ.get("OPCUA_NS", "2"))

    nodeids_env = os.environ.get("OPCUA_NODEIDS", "").strip()
    raw_nodes = [x.strip() for x in nodeids_env.split(",") if x.strip()] if nodeids_env else DEFAULT_ITEM_IDS
    nodeids = [to_nodeid(item, default_ns) for item in raw_nodes]

    print("OPC UA 测试工具")
    print("=" * 70)
    print(f"Endpoint : {endpoint}")
    print(f"Namespace: ns={default_ns}")
    print(f"用户名    : {username if username else '(未设置)'}")
    print("测试点位 :")
    for n in nodeids:
        print(f"  - {n}")
    print("=" * 70)

    client = Client(endpoint)
    if username:
        client.set_user(username)
        client.set_password(password or "")

    try:
        print("\n正在连接 OPC UA ...")
        client.connect()
        print("连接成功。")

        if args.watch:
            print(f"进入持续读取模式，每 {args.interval} 秒刷新一次，按 Ctrl+C 退出。")
            while True:
                read_once(client, nodeids)
                time.sleep(args.interval)
        else:
            read_once(client, nodeids)

    except KeyboardInterrupt:
        print("\n已停止。")
    except Exception as e:
        print(f"\n连接或读取失败: {e}")
        print("请检查 endpoint、端口、防火墙、用户名密码、NodeId 是否正确。")
        sys.exit(1)
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()

