using System;
using System.IO;
using System.Reflection;

class InspectJbpCtor {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        var ctor = jbpType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)[0];
        var il = ctor.GetMethodBody().GetILAsByteArray();
        Console.WriteLine("JbpReader ctor IL (" + il.Length + " bytes): " + BitConverter.ToString(il));
        var unpack = jbpType.GetMethod("Unpack");
        var uil = unpack.GetMethodBody().GetILAsByteArray();
        Console.WriteLine("JbpReader Unpack IL (" + uil.Length + " bytes): " + BitConverter.ToString(uil));
        // Also check Pb3Format.ReadMetaData IL or JBP1 magic!
        var pb3Reader = arcFormats.GetType("GameRes.Formats.Purple.Pb3Reader");
        var u1 = pb3Reader.GetMethod("UnpackV1", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        var u1il = u1.GetMethodBody().GetILAsByteArray();
        Console.WriteLine("Pb3Reader UnpackV1 IL (" + u1il.Length + " bytes)");
    }
}
