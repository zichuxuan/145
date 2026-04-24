import copy
import json
import os
from pathlib import Path

class ConfigManager:
    _instance = None
    _config_path = str(Path(__file__).resolve().parents[1] / "config.json")
    _default_config = {
        "admin_password": "123456",
        "api": {
            "base_url": "http://192.168.1.136:8000",
            "token": "changeme"
        },
        "mqtt": {
            "host": "192.168.1.136",
            "port": 1883,
            "username": "hmi",
            "password": "hmipassword",
            "client_id": "hmi_terminal_01",
            "keepalive": 60
        },
        "plc_control": {
            "enabled": True,
            "default_port": 502,
            "connect_timeout_ms": 1500,
            "response_timeout_ms": 1500,
            "flows": {
                "1#平台智能上料": {
                    "enabled": True,
                    "host": "192.168.1.22",
                    "port": 5020,
                    "unit_id": 1,
                    "start_commands": [
                        {
                            "function_code": 5,
                            "offset": 0,
                            "value": True,
                            "label": "电机1启动(地址1/偏移0)"
                        },
                        {
                            "function_code": 5,
                            "offset": 100,
                            "value": True,
                            "label": "阀门1打开(地址101/偏移100)"
                        }
                    ],
                    "stop_commands": [
                        {
                            "function_code": 5,
                            "offset": 0,
                            "value": False,
                            "label": "电机1停止(地址1/偏移0)"
                        },
                        {
                            "function_code": 5,
                            "offset": 100,
                            "value": False,
                            "label": "阀门1关闭(地址101/偏移100)"
                        }
                    ],
                    "status_feedback": {
                        "discrete_inputs": {
                            "motor_running": {
                                "function_code": 2,
                                "offset": 0
                            },
                            "motor_stopped": {
                                "function_code": 2,
                                "offset": 1
                            },
                            "motor_fault": {
                                "function_code": 2,
                                "offset": 2
                            },
                            "valve_opened": {
                                "function_code": 2,
                                "offset": 100
                            },
                            "valve_closed": {
                                "function_code": 2,
                                "offset": 101
                            },
                            "valve_fault": {
                                "function_code": 2,
                                "offset": 102
                            }
                        },
                        "input_registers": {
                            "motor_state_code": {
                                "function_code": 4,
                                "offset": 0
                            },
                            "valve_position": {
                                "function_code": 4,
                                "offset": 100
                            }
                        }
                    }
                },
                "三色瓶分选": {
                    "enabled": False
                },
                "3A瓶脱标工艺": {
                    "enabled": False
                },
                "绿瓶脱标工艺": {
                    "enabled": False
                }
            }
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._config = self._merge_defaults(self._default_config, loaded)
            except Exception:
                self._config = copy.deepcopy(self._default_config)
        else:
            self._config = copy.deepcopy(self._default_config)
            self._save_config()

    def _merge_defaults(self, defaults, actual):
        if not isinstance(defaults, dict):
            return actual
        if not isinstance(actual, dict):
            return copy.deepcopy(defaults)

        merged = copy.deepcopy(actual)
        for key, default_value in defaults.items():
            if key not in merged:
                merged[key] = copy.deepcopy(default_value)
                continue
            if isinstance(default_value, dict):
                merged[key] = self._merge_defaults(default_value, merged.get(key))
        return merged

    def _save_config(self):
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        self._save_config()

# Global instance
config_manager = ConfigManager()
