using System;
using System.IO;
using System.Reflection;

class TestVfsSubdir {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var catalogType = gameRes.GetType("GameRes.FormatCatalog");
        var catalog = catalogType.GetProperty("Instance").GetValue(null);
        using (var fs = File.OpenRead(Path.Combine(dir, "GameData", "Formats.dat"))) {
            catalogType.GetMethod("DeserializeScheme").Invoke(catalog, new object[] { fs });
        }
        var vfsType = gameRes.GetType("GameRes.VFS");
        var entryType = gameRes.GetType("GameRes.Entry");
        var chdirStr = vfsType.GetMethod("ChDir", new[] { typeof(string) });
        var chdirEntry = vfsType.GetMethod("ChDir", new[] { entryType });
        var find = vfsType.GetMethod("FindFile", new[] { typeof(string) });
        var openImg = vfsType.GetMethod("OpenImage", new[] { entryType });
        var flush = vfsType.GetMethod("Flush");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);

        string dataDir = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data";
        var cases = new[] {
            new[] { Path.Combine(dataDir, "pack"), "stand.cpz", @"01_メアリー", "st-mr_a102.pb3" },
            new[] { Path.Combine(dataDir, "pack"), "up.cpz", @"01_メアリー", "up-mr_a102.pb3" },
            new[] { Path.Combine(dataDir, "image"), "event", "", "h_mr01_01b.pb3" },
            new[] { Path.Combine(dataDir, "image"), "event", "", "ev_mr01b.pb3" },
        };
        foreach (var c in cases) {
            flush.Invoke(null, null);
            chdirStr.Invoke(null, new object[] { c[0] });
            var arcE = find.Invoke(null, new object[] { c[1] });
            chdirEntry.Invoke(null, new object[] { arcE });
            if (!string.IsNullOrEmpty(c[2])) {
                var subE = find.Invoke(null, new object[] { c[2] });
                chdirEntry.Invoke(null, new object[] { subE });
            }
            var e = find.Invoke(null, new object[] { c[3] });
            using (var dec = (IDisposable)openImg.Invoke(null, new object[] { e })) {
                var img = dec.GetType().GetProperty("Image").GetValue(dec);
                var w = img.GetType().GetProperty("Width").GetValue(img);
                var h = img.GetType().GetProperty("Height").GetValue(img);
                Console.WriteLine("OK {0}/{1}: {2}x{3}", c[1], c[3], w, h);
                using (var ofs = File.Create(Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", Path.GetFileNameWithoutExtension(c[3]) + ".png"))) {
                    pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, img });
                }
            }
        }
    }
}
