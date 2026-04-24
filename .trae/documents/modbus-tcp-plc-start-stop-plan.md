# 智能生产页面 Modbus TCP 启停 PLC 实现计划

## Summary

- 目标：在 `hmi/views/production_overview.py` 的“启动流程 / 停止流程 / 紧急停止 STOP”交互中，接入对局域网内西门子 SMART200 PLC 的 Modbus TCP 控制。
- 成功标准：
  - 点击蓝色按钮“启动流程”时，向当前选中流程对应的 PLC 配置发送启动指令。
  - 蓝色按钮处于“停止流程”态时，点击后向当前运行流程发送停止指令。
  - 点击红色 `STOP` 时：
    - 若存在运行中流程，则对运行中流程发送停止指令；
    - 若当前没有运行中流程，则对当前选中流程发送停止指令。
  - PLC 写入成功后再更新前端运行/停止状态，不再使用前端定时模拟。
  - 所有 PLC 连接参数、功能码、地址、写入值、超时等均从 `hmi/config.json` 读取。
  - 当前仅 `1#平台智能上料` 配置真实点位；其余 3 个流程未配置时，点击按钮提示“当前流程未配置 PLC 参数”，不发送指令。

## Current State Analysis

### 已确认现状

- `hmi/views/production_overview.py`
  - `ProductionOverview` 已接收 `vm`，可以直接绑定 ViewModel 信号。
  - `_handle_start_btn_click()` 当前逻辑：
    - 运行中时直接调用 `_stop_current_flow()`；
    - 未运行时调用 `_simulate_start_action()`。
  - `_simulate_start_action()` 仅通过 `QTimer.singleShot()` 在 1.4 秒后触发 `_complete_start_action()`，没有真实 IO。
  - 红色 `STOP` 当前直接绑定 `_stop_current_flow()`，只改本地 UI 状态。
- `hmi/viewmodels/device_viewmodel.py`
  - 已有通用 `ApiWorker` + `WorkerSignals` + `QThreadPool.globalInstance()`。
  - 当前 ViewModel 负责把 IO 放到线程池，符合本项目 MVVM 约束。
- `hmi/services/device_service.py`
  - 当前主要负责 HTTP API 与 MQTT，没有 Modbus TCP 能力。
- `hmi/utils/config.py`
  - 已存在 `ConfigManager`，配置文件固定为 `hmi/config.json`。
  - 支持默认配置写回，适合扩展 PLC 配置段。
- `hmi/main.py`
  - 负责实例化基础设施、Service、ViewModel 和主窗口。
- `hmi/requirements.txt`
  - 当前仅有 `PyQt6`、`paho-mqtt`、`requests<2.33`，未引入 Modbus 库。

### 已确认产品决策

- PLC 控制按流程分别配置，不共用一组参数。
- 启动/停止写入成功后，界面立即切换状态，不等待读回确认。
- 红色 `STOP` 与普通停止共用停止指令。
- 当前仅 `1#平台智能上料` 有真实点位。
- 其余 3 个流程未配置时，点击后提示未配置。
- 当无运行中流程而点击红色 `STOP` 时，作用于当前选中流程。

### 已确认的真实点位样例

- 流程：`1#平台智能上料`
- `unit_id = 1`
- 启停功能码：`05` 写单个线圈
- 启动地址：`1 (偏移 0)`，写入值 `0xFF00`
- 停止地址：`1 (偏移 0)`，写入值 `0x0000`
- 预留状态读取点位：
  - `02` / `10001 (偏移 0)` 运行中
  - `02` / `10002 (偏移 1)` 已停止
  - `02` / `10003 (偏移 2)` 故障
  - `04` / `30001 (偏移 0)` 状态码

## Proposed Changes

### 1. 新增 `hmi/infrastructure/modbus_tcp_client.py`

- 新建一个最小可控的 Modbus TCP 基础设施层，使用标准库 `socket` + `struct` 实现，不新增第三方依赖。
- 原因：
  - 当前需求只需要支持少量固定功能码；
  - 项目运行在 ARM64 开发板，避免增加额外安装风险；
  - 现阶段使用标准库更容易把行为完全写死并做日志追踪。
- 功能范围：
  - `write_single_coil(host, port, unit_id, offset, value, timeout_ms)`
  - `read_discrete_inputs(host, port, unit_id, offset, count, timeout_ms)` 预留
  - `read_input_registers(host, port, unit_id, offset, count, timeout_ms)` 预留
- 协议要求：
  - 自动构造 MBAP 头与 PDU。
  - 每次请求使用递增事务标识。
  - 校验返回的事务标识、协议标识、Unit ID、功能码。
  - 识别 Modbus 异常响应（功能码最高位为 1）并抛出带错误码的异常。
  - 对 socket 连接超时、收包长度不足、返回报文不匹配等错误统一抛业务可读异常。
- 日志要求：
  - 使用 `logging.getLogger("ModbusTcpClient")`。
  - 记录 host、port、unit_id、功能码、offset、耗时、结果。
  - 不输出无意义原始二进制，十六进制报文仅在 debug 或异常时输出。

