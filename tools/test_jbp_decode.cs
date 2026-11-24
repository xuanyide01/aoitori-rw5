using System;
using System.IO;
using System.Reflection;

class TestJbpDecode {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");

        foreach (var name in new[] { "op_frame100.jbp", "bg070a_frame0.jbp" }) {
            var p = Path.Combine(@"E:\Antigravity\aoitori-rw5\probe", name);
            var jraw = File.ReadAllBytes(p);
            var jbp = Activator.CreateInstance(jbpType, new object[] { jraw, 24 });
            var pixels = (byte[])jbpType.GetMethod("Unpack").Invoke(jbp, null);
            var w = (int)jbpType.GetProperty("Width").GetValue(jbp);
            var h = (int)jbpType.GetProperty("Height").GetValue(jbp);
            var stride = (int)jbpType.GetProperty("Stride").GetValue(jbp);
            Console.WriteLine(string.Format("Before Decode JBP {0}: {1}x{2}, stride={3}, pixels={4}", name, w, h, stride, pixels == null ? -1 : pixels.Length));
        }
        // Check what JbpReader constructor sets and what Decode() does!
        var jraw0 = File.ReadAllBytes(@"E:\Antigravity\aoitori-rw5\probe\op_frame100.jbp");
        Console.WriteLine("op_frame100.jbp header bytes [0..44]: " + BitConverter.ToString(jraw0, 0, 44));
        var jbp0 = Activator.CreateInstance(jbpType, new object[] { jraw0, 24 });
        foreach (var f in jbpType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) {
            Console.WriteLine("  field " + f.Name + " = " + f.GetValue(jbp0));
        }
    }
}
