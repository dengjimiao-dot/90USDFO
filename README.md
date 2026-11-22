# 90USDFO 服务端源码

90USDFO 项目源码，包含游戏服务端、GM 管理后台、玩家登录器和组队中继。

[搭建与联网](#搭建与联网) · [更新概要](#更新概要)

| 目录 | 内容 |
| --- | --- |
| `server_proto/` | Python 服务端、协议处理、玩法逻辑、SQLite 迁移和测试 |
| `server_proto/native_core/` | 服务端原生计算模块 |
| `server_proto/pvf/native/` | PVF 原生读取模块 |
| `server_proto/start/native_launcher/` | 本地会话启动辅助程序 |
| `gm_manager/` | Go GM 服务、桌面端、玩家登录器及下载器 |
| `player_launcher/` | WPF 登录器、原生启动程序及辅助桥接 |
| `party_relay/` | Go 组队中继和边缘节点服务 |
| `server-pack-win10/` | Windows 运行目录和启动相关辅助源码 |

[GM 后台与登录器构建及本地配置](player_launcher/README.md)。

## 搭建与联网

### 1. 准备什么

- Windows x64、Python **3.12.10 x64** 和 Go **1.26**。按 [原生 PVF 模块说明](server_proto/pvf/native/README.md) 构建模块，并将 `usdof_pvf_native.cp312-win_amd64.pyd` 放在 `server_proto`。
- 自己准备版本配套的游戏客户端、服务端和客户端的 `Script.pvf`、已初始化的兼容 SQLite 游戏库，以及 [配套登录器模板和运行库](player_launcher/README.md)。
- 准备玩家 HTTPS 的 RSA 2048 位以上证书和私钥。证书必须匹配玩家要访问的域名或 IP。

### 2. 怎么启动

在仓库根目录打开 PowerShell，将以下路径和示例 IP 换成自己的。局域网用内网 IPv4，公网用公网 IPv4。

```powershell
$serverIP = '192.168.1.50'
$env:USDOF_CLIENT_DIR = Join-Path (Get-Location) 'runtime\client'
$env:USDOF_PVF_PATH = Join-Path (Get-Location) 'runtime\server\Script.pvf'
$env:USDOF_SQLITE_DB = Join-Path (Get-Location) 'runtime\db\game.sqlite3'
python -B .\server_proto\start.py --host 0.0.0.0 --advertise-host $serverIP --control-host 127.0.0.1
```

另开终端回到仓库根目录，构建后台并生成配置。

```powershell
New-Item -ItemType Directory -Force build | Out-Null
go -C gm_manager build -o ..\build\gmserver.exe ./cmd/gmserver
$cfg = Join-Path (Get-Location) 'runtime\private\go-manager.json'
if (!(Test-Path -LiteralPath $cfg)) { .\build\gmserver.exe -init -config $cfg }
```

编辑 `go-manager.json`，保留生成的管理令牌。路径字段填实际绝对路径。

| 配置项 | 填写内容 |
| --- | --- |
| `direct_database`、`game_database` | `true`，以及 Python 使用的同一个 SQLite 游戏库 |
| `server_root`、`control_endpoint_file` | 仓库根目录，以及 Python 生成的 `server_proto/log/control_endpoint.json` |
| `launcher_listen`、`launcher_public_host` | 示例 `0.0.0.0:17443`，以及和 `--advertise-host` 一致的 IPv4 |
| `launcher_certificate`、`launcher_key` | 玩家 HTTPS 证书和私钥的路径 |

保存后运行 `.\build\gmserver.exe -config $cfg`。GM 桌面端用 `http://127.0.0.1:17890` 和管理令牌连接。

### 3. 别人怎么连

- 放行玩家 HTTPS、频道和游戏的 TCP 端口，示例为 **17443、7001、10052**。公网走路由器时把这些端口转发到服务器，额外频道和 UDP 端口按实际配置放行。GM 管理和 Python 控制接口留在本机。
- 在 GM「登录下载管理」填玩家能访问的 **HTTPS 地址**和对应的公开证书，生成玩家登录器。把配套登录器和游戏客户端一起发给对方。
- 对方解压打开登录器，注册或登录后选频道进游戏。先用另一台电脑试一次登录、选角和进城。

## 本地检查

Python 服务端的受支持环境为 Windows x64 和 CPython 3.12.10 x64。以下测试可用本地临时数据运行。

```powershell
Push-Location server_proto
$env:USDOF_NATIVE_CORE = 'off'
python -B -m unittest discover -s tests -p 'test_connection_repairs.py'
python -B -m unittest discover -s tests -p 'test_udp_effective_address.py'
Pop-Location
```

完整的 Python 联调另外依赖配套客户端、PVF 以及部分历史组队和团本测试夹具。本快照的选角回包联调还有四个已知失败用例。

GM 管理服务和组队中继是独立的 Go 模块，要求 Go 1.26。分别进入模块目录运行 `go test ./...`。

```powershell
Push-Location gm_manager
go build -o ..\build\gmserver.exe ./cmd/gmserver
Pop-Location

Push-Location party_relay
go build -o ..\build\party_relay.exe .
Pop-Location
```

## 更新概要

- 修复安徒恩、卢克团本的编队、进图、过门、重连、战况表和翻牌结算。
- 调整团本门票限购及材料扣除，修复部分任务完成条件、副本地图和材料掉落。
- 更新佣兵出战天数与奖励、永久装扮券、稀有克隆礼盒和部分装备属性。
- 修复改名卡、玩家交易和仓库整理，支持在线角色的点券余额刷新。
- GM 后台支持定时在线福利、普通 CDK 手动制码和游戏内 Coupon 兑换。
- 更新登录器、游戏内辅助和组队中继，改善客户端配对检查与联网兼容。

## 许可证

项目许可证待定。Go 第三方依赖见各模块的 `go.mod`，其各自的许可证继续适用。
