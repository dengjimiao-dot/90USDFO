# 90USDFO 运行版

[下载 Windows 运行版](https://github.com/jiaoziyu0008/90USDFO/releases/tag/runtime-20261123)。下载 ZIP 并解压完整目录后按下面操作。

此分支提供 Windows 运行文件。服务端业务编译为原生扩展，并以 AES-256-GCM 保存于 `server.runtime`。启动程序自动校验并加载编译产物。GM、组队中继及登录器提供混淆后的程序。`SHA256SUMS` 记录发行文件的摘要。

## 准备

- Windows x64 和 CPython **3.12.10 x64**。
- 准备配套游戏客户端、角色初始技能配置 `initial_skills_by_job.json`、服务端 `Script.pvf`、已初始化的兼容 SQLite 游戏库和玩家端 HTTPS 证书。请使用自己的数据与证书。
- GM 生成原版玩家登录器时，需要本地配套的受保护模板、保护证明及运行库。`wpf-template` 内为混淆后的 WPF 通用组件，使用 .NET Desktop Runtime 6.0.36 x86。

## 启动

把示例路径和 IP 换成自己的。建议用绝对路径。

```powershell
$env:USDOF_CLIENT_DIR = Join-Path (Get-Location) 'runtime\client'
$env:USDOF_PVF_PATH = Join-Path (Get-Location) 'runtime\server\Script.pvf'
$env:USDOF_SQLITE_DB = Join-Path (Get-Location) 'runtime\db\game.sqlite3'
$env:USDOF_INITIAL_SKILLS_JSON = Join-Path (Get-Location) 'runtime\server\initial_skills_by_job.json'
.\90USDFO-Server.exe -- --host 0.0.0.0 --advertise-host 192.168.1.50 --control-host 127.0.0.1
```

可通过 `-python` 指定解释器。另开 PowerShell 执行 `.\90USDFO-Server.exe -prepare` 可取得本次服务端运行目录。

首次运行 GM 时执行以下命令。

```powershell
$cfg = Join-Path (Get-Location) 'runtime\private\go-manager.json'
.\bin\gmserver.exe -init -config $cfg
```

编辑配置中的 `server_root`、`control_endpoint_file` 和 `game_database`。控制文件在上一步打印的服务端目录下 `log\control_endpoint.json`。启用 `direct_database` 时填写服务端使用的同一个 SQLite 游戏库。如需开启玩家 HTTPS，设置 `launcher_listen`、`launcher_public_host`、`launcher_certificate` 和 `launcher_key`。保存后运行 `.\bin\gmserver.exe -config $cfg`，用 `bin\gm-desktop.exe` 连接本机管理服务。

中继使用 `.\bin\party-relay.exe -config <配置文件路径>`。配置包含 `listen`、`tls_certificate`、`tls_private_key` 和 `control_key_file`。控制密钥文件使用本机生成的 32 字节随机值。

## 玩家连接

在登录器里配置玩家可访问的 HTTPS 地址，并使用匹配的公开证书。按实际配置开放频道、游戏和玩家 HTTPS 端口。GM 管理和服务端控制端口留在本机。把配套登录器与客户端一起分发。