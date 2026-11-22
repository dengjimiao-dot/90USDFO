#if PYTHON90
namespace DNFLogin.Services;

internal static partial class ClientCodeProtection
{
    internal static partial string CodeKey() =>
        throw new System.InvalidOperationException("缺少本地受保护客户端构建输入。");
}
#endif
