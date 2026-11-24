using System;
using System.IO;
using System.Reflection;

class InspectJbpHuffman {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        var htType = jbpType.GetNestedType("HuffmanTree", BindingFlags.Public | BindingFlags.NonPublic);
        var jbsType = jbpType.GetNestedType("JBitStream", BindingFlags.Public | BindingFlags.NonPublic);
        Console.WriteLine("HuffmanTree fields:");
        foreach (var f in htType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            Console.WriteLine("  " + f.FieldType.Name + " " + f.Name);
        foreach (var c in htType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            Console.WriteLine("  ctor IL (" + c.GetMethodBody().GetILAsByteArray().Length + "): " + BitConverter.ToString(c.GetMethodBody().GetILAsByteArray()));
        foreach (var m in htType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            Console.WriteLine("  meth " + m.Name + " IL (" + m.GetMethodBody().GetILAsByteArray().Length + "): " + BitConverter.ToString(m.GetMethodBody().GetILAsByteArray()));

        // Also check Pb3Reader.UnpackV1 to find a real JBP1 sample in data/image/!
        var pb3Type = arcFormats.GetType("GameRes.Formats.Purple.Pb3Reader");
        var u1 = pb3Type.GetMethod("UnpackV1", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        Console.WriteLine("UnpackV1 IL: " + BitConverter.ToString(u1.GetMethodBody().GetILAsByteArray()));
    }
}
