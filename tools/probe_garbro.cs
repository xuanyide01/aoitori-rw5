using System;
using System.IO;
using System.Linq;
using System.Reflection;

class ProbeGarbro {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var asm = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        foreach (var t in asm.GetTypes()) {
            var fn = t.FullName ?? "";
            if (fn.IndexOf("Purple", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Cpz", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Pb3", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Cmvs", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Ps2", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Ps3", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Nka", StringComparison.OrdinalIgnoreCase) >= 0) {
                Console.WriteLine(fn);
            }
        }
        var extra = Assembly.LoadFrom(Path.Combine(dir, "ArcExtra.dll"));
        foreach (var t in extra.GetTypes()) {
            var fn = t.FullName ?? "";
            if (fn.IndexOf("Purple", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Cpz", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Pb3", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Cmvs", StringComparison.OrdinalIgnoreCase) >= 0 ||
                fn.IndexOf("Nka", StringComparison.OrdinalIgnoreCase) >= 0) {
                Console.WriteLine("EXTRA: " + fn);
            }
        }
    }
}
