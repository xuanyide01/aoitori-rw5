using System;
using System.IO;
using System.Reflection;

class InspectPb3Reader {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var t = arcFormats.GetType("GameRes.Formats.Purple.Pb3Reader");
        foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)) {
            Console.WriteLine("M: " + m);
        }
        foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) {
            Console.WriteLine("F: " + f.FieldType.Name + " " + f.Name);
        }
        var vfs = gameRes.GetType("GameRes.VFS");
        foreach (var f in vfs.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static)) {
            Console.WriteLine("VFS F: " + f.FieldType.Name + " " + f.Name);
        }
        foreach (var m in vfs.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static)) {
            Console.WriteLine("VFS M: " + m);
        }
    }
}
