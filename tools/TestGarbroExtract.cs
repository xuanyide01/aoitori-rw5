using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows.Media.Imaging;
using GameRes;

class TestGarbroExtract
{
    static void Main(string[] args)
    {
        string garbroDir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, ev) =>
        {
            string name = new AssemblyName(ev.Name).Name + ".dll";
            string p = Path.Combine(garbroDir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        Run();
    }

    static void Run()
    {
        string garbroDir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        Assembly.LoadFrom(Path.Combine(garbroDir, "ArcFormats.dll"));
        using (var fs = File.OpenRead(Path.Combine(garbroDir, "GameData", "Formats.dat")))
        {
            FormatCatalog.Instance.DeserializeScheme(fs);
        }

        string dataDir = @"G:\SteamLibrary\steamapps\common\Aoi Tori\data";
        // Check what CPZ archives open and count entries
        foreach (string cpz in new[] { "bg.cpz", "stand.cpz", "up.cpz" })
        {
            string cpzPath = Path.Combine(dataDir, cpz);
            using (var arc = ArcFile.TryOpen(cpzPath))
            {
                Console.WriteLine("{0}: opened={1}, count={2}", cpz, arc != null, arc != null ? arc.Dir.Count() : 0);
                if (arc != null)
                {
                    var sample = arc.Dir.Take(5).Select(e => e.Name).ToArray();
                    Console.WriteLine("  sample: " + string.Join(", ", sample));
                }
            }
        }

        // Test decoding loose diff file h_mr01_01b.pb3 and CPZ file st-ak_a181.pb3 / st-ak_a192.pb3
        TestFile(Path.Combine(dataDir, @"image\event\h_mr01_01b.pb3"));
        TestFile(Path.Combine(dataDir, @"image\event\ev_mr01b.pb3"));

        // Test decoding from stand.cpz after setting VFS
        string standPath = Path.Combine(dataDir, "stand.cpz");
        VFS.ChDir(standPath);
        TestVfs("st-ak_a181.pb3");
        TestVfs("st-ak_a192.pb3");
        VFS.ChDir(Path.Combine(dataDir, "up.cpz"));
        TestVfs("up-ak_a198.pb3");
    }

    static void TestFile(string path)
    {
        try
        {
            VFS.ChDir(Path.GetDirectoryName(path));
            using (var s = VFS.OpenBinaryStream(Path.GetFileName(path)))
            {
                var img = ImageFormat.Read(s);
                Console.WriteLine("Loose {0}: ok={1} {2}x{3} bpp={4}", Path.GetFileName(path), img != null,
                    img != null ? img.Width : 0, img != null ? img.Height : 0, img != null ? img.BPP : 0);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("Loose {0} ERR: {1}", Path.GetFileName(path), ex.Message);
        }
    }

    static void TestVfs(string name)
    {
        try
        {
            using (var s = VFS.OpenBinaryStream(name))
            {
                var img = ImageFormat.Read(s);
                Console.WriteLine("VFS {0}: ok={1} {2}x{3} bpp={4}", name, img != null,
                    img != null ? img.Width : 0, img != null ? img.Height : 0, img != null ? img.BPP : 0);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("VFS {0} ERR: {1}", name, ex.Message);
        }
    }
}
