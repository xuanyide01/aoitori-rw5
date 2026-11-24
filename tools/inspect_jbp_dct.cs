using System;
using System.IO;
using System.Reflection;

class InspectJbpDct {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        var jbsType = jbpType.GetNestedType("JBitStream", BindingFlags.Public | BindingFlags.NonPublic);
        foreach (var f in jbsType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            Console.WriteLine("JBitStream field: " + f.FieldType.Name + " " + f.Name);
        foreach (var m in jbsType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            Console.WriteLine("JBitStream meth " + m.Name + " IL(" + m.GetMethodBody().GetILAsByteArray().Length + "): " + BitConverter.ToString(m.GetMethodBody().GetILAsByteArray()));
        var dct = jbpType.GetMethod("Dct", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        Console.WriteLine("Dct IL len=" + dct.GetMethodBody().GetILAsByteArray().Length);
        // Also check Pb3Reader.Unpack to see how JbpReader is constructed in UnpackV1/V5/V6!
        var pb3Type = arcFormats.GetType("GameRes.Formats.Purple.Pb3Reader");
        foreach (var mn in new[] { "Unpack", "UnpackV5", "UnpackV6" }) {
            var pm = pb3Type.GetMethod(mn, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            Console.WriteLine("Pb3Reader." + mn + " IL: " + BitConverter.ToString(pm.GetMethodBody().GetILAsByteArray()));
        }
    }
}
