"""
PumpGuard 飞书 Bot 告警推送

功能：
  1. 监听 Kafka Topic `alert.triggered`
  2. 构建告警卡片消息
  3. 通过飞书 Webhook Bot 推送至运维群

与架构说明书 3.4.2 / 开发步骤 Phase 6 完全对齐。
"""

import json
import os
import requests
from kafka import KafkaConsumer, KafkaProducer


class FeishuAlertBot:
    """飞书告警 Bot"""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.environ.get("FEISHU_BOT_WEBHOOK", "")
        self.kafka_broker = os.environ.get("KAFKA_BROKER", "localhost:9092")

    def build_alert_card(self, alert_data: dict) -> dict:
        """
        构建飞书消息卡片

        卡片内容：
          - 设备名称 + 位置
          - 健康指数（颜色编码）
          - 预测故障类型 + 置信度
          - 建议处置方案
          - 按钮：[一键生成工单] [查看详情]
        """
        hi = alert_data.get("health_index", 0)
        hi_color = "green" if hi >= 70 else ("orange" if hi >= 50 else "red")

        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "PumpGuard 设备健康告警"},
                    "template": "red" if hi < 50 else "orange",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**设备名称**：{alert_data.get('device_id', 'Unknown')}\n"
                                       f"**健康指数**：<font color='{hi_color}'>{hi}</font> / 100\n"
                                       f"**预测故障**：{alert_data.get('fault_type', '待分析')} "
                                       f"（置信度 {alert_data.get('probability', 0)}%）\n"
                                       f"**建议**：{alert_data.get('suggested_action', '请查看详情')}"
                        }
                    },
                    {"tag": "hr"},
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "一键生成工单"},
                                "type": "primary",
                                "value": json.dumps({"action": "create_workorder", "device_id": alert_data.get("device_id")})
                            },
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "查看详情"},
                                "type": "default",
                                "url": f"http://localhost:3000/pump/{alert_data.get('device_id')}"
                            }
                        ]
                    }
                ]
            }
        }
        return card

    def send_alert(self, alert_data: dict) -> bool:
        """发送告警到飞书"""
        if not self.webhook_url:
            print("[FeishuBot] Webhook URL 未配置，跳过推送")
            print(f"[FeishuBot] 告警内容: {json.dumps(alert_data, ensure_ascii=False, indent=2)}")
            return False

        card = self.build_alert_card(alert_data)
        try:
            resp = requests.post(self.webhook_url, json=card, timeout=10)
            if resp.status_code == 200:
                print(f"[FeishuBot] 告警已推送: {alert_data.get('device_id')}")
                return True
            else:
                print(f"[FeishuBot] 推送失败: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            print(f"[FeishuBot] 推送异常: {e}")
            return False

    def run(self):
        """主循环：监听 Kafka → 推送飞书"""
        try:
            consumer = KafkaConsumer(
                "alert.triggered",
                bootstrap_servers=self.kafka_broker,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="latest",
                group_id="feishu-bot",
            )
            print(f"[FeishuBot] 已启动，监听 Kafka topic: alert.triggered")

            for msg in consumer:
                alert_data = msg.value
                print(f"[FeishuBot] 收到告警: {alert_data.get('device_id')}")
                self.send_alert(alert_data)

        except Exception as e:
            print(f"[FeishuBot] Kafka 连接失败: {e}")
            print("[FeishuBot] 进入 Demo 模式 — 模拟一条告警")

            # Demo 模式：模拟推送一条告警
            demo_alert = {
                "device_id": "PUMP-0007",
                "health_index": 45,
                "fault_type": "bearing_inner_race_wear",
                "probability": 89,
                "suggested_action": "更换轴承，备件编号 SKF-6305，预计工时 4 小时",
            }
            self.send_alert(demo_alert)


if __name__ == "__main__":
    bot = FeishuAlertBot()
    bot.run()
