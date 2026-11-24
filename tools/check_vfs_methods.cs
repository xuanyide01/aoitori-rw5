using System;
using System.IO;
using System.Linq;
using System.Reflection;

class CheckVfsMethods {
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
        foreach (var m in vfsType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static)) {
            Console.WriteLine("VFS." + m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")");
        }
        // Test OpenArchive(arc) or FindFile!
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var cpzOpenerType = arcFormats.GetType("GameRes.Formats.Purple.CpzOpener");
        object cpzOpener = null;
        foreach (var a in (System.Collections.IEnumerable)catalogType.GetProperty("ArcFormats").GetValue(catalog)) {
            if (a.GetType() == cpzOpenerType) cpzOpener = a;
        }
        var arcViewType = gameRes.GetType("GameRes.ArcView");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);

        foreach (var item in new[] {
            new[] { "stand.cpz",   @"01_メアリー\st-mr_a101.pb3", "st_mr_101.png" },
            new[] { "stand.cpz",   @"01_メアリー\st-mr_a102.pb3", "st_mr_102.png" },
            new[] { "up.cpz",      @"01_メアリー\up-mr_a101.pb3", "up_mr_101.png" },
            new[] { "up.cpz",      @"01_メアリー\up-mr_a102.pb3", "up_mr_102.png" },
            new[] { "balloon.cpz", @"01_メアリー\fk1-mr_a101.pb3", "fk_mr_101.png" },
            new[] { "balloon.cpz", @"01_メアリー\fk1-mr_a102.pb3", "fk_mr_102.png" },
        }) {
            var arcPath = Path.Combine(@"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack", item[0]);
            // VFS.EnterArchive(ArcFile) or ChDir
            using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { arcPath }))
            using (var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view })) {
                var fsObj = arc.GetType().GetMethod("CreateFileSystem").Invoke(arc, null);
                var pushFs = vfsType.GetMethod("PushFileSystem", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
                if (pushFs == null) {
                    // Check Top setter
                    var topProp = vfsType.GetProperty("Top");
                    Console.WriteLine("Top prop: " + topProp);
                }
                var find = fsObj.GetType().GetMethod("FindFile", new[] { typeof(string) });
                // Set VFS.Top? No, let's see VFS methods first!
                break;
            }
        }
    }
}
