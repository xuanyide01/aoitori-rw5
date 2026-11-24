using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class TestJbpFrame {
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
        // Check JbpFormat / MvDecoder / ImageFormat on extracted op.cmv frame 30 and 240
        foreach (var fmt in (IEnumerable)catalogType.GetProperty("ImageFormats").GetValue(catalog)) {
            if (fmt.GetType().Name.Contains("Jbp") || fmt.GetType().Name.Contains("Cmv") || fmt.GetType().FullName.Contains("Purple")) {
                Console.WriteLine("ImageFmt: " + fmt.GetType().FullName);
            }
        }
        var mvType = arcFormats.GetType("GameRes.Formats.Purple.MvDecoder");
        var cmvPath = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\video\op.cmv";
        using (var fs = File.OpenRead(cmvPath))
        using (var br = new BinaryReader(fs)) {
            br.ReadBytes(4);
            uint resOff = br.ReadUInt32();
            br.ReadUInt32(); br.ReadUInt32();
            uint maxSeq = br.ReadUInt32();
            uint fps = br.ReadUInt32();
            foreach (uint fid in new uint[] { 0, 30, 100, 240, 2914 }) {
                fs.Seek(44 + fid * 20, SeekOrigin.Begin);
                uint seq = br.ReadUInt32(), csz = br.ReadUInt32(), usz = br.ReadUInt32(), rtype = br.ReadUInt32(), foff = br.ReadUInt32();
                fs.Seek(resOff + foff, SeekOrigin.Begin);
                byte[] buf = br.ReadBytes((int)csz);
                Console.WriteLine(string.Format("Frame {0}: csz={1} usz={2} rtype={3} hdr={4}",
                    fid, csz, usz, rtype, BitConverter.ToString(buf, 0, Math.Min(48, buf.Length))));
                // Try GARbro BinaryStream + ImageFormat.Read!
                try {
                    var bs = Activator.CreateInstance(gameRes.GetType("GameRes.BinaryStream"), new object[] { new MemoryStream(buf), "f.jbp", false });
                    var imgFmt = gameRes.GetType("GameRes.ImageFormat");
                    var imgData = imgFmt.GetMethod("Read").Invoke(null, new object[] { bs });
                    Console.WriteLine("  GARbro ImageFormat.Read -> " + (imgData != null ? imgData.GetType().Name : "null"));
                } catch (Exception ex) {
                    Console.WriteLine("  GARbro err: " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
                }
            }
        }
    }
}
