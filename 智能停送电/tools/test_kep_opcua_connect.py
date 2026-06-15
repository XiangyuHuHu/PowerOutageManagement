#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import time
from pathlib import Path

from opcua import Client, ua


def build_nodeids(device_id: str, device_name: str = ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.kep_opcua_address import build_nodeid, build_tag_name

    device_id = (device_id or "").strip()
    if not device_id:
        return []
    device_name = (device_name or "").strip()
    out = []
    for label, st in (("带电", "power_feedback"), ("挂牌", "tag_count")):
        tag = build_tag_name(device_id, device_name, st)
        if tag:
            out.append((label, build_nodeid(tag)))
    return out


def load_device_ids(device_id_arg: str, devices_file: str):
    result = []
    if device_id_arg:
        result.extend([item.strip() for item in device_id_arg.split(",") if item.strip()])
    if devices_file:
        for line in Path(devices_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            result.append(line)

    deduped = []
    seen = set()
    for item in result:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def read_node(client: Client, nodeid: str):
    node = client.get_node(nodeid)
    data_value = node.get_data_value()
    return {
        "value": data_value.Value.Value,
        "type": type(data_value.Value.Value).__name__,
        "status": str(data_value.StatusCode),
        "timestamp": str(data_value.SourceTimestamp or data_value.ServerTimestamp),
    }


def write_tag_value(client: Client, device_id: str, value: int, restore: bool = True):
    nodeid = f"ns=2;s={NODE_PREFIX}.{device_id}.挂牌"
    node = client.get_node(nodeid)
    before = read_node(client, nodeid)
    node.set_value(ua.DataValue(ua.Variant(int(value), ua.VariantType.Int16)))
    after = read_node(client, nodeid)
    restored = None
    if restore:
        node.set_value(ua.DataValue(ua.Variant(int(before["value"]), ua.VariantType.Int16)))
        restored = read_node(client, nodeid)
    return {
        "nodeid": nodeid,
        "before": before,
        "after": after,
        "restored": restored,
    }


def write_tag_value_with_watch(client: Client, device_id: str, value: int, watch_seconds: float = 5.0, interval: float = 0.5, restore: bool = True):
    nodeid = f"ns=2;s={NODE_PREFIX}.{device_id}.挂牌"
    node = client.get_node(nodeid)
    before = read_node(client, nodeid)
    node.set_value(ua.DataValue(ua.Variant(int(value), ua.VariantType.Int16)))
    samples = []
    end_at = time.time() + watch_seconds
    while time.time() < end_at:
        samples.append(read_node(client, nodeid))
        time.sleep(interval)
    restored = None
    if restore:
        node.set_value(ua.DataValue(ua.Variant(int(before["value"]), ua.VariantType.Int16)))
        restored = read_node(client, nodeid)
    return {
        "nodeid": nodeid,
        "before": before,
        "samples": samples,
        "restored": restored,
    }


def main():
    parser = argparse.ArgumentParser(description="测试 KEPServer OPC UA 连通性，并批量读取带电/挂牌点位")
    parser.add_argument("--endpoint", default="opc.tcp://192.168.10.50:49320", help="OPC UA endpoint")
    parser.add_argument("--username", default="kep", help="用户名")
    parser.add_argument("--password", default="111111", help="密码")
    parser.add_argument("--timeout", type=float, default=4.0, help="超时时间（秒）")
    parser.add_argument("--device-id", default="", help="单个或多个设备号，多个用逗号分隔，例如 111AL,404,301")
    parser.add_argument("--devices-file", default="", help="设备号文本文件路径，一行一个设备号")
    parser.add_argument("--write-tag-device", default="", help="测试写挂牌值的设备号，例如 111AL")
    parser.add_argument("--write-tag-value", type=int, default=None, help="测试写入的挂牌数量 Int16 值")
    parser.add_argument("--no-restore", action="store_true", help="写测试后不恢复原值")
    parser.add_argument("--watch-seconds", type=float, default=0, help="写入后连续观察秒数，例如 5")
    args = parser.parse_args()

    print("开始测试 OPC UA 连通性")
    print(f"Endpoint : {args.endpoint}")
    print(f"Username : {args.username}")
    print(f"Timeout  : {args.timeout}s")

    client = Client(args.endpoint, timeout=args.timeout)
    if args.username:
        client.set_user(args.username)
        client.set_password(args.password or "")

    try:
        client.connect()
        print("结果     : 连接成功")
        print("命名空间 :")
        for ns in client.get_namespace_array():
            print(f"  - {ns}")

        if args.write_tag_device and args.write_tag_value is not None:
            print("")
            print(f"开始测试挂牌写入：设备 {args.write_tag_device} -> {args.write_tag_value}")
            print("=" * 72)
            if args.watch_seconds > 0:
                result = write_tag_value_with_watch(
                    client,
                    args.write_tag_device.strip(),
                    args.write_tag_value,
                    watch_seconds=args.watch_seconds,
                    restore=not args.no_restore,
                )
                print(f"NodeId      : {result['nodeid']}")
                print(f"写入前值    : {result['before']['value']} ({result['before']['type']}, {result['before']['status']})")
                for idx, sample in enumerate(result["samples"], start=1):
                    print(f"读回[{idx:02d}]   : {sample['value']} ({sample['type']}, {sample['status']}) @ {sample['timestamp']}")
                if result["restored"] is not None:
                    print(f"恢复后值    : {result['restored']['value']} ({result['restored']['type']}, {result['restored']['status']})")
            else:
                result = write_tag_value(
                    client,
                    args.write_tag_device.strip(),
                    args.write_tag_value,
                    restore=not args.no_restore,
                )
                print(f"NodeId      : {result['nodeid']}")
                print(f"写入前值    : {result['before']['value']} ({result['before']['type']}, {result['before']['status']})")
                print(f"写入后值    : {result['after']['value']} ({result['after']['type']}, {result['after']['status']})")
                if result["restored"] is not None:
                    print(f"恢复后值    : {result['restored']['value']} ({result['restored']['type']}, {result['restored']['status']})")
            return 0

        device_ids = load_device_ids(args.device_id, args.devices_file)
        if not device_ids:
            print("未提供设备号列表，本次只测试连接。")
            return 0

        print("")
        print(f"开始批量读取，共 {len(device_ids)} 台设备")
        print("=" * 72)

        ok_count = 0
        fail_count = 0

        for device_id in device_ids:
            print(f"[设备] {device_id}")
            for label, nodeid in build_nodeids(device_id):
                try:
                    data = read_node(client, nodeid)
                    print(f"  [{label}] OK")
                    print(f"    NodeId : {nodeid}")
                    print(f"    Value  : {data['value']}")
                    print(f"    Type   : {data['type']}")
                    print(f"    Status : {data['status']}")
                    print(f"    Time   : {data['timestamp']}")
                    ok_count += 1
                except Exception as exc:
                    print(f"  [{label}] FAIL")
                    print(f"    NodeId : {nodeid}")
                    print(f"    Error  : {type(exc).__name__}: {exc}")
                    fail_count += 1
            print("-" * 72)

        print(f"读取完成：成功 {ok_count} 条，失败 {fail_count} 条")
        return 0 if fail_count == 0 else 2
    except Exception as exc:
        print("结果     : 连接失败")
        print(f"异常类型 : {type(exc).__name__}")
        print(f"异常信息 : {exc}")
        return 1
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
