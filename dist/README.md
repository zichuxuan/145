# RK3588 跨板部署说明

本目录用于把 HMI 工程打包后部署到其他 RK3588（aarch64）开发板，并支持一键启动。



## 1. 常见注意事项

- 目标板需要图形环境（默认 `DISPLAY=:0`）。
- 如果登录用户不是 `pi`，请在安装时设置 `RUN_USER`。
            你的程序默认按 pi 用户身份运行。如果你开发板上实际登录/运行桌面的用户不是 pi （比如是 ubuntu 、 root 、 rk ），安装时要手动指定。比如你的用户是 ubuntu ，就这样装：
            
            sudo RUN_USER=ubuntu RUN_GROUP=ubuntu ./deploy/install.sh --offline
        
- 如果图形环境的 `XAUTHORITY` 路径不同，请修改 `/etc/systemd/system/hmi.service` 后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart hmi.service
```

- 在tmp目录下创建hmi-release目录

## 2. 拷贝到目标板并安装

在目标板执行：

```bash
tar -xzf hmi-rk3588-*.tar.gz -C /tmp/hmi-release
cd /tmp/hmi-release
chmod +x deploy/install.sh
sudo ./deploy/install.sh
```

离线安装模式（不访问外网）：

```bash
tar -xzf hmi-rk3588-*.tar.gz -C /tmp/hmi-release
cd /tmp/hmi-release
sudo ./deploy/install.sh --offline
```

安装前一键自检（推荐）：

```bash
cd /tmp/hmi-release
./deploy/install.sh --offline --check-only
```

自检会输出并校验：

- `OS key`、`Architecture`、`Python tag`
- 将使用的离线目录（`wheels/debs`）
- 缺失系统依赖（如 `python3-venv`、`rsync`、`systemd`）
- 最终 `PASS/FAIL`

离线安装时脚本会自动识别：

- Ubuntu `20.04` / `22.04`
- 架构 `arm64/aarch64`
- Python 版本（自动选择 `py38` 或 `py310` wheel 目录）

并自动选择对应目录：

- `deploy/offline/wheels/<os_key>/<py_tag>/`
- `deploy/offline/debs/<os_key>/`

若检测到系统依赖缺失，会自动尝试从本地 `.deb` 安装。

默认安装目录是 `/opt/hmi`，默认运行用户是 `pi`。

可通过环境变量覆盖：

```bash
sudo APP_DIR=/opt/hmi RUN_USER=pi APP_NAME=hmi ./deploy/install.sh
```

离线模式也支持环境变量：

```bash
sudo OFFLINE_MODE=1 APP_DIR=/opt/hmi RUN_USER=pi APP_NAME=hmi ./deploy/install.sh
```

## 3. 一键启动

安装脚本会自动创建以下命令：

- `hmi-start`：启动服务
- `hmi-stop`：停止服务
- `hmi-status`：查看状态

系统重启后会自动拉起服务（`systemctl enable` 已完成）。



