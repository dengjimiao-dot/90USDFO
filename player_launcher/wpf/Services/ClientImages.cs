using System.IO;
using System.Windows.Markup;
using System.Windows.Media.Imaging;

namespace DNFLogin.Services;

public sealed class PlayerNotice {
 public string Title {get;set;}="";
 public string NoticeDate {get;set;}="";
}

// Assets belong to the client, never the managed cache or current directory.
public static class ClientImages {
 public static string DirectoryPath => Path.Combine(PythonLauncherPaths.LauncherDirectory,"Image");
 public static BitmapImage? Read(string name,int width=0) {
  if(string.IsNullOrWhiteSpace(name)||Path.GetFileName(name)!=name)return null;
  return ReadFile(Path.Combine(DirectoryPath,name),width);
 }
 public static BitmapImage? ReadFile(string path,int width=0) {
  try {
   var info=new FileInfo(path);if(!info.Exists||info.Length>64*1024*1024)return null;
   using var input=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);
   var bitmap=new BitmapImage();bitmap.BeginInit();bitmap.CacheOption=BitmapCacheOption.OnLoad;
   if(width>0)bitmap.DecodePixelWidth=width;
   bitmap.StreamSource=input;bitmap.EndInit();bitmap.Freeze();return bitmap;
  }catch{return null;}
 }
 public static IEnumerable<string> BackgroundFiles() {
  if(!Directory.Exists(DirectoryPath))return Array.Empty<string>();
  try {
   var files=Directory.GetFiles(DirectoryPath);
   return files.Where(p=>Path.GetFileName(p).Equals("default-bg-img.png",StringComparison.OrdinalIgnoreCase)
    ||Path.GetFileName(p).StartsWith("RotatingBackground",StringComparison.OrdinalIgnoreCase))
    .Where(p=>new[]{".png",".jpg",".jpeg",".bmp"}.Contains(Path.GetExtension(p).ToLowerInvariant()))
    .OrderBy(p=>Path.GetFileName(p).Equals("default-bg-img.png",StringComparison.OrdinalIgnoreCase)?0:1)
    .ThenBy(Path.GetFileName,StringComparer.OrdinalIgnoreCase).ToArray();
  }catch{return Array.Empty<string>();}
 }
}

[MarkupExtensionReturnType(typeof(BitmapImage))]
public sealed class ClientImageExtension:MarkupExtension {
 public string Name {get;set;}="";
 public ClientImageExtension(){}
 public ClientImageExtension(string name){Name=name;}
 public override object? ProvideValue(IServiceProvider serviceProvider)=>ClientImages.Read(Name);
}
