# 流程保存字段映射调整计划

## Summary

- 目标：调整 HMI 流程配置保存链路，使“启动状态”保存到 `workflow.enable_or_not`，“说明”保存到 `workflow.info`，远程控制画布中的节点顺序、设备配置、执行动作、输出动作等保存到 `workflow.workflow_detail`。
- 范围：仅针对当前 HMI 仓库中的流程配置前端保存、回显、服务层字段标准化与文档同步进行规划。
- 关键决策：
  - “说明”只写入 `info`，不再继续写入 `workflow_params.description`。
  - `workflow_detail` 采用“双层结构”：保留画布原始结构用于回显，同时补充结构化执行数据用于持久化和后续解析。
  - `workflow_params` 与 `conditions` 现有读写逻辑尽量不主动改动，仅在必要处保持兼容。
 
## Current State Analysis

### 1. 流程保存入口

- 界面保存入口在 `views/smart_production.py` 的 `_submit_workflow()` / `_collect_workflow_payload()`。
- 当前 payload 结构为：
  - `workflow_name`
  - `workflow_type`
  - `workflow_params.description`
  - `workflow_params.is_draft`
  - `workflow_detail`（直接取 `WorkflowCanvasEditor.get_workflow_detail()`）
  - `conditions`
  - `enable_or_not`
- 当前“说明”没有写入 `info`，而是放进 `workflow_params.description`。

### 2. 服务层字段过滤与兼容

- `services/device_service.py` 中 `self.workflow_fields` 当前仅允许：
  - `workflow_name`
  - `workflow_type`
  - `workflow_params`
  - `workflow_detail`
  - `conditions`
  - `enable_or_not`
- `_normalize_workflow_payload()` 当前别名映射为：
  - `description -> conditions`
  - `enabled -> enable_or_not`
- 这意味着即使界面层新增 `info` 字段，当前服务层也会直接过滤掉，无法提交给后端。

### 3. 工作流详情当前结构

- 画布数据来源于 `views/smart_production_canvas.py` 的 `WorkflowCanvasEditor.get_workflow_detail()`。
- 当前默认结构来自 `views/smart_production_utils.py` 的 `create_default_workflow_detail()`：
  - `{"version": 1, "sequence": []}`
- 每个节点按树形结构保存，节点自身含：
  - `id`
  - `type`
  - `config`
  - 分支节点额外含 `yes_branch` / `no_branch`
  - 循环节点额外含 `body_branch`
- 设备类节点配置 schema 见 `views/smart_production_constants.py`，当前已包含：
  - `device_name`
  - `action`
  - `output_property`
- 也就是说，画布原始结构本身已经具备“节点先后顺序”和“设备/动作配置”的基础信息，但缺少专门给后续执行使用的结构化归档层。

### 4. 回显依赖点

- 编辑回显在 `views/smart_production.py` 的 `_populate_workflow_editor()` 中，当前直接把 `workflow["workflow_detail"]` 传给 `set_workflow_detail()`。
- 列表页/表单“说明”回显依赖 `views/smart_production_utils.py` 的 `extract_workflow_description()`，当前优先从 `workflow_params.description` 和 `conditions.description` 读取。
- 如果直接改写 `workflow_detail` 或完全迁移“说明”字段，不补兼容读取，现有编辑和列表展示会退化。

### 5. 数据库脚本现状

- `SQL/workflow.sql` 已定义以下目标字段：
  - `workflow_detail`：流程详情 JSON
  - `enable_or_not`：是否启用
  - `info`：说明
- `init.sql` 中的 `workflow` 表结构仍未包含 `enable_or_not` 和 `info`，与 `SQL/workflow.sql` 不一致。

## Proposed Changes

### 1. 调整工作流 payload 字段白名单与映射

文件：`/home/pi/project/hmi/services/device_service.py`

- 将 `info` 加入 `self.workflow_fields`，确保服务层不会过滤掉该字段。
- 调整 `_normalize_workflow_payload()`：
  - 保留 `enabled -> enable_or_not` 兼容。
  - 删除或停用 `description -> conditions` 的旧映射，避免“说明”再误写到 `conditions`。
  - 为 `info` 增加字符串兜底处理，保证提交值稳定为字符串或不传。
  - 继续保留 `workflow_params` / `workflow_detail` / `conditions` 的 JSON 对象校验逻辑。
- 目标结果：界面层显式传入的 `info`、`enable_or_not`、`workflow_detail` 可无损提交到 `/api/v1/workflows`。

### 2. 在界面层改为按新字段收集和回显“说明”

文件：`/home/pi/project/hmi/views/smart_production.py`

- 修改 `_collect_workflow_payload()`：
  - `workflow_params` 保持现状，继续仅承载当前草稿等既有参数。
  - 不再写入 `workflow_params.description`。
  - 新增 `info: description`。
  - `enable_or_not` 继续沿用当前逻辑：
    - 草稿保存时强制为 `0`
    - 正常保存时根据“开启/禁用”单选框写入 `1/0`
- 修改 `_populate_workflow_editor()`：
  - “说明”回显优先读取 `info`。
  - 若旧数据没有 `info`，再回退到旧兼容提取逻辑。
- 修改列表展示相关逻辑：
  - 继续使用统一的描述提取函数，但让其优先读取 `info`，兼容旧字段。

### 3. 为 `workflow_detail` 建立双层结构

文件：
- `/home/pi/project/hmi/views/smart_production.py`
- `/home/pi/project/hmi/views/smart_production_utils.py`

