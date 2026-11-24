using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class UnpackAllPs3AndTestPb3 {
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

        // 1. Unpack all 86 .ps3 files to probe/ps3/
        var ps3OutDir = @"E:\Antigravity\aoitori-rw5\probe\ps3";
        Directory.CreateDirectory(ps3OutDir);
        var unpackPs2 = cpzOpenerType.GetMethod("UnpackPs2", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);
        var codeDir = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\code";
        int count = 0;
        foreach (var f in Directory.GetFiles(codeDir, "*.ps3")) {
            var raw = File.ReadAllBytes(f);
            var dec = (byte[])unpackPs2.Invoke(cpzOpener, new object[] { raw });
            File.WriteAllBytes(Path.Combine(ps3OutDir, Path.GetFileNameWithoutExtension(f) + ".bin"), dec);
            count++;
        }
        Console.WriteLine("Unpacked PS3 count: " + count);

        // 2. Also unpack ps.cpz (3 files) to probe/ps_cpz/
        var psCpzOut = @"E:\Antigravity\aoitori-rw5\probe\ps_cpz";
        Directory.CreateDirectory(psCpzOut);
        var arcViewType = gameRes.GetType("GameRes.ArcView");
        var extractMethod = cpzOpenerType.GetMethod("Extract");
        using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack\ps.cpz" }))
        using (var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view })) {
            var entries = (IEnumerable)arc.GetType().GetProperty("Dir").GetValue(arc);
            foreach (var entry in entries) {
                var name = (string)entry.GetType().GetProperty("Name").GetValue(entry);
                var outPath = Path.Combine(psCpzOut, name);
                using (var s = (Stream)cpzOpenerType.GetMethod("OpenEntry").Invoke(cpzOpener, new object[] { arc, entry }))
                using (var ofs = File.Create(outPath)) {
                    s.CopyTo(ofs);
                }
                Console.WriteLine("Extracted ps.cpz/" + name);
            }
        }

        // 3. Test PB3 via DecryptPb3 + Pb3Format, AND test opening PB3 inside bg.cpz via CpzOpener.OpenImage!
        var pb3FormatType = arcFormats.GetType("GameRes.Formats.Purple.Pb3Format");
        object pb3Format = null;
        foreach (var f in (IEnumerable)catalogType.GetProperty("ImageFormats").GetValue(catalog)) {
            if (f.GetType() == pb3FormatType) pb3Format = f;
        }
        var binStreamType = gameRes.GetType("GameRes.BinaryStream");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);
        var decryptPb3 = cpzOpenerType.GetMethod("DecryptPb3", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);

        var pb3Test = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\event\h_mr01_01r.pb3";
        try {
            var rawPb3 = File.ReadAllBytes(pb3Test);
            var decPb3 = (byte[])decryptPb3.Invoke(cpzOpener, new object[] { rawPb3 });
            Console.WriteLine("DecryptPb3 returned len=" + (decPb3 == null ? -1 : decPb3.Length));
            if (decPb3 != null) {
                using (var ms = new MemoryStream(decPb3))
                using (var bs = (IDisposable)Activator.CreateInstance(binStreamType, new object[] { ms, pb3Test, false })) {
                    var meta = pb3FormatType.GetMethod("ReadMetaData").Invoke(pb3Format, new object[] { bs });
                    bs.GetType().GetProperty("Position").SetValue(bs, 0L);
                    var img = pb3FormatType.GetMethod("Read").Invoke(pb3Format, new object[] { bs, meta });
                    using (var ofs = File.Create(@"E:\Antigravity\aoitori-rw5\probe\h_mr01_01r.png")) {
                        pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, img });
                    }
                    Console.WriteLine("PB3 DecryptPb3 + Read OK!");
                }
            }
        } catch (Exception ex) {
            Console.WriteLine("PB3 DecryptPb3 ERR: " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
        }

        // Test OpenImage on bg.cpz first entry
        try {
            using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack\bg.cpz" }))
            using (var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view })) {
                var firstEntry = ((IEnumerable)arc.GetType().GetProperty("Dir").GetValue(arc)).Cast<object>().First(e => ((string)e.GetType().GetProperty("Name").GetValue(e)).EndsWith(".pb3"));
                Console.WriteLine("Testing OpenImage on bg.cpz/" + firstEntry.GetType().GetProperty("Name").GetValue(firstEntry));
                var decoder = (IDisposable)cpzOpenerType.GetMethod("OpenImage").Invoke(cpzOpener, new object[] { arc, firstEntry });
                var imgData = decoder.GetType().GetProperty("Image").GetValue(decoder);
                using (var ofs = File.Create(@"E:\Antigravity\aoitori-rw5\probe\bg_sample.png")) {
                    pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, imgData });
                }
                Console.WriteLine("bg.cpz OpenImage OK!");
            }
        } catch (Exception ex) {
            Console.WriteLine("bg.cpz OpenImage ERR: " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
            if (ex.InnerException != null) Console.WriteLine(ex.InnerException.StackTrace);
        }
    }
}
