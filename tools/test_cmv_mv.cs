using System;
using System.IO;
using System.Reflection;

class TestCmvMv {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));

        // Check what ArcFormat / VideoFormat / ImageFormat opens .cmv or uses MvDecoder / Mv2Decoder / JbpReader!
        foreach (var t in arcFormats.GetTypes()) {
            if (t.Namespace == "GameRes.Formats.Purple") {
                Console.WriteLine(t.Name + " -> base=" + (t.BaseType != null ? t.BaseType.Name : ""));
                if (t.Name.Contains("Mv") || t.Name.Contains("Jbp") || t.Name.Contains("Pb3")) {
                    foreach (var c in t.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) {
                        Console.WriteLine("   ctor: " + c);
                    }
                    foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)) {
                        Console.WriteLine("   meth: " + m);
                    }
                }
            }
        }
    }
}
