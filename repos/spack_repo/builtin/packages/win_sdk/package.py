# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


import glob
import os
import platform
import re
import subprocess

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class WinSdk(Package):
    """
    Windows Desktop C++ development SDK
    Detectable as an external, or installable into a Spack prefix
    without elevation or registering the SDK with the system.
    """

    homepage = "https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/"
    tags = ["windows", "windows-system"]

    redistribute(source=False, binary=False)
    license("https://aka.ms/WinSDKLicense")

    # The sdk has many libraries and executables. Record one for detection purposes
    libraries = ["rcdll.dll"]

    version(
        "10.0.26100",
        sha256="a8e6b6cc2dcec9fdd4c35553a4cbf288c9ce5e4761d7a2762f06a3a95f1e530d",
        url="https://download.microsoft.com/download/e/b/3/eb320eb1-b21e-4e6e-899e-d6aec552ecb0/KIT_BUNDLE_WINDOWSSDK_MEDIACREATION/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.22621",
        sha256="73fe3cc0e50d946d0c0a83a1424111e60dee23f0803e305a8974a963b58290c0",
        url="https://download.microsoft.com/download/7/9/6/7962e9ce-cd69-4574-978c-1202654bd729/windowssdk/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.19041",
        sha256="42d2774274d1135fc598c180c2acbf2321eb4192f59e511e6ac7772870bf6de1",
        url="https://download.microsoft.com/download/4/d/2/4d2b7011-606a-467e-99b4-99550bf24ffc/windowssdk/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.18362",
        sha256="2e28117e82b4d02fe30d564b835ace9976612609271265872f20f2256a9c506b",
        url="https://download.microsoft.com/download/4/2/2/42245968-6A79-4DA7-A5FB-08C0AD0AE661/windowssdk/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.17763",
        sha256="bbd1c41f9ebf518e4482c5c85a0de9ad7a72b596112c392911ef6054cb5d70d7",
        url="https://download.microsoft.com/download/5/C/3/5C3770A3-12B4-4DB4-BAE7-99C624EB32AD/windowssdk/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.17134",
        sha256="93c9dca3a9f28061a601f3e6b737dede40c2c77cfd200ed5cb6efe2ab0c9d5cc",
        url="https://download.microsoft.com/download/5/A/0/5A08CEF4-3EC9-494A-9578-AB687E716C12/windowssdk/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.16299",
        sha256="d63cea29e4c5b5c4d70e1334fc47107e915214d4fd41705c68070550260451ec",
        url="https://download.microsoft.com/download/8/C/3/8C37C5CE-C6B9-4CC8-8B5F-149A9C976035/windowssdk/winsdksetup.exe",
        expand=False,
    )
    version(
        "10.0.15063",
        sha256="06661d9dcf9147bf3c4aa0b4d3adf74bb099b522f46a674b80cceba7b5361fcc",
        url="https://download.microsoft.com/download/E/1/B/E1B0E6C0-2FA2-4A1B-B322-714A5586BE63/windowssdk/winsdksetup.exe",
        expand=False,
    )
    # 10.0.14393 and 10.0.10586 use the older sdksetup.exe bootstrapper format
    version(
        "10.0.14393",
        sha256="0d3a5c94143fe14a45bb9608a951dea04cb01bf1ff90003e8c3d80dacfca05be",
        url="https://download.microsoft.com/download/C/D/8/CD8533F8-5324-4D30-824C-B834C5AD51F9/standalonesdk/sdksetup.exe",
        expand=False,
    )
    version(
        "10.0.10586",
        sha256="4cd4bfe507ea78d70aab139045b69ed57bd28be446b07a40251f1283bb8b1d92",
        url="https://download.microsoft.com/download/2/1/2/2122BA8F-7EA6-4784-9195-A8CFB7E7388E/StandaloneSDK/sdksetup.exe",
        expand=False,
    )
    # Detection-only: no known public installer for this version
    version("10.0.26639")

    variant(
        "plat", values=("x64", "x86", "arm", "arm64"), default="x64", description="Toolchain arch"
    )

    # WinSDK versions depend on compatible compilers
    # WDK versions do as well, but due to their one to one dep on the SDK
    # we can ensure that requirment here
    # WinSDK is very backwards compatible, however older
    # MSVC editions may have problems with newer SDKs
    conflicts("%msvc@:19.16.00000", when="@10.0.26100")
    conflicts("%msvc@:19.16.00000", when="@10.0.22621")
    conflicts("%msvc@:19.16.00000", when="@10.0.19041")
    conflicts("%msvc@:19.16.00000", when="@10.0.18362")
    conflicts("%msvc@:19.15.00000", when="@10.0.17763")
    conflicts("%msvc@:19.14.00000", when="@10.0.17134")
    conflicts("%msvc@:19.11.00000", when="@10.0.16299")
    conflicts("%msvc@:19.10.00000", when="@10.0.15063")
    conflicts("%msvc@:19.10.00000", when="@10.0.14393")
    conflicts("%msvc@:19.00.00000", when="@10.0.10586")

    # For now we don't support Windows development env
    # on other platforms
    for plat in ["linux", "darwin"]:
        conflicts("platform=%s" % plat)

    @classmethod
    def determine_version(cls, lib):
        """
        WinSDK that we would like to
        be discoverable externally by Spack.
        """
        # This version is found in the package's path
        # not by calling an exe or a libraries name
        version_match_pat = re.compile(r"[0-9][0-9].[0-9]+.[0-9][0-9][0-9][0-9][0-9]")
        ver_str = re.search(version_match_pat, lib)
        return ver_str if not ver_str else Version(ver_str.group())

    @classmethod
    def determine_variants(cls, libs, ver_str):
        """Allow for determination of toolchain arch for detected WGL"""
        variants = []
        for lib in libs:
            base, lib_name = os.path.split(lib)
            _, arch = os.path.split(base)
            variants.append("plat=%s" % arch)
        return variants

    @property
    def kits_root(self):
        """Equivalent of the system's KitsRoot10 for this SDK"""
        return os.path.join(self.prefix, "Windows Kits", "10")

    @property
    def kit_version(self):
        """Version as used in the SDK's Include/Lib/bin directory names"""
        return f"{self.version}.0"

    def install(self, spec, prefix):
        # 10.0.14393 and 10.0.10586 use the older sdksetup.exe, which only takes "+" (all)
        if spec.satisfies("@:10.0.14393"):
            bootstrapper = "sdksetup.exe"
            features = ["+"]
        else:
            plat_to_feature = {
                "x64": "OptionId.DesktopCPPx64",
                "x86": "OptionId.DesktopCPPx86",
                "arm": "OptionId.DesktopCPParm",
                "arm64": "OptionId.DesktopCPParm64",
            }
            bootstrapper = "winsdksetup.exe"
            features = [plat_to_feature[spec.variants["plat"].value]]
        install_kit_from_layout(self, bootstrapper, features)

        plat = spec.variants["plat"].value
        check_kit_files(
            self.kits_root,
            [
                os.path.join("Include", self.kit_version, "um", "Windows.h"),
                os.path.join("Include", self.kit_version, "ucrt", "stdio.h"),
                os.path.join("Lib", self.kit_version, "um", plat, "kernel32.lib"),
                os.path.join("Lib", self.kit_version, "ucrt", plat, "ucrt.lib"),
            ],
        )

    def setup_msvc_environment(self, env: EnvironmentModifications) -> None:
        """Add this SDK to an MSVC environment created without one (``VsDevCmd -winsdk=none``)

        This mirrors what VS's winsdk.bat sets for an SDK registered with the system, which
        is the only place vcvars will look for one."""
        root = self.kits_root + os.sep
        ver = self.kit_version
        plat = self.spec.variants["plat"].value
        host = "arm64" if platform.machine().lower() == "arm64" else "x64"

        env.set("WindowsSdkDir", root)
        env.set("WindowsSDKVersion", ver + os.sep)
        env.set("WindowsSDKLibVersion", ver + os.sep)
        env.set("WindowsSdkBinPath", os.path.join(root, "bin") + os.sep)
        env.set("WindowsSdkVerBinPath", os.path.join(root, "bin", ver) + os.sep)
        env.set("UniversalCRTSdkDir", root)
        env.set("UCRTVersion", ver)
        for sub in ("ucrt", "um", "shared", "winrt", "cppwinrt"):
            env.append_path("INCLUDE", os.path.join(root, "Include", ver, sub))
        for sub in ("ucrt", "um"):
            env.append_path("LIB", os.path.join(root, "Lib", ver, sub, plat))
        env.append_path("LIBPATH", os.path.join(root, "UnionMetadata", ver))
        env.append_path("LIBPATH", os.path.join(root, "References", ver))
        env.prepend_path("PATH", os.path.join(root, "bin", host))
        env.prepend_path("PATH", os.path.join(root, "bin", ver, host))


