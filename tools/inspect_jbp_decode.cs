using System;
using System.IO;
using System.Reflection;

class InspectJbpDecode {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        var m = jbpType.GetMethod("Decode", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        var il = m.GetMethodBody().GetILAsByteArray();
        Console.WriteLine("Decode IL (" + il.Length + " bytes): " + BitConverter.ToString(il));

        var y2r = jbpType.GetMethod("Ycc2Rgb", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        var yil = y2r.GetMethodBody().GetILAsByteArray();
        Console.WriteLine("Ycc2Rgb IL (" + yil.Length + " bytes): " + BitConverter.ToString(yil));

        // Also check Pb3Reader.UnpackV1 where JbpReader is called!
        var pb3 = arcFormats.GetType("GameRes.Formats.Purple.Pb3Reader");
        foreach (var mn in new[] { "UnpackV1", "UnpackV5", "UnpackV6" }) {
            var pm = pb3.GetMethod(mn, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            Console.WriteLine(mn + " IL len: " + pm.GetMethodBody().GetILAsByteArray().Length);
        }
    }
}
