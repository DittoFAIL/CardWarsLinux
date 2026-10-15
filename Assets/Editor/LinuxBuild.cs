using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// Deliberately uses the Unity 2017 string-returning BuildPlayer API.
public static class LinuxBuild
{
    private const string UnityVersion = "2017.4.40f1";
    private const BuildTarget Target = BuildTarget.StandaloneLinux64;

    [Serializable]
    private class BuildInfo
    {
        public string unityVersion = UnityVersion;
        public string target = "StandaloneLinux64";
        public string graphicsApi = "OpenGLCore";
        public string scriptingBackend = "Mono";
        public string sourceRevision;
        public string builtAtUtc;
        public int sceneCount;
    }

    [MenuItem("Card Wars/Switch to Linux x86_64")]
    public static void SwitchTarget()
    {
        RequireEditor();
        if (!EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Standalone, Target))
            throw new InvalidOperationException("Could not switch to Linux x86_64. Install Linux Build Support for " + UnityVersion + ".");
    }

    [MenuItem("Card Wars/Build Linux x86_64")]
    public static void Build()
    {
        RequireEditor();
        if (EditorUserBuildSettings.activeBuildTarget != Target)
            throw new InvalidOperationException("Select Card Wars > Switch to Linux x86_64 first, or start Unity with -buildTarget Linux64.");

        string projectRoot = Directory.GetParent(Application.dataPath).FullName;
        string output = Environment.GetEnvironmentVariable("CARDWARS_BUILD_DIR");
        if (string.IsNullOrEmpty(output))
            output = Path.Combine(projectRoot, "Builds/Linux");
        output = Path.GetFullPath(output);
        if (Directory.Exists(output) && Directory.GetFileSystemEntries(output).Length != 0)
            throw new InvalidOperationException("Build output must be empty to avoid stale files: " + output);

        List<string> scenes = new List<string>();
        foreach (EditorBuildSettingsScene scene in EditorBuildSettings.scenes)
        {
            if (!scene.enabled) continue;
            if (!File.Exists(Path.Combine(projectRoot, scene.path)))
                throw new FileNotFoundException("Enabled build scene is missing", scene.path);
            scenes.Add(scene.path);
        }
        if (scenes.Count == 0 || scenes[0] != "Assets/Scene/Scenes/StartupScene.unity")
            throw new InvalidOperationException("StartupScene must be the first enabled build scene.");

        // Build settings are temporary. Keep the existing company/product save identity.
        bool oldAutomatic = PlayerSettings.GetUseDefaultGraphicsAPIs(Target);
        GraphicsDeviceType[] oldApis = PlayerSettings.GetGraphicsAPIs(Target);
        ScriptingImplementation oldBackend = PlayerSettings.GetScriptingBackend(BuildTargetGroup.Standalone);
        int oldWidth = PlayerSettings.defaultScreenWidth;
        int oldHeight = PlayerSettings.defaultScreenHeight;
        bool oldNative = PlayerSettings.defaultIsNativeResolution;
        bool oldFullscreen = PlayerSettings.defaultIsFullScreen;
        ResolutionDialogSetting oldDialog = PlayerSettings.displayResolutionDialog;

        Directory.CreateDirectory(output);
        try
        {
            PlayerSettings.SetUseDefaultGraphicsAPIs(Target, false);
            PlayerSettings.SetGraphicsAPIs(Target, new GraphicsDeviceType[] { GraphicsDeviceType.OpenGLCore });
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, ScriptingImplementation.Mono2x);
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 800;
            PlayerSettings.defaultIsNativeResolution = false;
            PlayerSettings.defaultIsFullScreen = true;
            PlayerSettings.displayResolutionDialog = ResolutionDialogSetting.Disabled;

            string executable = Path.Combine(output, "CardWars.x86_64");
            string error = BuildPipeline.BuildPlayer(scenes.ToArray(), executable, Target, BuildOptions.None);
            if (!string.IsNullOrEmpty(error))
                throw new InvalidOperationException("Linux player build failed: " + error);
            if (!File.Exists(executable) || !Directory.Exists(Path.Combine(output, "CardWars_Data")))
                throw new InvalidOperationException("Unity did not produce the expected Linux player and data directory.");

            File.Copy(Path.Combine(projectRoot, "scripts/linux/run.sh"), Path.Combine(output, "run.sh"));
            File.Copy(Path.Combine(projectRoot, "docs/STEAM_DECK.md"), Path.Combine(output, "STEAM_DECK.md"));
            BuildInfo info = new BuildInfo();
            info.sourceRevision = Environment.GetEnvironmentVariable("CARDWARS_SOURCE_REVISION") ?? "unknown";
            info.builtAtUtc = DateTime.UtcNow.ToString("o");
            info.sceneCount = scenes.Count;
            // Only a completed build gets this marker; the packager requires it.
            File.WriteAllText(Path.Combine(output, "build-info.json"), JsonUtility.ToJson(info, true));
            Debug.Log("Linux build complete: " + output + ". Package it with scripts/package-linux.py.");
        }
        finally
        {
            PlayerSettings.SetGraphicsAPIs(Target, oldApis);
            PlayerSettings.SetUseDefaultGraphicsAPIs(Target, oldAutomatic);
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, oldBackend);
            PlayerSettings.defaultScreenWidth = oldWidth;
            PlayerSettings.defaultScreenHeight = oldHeight;
            PlayerSettings.defaultIsNativeResolution = oldNative;
            PlayerSettings.defaultIsFullScreen = oldFullscreen;
            PlayerSettings.displayResolutionDialog = oldDialog;
            AssetDatabase.SaveAssets();
        }
    }

    private static void RequireEditor()
    {
        if (Application.unityVersion != UnityVersion)
            throw new InvalidOperationException("This project requires Unity " + UnityVersion + "; running " + Application.unityVersion + ".");
        if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, Target))
            throw new InvalidOperationException("Install Linux Build Support for Unity " + UnityVersion + ".");
    }
}
