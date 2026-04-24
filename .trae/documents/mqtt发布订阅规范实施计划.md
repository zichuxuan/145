# MQTT 发布订阅规范实施计划

## Summary

目标：为当前 HMI + MQTT Broker + Modbus TCP 执行端场景定义一套统一的 MQTT 主题与消息规范，满足以下能力：

* HMI 客户端可以订阅全部设备状态，或仅订阅某个设备状态。

* HMI 客户端可以向某个设备下发动作指令，或向部分设备下发同一批动作指令。

* Modbus TCP 执行端客户端可以发布某个设备或多个设备的状态。

* Modbus TCP 执行端客户端可以只接收自己负责的某个设备或部分设备的动作指令。

* 保留独立的命令回执/执行结果主题，便于追踪。

本计划采用以下已确认决策：

* MQTT 设备标识统一使用 `device_code`，不使用数据库自增 `id` 作为主题路径主键。

* “部分设备”采用显式设备列表，不按产线、类别、PLC 分组做主路径设计。

* 状态发布采用“逐设备逐条消息”，不做多设备混装消息作为主通道。

* 命令结果采用独立回执主题。

* 设备状态主题启用 retained，保证新订阅者可立即获取最后状态。

* Modbus TCP 执行端采用“一客户端管多 PLC”模型，但 PLC 数量不固化进主题层级。

## Current State Analysis

已发现的仓库现状如下：

1. `/home/pi/project/hmi/viewmodels/device_viewmodel.py`

   * 当前连接成功后固定订阅 `telemetry/plc/+`。

   * 当前只按 `telemetry/plc/` 前缀处理状态消息。

   * 该实现只能粗粒度订阅全部 PLC 遥测，不能表达“单设备订阅”。

2. `/home/pi/project/hmi/services/device_service.py`

   * `format_command()` 当前固定生成 `command/plc/{device_id}`。

   * `parse_telemetry()` 只解析简化 payload，没有主题语义解析。

   * 该实现没有定义批量下发、命令追踪、执行回执、状态 retained 约束。

3. `/home/pi/project/hmi/API文档.md`

   * 已存在 MQTT 直接下发主题 `command/plc/{device_id}`。

   * 已存在执行结果主题 `event/plc/{device_id}`。

   * 文档中命令消息体字段与代码不完全一致：文档示例使用 `type`，代码使用 `command_type`。

   * 文档尚未定义“订阅全部设备状态 / 单设备状态 / 部分设备命令”规范。

4. `/home/pi/project/hmi/doc/系统架构.txt`

   * 已明确 HMI 通过 MQTT 下发指令，网关/执行端通过 MQTT 发布实时状态。

   * 该文档没有约束具体 topic 设计。

5. `/home/pi/project/hmi/SQL/device_instance.sql`

   * `device_code` 唯一，适合作为 MQTT 主题中的稳定设备标识。

   * `device_data` 可承载 PLC 地址、端口、控制模式、通讯协议等扩展映射。

6. `/home/pi/project/hmi/SQL/device_action.sql`

   * 行为事件按 `device_instance_id` 关联设备。

   * `action_command_params` 已天然适合作为下发命令 `params` 的业务来源。

## Proposed Changes

### 1. 新增统一 MQTT 规范文档

建议新增文件：

* `/home/pi/project/hmi/doc/MQTT主题规范.md`

内容定义为最终单一事实来源，明确以下主题树：

```text
iot/v1/status/device/{device_code}
iot/v1/command/device/{device_code}
iot/v1/command-result/device/{device_code}
iot/v1/client/{client_id}/state
```

说明：

* `iot/v1/status/device/{device_code}`

  * 设备实时状态主题。

  * HMI 订阅全部设备：`iot/v1/status/device/+`

  * HMI 订阅单设备：`iot/v1/status/device/DEV-001`

  * 执行端发布单设备状态到对应主题。

  * `retain = true`

* `iot/v1/command/device/{device_code}`

  * 单设备动作指令主题。

  * HMI 下发单设备命令时发布到该主题。

  * HMI 下发“部分设备”命令时，对设备列表逐个发布多条消息，每个目标设备一条。

  * 执行端若接收全部设备命令则订阅 `iot/v1/command/device/+`。

  * 执行端若只接收部分设备命令，则只订阅自己负责的多个设备主题，例如：

    * `iot/v1/command/device/DEV-001`

    * `iot/v1/command/device/DEV-003`

    * `iot/v1/command/device/DEV-008`

* `iot/v1/command-result/device/{device_code}`

  * 执行端回执主题。

  * 用于接收确认、执行成功、执行失败。

  * HMI 可订阅全部：`iot/v1/command-result/device/+`

  * HMI 可订阅单设备：`iot/v1/command-result/device/DEV-001`

  * `retain = false`

