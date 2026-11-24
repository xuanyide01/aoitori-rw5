using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

class CheckStandVsUpClean {
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
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);
        var chdirStr = vfsType.GetMethod("ChDir", new[] { typeof(string) });
        var chdirEntry = vfsType.GetMethod("ChDir", new[] { entryType });
        var find = vfsType.GetMethod("FindFile", new[] { typeof(string) });
        var openImg = vfsType.GetMethod("OpenImage", new[] { entryType });

        string packRoot = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack";
        chdirStr.Invoke(null, new object[] { packRoot });

        var byPack = new[] {
            new { arc = "stand.cpz",   files = new[] { new[] { @"01_メアリー\st-mr_a101.pb3", "st_mr_101.png" }, new[] { @"01_メアリー\st-mr_a102.pb3", "st_mr_102.png" } } },
            new { arc = "up.cpz",      files = new[] { new[] { @"01_メアリー\up-mr_a101.pb3", "up_mr_101.png" }, new[] { @"01_メアリー\up-mr_a102.pb3", "up_mr_102.png" } } },
            new { arc = "balloon.cpz", files = new[] { new[] { @"01_メアリー\fk1-mr_a101.pb3", "fk_mr_101.png" }, new[] { @"01_メアリー\fk1-mr_a102.pb3", "fk_mr_102.png" } } },
            new { arc = "bg.cpz",      files = new[] { new[] { @"pb3\bg010a.pb3", "bg010a.png" } } },
        };

        foreach (var grp in byPack) {
            var arcEntry = find.Invoke(null, new object[] { grp.arc });
            chdirEntry.Invoke(null, new object[] { arcEntry });
            foreach (var f in grp.files) {
                var entry = find.Invoke(null, new object[] { f[0] });
                using (var decoder = (IDisposable)openImg.Invoke(null, new object[] { entry })) {
                    var imgData = decoder.GetType().GetProperty("Image").GetValue(decoder);
                    var w = imgData.GetType().GetProperty("Width").GetValue(imgData);
                    var h = imgData.GetType().GetProperty("Height").GetValue(imgData);
                    var bpp = imgData.GetType().GetProperty("BPP").GetValue(imgData);
                    var outP = Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", f[1]);
                    using (var ofs = File.Create(outP)) {
                        pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, imgData });
                    }
                    Console.WriteLine(string.Format("{0}/{1} -> {2}x{3} {4}bpp", grp.arc, f[0], w, h, bpp));
                }
            }
            chdirStr.Invoke(null, new object[] { ".." });
        }
    }
}
