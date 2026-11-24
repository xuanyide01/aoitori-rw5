using System;
using System.IO;
using System.Reflection;

class InspectIFileSystem {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        var g = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var ifs = g.GetType("GameRes.IFileSystem");
        foreach (var m in ifs.GetMembers()) Console.WriteLine("IFS: " + m);
        var fss = g.GetType("GameRes.VFS").GetField("m_vfs", BindingFlags.NonPublic | BindingFlags.Static).FieldType;
        Console.WriteLine("Stack type: " + fss);
        foreach (var f in fss.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) Console.WriteLine("  FLD: " + f.FieldType + " " + f.Name);
        foreach (var m in fss.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static)) Console.WriteLine("  MTH: " + m);
    }
}
