# 动态下拉框数据源改造计划

## 1. 概述 (Summary)
将智能生产模块中设备节点弹窗的下拉框（选择设备、执行动作、输出属性）由目前的本地硬编码静态数据，改造为从 API 接口动态获取。下拉框将根据选择的设备类型自动筛选设备实例，并根据选中的设备实例自动拉取对应的设备动作表。

## 2. 当前状态分析 (Current State Analysis)
- **静态配置**: 目前 `/workspace/views/smart_production_constants.py` 中的 `NODE_SCHEMAS` 包含了硬编码的 `options`（如 `["螺旋输送机-01", "螺旋输送机-02"]`）。
- **前端渲染**: `/workspace/views/smart_production_dialogs.py` 中的 `WorkflowNodeConfigDialog` 仅支持渲染静态的 `QComboBox`。
- **接口支持**: 接口文档 `/workspace/API文档.md` 已有 `GET /api/v1/devices` 和 `GET /api/v1/device-actions`，但获取设备的接口当前不支持直接根据“类别”或“关键字”过滤。

## 3. 具体修改方案 (Proposed Changes)

### 3.1 修改 `views/smart_production_constants.py`
将所有设备类型（如 `screw_conveyor`, `belt_conveyor` 等）在 `NODE_SCHEMAS` 中的配置项改造为动态标识：
- `device_name` 字段：移除 `options`，增加 `"dynamic_source": "device_instance"`。
- `action` 字段：移除 `options`，增加 `"dynamic_source": "device_action"`。
- `output_property` 字段：移除 `options`，增加 `"dynamic_source": "device_action"`。

### 3.2 修改 `views/smart_production_dialogs.py`
为避免网络请求阻塞 PyQt UI 线程，需实现异步数据加载：
1. **新增 `ApiFetcher(QThread)` 类**: 封装 `requests` 调用，负责在后台线程请求 API，并通过 `pyqtSignal` 将数据或错误传回主线程。
2. **改造 `_create_field_widget`**: 识别 `dynamic_source` 字段，若存在则初始化 `QComboBox` 为不可用状态，并添加 "加载中..." 提示。
3. **实现 `_load_dynamic_data` 方法**:
   - 在弹窗初始化时调用，发起 `GET /api/v1/devices?size=200` 请求。
   - 数据返回后，在前端使用 `NODE_LIBRARY[self.node_type]["label"]`（如"螺旋输送机"）对 `device_name` 或 `device_category` 进行过滤筛选。
   - 将过滤后的设备名称填入 `device_name` 下拉框，并在内部维护一个 `device_name -> device_id` 的映射字典（以兼容原有的 `get_config()` 直接读取文本的逻辑）。
4. **实现级联加载 `_on_device_changed`**:
   - 监听 `device_name` 下拉框的 `currentIndexChanged` 信号。
   - 当设备切换时，通过映射字典获取 `device_instance_id`，发起 `GET /api/v1/device-actions?device_instance_id={id}` 请求。
   - 请求完成后，提取 `action_name`，刷新并激活 `action` 和 `output_property` 下拉框。
   - 在加载过程中注意恢复用户上次保存的配置值（`node_config` 中的回显）。

### 3.3 修改 `API文档.md` (设计新接口能力)
为提升获取设备的效率，在 API 文档的 `GET /api/v1/devices` 中设计新增查询参数：
- 增加 `keyword`: 按设备名称或设备编号模糊搜索。
- 增加 `device_category`: 按设备类别精确筛选。
*(注：由于后端代码不在本工程内，前端代码先通过 `size=200` 并辅以本地过滤来实现，文档中记录新设计的参数供后端后续支持)*。

## 4. 假设与决策 (Assumptions & Decisions)
- **兼容性**: 弹窗配置最终通过 `get_config()` 收集表单数据。为不破坏已有流程，下拉框的实际值（Value）仍然保存为中文名称（如 "螺旋输送机-01", "启动"），而不是对应的 ID。通过内部字典解决名称到 ID 的转换问题。
- **异步处理**: 使用 `QThread` 替代同步的 `requests.get`，确保在网络不佳时弹窗不会出现界面卡死 (ANR)。

## 5. 测试验证 (Verification Steps)
1. 启动应用并进入智能生产页面，拖拽一个“螺旋输送机”节点并双击打开配置弹窗。
2. 观察“选择设备”下拉框是否先显示“加载中...”，随后成功显示通过 API 获取的设备列表。
3. 切换设备下拉框的值，观察“执行动作”和“输出属性”是否正确级联更新为对应设备的动作列表。
4. 点击保存后再次打开弹窗，验证上次选中的设备和动作是否能正确回显。