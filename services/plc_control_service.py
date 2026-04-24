import logging

from infrastructure.modbus_tcp_client import ModbusTcpClient
from utils.config import config_manager


class PlcControlService:
    """按流程读取配置并执行 PLC 启停控制。"""

    def __init__(self, modbus_client=None):
        self.logger = logging.getLogger("PlcControlService")
        self.modbus_client = modbus_client or ModbusTcpClient()

    def get_flow_config(self, flow_name):
        plc_cfg = config_manager.get("plc_control", {}) or {}
        flows = plc_cfg.get("flows", {}) if isinstance(plc_cfg, dict) else {}
        flow_cfg = flows.get(flow_name, {})
        if isinstance(flow_cfg, dict):
            return flow_cfg
        return {}

    def is_flow_configured(self, flow_name):
        plc_cfg = config_manager.get("plc_control", {}) or {}
        if not isinstance(plc_cfg, dict) or not plc_cfg.get("enabled", True):
            return False

        flow_cfg = self.get_flow_config(flow_name)
        return bool(flow_cfg.get("enabled"))

    def start_flow(self, flow_name):
        return self._execute_flow_command(flow_name, "start")

    def stop_flow(self, flow_name):
        return self._execute_flow_command(flow_name, "stop")

    def get_flow_commands(self, flow_name, action):
        flow_cfg = self.get_flow_config(flow_name)
        command_key = "start_commands" if action == "start" else "stop_commands"
        commands = flow_cfg.get(command_key)
        if not isinstance(commands, list) or not commands:
            raise ValueError(f"流程 PLC 配置缺少 {command_key}")
        return commands

    def _execute_flow_command(self, flow_name, action):
        if not isinstance(flow_name, str) or not flow_name.strip():
            raise ValueError("流程名称不能为空")

        plc_cfg = config_manager.get("plc_control", {}) or {}
        if not isinstance(plc_cfg, dict) or not plc_cfg.get("enabled", True):
            raise ValueError("PLC 控制未启用")

        flow_cfg = self.get_flow_config(flow_name)
        if not flow_cfg or not flow_cfg.get("enabled"):
            raise ValueError("当前流程未配置 PLC 参数")

        host = str(flow_cfg.get("host", "")).strip()
        if not host:
            raise ValueError("流程 PLC 配置缺少 host")

        port = int(flow_cfg.get("port") or plc_cfg.get("default_port") or 502)
        unit_id = flow_cfg.get("unit_id")
        if unit_id is None:
            raise ValueError("流程 PLC 配置缺少 unit_id")

        connect_timeout_ms = int(plc_cfg.get("connect_timeout_ms", 1500))
        response_timeout_ms = int(plc_cfg.get("response_timeout_ms", 1500))
        start_commands = self.get_flow_commands(flow_name, "start")
        stop_commands = self.get_flow_commands(flow_name, "stop")
        if len(start_commands) != len(stop_commands):
            raise ValueError("流程 PLC 配置错误: start_commands 与 stop_commands 数量不一致")

        if action == "start":
            return self._execute_start_sequence(
                flow_name,
                host,
                port,
                unit_id,
                start_commands,
                stop_commands,
                connect_timeout_ms,
                response_timeout_ms,
            )
        return self._execute_stop_sequence(
            flow_name,
            host,
            port,
            unit_id,
            stop_commands,
            connect_timeout_ms,
            response_timeout_ms,
        )

    def _execute_start_sequence(
        self,
        flow_name,
        host,
        port,
        unit_id,
        start_commands,
        stop_commands,
        connect_timeout_ms,
        response_timeout_ms,
    ):
        details = []
        successful_indexes = []
        failed_messages = []

        for index, command_cfg in enumerate(start_commands):
            try:
                normalized_command = self._normalize_command(command_cfg, "start_commands", index)
                self._write_command(
                    flow_name,
                    "start",
                    host,
                    port,
                    unit_id,
                    index,
                    normalized_command,
                    connect_timeout_ms,
                    response_timeout_ms,
                )
                successful_indexes.append(index)
                details.append({
                    "index": index,
                    "label": normalized_command["label"],
                    "success": True,
                    "rolled_back": False,
                })
            except Exception as exc:
                failed_messages.append(f"第{index + 1}台设备[{self._safe_command_label(command_cfg, index)}]下发失败: {exc}")
                details.append({
                    "index": index,
                    "label": self._safe_command_label(command_cfg, index),
                    "success": False,
                    "rolled_back": False,
                    "error": str(exc),
                })

                rollback_errors = self._rollback_started_commands(
                    flow_name,
                    host,
                    port,
                    unit_id,
                    successful_indexes,
                    stop_commands,
                    details,
                    connect_timeout_ms,
                    response_timeout_ms,
                )
                rollback_message = "；已对前序成功设备执行回滚"
                if rollback_errors:
                    rollback_message = "；回滚存在失败: " + "；".join(rollback_errors)

                raise ValueError("流程启动失败：" + "；".join(failed_messages) + rollback_message)

        return {
            "success": True,
            "flow_name": flow_name,
            "action": "start",
            "message": "PLC 启动指令发送成功",
            "executed_count": len(details),
            "failed_count": 0,
            "details": details,
        }

    def _execute_stop_sequence(
        self,
        flow_name,
        host,
        port,
        unit_id,
        stop_commands,
        connect_timeout_ms,
        response_timeout_ms,
    ):
        details = []
        failed_messages = []

        for index in range(len(stop_commands) - 1, -1, -1):
            command_cfg = stop_commands[index]
            try:
                normalized_command = self._normalize_command(command_cfg, "stop_commands", index)
                self._write_command(
                    flow_name,
                    "stop",
                    host,
                    port,
                    unit_id,
                    index,
                    normalized_command,
                    connect_timeout_ms,
                    response_timeout_ms,
                )
                details.append({
                    "index": index,
                    "label": normalized_command["label"],
                    "success": True,
                })
            except Exception as exc:
                failed_messages.append(f"[{self._safe_command_label(command_cfg, index)}] {exc}")
                details.append({
                    "index": index,
                    "label": self._safe_command_label(command_cfg, index),
                    "success": False,
                    "error": str(exc),
                })

        failed_count = len(failed_messages)
        if failed_count:
            raise ValueError(
                f"流程停止失败：共{len(stop_commands)}条命令，失败{failed_count}条："
                + "；".join(failed_messages)
            )

        return {
            "success": True,
            "flow_name": flow_name,
            "action": "stop",
            "message": "PLC 停止指令发送成功",
            "executed_count": len(details),
            "failed_count": 0,
            "details": details,
        }

    def _rollback_started_commands(
        self,
        flow_name,
        host,
        port,
        unit_id,
        successful_indexes,
        stop_commands,
        details,
        connect_timeout_ms,
        response_timeout_ms,
    ):
        rollback_errors = []
        for index in reversed(successful_indexes):
            command_cfg = stop_commands[index]
            try:
                normalized_command = self._normalize_command(command_cfg, "stop_commands", index)
                self._write_command(
                    flow_name,
                    "rollback",
                    host,
                    port,
                    unit_id,
                    index,
                    normalized_command,
                    connect_timeout_ms,
                    response_timeout_ms,
                )
                self._mark_detail_rolled_back(details, index)
            except Exception as exc:
                message = f"第{index + 1}台设备[{self._safe_command_label(command_cfg, index)}]回滚失败: {exc}"
                rollback_errors.append(message)
        return rollback_errors

    def _mark_detail_rolled_back(self, details, command_index):
        for detail in details:
            if detail.get("index") == command_index and detail.get("success") is True:
                detail["rolled_back"] = True
                return

    def _normalize_command(self, command_cfg, command_key, index):
        if not isinstance(command_cfg, dict):
            raise ValueError(f"流程 PLC 配置缺少 {command_key}[{index}]")

        function_code = int(command_cfg.get("function_code", 0))
        if function_code != 5:
            raise ValueError("当前仅支持 Modbus 功能码 05")

        offset = command_cfg.get("offset")
        if offset is None:
            raise ValueError(f"流程 PLC 配置缺少 {command_key}[{index}].offset")

        if "value" not in command_cfg:
            raise ValueError(f"流程 PLC 配置缺少 {command_key}[{index}].value")

        return {
            "function_code": function_code,
            "offset": int(offset),
            "value": bool(command_cfg.get("value")),
            "label": self._safe_command_label(command_cfg, index),
        }

    def _write_command(
        self,
        flow_name,
        action,
        host,
        port,
        unit_id,
        command_index,
        command,
        connect_timeout_ms,
        response_timeout_ms,
    ):
        self.logger.info(
            "[PLC_CONTROL] flow=%s action=%s command_index=%s label=%s host=%s port=%s unit_id=%s offset=%s value=%s",
            flow_name,
            action,
            command_index,
            command["label"],
            host,
            port,
            unit_id,
            command["offset"],
            command["value"],
        )
        self.modbus_client.write_single_coil(
            host,
            port,
            unit_id,
            command["offset"],
            command["value"],
            connect_timeout_ms=connect_timeout_ms,
            response_timeout_ms=response_timeout_ms,
        )

    def _safe_command_label(self, command_cfg, index):
        if isinstance(command_cfg, dict):
            label = str(command_cfg.get("label", "")).strip()
            if label:
                return label
        return f"命令{index + 1}"
