using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class TestMvDecoder {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        Run(dir);
    }

    static void Run(string dir) {
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var catalogType = gameRes.GetType("GameRes.FormatCatalog");
        var catalog = catalogType.GetProperty("Instance").GetValue(null);
        using (var fs = File.OpenRead(Path.Combine(dir, "GameData", "Formats.dat"))) {
            catalogType.GetMethod("DeserializeScheme").Invoke(catalog, new object[] { fs });
        }

        // Check MvDecoder methods & JbpFormat methods
        var jbpFmt = ((IEnumerable)catalogType.GetProperty("ImageFormats").GetValue(catalog))
            .Cast<object>().First(f => f.GetType().FullName == "GameRes.Formats.Sviu.JbpFormat");
        Console.WriteLine("JbpFormat type: " + jbpFmt.GetType());

        var mvType = arcFormats.GetType("GameRes.Formats.Purple.MvDecoder");
        foreach (var m in mvType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            Console.WriteLine("MvDecoder M: " + m);
        foreach (var f in mvType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            Console.WriteLine("MvDecoder F: " + f.FieldType.Name + " " + f.Name);

        // Test JbpFormat on frames 0, 30, 100, 240, 2914!
        var cmvPath = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\video\op.cmv";
        using (var fs = File.OpenRead(cmvPath))
        using (var br = new BinaryReader(fs)) {
            br.ReadBytes(4);
            uint resOff = br.ReadUInt32();
            br.ReadUInt32(); br.ReadUInt32(); br.ReadUInt32(); br.ReadUInt32();
            foreach (uint fid in new uint[] { 0, 30, 100, 240, 2914 }) {
                fs.Seek(44 + fid * 20, SeekOrigin.Begin);
                uint seq = br.ReadUInt32(), csz = br.ReadUInt32(), usz = br.ReadUInt32(), rtype = br.ReadUInt32(), foff = br.ReadUInt32();
                fs.Seek(resOff + foff, SeekOrigin.Begin);
                byte[] buf = br.ReadBytes((int)csz);
                try {
                    var bs = Activator.CreateInstance(gameRes.GetType("GameRes.BinaryStream"), new object[] { new MemoryStream(buf), "f.jbp", false });
                    var meta = jbpFmt.GetType().GetMethod("ReadMetaData").Invoke(jbpFmt, new object[] { bs });
                    bs.GetType().GetProperty("Position").SetValue(bs, 0L);
                    var img = jbpFmt.GetType().GetMethod("Read").Invoke(jbpFmt, new object[] { bs, meta });
                    Console.WriteLine("JbpFormat frame " + fid + ": OK " + meta.GetType().GetProperty("Width").GetValue(meta) + "x" + meta.GetType().GetProperty("Height").GetValue(meta));
                } catch (Exception ex) {
                    Console.WriteLine("JbpFormat frame " + fid + " ERR: " + (ex.InnerException != null ? ex.InnerException.GetType().Name + ": " + ex.InnerException.Message : ex.Message));
                }
            }
        }
    }
}
