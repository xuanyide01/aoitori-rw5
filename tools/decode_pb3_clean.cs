using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

class DecodePb3Clean {
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
        var arcViewType = gameRes.GetType("GameRes.ArcView");
        var binStreamType = gameRes.GetType("GameRes.BinaryStream");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);

        string packRoot = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack";
        var byPack = new[] {
            new { arc = "stand.cpz",   files = new[] { new[] { @"01_メアリー\st-mr_a101.pb3", "st_mr_101.png" }, new[] { @"01_メアリー\st-mr_a102.pb3", "st_mr_102.png" } } },
            new { arc = "up.cpz",      files = new[] { new[] { @"01_メアリー\up-mr_a101.pb3", "up_mr_101.png" }, new[] { @"01_メアリー\up-mr_a102.pb3", "up_mr_102.png" } } },
            new { arc = "balloon.cpz", files = new[] { new[] { @"01_メアリー\fk1-mr_a101.pb3", "fk_mr_101.png" }, new[] { @"01_メアリー\fk1-mr_a102.pb3", "fk_mr_102.png" } } },
            new { arc = "bg.cpz",      files = new[] { new[] { @"pb3\bg010a.pb3", "bg010a.png" } } },
        };

        foreach (var grp in byPack) {
            var arcPath = Path.Combine(packRoot, grp.arc);
            using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { arcPath }))
            using (var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view })) {
                var dirEntries = ((IEnumerable)arc.GetType().GetProperty("Dir").GetValue(arc)).Cast<object>()
                    .ToDictionary(e => (string)e.GetType().GetProperty("Name").GetValue(e), StringComparer.OrdinalIgnoreCase);
                foreach (var f in grp.files) {
                    var entry = dirEntries[f[0]];
                    byte[] raw;
                    using (var s = (Stream)cpzOpenerType.GetMethod("OpenEntry").Invoke(cpzOpener, new object[] { arc, entry }))
                    using (var ms = new MemoryStream()) {
                        s.CopyTo(ms);
                        raw = ms.ToArray();
                    }
                    int t1 = BitConverter.ToUInt16(raw, 0x1c);
                    int w = BitConverter.ToUInt16(raw, 0x1e);
                    int h = BitConverter.ToUInt16(raw, 0x20);
                    int bpp = BitConverter.ToUInt16(raw, 0x22);
                    Console.WriteLine(string.Format("{0}/{1}: len={2}, type={3}, {4}x{5} {6}bpp", grp.arc, f[0], raw.Length, t1, w, h, bpp));
                    if (t1 != 6 && t1 != 8) {
                        using (var ms = new MemoryStream(raw))
                        using (var bs = (IDisposable)Activator.CreateInstance(binStreamType, new object[] { ms, f[0], false })) {
                            var meta = pb3FormatType.GetMethod("ReadMetaData").Invoke(pb3Format, new object[] { bs });
                            bs.GetType().GetProperty("Position").SetValue(bs, 0L);
                            var imgData = pb3FormatType.GetMethod("Read").Invoke(pb3Format, new object[] { bs, meta });
                            using (var ofs = File.Create(Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", f[1]))) {
                                pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, imgData });
                            }
                        }
                    } else {
                        // Print decoded base name
                        byte[] k = { 0xA6, 0x75, 0xF3, 0x9C, 0xC5, 0x69, 0x78, 0xA3, 0x3E, 0xA5, 0x4F, 0x79, 0x59, 0xFE, 0x3A, 0xC7 };
                        var nb = new List<byte>();
                        for (int i = 0; i < 0x20; i++) {
                            byte b = (byte)(raw[0x34 + i] ^ k[i & 0xf]);
                            if (b == 0) break;
                            nb.Add(b);
                        }
                        Console.WriteLine("  diff base image = " + System.Text.Encoding.GetEncoding(932).GetString(nb.ToArray()));
                    }
                }
            }
        }
    }
}