### 2. 新增 `hmi/services/plc_control_service.py`

- 新建独立 PLC 控制服务，避免把 Modbus 逻辑继续堆到 `DeviceService`。
- 职责：
  - 从 `config_manager` 读取 `plc_control` 配置。
  - 根据流程名称解析对应 PLC 参数。
  - 调用 `ModbusTcpClient` 发送启动/停止指令。
  - 对未配置流程、配置缺项、非法功能码做前置校验。
  - 返回统一结果结构，供 ViewModel 驱动 UI。
- 对外接口：
  - `start_flow(flow_name: str) -> dict`
  - `stop_flow(flow_name: str) -> dict`
  - `get_flow_config(flow_name: str) -> dict`
  - `is_flow_configured(flow_name: str) -> bool`
- 返回结构固定为：

```python
{
    "success": True,
    "flow_name": "1#平台智能上料",
    "action": "start",  # start | stop
    "message": "PLC 启动指令发送成功"
}
```

- 失败时抛出可直接展示的异常文本，例如：
  - `当前流程未配置 PLC 参数`
  - `流程 PLC 配置缺少 host`
  - `当前仅支持 Modbus 功能码 05`
  - `PLC 写单个线圈失败: 异常码 02`

### 3. 更新 `hmi/viewmodels/device_viewmodel.py`

- 在 `DeviceViewModel` 中新增 PLC 控制编排，不让 View 直接访问 Service。
- 构造函数改为注入 `plc_control_service`：

```python
def __init__(self, mqtt_client, device_service, plc_control_service):
```

- 新增信号：
  - `flow_control_started = pyqtSignal(str, str)`  
    含义：`flow_name, action`
  - `flow_control_succeeded = pyqtSignal(dict)`
  - `flow_control_failed = pyqtSignal(str, str, str)`  
    含义：`flow_name, action, message`
- 新增方法：
  - `start_flow(flow_name: str)`
  - `stop_flow(flow_name: str)`
- 实现方式：
  - 复用现有 `ApiWorker` 在线程池中执行 `plc_control_service.start_flow/stop_flow`。
  - ViewModel 收到成功结果后发 `flow_control_succeeded`。
  - 收到异常后发 `flow_control_failed`，同时保持 `error_occurred` 不用于 PLC 控制流程的主提示，避免与全局弹窗逻辑混淆。
- 这样可以保证：
  - UI 线程不做 socket IO；
  - View 只处理状态渲染与提示；
  - PLC 逻辑仍保持在 Service/Infrastructure 层。

### 4. 更新 `hmi/main.py`

- 新增 `PlcControlService` 的实例化与注入。
- 目标结构：

```python
from services.plc_control_service import PlcControlService

plc_control_service = PlcControlService()
device_vm = DeviceViewModel(mqtt_client, device_service, plc_control_service)
```

- 不改变主窗口或其他页面构造方式。

### 5. 更新 `hmi/views/production_overview.py`

- 用真实异步 PLC 控制替换 `_simulate_start_action()`。
- 增加流程名称映射，直接复用当前卡片标题作为配置 key：
  - `1#平台智能上料`
  - `三色瓶分选`
  - `3A瓶脱标工艺`
  - `绿瓶脱标工艺`
- 页面新增状态字段：
  - `_pending_flow_action`：当前正在执行的动作，避免重复点击。
  - `_pending_flow_name`：当前动作对应流程。
- 绑定 ViewModel 信号：
  - `flow_control_started`
  - `flow_control_succeeded`
  - `flow_control_failed`
- 按钮行为改造：
  - 蓝色按钮：
    - 若 `_is_process_running == False`，对当前选中流程调用 `vm.start_flow(flow_name)`。
    - 若 `_is_process_running == True`，对当前运行流程调用 `vm.stop_flow(flow_name)`。
  - 红色 `STOP`：
    - 若有运行中流程，对运行中流程 `vm.stop_flow(flow_name)`。
    - 若无运行中流程，对当前选中流程 `vm.stop_flow(flow_name)`。
- UI 状态规则：
  - 发送前：按钮切 `loading`，禁用蓝色按钮与红色按钮，防止重复触发。
  - 启动成功：调用 `_apply_running_state()`，并把运行流程锁定为返回的 `flow_name` 对应索引。
  - 停止成功：调用 `_stop_current_flow()`，并恢复按钮可用。
  - 失败：
    - 恢复可点击；
    - 蓝色按钮切 `error`；
    - 用 `QMessageBox.warning()` 提示具体失败原因；
    - 不修改当前运行/停止 UI 状态。
- 删除或停用：
  - `_simulate_start_action()`
  - `_complete_start_action()` 中基于定时器的成功模拟
- 保留：
  - `_set_start_btn_state()`
  - `_apply_running_state()`
  - `_stop_current_flow()`
  - `_set_flow_nodes_status()`
  - `_set_stage_cards_running()`
  - 但会调整它们的调用入口，让它们只在 PLC 真正成功后执行。

