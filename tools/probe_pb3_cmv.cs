using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class ProbePb3Cmv {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        try {
            var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
            var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));

            var catalogType = gameRes.GetType("GameRes.FormatCatalog");
            var catalog = catalogType.GetProperty("Instance").GetValue(null);
            using (var fs = File.OpenRead(Path.Combine(dir, "GameData", "Formats.dat"))) {
                catalogType.GetMethod("DeserializeScheme").Invoke(catalog, new object[] { fs });
            }

            var binStreamType = gameRes.GetType("GameRes.BinaryStream");
            var pb3FormatType = arcFormats.GetType("GameRes.Formats.Purple.Pb3Format");
            var pngFormatType = gameRes.GetType("GameRes.ImageFormat");
            var pngFmt = pngFormatType.GetProperty("Png").GetValue(null);

            object pb3Format = null;
            foreach (var f in (IEnumerable)catalogType.GetProperty("ImageFormats").GetValue(catalog)) {
                if (f.GetType() == pb3FormatType) pb3Format = f;
            }

            var pb3Files = new[] {
                @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\event\h_mr01_01r.pb3",
                @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\chip\backlog.pb3",
                @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\update\ed-base.pb3",
            };
            var outDir = @"E:\Antigravity\aoitori-rw5\probe";
            foreach (var pf in pb3Files) {
                using (var fs = File.OpenRead(pf))
                using (var bs = (IDisposable)Activator.CreateInstance(binStreamType, new object[] { fs, pf, false })) {
                    var meta = pb3FormatType.GetMethod("ReadMetaData").Invoke(pb3Format, new object[] { bs });
                    if (meta == null) {
                        Console.WriteLine("PB3 meta NULL: " + Path.GetFileName(pf));
                        continue;
                    }
                    bs.GetType().GetProperty("Position").SetValue(bs, 0L);
                    var imgData = pb3FormatType.GetMethod("Read").Invoke(pb3Format, new object[] { bs, meta });
                    var w = meta.GetType().GetProperty("Width").GetValue(meta);
                    var h = meta.GetType().GetProperty("Height").GetValue(meta);
                    var bpp = meta.GetType().GetProperty("BPP").GetValue(meta);
                    var outPng = Path.Combine(outDir, Path.GetFileNameWithoutExtension(pf) + ".png");
                    using (var ofs = File.Create(outPng)) {
                        pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, imgData });
                    }
                    Console.WriteLine("PB3 DECODED: " + Path.GetFileName(pf) + " -> " + w + "x" + h + " " + bpp + "bpp -> " + outPng);
                }
            }

            Console.WriteLine("Purple types & methods for CMV:");
            foreach (var t in arcFormats.GetTypes().Where(t => t.Namespace == "GameRes.Formats.Purple" && (t.Name.Contains("Mv") || t.Name.Contains("Cmv")))) {
                Console.WriteLine("  Type: " + t.FullName + " (base: " + t.BaseType + ")");
                foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)) {
                    Console.WriteLine("    " + m);
                }
            }
        } catch (Exception ex) {
            Console.WriteLine("ERR: " + ex.GetType().FullName + " - " + ex.Message);
            if (ex.InnerException != null) {
                Console.WriteLine("INNER: " + ex.InnerException.GetType().FullName + " - " + ex.InnerException.Message);
                Console.WriteLine(ex.InnerException.StackTrace);
            }
        }
    }
}
