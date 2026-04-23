# MQTT 主题规范

## 1. 适用范围

本规范适用于当前系统中的以下角色：

- HMI 客户端：订阅设备状态，发布设备动作指令，接收命令回执。
- Modbus TCP 执行端客户端：订阅自己负责设备的动作指令，发布设备状态与命令回执。
- MQTT Broker：作为消息总线转发消息，不承载业务路由逻辑。

## 2. 设计原则

- 设备主标识统一使用 `device_code`。
- 单设备消息使用单设备主题，不在主通道中混装多设备状态。
- “部分设备”通过设备列表逐条发布实现，不单独设计批量设备主题。
- 设备状态主题启用 retained，命令主题与命令回执主题不启用 retained。
- PLC 维度信息保留在消息体字段中，不进入主 topic 层级。

## 3. Topic 结构

统一前缀：

```text
iot/v1
```

核心主题：

```text
iot/v1/status/device/{device_code}
iot/v1/command/device/{device_code}
iot/v1/command-result/device/{device_code}
iot/v1/client/{client_id}/state
```

### 3.1 设备状态主题

```text
iot/v1/status/device/{device_code}
```

用途：

- 执行端客户端发布设备最新状态与遥测。
- HMI 客户端可订阅全部设备状态或某个设备状态。

订阅示例：

- 订阅全部设备状态：`iot/v1/status/device/+`
- 订阅单设备状态：`iot/v1/status/device/DEV-001`

发布规则：

- 每条消息只描述一个设备。
- `retain = true`

### 3.2 设备动作指令主题

```text
iot/v1/command/device/{device_code}
```

用途：

- HMI 客户端向单设备下发动作指令。
- HMI 客户端向部分设备下发同一动作时，对设备列表逐条发布。

订阅示例：

- 执行端接收全部设备命令：`iot/v1/command/device/+`
- 执行端仅接收负责设备：
  - `iot/v1/command/device/DEV-001`
  - `iot/v1/command/device/DEV-003`
  - `iot/v1/command/device/DEV-008`

发布规则：

- 单设备一条消息。
- 多设备批量控制时，每个目标设备单独发布一条消息。
- 同一批次命令使用相同 `batch_id`，每条消息拥有独立 `command_id`。
- `retain = false`

### 3.3 命令回执主题

```text
iot/v1/command-result/device/{device_code}
```

用途：

- 执行端回传命令接收确认、执行中、执行成功、执行失败。

订阅示例：

- HMI 订阅全部命令回执：`iot/v1/command-result/device/+`
- HMI 订阅单设备命令回执：`iot/v1/command-result/device/DEV-001`

发布规则：

- 至少回传一条 `received`。
- 最终必须回传一条 `executed` 或 `failed`。
- `retain = false`

### 3.4 MQTT 客户端在线状态主题

```text
iot/v1/client/{client_id}/state
```

用途：

- 表示执行端 MQTT 客户端自身在线/离线。
- 不替代设备状态主题。

发布规则：

- 客户端连接成功后发布 `online`。
- 客户端断连时使用 LWT 发布 `offline`。
- `retain = true`

## 4. 消息体规范

### 4.1 设备状态消息

主题：

```text
iot/v1/status/device/{device_code}
```

消息体：

```json
{
  "device_code": "DEV-001",
  "ts": "2026-04-23T10:00:00Z",
  "status": {
    "device_status": 2,
    "online": true,
    "alarm": false
  },
  "telemetry": {
    "temperature": 36.5,
    "pressure": 0.8
  },
  "source": {
    "client_id": "gateway-main",
    "protocol": "modbus-tcp"
  },
  "plc": {
    "plc_code": "PLC-01"
  }
}
```

字段要求：

- `device_code` 必须与 topic 中的 `{device_code}` 完全一致。
- `status.device_status` 与设备表状态枚举一致：
  - `0`: 离线
  - `1`: 在线
  - `2`: 运行中
  - `3`: 故障
- `telemetry` 允许扩展业务字段。
- `source.client_id` 表示发布该状态的执行端客户端。
- `plc.plc_code` 表示该设备当前隶属或对应的 PLC。

### 4.2 动作指令消息

主题：

```text
iot/v1/command/device/{device_code}
```

消息体：

```json
{
  "command_id": "cmd-20260423-0001",
  "batch_id": "batch-20260423-01",
  "device_code": "DEV-001",
  "action_name": "启动",
  "command_type": "START",
  "params": {
    "point_address": 0,
    "function_code": "0x06",
    "offset": 2,
    "data": 1
  },
  "ts": "2026-04-23T10:00:00Z",
  "source": {
    "client_id": "hmi-terminal-01"
  }
}
```

字段要求：

- `command_id` 为单条命令唯一标识。
- `batch_id` 用于关联同一批次下发的多台设备命令，可为空。
- `action_name` 对应 `device_action.action_name`。
- `params` 对应 `device_action.action_command_params`。
- `command_type` 为标准字段名，统一替代旧字段 `type`。

### 4.3 命令回执消息

主题：

```text
iot/v1/command-result/device/{device_code}
```

消息体：

```json
{
  "command_id": "cmd-20260423-0001",
  "batch_id": "batch-20260423-01",
  "device_code": "DEV-001",
  "result_code": "EXECUTED",
  "result_message": "write success",
  "stage": "executed",
  "ts": "2026-04-23T10:00:02Z",
  "source": {
    "client_id": "gateway-main"
  }
}
```

字段要求：

- `stage` 固定取值：
  - `received`
  - `executing`
  - `executed`
  - `failed`
- `result_code` 为机器可判定枚举，推荐值：
  - `RECEIVED`
  - `EXECUTED`
  - `MODBUS_TIMEOUT`
  - `DEVICE_OFFLINE`
  - `PARAM_INVALID`

## 5. 部分设备的实现规则

### 5.1 HMI 订阅部分设备状态

按需要订阅多个单设备主题，例如：

```text
iot/v1/status/device/DEV-001
iot/v1/status/device/DEV-003
iot/v1/status/device/DEV-008
```

### 5.2 执行端接收部分设备命令

执行端只订阅自己负责的设备命令主题，例如：

```text
iot/v1/command/device/DEV-001
iot/v1/command/device/DEV-003
iot/v1/command/device/DEV-008
```

### 5.3 HMI 向部分设备批量下发

HMI 对每个目标设备分别发布一条命令消息：

- 主题不同：`iot/v1/command/device/{device_code}`
- `batch_id` 相同
- `command_id` 各不相同

## 6. 兼容迁移

历史主题如下：

```text
telemetry/plc/{device_id}
command/plc/{device_id}
event/plc/{device_id}
```

迁移建议：

1. 兼容期内，HMI 可同时解析旧状态主题与新状态主题。
2. 新增开发统一使用 `iot/v1/*`。
3. 联调完成后，逐步下线旧主题。
