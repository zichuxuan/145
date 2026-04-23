import logging
import json
import time
from datetime import datetime, timezone
from uuid import uuid4
import requests
from typing import List, Dict, Optional, Any
from utils.config import config_manager

MQTT_TOPIC_PREFIX = "iot/v1"
MQTT_TOPIC_STATUS_DEVICE = f"{MQTT_TOPIC_PREFIX}/status/device/{{device_code}}"
MQTT_TOPIC_STATUS_DEVICE_ALL = f"{MQTT_TOPIC_PREFIX}/status/device/+"
MQTT_TOPIC_COMMAND_DEVICE = f"{MQTT_TOPIC_PREFIX}/command/device/{{device_code}}"
MQTT_TOPIC_COMMAND_DEVICE_ALL = f"{MQTT_TOPIC_PREFIX}/command/device/+"
MQTT_TOPIC_COMMAND_RESULT_DEVICE = f"{MQTT_TOPIC_PREFIX}/command-result/device/{{device_code}}"
MQTT_TOPIC_COMMAND_RESULT_DEVICE_ALL = f"{MQTT_TOPIC_PREFIX}/command-result/device/+"
MQTT_TOPIC_CLIENT_STATE = f"{MQTT_TOPIC_PREFIX}/client/{{client_id}}/state"

LEGACY_TOPIC_STATUS_DEVICE = "telemetry/plc/+"
LEGACY_TOPIC_STATUS_PREFIX = "telemetry/plc/"
LEGACY_TOPIC_COMMAND_DEVICE = "command/plc/{device_id}"
LEGACY_TOPIC_COMMAND_RESULT_PREFIX = "event/plc/"

