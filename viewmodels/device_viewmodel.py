from PyQt6.QtCore import pyqtSignal, pyqtSlot, QThreadPool, QRunnable, QObject
from uuid import uuid4
from viewmodels.base_viewmodel import BaseViewModel

class WorkerSignals(QObject):
    """
    Worker 信号定义。

    后台任务统一通过这两个信号把结果送回主线程：
    - finished: 返回成功结果对象；
    - error: 返回异常信息字符串。
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

class ApiWorker(QRunnable):
    """
    用于执行 API 请求的后台任务。

    通过 QThreadPool 执行耗时操作，避免 UI 线程因网络请求或解析阻塞。
    """
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        """在线程池中执行目标函数，并通过信号反馈执行结果。"""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

class DeviceViewModel(BaseViewModel):
    """
    设备管理与控制 ViewModel
    连接 View 与 Infrastructure (MQTT) 及 Service (API)。

    在当前 MVVM 结构中：
    - View 只负责界面展示和事件响应；
    - ViewModel 负责异步编排、数据规范化与信号派发；
    - Service 负责 API/MQTT 的具体协议处理。
    """
    # UI 状态信号
    mqtt_status_changed = pyqtSignal(bool)
    telemetry_updated = pyqtSignal(dict)  # 发送处理后的遥测数据给 UI
    command_result_received = pyqtSignal(dict)  # 发送设备命令回执给 UI
    
    # 设备管理信号
    devices_loaded = pyqtSignal(list)
    device_models_loaded = pyqtSignal(list)
    device_actions_loaded = pyqtSignal(int, list)
    device_operation_finished = pyqtSignal(bool, str)  # 成功标志, 提示信息
    workflows_loaded = pyqtSignal(list)
    workflow_detail_loaded = pyqtSignal(dict)
    workflow_operation_finished = pyqtSignal(bool, str)
    
    def __init__(self, mqtt_client, device_service):
        super().__init__()
        self.mqtt_client = mqtt_client
        self.device_service = device_service
        # 使用全局线程池复用线程资源，避免频繁创建销毁后台线程。
        self.thread_pool = QThreadPool.globalInstance()
        
        # 将 MQTT 层的连接状态、消息和错误统一桥接到 ViewModel。
        self.mqtt_client.connected.connect(self._on_mqtt_connected)
        self.mqtt_client.disconnected.connect(lambda: self.mqtt_status_changed.emit(False))
        self.mqtt_client.message_received.connect(self._handle_mqtt_message)
        self.mqtt_client.error_occurred.connect(self.error_occurred.emit)

    def _on_mqtt_connected(self):
        """MQTT 建连成功后的初始化逻辑。"""
        self.mqtt_status_changed.emit(True)
        # 默认订阅全部设备状态和命令回执，同时保留旧 PLC 主题兼容旧链路。
        topics = [
            self.device_service.build_status_subscription_topic(),
            self.device_service.build_command_result_subscription_topic(),
            "telemetry/plc/+",
        ]
        if hasattr(self.mqtt_client, "subscribe_many"):
            self.mqtt_client.subscribe_many(topics)
        else:
            for topic in topics:
                self.mqtt_client.subscribe(topic)

    def subscribe_all_device_status(self):
        """订阅所有设备状态主题。"""
        self.mqtt_client.subscribe(self.device_service.build_status_subscription_topic())

    def subscribe_device_status(self, device_code):
        """订阅单个设备状态主题。"""
        self.mqtt_client.subscribe(self.device_service.build_status_subscription_topic(device_code))

    def subscribe_device_command_result(self, device_code):
        """订阅单个设备的命令回执主题。"""
        self.mqtt_client.subscribe(self.device_service.build_command_result_subscription_topic(device_code))

    def _handle_mqtt_message(self, topic, payload):
        """处理接收到的 MQTT 消息。

        当前将消息分为两类：
        - 状态/遥测消息：统一解析后通过 `telemetry_updated` 发给界面；
        - 命令回执消息：统一解析后通过 `command_result_received` 发给界面。
        """
        if topic.startswith("iot/v1/status/device/") or topic.startswith("telemetry/plc/"):
            processed_data = self.device_service.parse_status_message(topic, payload)
            if processed_data:
                self.telemetry_updated.emit(processed_data)
        elif topic.startswith("iot/v1/command-result/device/") or topic.startswith("event/plc/"):
            command_result = self.device_service.parse_command_result_message(topic, payload)
            if command_result:
                self.command_result_received.emit(command_result)

    @pyqtSlot()
    def load_devices(self, page=1, size=15):
        """异步加载设备列表。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.get_devices, page=page, size=size)
        worker.signals.finished.connect(self._on_devices_loaded)
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_devices_loaded(self, devices):
        """设备列表加载完成后的统一收口。"""
        self.is_busy = False
        # 兼容分页响应（dict）与列表响应（list），保证信号始终发 list。
        if isinstance(devices, dict):
            for key in ("items", "devices", "data", "rows", "list"):
                value = devices.get(key)
                if isinstance(value, list):
                    devices = value
                    break
            else:
                devices = []
        elif isinstance(devices, tuple):
            devices = list(devices)
        elif not isinstance(devices, list):
            devices = []

        self.devices_loaded.emit(devices)

    @pyqtSlot()
    def load_device_models(self):
        """异步加载设备型号列表。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.get_device_models)
        worker.signals.finished.connect(self._on_device_models_loaded)
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_device_models_loaded(self, models):
        """设备型号加载完成后通知界面。"""
        self.is_busy = False
        self.device_models_loaded.emit(models)

    @pyqtSlot(int)
    def load_device_actions(self, device_instance_id):
        """异步加载设备行为事件列表（用于编辑弹窗回显）。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.get_device_actions, device_instance_id)
        # 通过闭包把当前设备 ID 带到回调里，避免异步返回后丢失上下文。
        worker.signals.finished.connect(
            lambda actions, did=device_instance_id: self._on_device_actions_loaded(did, actions)
        )
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_device_actions_loaded(self, device_instance_id, actions):
        """设备行为事件加载完成后的统一收口。"""
        self.is_busy = False
        if isinstance(actions, dict):
            for key in ("items", "actions", "data", "rows", "list"):
                value = actions.get(key)
                if isinstance(value, list):
                    actions = value
                    break
            else:
                actions = []
        elif isinstance(actions, tuple):
            actions = list(actions)
        elif not isinstance(actions, list):
            actions = []

        self.device_actions_loaded.emit(device_instance_id, actions)

    @pyqtSlot(dict)
    def add_device(self, device_data):
        """异步添加设备。"""
        self.is_busy = True
        worker = ApiWorker(self._create_device_with_actions, device_data)
        worker.signals.finished.connect(lambda res: self._on_operation_finished(res, "添加设备成功"))
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _create_device_with_actions(self, device_data):
        """先创建设备，再按行创建行为事件。

        行为事件依赖新建设备返回的 `id` 作为 `device_instance_id`，
        因此必须先建主记录，再逐条创建动作记录。
        """
        payload = dict(device_data or {})
        actions = payload.pop("actions", [])

        created_device = self.device_service.create_device(payload)
        if not isinstance(created_device, dict):
            return created_device

        device_id = created_device.get("id")
        if not device_id or not isinstance(actions, list):
            return created_device

        # 逐条创建行为事件，确保每条动作都与当前设备实例关联。
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_payload = dict(action)
            action_payload["device_instance_id"] = device_id
            self.device_service.create_device_action(action_payload)

        return created_device

    @pyqtSlot(int, dict)
    def update_device(self, device_id, device_data):
        """异步更新设备。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.update_device, device_id, device_data)
        worker.signals.finished.connect(lambda res: self._on_operation_finished(res, "更新设备成功"))
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    @pyqtSlot(int)
    def delete_device(self, device_id):
        """异步删除设备。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.delete_device, device_id)
        worker.signals.finished.connect(lambda res: self._on_operation_finished(res, "删除设备成功"))
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_operation_finished(self, result, success_msg):
        """统一处理新增、更新、删除完成态。"""
        self.is_busy = False
        if result:
            self.device_operation_finished.emit(True, success_msg)
        else:
            self.device_operation_finished.emit(False, "操作失败，请重试")

    def _on_api_error(self, error_msg):
        """统一处理后台任务中的接口异常。"""
        self.is_busy = False
        self.error_occurred.emit(f"API 错误: {error_msg}")

    @pyqtSlot()
    def load_workflows(self, page=1, size=10):
        """异步加载工作流列表。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.get_workflows, page=page, size=size)
        worker.signals.finished.connect(self._on_workflows_loaded)
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_workflows_loaded(self, workflows):
        """工作流列表加载完成后的统一收口。"""
        self.is_busy = False
        if isinstance(workflows, dict):
            for key in ("items", "workflows", "data", "rows", "list"):
                value = workflows.get(key)
                if isinstance(value, list):
                    workflows = value
                    break
            else:
                workflows = []
        elif isinstance(workflows, tuple):
            workflows = list(workflows)
        elif not isinstance(workflows, list):
            workflows = []

        self.workflows_loaded.emit(workflows)

    @pyqtSlot(int)
    def load_workflow_detail(self, workflow_id):
        """异步加载工作流详情。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.get_workflow_detail, workflow_id)
        worker.signals.finished.connect(self._on_workflow_detail_loaded)
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_workflow_detail_loaded(self, workflow_detail):
        """工作流详情加载完成后的统一收口。"""
        self.is_busy = False
        if not isinstance(workflow_detail, dict):
            workflow_detail = {}
        self.workflow_detail_loaded.emit(workflow_detail)

    @pyqtSlot(dict)
    def add_workflow(self, workflow_data):
        """异步创建工作流。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.create_workflow, workflow_data)
        worker.signals.finished.connect(lambda res: self._on_workflow_operation_finished(res, "保存流程成功"))
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    @pyqtSlot(int, dict)
    def update_workflow(self, workflow_id, workflow_data):
        """异步更新工作流。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.update_workflow, workflow_id, workflow_data)
        worker.signals.finished.connect(lambda res: self._on_workflow_operation_finished(res, "更新流程成功"))
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    @pyqtSlot(int)
    def delete_workflow(self, workflow_id):
        """异步删除工作流。"""
        self.is_busy = True
        worker = ApiWorker(self.device_service.delete_workflow, workflow_id)
        worker.signals.finished.connect(lambda res: self._on_workflow_operation_finished(res, "删除流程成功"))
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_workflow_operation_finished(self, result, success_msg):
        """统一处理工作流新增、编辑、删除完成态。"""
        self.is_busy = False
        if result:
            self.workflow_operation_finished.emit(True, success_msg)
        else:
            self.workflow_operation_finished.emit(False, "工作流操作失败，请重试")

    @pyqtSlot()
    def toggle_connection(self):
        """处理 UI 的连接/断开按钮点击。

        当前逻辑仅发起连接；如后续需要支持断开，可在此继续补充分支。
        """
        self.is_busy = True
        try:
            self.mqtt_client.connect_to_broker()
        finally:
            self.is_busy = False

    @pyqtSlot(str, str)
    def send_device_command(self, device_id, cmd_type, params=None, action_name=None, batch_id=None, source_client_id=None):
        """发送单条设备控制指令。

        具体 topic/payload 拼装交给 Service，ViewModel 只负责调度发布。
        """
        topic, payload = self.device_service.format_command(
            device_id,
            cmd_type,
            params=params,
            action_name=action_name,
            batch_id=batch_id,
            source_client_id=source_client_id or getattr(self.mqtt_client, "client_id", "hmi-terminal"),
        )
        self.mqtt_client.publish(topic, payload)

    def send_batch_device_command(self, device_codes, action_name, command_type, params=None, source_client_id=None):
        """按设备列表逐条下发同一批次指令。

        通过统一的 `batch_id` 把多台设备上的同一轮指令关联起来，
        便于后续界面按批次跟踪命令回执。
        """
        normalized_device_codes = [str(code).strip() for code in (device_codes or []) if str(code).strip()]
        if not normalized_device_codes:
            return

        # 每次批量下发都生成唯一批次号，避免不同批次回执混淆。
        batch_id = f"batch-{uuid4().hex}"
        source = source_client_id or getattr(self.mqtt_client, "client_id", "hmi-terminal")

        for device_code in normalized_device_codes:
            topic, payload = self.device_service.format_command(
                device_code,
                command_type,
                params=params,
                action_name=action_name,
                batch_id=batch_id,
                source_client_id=source,
            )
            self.mqtt_client.publish(topic, payload)
