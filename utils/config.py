import json
import os

class ConfigManager:
    _instance = None
    _config_path = "/home/pi/project/hmi/config.json"
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
                    self._config = json.load(f)
            except Exception:
                self._config = self._default_config.copy()
        else:
            self._config = self._default_config.copy()
            self._save_config()

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
