using System;
using System.IO;
using System.Reflection;

class TestDirectChdir {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        try {
            Run(dir);
        } catch (Exception ex) {
            Console.WriteLine("TOP ERR: " + ex.GetType() + ": " + ex.Message);
            if (ex.InnerException != null) Console.WriteLine("INNER: " + ex.InnerException.GetType() + ": " + ex.InnerException.Message);
        }
    }

    static void Run(string dir) {
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

        string packRoot = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack";
        foreach (var item in new[] {
            new[] { "stand.cpz", @"01_メアリー", "st-mr_a101.pb3" },
            new[] { "stand.cpz", @"01_メアリー", "st-mr_a102.pb3" },
            new[] { "up.cpz", @"01_メアリー", "up-mr_a102.pb3" },
        }) {
            try {
                flush.Invoke(null, null);
                chdirStr.Invoke(null, new object[] { packRoot });
                var arcE = find.Invoke(null, new object[] { item[0] });
                chdirEntry.Invoke(null, new object[] { arcE });
                chdirStr.Invoke(null, new object[] { item[1] });
                var e = find.Invoke(null, new object[] { item[2] });
                using (var dec = (IDisposable)openImg.Invoke(null, new object[] { e })) {
                    var img = dec.GetType().GetProperty("Image").GetValue(dec);
                    var w = img.GetType().GetProperty("Width").GetValue(img);
                    var h = img.GetType().GetProperty("Height").GetValue(img);
                    Console.WriteLine("OK {0}/{1} -> {2}x{3}", item[0], item[2], w, h);
                }
            } catch (Exception ex) {
                Console.WriteLine("FAIL {0}: {1} -> {2}", item[2], ex.Message, ex.InnerException != null ? ex.InnerException.Message : "");
            }
        }
    }
}
