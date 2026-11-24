using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

class ProbeCmvsDecode {
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
        var pb3FormatType = arcFormats.GetType("GameRes.Formats.Purple.Pb3Format");
        var arcViewType = gameRes.GetType("GameRes.ArcView");
        var ibStreamType = gameRes.GetType("GameRes.IBinaryStream");
        var binStreamType = gameRes.GetType("GameRes.BinaryStream");

        object cpzOpener = null;
        object pb3Format = null;
        foreach (var a in (IEnumerable)catalogType.GetProperty("ArcFormats").GetValue(catalog)) {
            if (a.GetType() == cpzOpenerType) cpzOpener = a;
        }
        foreach (var f in (IEnumerable)catalogType.GetProperty("ImageFormats").GetValue(catalog)) {
            if (f.GetType() == pb3FormatType) pb3Format = f;
        }

        // 1. Inspect Aoi Tori scheme fields
        var scheme = cpzOpenerType.GetProperty("Scheme").GetValue(cpzOpener);
        var ks = (IDictionary)scheme.GetType().GetField("KnownSchemes").GetValue(scheme);
        var aoiScheme = ks["Aoi Tori"];
        Console.WriteLine("=== Aoi Tori CpzScheme ===");
        foreach (var prop in aoiScheme.GetType().GetProperties()) {
            var val = prop.GetValue(aoiScheme);
            var arr = val as Array;
            if (arr != null) {
                Console.WriteLine("  " + prop.Name + " = [" + string.Join(", ", arr.Cast<object>().Select(x => x.ToString())) + "]");
            } else {
                Console.WriteLine("  " + prop.Name + " = " + val);
            }
        }
        foreach (var fld in aoiScheme.GetType().GetFields()) {
            var val = fld.GetValue(aoiScheme);
            var arr = val as Array;
            if (arr != null) {
                Console.WriteLine("  " + fld.Name + " = [" + string.Join(", ", arr.Cast<object>().Select(x => x.ToString())) + "]");
            } else {
                Console.WriteLine("  " + fld.Name + " = " + val);
            }
        }

        // 2. Test all 5 .cpz packs
        var packs = new[] { "ps.cpz", "bg.cpz", "stand.cpz", "up.cpz", "balloon.cpz" };
        foreach (var p in packs) {
            var full = Path.Combine(@"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack", p);
            using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { full })) {
                var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view });
                if (arc == null) {
                    Console.WriteLine("FAIL TryOpen: " + p);
                    continue;
                }
                using (arc) {
                    var entries = ((IEnumerable)arc.GetType().GetProperty("Dir").GetValue(arc)).Cast<object>().ToList();
                    var samples = entries.Take(8).Select(e => e.GetType().GetProperty("Name").GetValue(e) + "(" + e.GetType().GetProperty("Size").GetValue(e) + ")");
                    Console.WriteLine(string.Format("PACK {0}: {1} entries. Samples: {2}", p, entries.Count, string.Join(", ", samples)));
                }
            }
        }

        // 3. Test PS3 decrypt/unpack
        var ps3Sample = File.ReadAllBytes(@"G:\SteamLibrary\steamapps\common\Aoi Tori\data\code\sn101.ps3");
        try {
            var unpackPs2 = cpzOpenerType.GetMethod("UnpackPs2", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);
            var dec = (byte[])unpackPs2.Invoke(cpzOpener, new object[] { ps3Sample });
            var outDir = @"E:\Antigravity\aoitori-rw5\probe";
            Directory.CreateDirectory(outDir);
            File.WriteAllBytes(Path.Combine(outDir, "sn101_unpacked.bin"), dec);
            Console.WriteLine("PS3 UnpackPs2 sn101.ps3 -> " + dec.Length + " bytes! First 32 hex: " + BitConverter.ToString(dec, 0, Math.Min(32, dec.Length)));
        } catch (Exception ex) {
            Console.WriteLine("PS3 UnpackPs2 error: " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
        }

        // 4. Test PB3 decode
        var pb3Files = new[] {
            @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\event\h_mr01_01r.pb3",
            @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\chip\backlog.pb3",
            @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\update\ed-base.pb3",
        };
        foreach (var pf in pb3Files) {
            try {
                using (var fs = File.OpenRead(pf))
                using (var bs = (IDisposable)Activator.CreateInstance(binStreamType, new object[] { fs, pf })) {
                    var meta = pb3FormatType.GetMethod("ReadMetaData").Invoke(pb3Format, new object[] { bs });
                    if (meta == null) {
                        Console.WriteLine("PB3 ReadMetaData NULL: " + Path.GetFileName(pf));
                    } else {
                        var w = meta.GetType().GetProperty("Width").GetValue(meta);
                        var h = meta.GetType().GetProperty("Height").GetValue(meta);
                        var bpp = meta.GetType().GetProperty("BPP").GetValue(meta);
                        bs.GetType().GetProperty("Position").SetValue(bs, 0L);
                        var img = pb3FormatType.GetMethod("Read").Invoke(pb3Format, new object[] { bs, meta });
                        Console.WriteLine("PB3 OK: " + Path.GetFileName(pf) + " -> " + w + "x" + h + " " + bpp + "bpp (" + img.GetType().Name + ")");
                    }
                }
            } catch (Exception ex) {
                Console.WriteLine("PB3 ERR " + Path.GetFileName(pf) + ": " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
            }
        }
    }
}
