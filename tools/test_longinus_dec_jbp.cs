using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class TestLonginusDecryptAndJbp {
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
        var decryptPs2 = cpzOpenerType.GetMethod("DecryptPs2", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);
        Console.WriteLine("DecryptPs2 sig: " + decryptPs2);

        var rawDir = @"E:\Antigravity\aoitori-rw5\probe\longinus_raw";
        var decDir = @"E:\Antigravity\aoitori-rw5\probe\longinus_dec";
        Directory.CreateDirectory(decDir);
        int ok = 0, fail = 0;
        foreach (var f in Directory.GetFiles(rawDir, "*.ps3")) {
            var raw = File.ReadAllBytes(f);
            try {
                // DecryptPs2 might return byte[] or void; check!
                object res = decryptPs2.Invoke(cpzOpener, new object[] { raw });
                byte[] dec = res as byte[] ?? raw;
                File.WriteAllBytes(Path.Combine(decDir, Path.GetFileNameWithoutExtension(f) + ".bin"), dec);
                ok++;
            } catch (Exception ex) {
                Console.WriteLine("DecryptPs2 fail " + Path.GetFileName(f) + ": " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
                fail++;
            }
        }
        Console.WriteLine("Longinus DecryptPs2: ok=" + ok + ", fail=" + fail);

        // Test JbpReader on op_frame100.jbp and bg070a_frame0.jbp
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        foreach (var name in new[] { "op_frame100.jbp", "bg070a_frame0.jbp" }) {
            var p = Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", name);
            var jraw = File.ReadAllBytes(p);
            var jbp = Activator.CreateInstance(jbpType, new object[] { jraw, 24 });
            var w = (int)jbpType.GetProperty("Width").GetValue(jbp);
            var h = (int)jbpType.GetProperty("Height").GetValue(jbp);
            var stride = (int)jbpType.GetProperty("Stride").GetValue(jbp);
            var pixels = (byte[])jbpType.GetMethod("Unpack").Invoke(jbp, null);
            Console.WriteLine(string.Format("JBP {0}: {1}x{2}, stride={3}, unpacked={4} bytes", name, w, h, stride, pixels.Length));
            File.WriteAllBytes(Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", Path.GetFileNameWithoutExtension(name) + ".bgr"), pixels);
        }
    }
}
