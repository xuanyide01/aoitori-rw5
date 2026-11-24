using System;
using System.IO;
using System.Reflection;

class CheckJbpMeta {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var jbpType = arcFormats.GetType("GameRes.Formats.Purple.JbpReader");
        // Test modifying m_format or checking what happens if offset 0x08 is 0x00000002 or 0x10000002 or 0x20000002!
        var jraw = File.ReadAllBytes(@"E:\Antigravity\aoitori-rw5\probe\op_frame100.jbp");
        Console.WriteLine("orig format=0x" + BitConverter.ToUInt32(jraw, 8).ToString("x8"));
        // Also dump field tokens of JbpReader
        foreach (var f in jbpType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) {
            Console.WriteLine("field 0x" + f.MetadataToken.ToString("x8") + ": " + f.FieldType.Name + " " + f.Name);
        }
        foreach (var m in jbpType.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)) {
            Console.WriteLine("meth 0x" + m.MetadataToken.ToString("x8") + ": " + m.Name);
        }
        // Try bg070a_frame0.jbp too!
        try {
            var bgraw = File.ReadAllBytes(@"E:\Antigravity\aoitori-rw5\probe\bg070a_frame0.jbp");
            var jbp = Activator.CreateInstance(jbpType, new object[] { bgraw, 0 });
            var pix = (byte[])jbpType.GetMethod("Unpack").Invoke(jbp, null);
            Console.WriteLine("bg070a Unpack OK! len=" + pix.Length);
        } catch (Exception ex) {
            Console.WriteLine("bg070a ERR: " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message));
        }
    }
}