class DeviceService:
    """
    业务逻辑层：负责设备数据的 CRUD 操作，整合 API 和数据库
    """
    def __init__(self):
        self.logger = logging.getLogger("DeviceService")
        api_cfg = config_manager.get("api", {})
        self.api_base = api_cfg.get("base_url", "http://192.168.1.136:8000")
        self.api_token = api_cfg.get("token", "changeme")
        self.headers = {
            "API_TOKEN": self.api_token
        }
        # `device_instance` 表字段 + API 文档要求字段
        self.device_instance_fields = {
            "device_model_id",
            "device_code",
            "device_name",
            "device_category",
            "production_line",
            "location",
            "device_status",
            "device_data",
            "communication_protocol",
            "recent_maintenance_time",
            "commissioning_time",
            "device_image",
            "enable_or_not",
        }
        # `device_action` 表字段 + API 文档要求字段
        self.device_action_fields = {
            "device_instance_id",
            "action_name",
            "action_command_params",
        }
        self.workflow_fields = {
            "workflow_name",
            "workflow_type",
            "workflow_params",
            "workflow_detail",
            "conditions",
            "enable_or_not",
        }

    def _to_log_text(self, value: Any) -> str:
        if value is None:
            return "None"
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, (dict, list, tuple)):
            try:
                return json.dumps(value, ensure_ascii=False, default=str)
            except Exception:
                return str(value)
        return str(value)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        timeout: int = 5,
    ) -> requests.Response:
        method_upper = method.upper()
        url = f"{self.api_base}{path}"
        start = time.perf_counter()

        self.logger.info(
            "[HTTP_REQUEST] method=%s url=%s timeout=%ss headers=%s params=%s json=%s",
            method_upper,
            url,
            timeout,
            self._to_log_text(self.headers),
            self._to_log_text(params),
            self._to_log_text(json_body),
        )

        try:
            response = requests.request(
                method_upper,
                url,
                params=params,
                json=json_body,
                headers=self.headers,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            request_body = getattr(response.request, "body", None)
            self.logger.info(
                "[HTTP_RESPONSE] method=%s url=%s status=%s elapsed_ms=%.2f req_headers=%s req_body=%s resp_headers=%s resp_body=%s",
                method_upper,
                url,
                response.status_code,
                elapsed_ms,
                self._to_log_text(dict(response.request.headers)),
                self._to_log_text(request_body),
                self._to_log_text(dict(response.headers)),
                self._to_log_text(response.text),
            )
            response.raise_for_status()
            return response
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.exception(
                "[HTTP_ERROR] method=%s url=%s elapsed_ms=%.2f timeout=%ss headers=%s params=%s json=%s",
                method_upper,
                url,
                elapsed_ms,
                timeout,
                self._to_log_text(self.headers),
                self._to_log_text(params),
                self._to_log_text(json_body),
            )
            raise

    def _normalize_device_payload(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """仅保留 `device_instance` 表相关字段，并做常用别名映射。"""
        if not isinstance(device_data, dict):
            return {}

        payload: Dict[str, Any] = {}
        alias_to_field = {
            "category": "device_category",
            "status": "device_status",
            "image": "device_image",
            "enabled": "enable_or_not",
        }

        for key, value in device_data.items():
            normalized_key = alias_to_field.get(key, key)
            if normalized_key in self.device_instance_fields and value is not None:
                payload[normalized_key] = value

        # 后端 JSON 字段需要保证是对象
        if "device_data" in payload and not isinstance(payload["device_data"], dict):
            payload["device_data"] = {}

        return payload

    def _normalize_action_payload(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """兼容远程控制表格字段，统一映射到 `device_action` API。"""
        if not isinstance(action_data, dict):
            return {}

        payload: Dict[str, Any] = {}
        for key in self.device_action_fields:
            if key in action_data and action_data[key] is not None:
                payload[key] = action_data[key]

        # 兼容 UI 直接传扁平参数，自动包装成 action_command_params
        if "action_command_params" not in payload:
            command_params_keys = {"point_address", "function_code", "offset", "data", "description"}
            command_params = {k: action_data.get(k) for k in command_params_keys if action_data.get(k) is not None}
            if command_params:
                payload["action_command_params"] = command_params

        return payload

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _normalize_workflow_payload(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化 workflow 请求体，兼容界面层的常用别名。"""
        if not isinstance(workflow_data, dict):
            return {}

        alias_to_field = {
            "description": "conditions",
            "enabled": "enable_or_not",
        }
        payload: Dict[str, Any] = {}

        for key, value in workflow_data.items():
            normalized_key = alias_to_field.get(key, key)
            if normalized_key not in self.workflow_fields or value is None:
                continue
            payload[normalized_key] = value

        for json_key in ("workflow_params", "workflow_detail", "conditions"):
            if json_key in payload and not isinstance(payload[json_key], dict):
                payload[json_key] = {}

        if "enable_or_not" in payload:
            payload["enable_or_not"] = 1 if bool(payload["enable_or_not"]) else 0

        return payload

    def _parse_json_object(self, value: Any) -> Dict[str, Any]:
        """兼容接口把 JSON 字段返回成字符串的场景。"""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {}
        return {}

    def _normalize_workflow_item(self, workflow: Any) -> Dict[str, Any]:
        """统一整理单条工作流数据，保证界面层读取稳定。"""
        if not isinstance(workflow, dict):
            return {}

        result = dict(workflow)
        for json_key in ("workflow_params", "workflow_detail", "conditions"):
            result[json_key] = self._parse_json_object(result.get(json_key))
        return result

    def _extract_workflow_list(self, response_data: Any) -> List[Dict[str, Any]]:
        """兼容分页/包装响应，统一返回工作流列表。"""
        workflows = response_data
        if isinstance(workflows, dict):
            for key in ("items", "workflows", "data", "rows", "list"):
                value = workflows.get(key)
                if isinstance(value, list):
                    workflows = value
                    break
            else:
                workflows = []

        if isinstance(workflows, tuple):
            workflows = list(workflows)
        if not isinstance(workflows, list):
            return []

        return [self._normalize_workflow_item(item) for item in workflows if isinstance(item, dict)]

    def _extract_workflow_detail(self, response_data: Any) -> Dict[str, Any]:
        """兼容详情接口的包装结构。"""
        workflow = response_data
        if isinstance(workflow, dict):
            for key in ("data", "workflow", "item"):
                value = workflow.get(key)
                if isinstance(value, dict):
                    workflow = value
                    break
        return self._normalize_workflow_item(workflow)

    def _normalize_device_code(self, device_code: Any) -> str:
        return str(device_code or "").strip()

    def _extract_topic_value(self, topic: str, prefix: str) -> str:
        if isinstance(topic, str) and topic.startswith(prefix):
            return topic[len(prefix):]
        return ""

    def _parse_new_status_payload(self, topic: str, payload: Dict[str, Any]):
        status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
        telemetry = payload.get("telemetry") if isinstance(payload.get("telemetry"), dict) else {}
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        plc = payload.get("plc") if isinstance(payload.get("plc"), dict) else {}
        device_code = self._normalize_device_code(
            payload.get("device_code") or self._extract_topic_value(topic, f"{MQTT_TOPIC_PREFIX}/status/device/")
        )

        if not device_code:
            return None

        return {
            "id": device_code,
            "device_code": device_code,
            "temp": telemetry.get("temperature", 0.0),
            "press": telemetry.get("pressure", 0.0),
            "time": payload.get("ts", ""),
            "device_status": status.get("device_status"),
            "online": status.get("online"),
            "alarm": status.get("alarm"),
            "telemetry": telemetry,
            "source": source,
            "plc": plc,
            "raw": payload,
        }

    def _parse_legacy_telemetry(self, topic: str, payload: Dict[str, Any]):
        device_code = self._normalize_device_code(
            payload.get("device_code") or payload.get("device_id") or self._extract_topic_value(topic, LEGACY_TOPIC_STATUS_PREFIX)
        )
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}

        return {
            "id": device_code or "unknown",
            "device_code": device_code or "unknown",
            "temp": data.get("temperature", 0.0),
            "press": data.get("pressure", 0.0),
            "time": payload.get("timestamp", ""),
            "device_status": payload.get("device_status"),
            "online": payload.get("online"),
            "alarm": payload.get("alarm"),
            "telemetry": data,
            "source": payload.get("source", {}),
            "plc": payload.get("plc", {}),
            "raw": payload,
        }

    # --- 设备实例管理 (Device Instance) ---

    def get_devices(self, page=1, size=15) -> List[Dict]:
        """获取所有活跃设备列表"""
        params = {"page": page, "size": size}
        response = self._request("GET", "/api/v1/devices", params=params)
        return response.json()

    def get_device_detail(self, device_id: int) -> Optional[Dict]:
        """获取指定设备详情"""
        response = self._request("GET", f"/api/v1/devices/{device_id}")
        return response.json()

    def create_device(self, device_data: Dict) -> Optional[Dict]:
        """注册新设备实例"""
        payload = self._normalize_device_payload(device_data)
        response = self._request("POST", "/api/v1/devices", json_body=payload)
        return response.json()

    def update_device(self, device_id: int, device_data: Dict) -> Optional[Dict]:
        """更新设备实例信息"""
        payload = self._normalize_device_payload(device_data)
        response = self._request("PATCH", f"/api/v1/devices/{device_id}", json_body=payload)
        return response.json()

    def delete_device(self, device_id: int) -> bool:
        """逻辑删除设备实例"""
        self._request("DELETE", f"/api/v1/devices/{device_id}")
        return True

    # --- 设备行为事件管理 (Device Action) ---

    def get_device_actions(self, device_instance_id: int) -> List[Dict]:
        """按设备查询行为事件列表"""
        params = {"device_instance_id": device_instance_id}
        response = self._request("GET", "/api/v1/device-actions", params=params)
        return response.json()

    def get_device_action_detail(self, action_id: int) -> Optional[Dict]:
        """获取行为事件详情"""
        response = self._request("GET", f"/api/v1/device-actions/{action_id}")
        return response.json()

    def create_device_action(self, action_data: Dict) -> Optional[Dict]:
        """新增行为事件"""
        payload = self._normalize_action_payload(action_data)
        response = self._request("POST", "/api/v1/device-actions", json_body=payload)
        return response.json()

    def update_device_action(self, action_id: int, action_data: Dict) -> Optional[Dict]:
        """更新行为事件（局部更新）"""
        payload = self._normalize_action_payload(action_data)
        response = self._request("PATCH", f"/api/v1/device-actions/{action_id}", json_body=payload)
        return response.json()

    def delete_device_action(self, action_id: int) -> bool:
        """逻辑删除行为事件"""
        self._request("DELETE", f"/api/v1/device-actions/{action_id}")
        return True

    # --- 设备型号管理 (Device Model) ---

    def get_device_models(self) -> List[Dict]:
        """获取所有设备型号列表"""
        response = self._request("GET", "/api/v1/device-models")
        return response.json()

    # --- 工作流管理 (Workflow) ---

    def get_workflows(self, page=1, size=10) -> List[Dict]:
        """获取所有活跃工作流列表。"""
        params = {"page": page, "size": size}
        response = self._request("GET", "/api/v1/workflows", params=params)
        return self._extract_workflow_list(response.json())

    def get_workflow_detail(self, workflow_id: int) -> Optional[Dict]:
        """获取工作流详情。"""
        response = self._request("GET", f"/api/v1/workflows/{workflow_id}")
        return self._extract_workflow_detail(response.json())

    def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict]:
        """创建工作流。"""
        payload = self._normalize_workflow_payload(workflow_data)
        response = self._request("POST", "/api/v1/workflows", json_body=payload)
        return self._extract_workflow_detail(response.json())

    def update_workflow(self, workflow_id: int, workflow_data: Dict[str, Any]) -> Optional[Dict]:
        """更新工作流。"""
        payload = self._normalize_workflow_payload(workflow_data)
        response = self._request("PATCH", f"/api/v1/workflows/{workflow_id}", json_body=payload)
        return self._extract_workflow_detail(response.json())

    def delete_workflow(self, workflow_id: int) -> bool:
        """逻辑删除工作流。"""
        self._request("DELETE", f"/api/v1/workflows/{workflow_id}")
        return True

    # --- 遥测与控制 (MQTT 相关) ---

    def build_status_topic(self, device_code: str) -> str:
        device_code = self._normalize_device_code(device_code)
        return MQTT_TOPIC_STATUS_DEVICE.format(device_code=device_code)

    def build_status_subscription_topic(self, device_code: Optional[str] = None) -> str:
        normalized = self._normalize_device_code(device_code)
        if normalized:
            return self.build_status_topic(normalized)
        return MQTT_TOPIC_STATUS_DEVICE_ALL

    def build_command_topic(self, device_code: str) -> str:
        device_code = self._normalize_device_code(device_code)
        return MQTT_TOPIC_COMMAND_DEVICE.format(device_code=device_code)

    def build_command_subscription_topic(self, device_code: Optional[str] = None) -> str:
        normalized = self._normalize_device_code(device_code)
        if normalized:
            return self.build_command_topic(normalized)
        return MQTT_TOPIC_COMMAND_DEVICE_ALL

    def build_command_result_topic(self, device_code: str) -> str:
        device_code = self._normalize_device_code(device_code)
        return MQTT_TOPIC_COMMAND_RESULT_DEVICE.format(device_code=device_code)

    def build_command_result_subscription_topic(self, device_code: Optional[str] = None) -> str:
        normalized = self._normalize_device_code(device_code)
        if normalized:
            return self.build_command_result_topic(normalized)
        return MQTT_TOPIC_COMMAND_RESULT_DEVICE_ALL

    def build_client_state_topic(self, client_id: str) -> str:
        return MQTT_TOPIC_CLIENT_STATE.format(client_id=str(client_id or "").strip())

    def build_command_payload(
        self,
        device_code: str,
        action_name: str,
        command_type: str,
        params: Optional[Dict[str, Any]] = None,
        source_client_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_device_code = self._normalize_device_code(device_code)
        payload = {
            "command_id": command_id or f"cmd-{uuid4().hex}",
            "device_code": normalized_device_code,
            "action_name": action_name or command_type,
            "command_type": command_type,
            "params": params or {},
            "ts": self._utc_now_iso(),
            "source": {
                "client_id": source_client_id or "hmi-terminal",
            },
        }
        if batch_id:
            payload["batch_id"] = batch_id
        return payload

    def parse_status_message(self, topic: str, payload: Dict[str, Any]):
        """解析新旧状态主题，统一输出给 ViewModel。"""
        try:
            if not isinstance(payload, dict):
                return None
            if isinstance(topic, str) and topic.startswith(f"{MQTT_TOPIC_PREFIX}/status/device/"):
                return self._parse_new_status_payload(topic, payload)
            if isinstance(topic, str) and topic.startswith(LEGACY_TOPIC_STATUS_PREFIX):
                return self._parse_legacy_telemetry(topic, payload)
            if "status" in payload or "telemetry" in payload:
                return self._parse_new_status_payload(topic or "", payload)
            return self._parse_legacy_telemetry(topic or "", payload)
        except Exception as e:
            self.logger.error(f"解析设备状态失败: {e}")
            return None

    def parse_telemetry(self, payload: dict, topic: str = ""):
        """兼容旧调用入口，内部转为统一状态解析。"""
        return self.parse_status_message(topic, payload)

    def parse_command_result_message(self, topic: str, payload: Dict[str, Any]):
        """解析命令回执主题，统一输出给 ViewModel。"""
        try:
            if not isinstance(payload, dict):
                return None
            if not isinstance(topic, str):
                topic = ""

            device_code = self._normalize_device_code(
                payload.get("device_code") or self._extract_topic_value(topic, f"{MQTT_TOPIC_PREFIX}/command-result/device/")
            )
            if not device_code and topic.startswith(LEGACY_TOPIC_COMMAND_RESULT_PREFIX):
                device_code = self._extract_topic_value(topic, LEGACY_TOPIC_COMMAND_RESULT_PREFIX)

            return {
                "command_id": payload.get("command_id"),
                "batch_id": payload.get("batch_id"),
                "device_code": device_code,
                "result_code": payload.get("result_code") or payload.get("status"),
                "result_message": payload.get("result_message") or payload.get("result"),
                "stage": payload.get("stage") or payload.get("status"),
                "time": payload.get("ts") or payload.get("timestamp", ""),
                "source": payload.get("source", {}),
                "raw": payload,
            }
        except Exception as e:
            self.logger.error(f"解析命令回执失败: {e}")
            return None

    def format_command(
        self,
        device_id: str,
        cmd_type: str,
        params: Optional[Dict[str, Any]] = None,
        action_name: Optional[str] = None,
        source_client_id: Optional[str] = None,
        batch_id: Optional[str] = None,
    ):
        """按新规范构造下发给设备的指令 topic 和 payload。"""
        topic = self.build_command_topic(device_id)
        command = self.build_command_payload(
            device_code=device_id,
            action_name=action_name or cmd_type,
            command_type=cmd_type,
            params=params,
            source_client_id=source_client_id,
            batch_id=batch_id,
        )
        return topic, command
