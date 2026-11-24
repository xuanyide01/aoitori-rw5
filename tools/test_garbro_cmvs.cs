using System;
using System.IO;
using System.Linq;
using System.Reflection;

class TestGarbroCmvs {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));

        // Print CpzOpener / Pb3Format / MvDecoder methods or test opening via ArcFile.TryOpen
        var vfsType = gameRes.GetType("GameRes.VFS");
        var arcFormatType = gameRes.GetType("GameRes.ArchiveFormat");
        var formatCatalog = gameRes.GetType("GameRes.FormatCatalog");
        var instanceProp = formatCatalog.GetProperty("Instance");
        var catalog = instanceProp.GetValue(null);
        // DeserializeFormats or check Schemes
        var cpzOpener = arcFormats.GetType("GameRes.Formats.Purple.CpzOpener");
        Console.WriteLine("CpzOpener methods:");
        foreach (var m in cpzOpener.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) {
            Console.WriteLine("  " + m.Name + "(" + string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)) + ")");
        }
        var cpzScheme = arcFormats.GetType("GameRes.Formats.Purple.CpzScheme");
        Console.WriteLine("CpzScheme fields/props:");
        foreach (var f in cpzScheme.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) {
            Console.WriteLine("  field: " + f.FieldType.Name + " " + f.Name);
        }
        foreach (var p in cpzScheme.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) {
            Console.WriteLine("  prop: " + p.PropertyType.Name + " " + p.Name);
        }
    }
}
