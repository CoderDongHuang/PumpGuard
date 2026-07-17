"""
飞书 API 客户端

支持：
  - Bot 消息推送
  - 多维表格记录写入（运维台账）
  - 审批流发起（工单审批）

需要配置（由用户提供）：
  FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_BOT_WEBHOOK
  FEISHU_BITABLE_APP_TOKEN / FEISHU_BITABLE_TABLE_ID
"""

import os
import json
import time
import requests


class FeishuClient:
    """飞书 API 客户端"""

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self):
        self.app_id = os.environ.get("FEISHU_APP_ID", "")
        self.app_secret = os.environ.get("FEISHU_APP_SECRET", "")
        self.bot_webhook = os.environ.get("FEISHU_BOT_WEBHOOK", "")
        self.bitable_app_token = os.environ.get("FEISHU_BITABLE_APP_TOKEN", "")
        self.bitable_table_id = os.environ.get("FEISHU_BITABLE_TABLE_ID", "")
        self._tenant_token: str | None = None
        self._token_expire: float = 0

    # ── 认证 ──────────────────────────────────────────────────────

    def _get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        if self._tenant_token and time.time() < self._token_expire:
            return self._tenant_token

        resp = requests.post(f"{self.BASE_URL}/auth/v3/tenant_access_token/internal", json={
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        })
        data = resp.json()
        self._tenant_token = data.get("tenant_access_token", "")
        self._token_expire = time.time() + data.get("expire", 3600) - 300
        return self._tenant_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_tenant_token()}",
            "Content-Type": "application/json",
        }

    # ── Bot 消息推送 ──────────────────────────────────────────────

    def send_bot_message(self, card: dict) -> bool:
        """通过 Webhook 发送 Bot 消息卡片"""
        if not self.bot_webhook:
            print("[Feishu] Webhook 未配置")
            return False
        resp = requests.post(self.bot_webhook, json=card, timeout=10)
        return resp.status_code == 200

    def send_text_message(self, chat_id: str, text: str) -> bool:
        """发送文本消息到指定群聊"""
        resp = requests.post(
            f"{self.BASE_URL}/im/v1/messages?receive_id_type=chat_id",
            headers=self._headers(),
            json={
                "receive_id": chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )
        return resp.status_code == 200

    # ── 多维表格 ──────────────────────────────────────────────────

    def write_maintenance_record(self, device_id: str, fault_type: str,
                                  health_index: float, action: str, engineer: str = "") -> bool:
        """
        写入运维台账到多维表格

        对应飞书多维表格智能体的"运维台账自动记录"功能
        """
        if not self.bitable_app_token or not self.bitable_table_id:
            print("[Feishu] 多维表格未配置，跳过写入")
            return False

        url = (f"{self.BASE_URL}/bitable/v1/apps/{self.bitable_app_token}"
               f"/tables/{self.bitable_table_id}/records")
        resp = requests.post(url, headers=self._headers(), json={
            "fields": {
                "设备编号": device_id,
                "故障类型": fault_type,
                "健康指数": health_index,
                "处置方案": action,
                "维修工程师": engineer,
                "记录时间": int(time.time() * 1000),
            }
        })
        if resp.status_code == 200:
            print(f"[Feishu] 多维表格已写入: {device_id}")
            return True
        else:
            print(f"[Feishu] 多维表格写入失败: {resp.status_code} {resp.text}")
            return False

    def query_health(self, device_id: str) -> dict | None:
        """查询设备健康状态（从多维表格读取最新记录）"""
        if not self.bitable_app_token or not self.bitable_table_id:
            return None
        url = (f"{self.BASE_URL}/bitable/v1/apps/{self.bitable_app_token}"
               f"/tables/{self.bitable_table_id}/records"
               f"?filter=CurrentValue.[设备编号]=\"{device_id}\"&page_size=1")
        resp = requests.get(url, headers=self._headers())
        if resp.status_code == 200:
            items = resp.json().get("data", {}).get("items", [])
            return items[0] if items else None
        return None

    # ── 审批流 ────────────────────────────────────────────────────

    def create_approval(self, device_id: str, fault_type: str,
                         severity: str, suggested_action: str) -> str | None:
        """
        发起工单审批

        飞书审批流 → 工单审批流转
        """
        if not self.app_id:
            print("[Feishu] 审批流未配置")
            return None

        # 审批定义 code（需要在飞书后台创建审批模板后获取）
        approval_code = os.environ.get("FEISHU_APPROVAL_CODE", "pumpguard-workorder")

        resp = requests.post(
            f"{self.BASE_URL}/approval/v4/instances",
            headers=self._headers(),
            json={
                "approval_code": approval_code,
                "user_id": "",  # 发起人 user_id（飞书用户 ID）
                "form": json.dumps([
                    {"id": "device_id", "type": "input", "value": device_id},
                    {"id": "fault_type", "type": "input", "value": fault_type},
                    {"id": "severity", "type": "input", "value": severity},
                    {"id": "action", "type": "textarea", "value": suggested_action},
                ]),
            },
        )
        if resp.status_code == 200:
            instance_id = resp.json().get("data", {}).get("instance_code", "")
            print(f"[Feishu] 审批已发起: {instance_id}")
            return instance_id
        else:
            print(f"[Feishu] 审批发起失败: {resp.status_code} {resp.text}")
            return None