- 在保存前新增一个“详情构造”步骤，把当前画布原始结构包装为双层 JSON。
- 推荐目标结构：

```json
{
  "version": 2,
  "canvas": {
    "version": 1,
    "sequence": []
  },
  "execution": {
    "nodes": [],
    "root_sequence": [],
    "meta": {
      "node_count": 0
    }
  }
}
```

- 其中：
  - `canvas`：原样保留当前 `WorkflowCanvasEditor.get_workflow_detail()` 的返回值，用于编辑器直接回显。
  - `execution`：新增结构化执行视图，用于明确保存：
    - 节点先后顺序
    - 节点类型
    - 分支/循环关系
    - 设备配置
    - 执行动作
    - 输出动作
    - 判断/等待/消息等节点配置

### 4. 设计 `execution` 归一化规则

文件：`/home/pi/project/hmi/views/smart_production_utils.py`

- 新增一个专门的构造函数，例如：
  - `build_workflow_detail_payload(canvas_detail)`
  - `build_execution_snapshot(canvas_detail)`
- 采用递归遍历 `sequence` / `yes_branch` / `no_branch` / `body_branch` 的方式，把树形画布结构转换为结构化节点列表。
- 每个结构化节点建议包含：
  - `node_id`
  - `node_type`
  - `order`
  - `parent_node_id`
  - `branch_key`
  - `config`
  - `device_config`
  - `execute_action`
  - `output_action`
- 建议归一化字段规则：
  - `device_config`：
    - 对设备类节点，从 `config.device_name`、必要时补充设备类别/显示名称
  - `execute_action`：
    - 取 `config.action`
  - `output_action`：
    - 取 `config.output_property`
  - `config`：
    - 保留原节点配置全文，避免信息损失
  - `order`：
    - 表示同一序列中的相对顺序
  - `parent_node_id + branch_key`：
    - 表示节点属于根序列、判断 `yes/no` 分支还是循环体
- `execution.root_sequence` 建议保存根层节点 ID 顺序，便于后续执行器快速定位主链路。
- `execution.meta.node_count` 保存总节点数，便于校验。

### 5. 兼容旧数据读取，避免编辑回显中断

文件：
- `/home/pi/project/hmi/views/smart_production.py`
- `/home/pi/project/hmi/views/smart_production_utils.py`
- `/home/pi/project/hmi/services/device_service.py`

- 读取 `workflow_detail` 时兼容两种格式：
  - 旧格式：`{"version": 1, "sequence": [...]}`
  - 新格式：`{"version": 2, "canvas": {...}, "execution": {...}}`
- 编辑器回显时：
  - 若存在 `workflow_detail.canvas`，传 `canvas`
  - 否则直接传旧版 `workflow_detail`
- 避免一次上线后旧流程无法编辑。

### 6. 同步补齐领域模型与初始化脚本定义

文件：
- `/home/pi/project/hmi/domain/workflow.py`
- `/home/pi/project/hmi/init.sql`
- 可选：`/home/pi/project/hmi/API文档.md`

- `domain/workflow.py` 补充缺失的字段定义：
  - `enable_or_not`
  - `info`
- `init.sql` 中的 `workflow` 表结构应与 `SQL/workflow.sql` 对齐，补上：
  - `enable_or_not`
  - `info`
- `API文档.md` 中工作流创建/更新请求体示例同步更新，体现：
  - `info`
  - `enable_or_not`
  - 新版 `workflow_detail` 结构

## Assumptions & Decisions

- 本次只规划 HMI 仓库内可见的前端/客户端代码与随仓 SQL/文档，不假设后端仓库会同步自动适配。
- 假设后端 `/api/v1/workflows` 接口在字段透传层面可接受新增的 `info`，或后续将按该字段接入。
- `workflow_params` 保持现状，不借本次需求重定义其业务含义。
- `conditions` 保持现状，不借本次需求扩展工况语义。
- “说明”字段业务来源仍为基础属性页中的 `workflow_description_input`。
- `workflow_detail.execution` 的设计目标是“结构清晰且不丢原始数据”，因此采用“保留 canvas + 追加 execution”而不是彻底替换旧结构。

## Verification Steps

### 代码级验证

- 检查 `SmartProduction._collect_workflow_payload()` 输出：
  - 包含 `info`
  - 不再写 `workflow_params.description`
  - `enable_or_not` 值正确
  - `workflow_detail` 为双层结构
- 检查 `DeviceService._normalize_workflow_payload()`：
  - 不过滤 `info`
  - 不再把 `description` 映射到 `conditions`
  - JSON 字段校验不破坏新版 `workflow_detail`

### 交互级验证

- 新建流程，填写：
  - 名称
  - 启动状态
  - 说明
  - 远程控制画布若干节点
- 点击“保存”后确认请求体中：
  - `enable_or_not` 正确
  - `info` 为说明文本
  - `workflow_detail.canvas` 包含原始画布
  - `workflow_detail.execution` 包含结构化节点信息
- 再次进入编辑页，确认：
  - 说明正常回显
  - 启动状态正常回显
  - 画布节点顺序与配置正常回显

### 兼容性验证

- 读取旧流程数据（仅有旧版 `workflow_detail`、说明可能在 `workflow_params.description`）：
  - 列表页说明仍可显示
  - 编辑页仍可正常打开并回显

### 文档/脚本一致性验证

- 确认 `SQL/workflow.sql` 与 `init.sql` 的 `workflow` 表字段一致。
- 确认 `API文档.md` 与实际 payload 设计一致。
