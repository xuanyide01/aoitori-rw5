using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;

class ProbePb3AndCmv {
    static void Main() {
        var dir = @"E:\Antigravity\tools\downloads\GARbro-Mod";
        AppDomain.CurrentDomain.AssemblyResolve += (s, a) => {
            var name = new AssemblyName(a.Name).Name + ".dll";
            var p = Path.Combine(dir, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };
        var gameRes = Assembly.LoadFrom(Path.Combine(dir, "GameRes.dll"));
        var arcFormats = Assembly.LoadFrom(Path.Combine(dir, "ArcFormats.dll"));
        var catalogType = gameRes.GetType("GameRes.FormatCatalog");
        var catalog = catalogType.GetProperty("Instance").GetValue(null);
        using (var fs = File.OpenRead(Path.Combine(dir, "GameData", "Formats.dat"))) {
            catalogType.GetMethod("DeserializeScheme").Invoke(catalog, new object[] { fs });
        }

        // Check Pb3Reader / CpzOpener.DecryptPb3 / ArcFile.OpenImage
        var pb3ReaderType = arcFormats.GetType("GameRes.Formats.Purple.Pb3Reader");
        Console.WriteLine("Pb3Reader ctors & methods:");
        foreach (var c in pb3ReaderType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) {
            Console.WriteLine("  ctor: " + c);
        }
        var cpzOpenerType = arcFormats.GetType("GameRes.Formats.Purple.CpzOpener");
        object cpzOpener = null;
        foreach (var a in (IEnumerable)catalogType.GetProperty("ArcFormats").GetValue(catalog)) {
            if (a.GetType() == cpzOpenerType) cpzOpener = a;
        }
        // Test CpzOpener.OpenImage on loose PB3 vs inside stand.cpz!
        var arcViewType = gameRes.GetType("GameRes.ArcView");
        var pngFmt = gameRes.GetType("GameRes.ImageFormat").GetProperty("Png").GetValue(null);
        using (var view = (IDisposable)Activator.CreateInstance(arcViewType, new object[] { @"G:\SteamLibrary\steamapps\common\Aoi Tori\data\pack\stand.cpz" }))
        using (var arc = (IDisposable)cpzOpenerType.GetMethod("TryOpen").Invoke(cpzOpener, new object[] { view })) {
            var firstEntry = ((IEnumerable)arc.GetType().GetProperty("Dir").GetValue(arc)).Cast<object>().First();
            Console.WriteLine("Testing stand.cpz/" + firstEntry.GetType().GetProperty("Name").GetValue(firstEntry));
            var decoder = (IDisposable)cpzOpenerType.GetMethod("OpenImage").Invoke(cpzOpener, new object[] { arc, firstEntry });
            var imgData = decoder.GetType().GetProperty("Image").GetValue(decoder);
            using (var ofs = File.Create(@"E:\Antigravity\aoitori-rw5\probe\stand_sample.png")) {
                pngFmt.GetType().GetMethod("Write").Invoke(pngFmt, new object[] { ofs, imgData });
            }
            Console.WriteLine("stand.cpz OpenImage OK!");
        }

        // Test loose h_mr01_01r.pb3 by reading Pb3Reader's Unpack/fields or DecryptPb3!
        // Note: earlier DecryptPb3 returned -1? Why? Let's check DecryptPb3 return type!
        var decMethod = cpzOpenerType.GetMethod("DecryptPb3", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance);
        Console.WriteLine("DecryptPb3 signature: " + decMethod);
        var raw = File.ReadAllBytes(@"G:\SteamLibrary\steamapps\common\Aoi Tori\data\image\event\h_mr01_01r.pb3");
        var res = (byte[])decMethod.Invoke(cpzOpener, new object[] { raw });
        Console.WriteLine("DecryptPb3 result is null? " + (res == null));

        // Also test VFS.OpenImage or ImageFormat.Read on op.cmv / mv!
        var mvType = arcFormats.GetType("GameRes.Formats.Purple.MvDecoder");
        Console.WriteLine("MvDecoder ctors:");
        foreach (var c in mvType.GetConstructors(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)) {
            Console.WriteLine("  " + c);
        }
        var mvAudioType = arcFormats.GetType("GameRes.Formats.Purple.MvAudio");
        Console.WriteLine("MvAudio: " + mvAudioType);
    }
}
