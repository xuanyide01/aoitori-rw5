using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class TestLonginusAndJbp {
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
        var unpackPs2 = cpzOpenerType.GetMethod("UnpackPs2", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);

        var rawDir = @"E:\Antigravity\aoitori-rw5\probe\longinus_raw";
        var decDir = @"E:\Antigravity\aoitori-rw5\probe\longinus_ps3";
        Directory.CreateDirectory(decDir);
        int ok = 0, fail = 0;
        foreach (var f in Directory.GetFiles(rawDir, "*.ps3")) {
            var raw = File.ReadAllBytes(f);
            try {
                var dec = (byte[])unpackPs2.Invoke(cpzOpener, new object[] { raw });
                File.WriteAllBytes(Path.Combine(decDir, Path.GetFileNameWithoutExtension(f) + ".bin"), dec);
                ok++;
            } catch (Exception ex) {
                if (fail < 3) Console.WriteLine("UnpackPs2 fail " + Path.GetFileName(f) + ": " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
                fail++;
            }
        }
        Console.WriteLine("Longinus UnpackPs2: ok=" + ok + ", fail=" + fail);

        // Inspect JbpReader and decode op_frame100.jbp / bg070a_frame0.jbp
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        Console.WriteLine("JbpReader ctors/methods:");
        foreach (var c in jbpType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) Console.WriteLine("  ctor: " + c);
        foreach (var m in jbpType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly)) Console.WriteLine("  meth: " + m);
        // Also check MvOpener / CmvOpener in ArcFormats
        foreach (var t in arcFormats.GetTypes().Where(t => t.Namespace == "GameRes.Formats.Purple")) {
            Console.WriteLine("  Purple type: " + t.Name);
        }
    }
}
