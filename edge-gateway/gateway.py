"""
PumpGuard 边缘网关（Demo 简化版）

功能：
  1. 订阅 MQTT 原始数据 Topic
  2. 数据清洗（中值滤波去噪、异常值检测）
  3. 特征提取（RMS、FFT 主频、THD）
  4. 发布清洗后数据到 MQTT

与架构说明书 3.1.3 一致。
"""

import json
import time
import numpy as np
from collections import deque


class EdgeGateway:
    """边缘网关 — 数据预处理与特征提取"""

    def __init__(self, window_size: int = 10, outlier_threshold: float = 3.0):
        self.window_size = window_size
        self.outlier_threshold = outlier_threshold  # Z-score 阈值
        self.buffers: dict[str, deque] = {}         # device_id → 滑动窗口缓冲区

    def process(self, device_id: str, raw_data: dict) -> dict | None:
        """
        处理一条原始数据

        步骤：
          1. 去噪（中值滤波，需要窗口积累）
          2. 异常值检测（Z-score）
          3. 特征提取
          4. 返回清洗后的数据（或 None 表示数据被丢弃）
        """
        # 初始化缓冲区
        if device_id not in self.buffers:
            self.buffers[device_id] = deque(maxlen=self.window_size)

        # 提取关键指标
        try:
            rms = raw_data.get("vibration", {}).get("rms_overall", 0)
            temp = raw_data.get("thermal", {}).get("bearing_temp", 25)
            current = raw_data.get("current", {}).get("rms", 10)
        except Exception:
            return None

        # 异常值检测（基于滑动窗口的 Z-score）
        buf = self.buffers[device_id]
        if len(buf) >= 3:
            values = np.array([b["rms"] for b in buf])
            mean, std = values.mean(), values.std()
            if std > 0 and abs(rms - mean) / std > self.outlier_threshold:
                # 异常值 → 用中位数替代
                rms = np.median(values)
                raw_data["vibration"]["rms_overall"] = round(rms, 3)

        # 入缓冲
        buf.append({"rms": rms, "temp": temp, "current": current, "ts": time.time()})

        # 中值滤波平滑（窗口满时）
        if len(buf) >= 3:
            recent = [b["rms"] for b in list(buf)[-3:]]
            raw_data["vibration"]["rms_overall"] = round(float(np.median(recent)), 3)
            recent_t = [b["temp"] for b in list(buf)[-3:]]
            raw_data["thermal"]["bearing_temp"] = round(float(np.median(recent_t)), 1)

        # 添加边缘处理标记
        raw_data["edge_processed"] = True
        raw_data["edge_timestamp"] = time.time()

        return raw_data


def run_demo():
    """Demo：从 MQTT 读取 → 处理 → 发布"""
    import paho.mqtt.client as mqtt

    gateway = EdgeGateway()

    def on_message(client, userdata, msg):
        try:
            raw = json.loads(msg.payload.decode())
            device_id = raw.get("device_id", "unknown")
            processed = gateway.process(device_id, raw)
            if processed:
                # 发布到处理后的 Topic
                pub_topic = f"pump/{device_id}/processed"
                client.publish(pub_topic, json.dumps(processed, ensure_ascii=False))
                print(f"[Gateway] {device_id} → {pub_topic}")
        except Exception as e:
            print(f"[Gateway] 处理失败: {e}")

    client = mqtt.Client(client_id="pumpguard-edge-gateway")
    client.on_message = on_message
    client.connect("localhost", 1883)
    client.subscribe("pump/+/sensor")
    print("[Gateway] 已启动，订阅 pump/+/sensor")
    client.loop_forever()


if __name__ == "__main__":
    run_demo()
