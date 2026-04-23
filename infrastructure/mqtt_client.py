import json
import logging
import time
from PyQt6.QtCore import QObject, pyqtSignal
import paho.mqtt.client as mqtt

class MqttClient(QObject):
    """
    MQTT 客户端基础设施层
    负责与网关进行物理连接、订阅主题及消息收发
    通过 PyQt 信号将消息推送到 ViewModel 层
    """
    
    # 定义信号
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(str, dict)  # topic, payload_dict
    error_occurred = pyqtSignal(str)

    def __init__(self, host="localhost", port=1883, username=None, password=None, client_id="hmi_terminal"):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        
        # 初始化 paho-mqtt 客户端
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        
        # 设置认证信息
        if self.username:
            self.client.username_pw_set(self.username, self.password)
        
        # 绑定回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        self.logger = logging.getLogger("MqttClient")

    def connect_to_broker(self):
        """异步连接到 MQTT Broker"""
        try:
            self.logger.info(f"正在尝试连接到 MQTT Broker: {self.host}:{self.port}")
            self.logger.info(
                "[MQTT_CONNECT_REQUEST] host=%s port=%s client_id=%s username=%s keepalive=%s",
                self.host,
                self.port,
                self.client_id,
                self.username,
                60,
            )
            self.client.connect_async(self.host, self.port, 60)
            self.client.loop_start()  # 在后台线程运行循环
        except Exception as e:
            self.error_occurred.emit(f"连接失败: {str(e)}")

    def disconnect_from_broker(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic):
        """订阅主题"""
        start = time.perf_counter()
        result, mid = self.client.subscribe(topic, qos=0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.logger.info(
            "[MQTT_SUBSCRIBE_REQUEST] topic=%s qos=%s mid=%s rc=%s elapsed_ms=%.2f",
            topic,
            0,
            mid,
            result,
            elapsed_ms,
        )
        if result != mqtt.MQTT_ERR_SUCCESS:
            self.error_occurred.emit(f"订阅失败: {result}")
            self.logger.error("[MQTT_SUBSCRIBE_ERROR] topic=%s mid=%s rc=%s", topic, mid, result)
        else:
            self.logger.info(f"已订阅主题: {topic}")

    def subscribe_many(self, topics):
        """批量订阅多个主题。"""
        for topic in topics or []:
            if not topic:
                continue
            self.subscribe(topic)

    def publish(self, topic, payload, retain=False):
        """
        发布消息
        payload: 字典或字符串
        """
        start = time.perf_counter()
        if isinstance(payload, dict):
            msg = json.dumps(payload)
        else:
            msg = str(payload)

        self.logger.info(
            "[MQTT_PUBLISH_REQUEST] topic=%s qos=%s retain=%s payload_bytes=%s payload=%s",
            topic,
            0,
            retain,
            len(msg.encode("utf-8")),
            msg,
        )
        result = self.client.publish(topic, msg, qos=0, retain=retain)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.logger.info(
            "[MQTT_PUBLISH_RESULT] topic=%s mid=%s rc=%s elapsed_ms=%.2f",
            topic,
            getattr(result, "mid", None),
            result.rc,
            elapsed_ms,
        )
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            self.error_occurred.emit(f"发布失败: {result.rc}")
            self.logger.error(
                "[MQTT_PUBLISH_ERROR] topic=%s mid=%s rc=%s payload=%s",
                topic,
                getattr(result, "mid", None),
                result.rc,
                msg,
            )

    def set_last_will(self, topic, payload="offline", retain=True):
        """为执行端在线状态保留 LWT 配置入口。"""
        if isinstance(payload, dict):
            msg = json.dumps(payload)
        else:
            msg = str(payload)
        self.client.will_set(topic, msg, qos=0, retain=retain)

    # --- 内部回调 ---

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.logger.info("成功连接到 MQTT Broker")
            self.connected.emit()
        else:
            # rc 为 5 表示认证失败 (Connection Refused: not authorised)
            error_msg = f"连接失败，错误代码: {rc}"
            if rc == 5:
                error_msg = "MQTT 认证失败: 用户名或密码错误"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        self.logger.warning(f"MQTT 断开连接: {rc}")
        self.disconnected.emit()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
            self.message_received.emit(topic, payload)
        except Exception as e:
            self.logger.error(f"解析 JSON 消息失败: {e}")
            self.message_received.emit(topic, {"raw": msg.payload.decode()})