* `iot/v1/client/{client_id}/state`

  * 客户端在线状态主题，用于描述执行端客户端存活。

  * 执行端连接 Broker 时发布 `online`，断开时通过 LWT 发布 `offline`。

  * `retain = true`

  * 该主题不替代设备状态，只描述 MQTT 客户端本身。

### 2. 统一消息体结构

在新增规范文档与 API 文档中统一以下 JSON 结构。

#### 2.1 设备状态消息

主题：

* `iot/v1/status/device/{device_code}`

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

规则：

* `device_code` 必须与 topic 末段一致。

* `status.device_status` 与 `device_instance.device_status` 枚举保持一致。

* `source.client_id` 表示发布状态的执行端客户端。

* `plc.plc_code` 作为消息体字段保留，不进入主 topic 层级。

* retained 开启，仅保留每台设备最近一条状态。

#### 2.2 单设备动作指令消息

主题：

* `iot/v1/command/device/{device_code}`

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

规则：

* 单设备命令每个目标设备只发一条消息。

* 对“部分设备”批量控制时，HMI 对设备列表逐条发布，`batch_id` 相同，`command_id` 不同。

* `action_name` 直接来源于 `device_action.action_name`。

* `params` 直接来源于 `device_action.action_command_params`。

* `command_type` 作为标准字段名，替代 API 文档中现有不一致的 `type`。

* `retain = false`

#### 2.3 命令回执消息

主题：

* `iot/v1/command-result/device/{device_code}`

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

规则：

* `stage` 取值固定为：`received`、`executing`、`executed`、`failed`。

* `result_code` 为机器可判定的枚举值，如：`RECEIVED`、`EXECUTED`、`MODBUS_TIMEOUT`、`DEVICE_OFFLINE`、`PARAM_INVALID`。

* 同一 `command_id` 可以发多条阶段性回执。

* 最终结果必须至少有一条 `executed` 或 `failed`。

### 3. HMI 侧实现改造

#### 3.1 更新 `/home/pi/project/hmi/services/device_service.py`

目标：

* 将该文件从“仅拼接旧 topic”升级为“统一 MQTT 主题与消息构造/解析入口”。

实施内容：

* 增加 MQTT topic 常量，例如：

  * `MQTT_TOPIC_STATUS_DEVICE = "iot/v1/status/device/{device_code}"`

  * `MQTT_TOPIC_COMMAND_DEVICE = "iot/v1/command/device/{device_code}"`

  * `MQTT_TOPIC_COMMAND_RESULT_DEVICE = "iot/v1/command-result/device/{device_code}"`

* 新增方法：

  * `build_status_topic(device_code)`

  * `build_command_topic(device_code)`

  * `build_command_result_topic(device_code)`

  * `build_command_payload(device_code, action_name, command_type, params, source_client_id, batch_id=None)`

  * `parse_status_message(topic, payload)`

  * `parse_command_result_message(topic, payload)`

* 保留旧方法时做兼容跳转，避免直接断裂。

* 将 `format_command()` 的输出切换到新 topic 和新字段名。

* 将 `parse_telemetry()` 重构为解析标准状态消息，不再假设旧版 `telemetry/plc/*` 结构。

#### 3.2 更新 `/home/pi/project/hmi/viewmodels/device_viewmodel.py`

目标：

* 支持全部设备状态订阅、单设备状态订阅、命令结果订阅。

实施内容：

* 连接成功后的默认订阅从 `telemetry/plc/+` 切换为：

  * `iot/v1/status/device/+`

  * `iot/v1/command-result/device/+`

* 增加精确订阅方法，例如：

  * `subscribe_device_status(device_code)`

  * `subscribe_all_device_status()`

  * 如 UI 需要，再增加 `subscribe_device_command_result(device_code)`

* `_handle_mqtt_message()` 中按 topic 前缀分发：

  * `iot/v1/status/device/` -> 状态解析并发出 `telemetry_updated`

  * `iot/v1/command-result/device/` -> 新增命令回执信号给 UI

* `send_device_command()` 改为显式接收命令元数据或行为事件数据。

* 另增一个批量发送接口，例如 `send_batch_device_command(device_codes, action_name, command_type, params)`：

  * 遍历设备列表逐条发布。

  * 同一批次使用相同 `batch_id`。

#### 3.3 更新 `/home/pi/project/hmi/infrastructure/mqtt_client.py`

目标：

* 让基础设施层更方便支持多 topic 订阅与客户端在线状态扩展。

