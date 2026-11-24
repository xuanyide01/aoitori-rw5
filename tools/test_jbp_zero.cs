using System;
using System.IO;
using System.Reflection;

class TestJbpZeroOffset {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        try {
            var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
            var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
            var p = @"E:\Antigravity\aoitori-rw5\probe\op_frame100.jbp";
            var jraw = File.ReadAllBytes(p);
            var jbp = Activator.CreateInstance(jbpType, new object[] { jraw, 0 });
            Console.WriteLine("Created JbpReader! Width=" + jbpType.GetProperty("Width").GetValue(jbp) + " Height=" + jbpType.GetProperty("Height").GetValue(jbp) + " Stride=" + jbpType.GetProperty("Stride").GetValue(jbp));
            foreach (var f in jbpType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) {
                Console.WriteLine("  field " + f.Name + " = " + f.GetValue(jbp));
            }
            var pixels = (byte[])jbpType.GetMethod("Unpack").Invoke(jbp, null);
            Console.WriteLine("Unpack len=" + pixels.Length);
        } catch (Exception ex) {
            Console.WriteLine("ERR: " + ex.GetType().FullName + ": " + ex.Message);
            if (ex.InnerException != null) {
                Console.WriteLine("INNER: " + ex.InnerException.GetType().FullName + ": " + ex.InnerException.Message);
                Console.WriteLine(ex.InnerException.StackTrace);
            }
        }
    }
}
