using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class ProbeLoosePb3AndCmv {
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
        var pb3FormatType = arcFormats.GetType("GameRes.Formats.Purple.Pb3Format");
        object pb3Format = null;
        foreach (var f in (IEnumerable)catalogType.GetProperty("ImageFormats").GetValue(catalog)) {
            if (f.GetType() == pb3FormatType) pb3Format = f;
        }
        var binStreamType = gameRes.GetType("GameRes.BinaryStream");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);
        var decMethod = cpzOpenerType.GetMethod("DecryptPb3", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);

        var pb3Files = new[] {
            @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\event\h_mr01_01r.pb3",
            @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\chip\backlog.pb3",
            @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\update\ed-base.pb3",
        };
        foreach (var pf in pb3Files) {
            try {
                var raw = File.ReadAllBytes(pf);
                decMethod.Invoke(cpzOpener, new object[] { raw });
                using (var ms = new MemoryStream(raw))
                using (var bs = (IDisposable)Activator.CreateInstance(binStreamType, new object[] { ms, pf, false })) {
                    var meta = pb3FormatType.GetMethod("ReadMetaData").Invoke(pb3Format, new object[] { bs });
                    bs.GetType().GetProperty("Position").SetValue(bs, 0L);
                    var img = pb3FormatType.GetMethod("Read").Invoke(pb3Format, new object[] { bs, meta });
                    var w = meta.GetType().GetProperty("Width").GetValue(meta);
                    var h = meta.GetType().GetProperty("Height").GetValue(meta);
                    var outPath = Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", Path.GetFileNameWithoutExtension(pf) + ".png");
                    using (var ofs = File.Create(outPath)) {
                        pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, img });
                    }
                    Console.WriteLine("Loose PB3 OK: " + Path.GetFileName(pf) + " -> " + w + "x" + h);
                }
            } catch (Exception ex) {
                Console.WriteLine("Loose PB3 ERR " + Path.GetFileName(pf) + ": " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
            }
        }

        // Check MvOpener / MvDecoder on op.cmv and bg070a.cmv!
        var mvType = arcFormats.GetType("GameRes.Formats.Purple.MvDecoder");
        Console.WriteLine("MvDecoder props/methods:");
        foreach (var p in mvType.GetProperties()) Console.WriteLine("  prop: " + p);
        foreach (var m in mvType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly)) Console.WriteLine("  meth: " + m);
    }
}