实施内容：

* 保持现有单主题 `subscribe()` 能力。

* 增加可选的批量订阅辅助方法，例如 `subscribe_many(topics: list[str])`。

* 为后续 LWT/retain 策略预留配置注释或参数入口。

* 不在该层耦合业务 topic 规则，topic 规则保持在 `DeviceService`。

### 4. 文档对齐

#### 4.1 更新 `/home/pi/project/hmi/API文档.md`

目标：

* 让 HTTP 和 MQTT 两种命令通道使用一致字段名和一致语义。

实施内容：

* 将 MQTT 章节中的旧主题：

  * `command/plc/{device_id}`

  * `event/plc/{device_id}`
    替换或标记废弃为新主题：

  * `iot/v1/command/device/{device_code}`

  * `iot/v1/command-result/device/{device_code}`

* 明确字段统一使用 `command_type`，不再混用 `type`。

* 增加“全部设备订阅 / 单设备订阅 / 批量设备下发”示例。

* 明确 retained 策略只用于状态主题，不用于命令主题和结果主题。

#### 4.2 网关/执行端契约说明

说明：

* 当前仓库中未发现网关执行端代码，因此不在本次仓库内直接实现。

* 需在规范文档中明确另一客户端的最小实现契约：

  * 订阅全部设备命令：`iot/v1/command/device/+`

  * 订阅部分设备命令：对每个负责设备单独订阅对应主题

  * 发布设备状态：`iot/v1/status/device/{device_code}`

  * 发布命令回执：`iot/v1/command-result/device/{device_code}`

  * 连接态心跳：`iot/v1/client/{client_id}/state`

### 5. 兼容与迁移策略

为避免一次性切换带来的联调中断，实施时按两阶段推进：

1. 兼容阶段

   * HMI 侧可同时兼容旧状态 topic 与新状态 topic 的解析。

   * API 文档中将旧主题标记为“过渡兼容，待废弃”。

2. 切换阶段

   * 联调完成后，默认订阅与默认发布全部切换到 `iot/v1/*`。

   * 删除或下线旧 `telemetry/plc/*`、`command/plc/*`、`event/plc/*` 方案。

## Assumptions & Decisions

* 采用 `device_code` 作为 MQTT 主题主键，因为其在 `device_instance` 中唯一，且比数据库 `id` 更稳定。

* 不把 `plc_code` 放进主 topic 层级，原因是用户已确认“部分设备”按设备列表组织，而非按 PLC 分组组织。

* 采用“批量命令 = 多条单设备命令 + 相同 batch\_id”，而不是“一个批量 topic + 一个数组 payload”。

* 采用“逐设备逐条状态消息”作为主通道，以适配单设备订阅、通配订阅和 retained 语义。

* `device_action.action_command_params` 作为 Modbus TCP 下发参数源，不在 topic 中编码寄存器地址等业务细节。

* 系统实际 PLC 数量按用户描述视为 3 台，`系统架构.txt` 中示意图的 2 台 PLC 仅视为示例，不作为主题设计约束。

* 网关/执行端可能管理多 PLC，但 topic 只面向设备，不面向 PLC。

## Verification Steps

执行阶段完成后，应至少验证以下内容：

1. HMI 订阅全部状态

   * 订阅 `iot/v1/status/device/+`

   * 任意设备状态发布后，HMI 可收到并正确解析 `device_code`、`device_status`、遥测值。

2. HMI 订阅单设备状态

   * 订阅 `iot/v1/status/device/DEV-001`

   * 仅 `DEV-001` 状态被接收，其他设备不触发 UI 更新。

3. 执行端订阅部分设备命令

   * 执行端仅订阅 `DEV-001`、`DEV-003`

   * HMI 向 `DEV-001`、`DEV-002`、`DEV-003` 批量下发时，执行端仅接收自己负责的 2 台设备命令。

4. 批量命令追踪

   * 同批设备命令使用同一 `batch_id`

   * 每台设备拥有独立 `command_id`

   * 回执中 `command_id` 与 `batch_id` 均可追踪。

5. retained 验证

   * 执行端向 `iot/v1/status/device/DEV-001` 发布 retained 状态。

   * 新启动的 HMI 订阅后无需等待下一次采集即可拿到最后状态。

6. 回执链路验证

   * 执行端收到命令后至少发布 `received`。

   * 执行完成后发布 `executed` 或 `failed`。

   * HMI 能将结果关联到对应设备与对应命令。

7. 兼容验证

   * 过渡阶段内，如旧 topic 仍存在，HMI 不因旧消息而报错。

   * 切换完成后，关闭旧 topic 仍不影响新链路。

