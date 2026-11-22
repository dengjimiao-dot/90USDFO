# 90USDFO 服务端源码

90USDFO 项目源码，包含游戏服务端、GM 管理后台、玩家登录器和组队中继。

[查看项目修改记录](CHANGELOG.md)。

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

## 本地运行所需资源

- 游戏服务端需要自行准备兼容客户端、PVF 和本地 SQLite 数据库。用 `USDOF_CLIENT_DIR`、`USDOF_PVF_PATH`、`USDOF_SQLITE_DB` 指向自己的测试资源。运行 `python -B server_proto/start.py --help` 查看监听端口与启动参数。原生模块的构建要求见 [计算模块](server_proto/native_core/README.md) 和 [PVF 模块](server_proto/pvf/native/README.md)。
- GM 管理服务可用 `gmserver.exe -init -config <本地配置路径>` 生成初始配置。组队中继通过 `-config <本地配置路径>` 读取独立的服务配置，并需要本地 TLS 材料。
- 游戏客户端、素材、发布产物和正式服私有配置由各使用方管理。实际联机依赖配套运行资源。

## 许可证

项目许可证待定。Go 第三方依赖见各模块的 `go.mod`，其各自的许可证继续适用。