def install_kit_from_layout(pkg, bootstrapper: str, features: List[str]) -> None:
    """Install a Windows Kit (SDK or WDK) into ``pkg.prefix`` without running its installer

    The installer requires elevation, registers the Kit machine-wide, and installs every Kit
    into the single registered Kits root no matter where it is told to go. Instead the
    bootstrapper is only used to download the Kit's MSIs (``/layout``) and each MSI is
    extracted with an administrative install (``msiexec /a``), which writes files only.
    Neither step needs elevation or touches the registry.
    """
    stage = pkg.stage.source_path
    layout = os.path.join(stage, "layout")
    Executable(os.path.join(stage, bootstrapper))(
        "/layout",
        layout,
        "/features",
        *features,
        "/quiet",
        "/norestart",
        "/log",
        os.path.join(stage, "layout.log"),
    )

    msis = sorted(glob.glob(os.path.join(layout, "Installers", "*.msi")))
    if not msis:
        raise InstallError(f"{bootstrapper} /layout produced no MSIs, see {stage}\\layout.log")

    log_dir = os.path.join(stage, "msi-logs")
    mkdirp(log_dir)
    failed = []
    for msi in msis:
        name = os.path.basename(msi)
        # msiexec parses its own command line and requires PROPERTY="value" quoting,
        # which list based argument quoting cannot produce for paths with spaces.
        # Extract straight into the prefix: Kit file paths run deep enough that a longer
        # root, like the stage's, pushes some past MAX_PATH
        cmd = (
            f'msiexec.exe /a "{msi}" /qn TARGETDIR="{pkg.prefix}" '
            f'/le "{os.path.join(log_dir, name)}.log"'
        )
        if subprocess.run(cmd).returncode != 0:
            failed.append(name)
        # Administrative installs leave a copy of the MSI in TARGETDIR
        force_remove(os.path.join(pkg.prefix, name))

    # Some MSIs ship only WinRT/IntelliSense metadata with paths too long for any
    # reasonable prefix; installs are validated by the files consumers need instead
    if failed:
        tty.warn(f"Failed to extract (logs in {log_dir}):\n    " + "\n    ".join(failed))


def check_kit_files(root: str, files: List[str]) -> None:
    missing = [f for f in files if not os.path.exists(os.path.join(root, f))]
    if missing:
        raise InstallError(f"Kit install in {root} is missing:\n    " + "\n    ".join(missing))
