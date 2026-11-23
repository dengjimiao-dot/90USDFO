# 90USDFO

本仓库的当前版本以 Windows x64 加密源码包分发。下载 `90USDFO-Protected.exe`，使用维护者单独保管的 `source.key` 还原源码。包内使用 AES-256-GCM 加密并验证完整性。

## 验证并还原源码

可用 PowerShell 计算下载文件的 SHA-256，并与本目录中的 `SHA256SUMS` 核对。

```powershell
Get-FileHash .\90USDFO-Protected.exe -Algorithm SHA256
.\90USDFO-Protected.exe -key-file .\source.key -verify
.\90USDFO-Protected.exe -key-file .\source.key -output .\90USDFO-source.zip
```

命令中的 `-key-file` 可填写密钥的实际保存路径。解压 `90USDFO-source.zip` 后，查看其中的 `README.md` 了解原项目的构建、配置和启动方式。还原会生成明文源码，请保存在受控目录。
