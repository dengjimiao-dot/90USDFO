# GM 管理端与玩家登录器

公开源码含 Go GM 服务、Windows GM 桌面端、Go 玩家登录器与下载器，以及配套 WPF 登录器、原生启动程序和辅助桥接模块。

| 入口 | 源码 |
| --- | --- |
| Go GM 桌面端 | [gm_manager](../gm_manager) |
| Go GM 服务 | [gmserver](../gm_manager/cmd/gmserver) |
| Go 玩家登录器与下载器 | [player-launcher](../gm_manager/cmd/player-launcher)、[player-downloader](../gm_manager/cmd/player-downloader) |
| WPF 登录器与原生辅助源码 | [wpf](wpf) |
| Go 原生启动程序 | [bootstrap](bootstrap) |
| WPF 游戏辅助桥接 | [bridge](bridge) |

## Go 构建

使用 Windows 和 Go 1.26。在仓库根目录运行以下命令。

```powershell
Push-Location gm_manager
go test ./...
go build -trimpath -o ..\build\gmserver.exe ./cmd/gmserver
go build -trimpath -ldflags "-H windowsgui" -o ..\build\gm-desktop.exe .
go build -trimpath -ldflags "-H windowsgui" -o ..\build\player-launcher.exe ./cmd/player-launcher
go build -trimpath -ldflags "-H windowsgui" -o ..\build\player-downloader.exe ./cmd/player-downloader
Copy-Item app.manifest ..\build\gm-desktop.exe.manifest
Copy-Item app.manifest ..\build\player-launcher.exe.manifest
Copy-Item cmd\player-downloader\app.manifest ..\build\player-downloader.exe.manifest
Pop-Location

Push-Location player_launcher\bootstrap
go test ./...
go build -trimpath -o ..\..\build\player-bootstrap.exe ./cmd/player-bootstrap
Pop-Location
```

## WPF 构建

使用 Windows 和 .NET 8 SDK。登录器目标为 .NET 6.0.36 Windows x86。

```powershell
dotnet build player_launcher\bridge\GameAssistBridge.csproj -c Release -p:UseAppHost=false -o build\assist-bridge
$bridge = Join-Path (Get-Location) 'build\assist-bridge'
dotnet build player_launcher\wpf\DNFLogin.csproj -c Release "-p:GameAssistBridgeOutput=$bridge" -o build\wpf-launcher
```

普通构建可检查源码是否编译。制作受保护的单文件玩家版时，请设置 `ClientProtectionSecretsSource` 和既有保护工具的本机路径，并准备配套的原生辅助组件和桥接文件。受保护的游戏启动要求有效的本机构建输入。原生组件的可编辑源码位于 [wpf/Helper](wpf/Helper)。

## 本地连接

- GM 服务用 `gmserver.exe -init -config <本地配置路径>` 生成本机配置。通过 GM 桌面端填写自己的管理地址、信任证书和令牌。
- 生成玩家登录器时，在 GM 桌面端选择自己的 HTTPS 登录地址及与其匹配的公开证书。客户端会继续核验证书及更新签名。
- 登录器可以从自己的兼容客户端 `Image` 目录读取界面素材。GitHub 仓库提供源码与构建说明，游戏程序、界面素材、正式发布配置和运维脚本由部署者本地管理。