### 6. 更新 `hmi/utils/config.py`

- 扩展 `_default_config`，新增 `plc_control` 段。
- 默认配置中提供完整结构和占位值，便于首次启动自动生成。
- 建议结构：

```json
{
  "plc_control": {
    "enabled": true,
    "default_port": 502,
    "connect_timeout_ms": 1500,
    "response_timeout_ms": 1500,
    "flows": {
      "1#平台智能上料": {
        "enabled": true,
        "host": "192.168.1.200",
        "port": 502,
        "unit_id": 1,
        "start_command": {
          "function_code": 5,
          "offset": 0,
          "value": true,
          "label": "地址1(偏移0)"
        },
        "stop_command": {
          "function_code": 5,
          "offset": 0,
          "value": false,
          "label": "地址1(偏移0)"
        },
        "status_feedback": {
          "discrete_inputs": {
            "running": {"function_code": 2, "offset": 0},
            "stopped": {"function_code": 2, "offset": 1},
            "fault": {"function_code": 2, "offset": 2}
          },
          "input_registers": {
            "state_code": {"function_code": 4, "offset": 0}
          }
        }
      },
      "三色瓶分选": {
        "enabled": false
      },
      "3A瓶脱标工艺": {
        "enabled": false
      },
      "绿瓶脱标工艺": {
        "enabled": false
      }
    }
  }
}
```

- 关键决策：
  - 配置中统一保存 `offset`，即零基址，避免地址 `1` / 偏移 `0` 混用。
  - `label` 仅作可读说明，不参与协议计算。
  - 当前保留 `status_feedback` 配置，但本次不用于 UI 成功判定。

### 7. 更新 `hmi/config.json`

- 在现有配置文件中追加 `plc_control` 实例配置。
- `1#平台智能上料` 按已确认点位写入。
- `host` 先填用户最终提供的 PLC IP；若当前尚未最终确认，则先留占位值并在启动时做必填校验。
- 其余 3 个流程写成 `enabled: false`，用于明确“未配置”状态。

### 8. 依赖策略

- `hmi/requirements.txt` 本次不改。
- 决策原因：
  - 当前仅需支持 `05` 写单个线圈；
  - 未来若需要更复杂批量寄存器写入、连接池、完整 Modbus 异常码支持，再评估引入 `pymodbus`。

## Assumptions & Decisions

- 使用现有中文流程标题作为配置 key，不再额外引入流程 ID 映射表。
- Modbus TCP 端口默认 `502`，但实际以 `config.json` 为准。
- 本次成功标准为“写入响应成功”，不做状态读回闭环。
- 当前只实现 `function_code = 05` 的启动/停止控制；`02` 和 `04` 仅读配置，不进入本次主流程。
- 未配置流程点击时，前端提示后直接返回，不改任何当前运行状态。
- 红色 `STOP` 与普通停止共用 `stop_command`。
- 红色 `STOP` 在无运行中流程时，作用于当前选中流程。
- 若用户在 PLC 指令执行中重复点击按钮，前端直接忽略，直到当前请求完成。
- 若 PLC 返回失败，界面保持原状态，不做“半成功”渲染。

## Verification Steps

### 代码级验证

- 检查 `ProductionOverview` 不再调用 `_simulate_start_action()` 作为真实入口。
- 检查所有 Modbus socket IO 均位于 ViewModel 线程池任务中执行。
- 检查 View 不直接访问 `PlcControlService` 或 `ModbusTcpClient`。
- 检查 `config_manager` 在无 `plc_control` 配置时能自动生成默认结构。

### 手工联调

1. 在 `hmi/config.json` 中填入 `1#平台智能上料` 的真实 `host/port/unit_id`。
2. 启动 HMI，进入总览页的“智能生产”页签。
3. 保持当前选中 `1#平台智能上料`，点击“启动流程”。
4. 预期：
   - 按钮先显示 `启动中...`
   - PLC 收到 `FC05` 写单个线圈 `offset=0, value=True`
   - 返回成功后按钮文字切为 `停止流程`
   - 对应流程节点状态切为“开启”
   - 对应底部卡片显示“运行中”
5. 再点击蓝色“停止流程”。
6. 预期：
   - PLC 收到 `FC05` 写单个线圈 `offset=0, value=False`
   - 返回成功后按钮恢复 `启动流程`
   - 对应流程节点状态切回“停止”
7. 切换到未配置流程，例如 `三色瓶分选`，点击“启动流程”。
8. 预期：
   - 弹出提示 `当前流程未配置 PLC 参数`
   - 不发送任何 Modbus 报文
   - 当前 UI 状态不改变
9. 在无运行中流程时点击红色 `STOP`。
10. 预期：
   - 对当前选中流程发送停止命令
   - 成功后界面保持停止态

### 回归检查

- MQTT 连接、设备管理、流程配置页面不受影响。
- `MainWindow` 原有全局错误弹窗逻辑不因 PLC 功能产生无关 API 错误弹窗。
- 启动后 `hmi/config.json` 未破坏现有 `mqtt`、`api`、`ui` 配置。
