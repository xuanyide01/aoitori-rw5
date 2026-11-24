using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class CheckStandVsUp {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var catalogType = gameRes.GetType("GameRes.FormatCatalog");
        var catalog = catalogType.GetProperty("Instance").GetValue(null);
        using (var fs = File.OpenRead(Path.Combine(dir, "GameData", "Formats.dat"))) {
            catalogType.GetMethod("DeserializeScheme").Invoke(catalog, new object[] { fs });
        }
        var cpzOpenerType = arcFormats.GetType("GameRes.Formats.Purple.CpzOpener");
        object cpzOpener = null;
        foreach (var a in (IEnumerable)catalogType.GetProperty("ArcFormats").GetValue(catalog)) {
            if (a.GetType() == cpzOpenerType) cpzOpener = a;
        }
        var arcViewType = gameRes.GetType("GameRes.ArcView");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);

        foreach (var item in new[] {
            new[] { "stand.cpz", @"01_メアリー\st-mr_a101.pb3", "st_mr_base.png" },
            new[] { "stand.cpz", @"01_メアリー\st-mr_a102.pb3", "st_mr_diff.png" },
            new[] { "up.cpz",    @"01_メアリー\up-mr_a101.pb3", "up_mr_base.png" },
            new[] { "up.cpz",    @"01_メアリー\up-mr_a102.pb3", "up_mr_diff.png" },
            new[] { "balloon.cpz", @"01_メアリー\fk1-mr_a101.pb3", "fk_mr_base.png" },
        }) {
            var path = Path.Combine(@"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack", item[0]);
            using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { path }))
            using (var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view })) {
                var entry = ((IEnumerable)arc.GetType().GetProperty("Dir").GetValue(arc)).Cast<object>()
                    .First(e => ((string)e.GetType().GetProperty("Name").GetValue(e)) == item[1]);
                var decoder = (IDisposable)cpzOpenerType.GetMethod("OpenImage").Invoke(cpzOpener, new object[] { arc, entry });
                using (decoder) {
                    var imgData = decoder.GetType().GetProperty("Image").GetValue(decoder);
                    var w = imgData.GetType().GetProperty("Width").GetValue(imgData);
                    var h = imgData.GetType().GetProperty("Height").GetValue(imgData);
                    var bpp = imgData.GetType().GetProperty("BPP").GetValue(imgData);
                    var outP = Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", item[2]);
                    using (var ofs = File.Create(outP)) {
                        pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, imgData });
                    }
                    Console.WriteLine(string.Format("{0}/{1} -> {2}x{3} {4}bpp", item[0], item[1], w, h, bpp));
                }
            }
        }
    }
}
