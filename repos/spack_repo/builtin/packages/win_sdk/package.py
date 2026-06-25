# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


import glob
import os
import re

from spack_repo.builtin.build_systems.generic import Package

from spack.package import *


class WinSdk(Package):
    """
    Windows Desktop C++ development SDK
    Installs from the Microsoft binary bootstrapper into a Spack prefix.
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

    @run_before("install")
    def rename_downloaded_executable(self):
        """SDK bootstrapper downloaded via link redirect may have a non-.exe name;
        rename so Windows can execute it."""
        # Direct CDN URLs already produce the correct filename; nothing to do
        for known_name in ("winsdksetup.exe", "sdksetup.exe"):
            if os.path.exists(os.path.join(self.stage.source_path, known_name)):
                return
        installer = glob.glob(os.path.join(self.stage.source_path, "linkid=*"))
        fetch_size = len(installer)
        if fetch_size > 1:
            raise RuntimeError(
                "Fetch has failed, ambiguous behavior, fetch has pulled too much. "
                "Unable to determine installer path from:\n%s" % "\n".join(installer)
            )
        elif fetch_size < 1:
            raise RuntimeError(
                "Fetch has failed, nothing was fetched from:\n%s" % "\n".join(installer)
            )
        os.rename(installer[0], os.path.join(self.stage.source_path, "winsdksetup.exe"))

    def install(self, spec, prefix):
        # 10.0.14393 and 10.0.10586 use the older sdksetup.exe with /features +
        # Newer versions use winsdksetup.exe with architecture-specific OptionId features
        if spec.satisfies("@:10.0.14393"):
            installer_exe = "sdksetup.exe"
            install_args = ["/features", "+", "/quiet", "/norestart", "/installpath", self.prefix]
        else:
            plat_to_feature = {
                "x64": "OptionId.DesktopCPPx64",
                "x86": "OptionId.DesktopCPPx86",
                "arm": "OptionId.DesktopCPParm",
                "arm64": "OptionId.DesktopCPParm64",
            }
            installer_exe = "winsdksetup.exe"
            feature = plat_to_feature[spec.variants["plat"].value]
            install_args = [
                "/features",
                feature,
                "/quiet",
                "/norestart",
                "/installpath",
                self.prefix,
            ]
        with working_dir(self.stage.source_path):
            try:
                Executable(installer_exe)(*install_args)
            except ProcessError as pe:
                reg = WindowsRegistryView(
                    "SOFTWARE\\Microsoft\\Windows Kits\\Installed Roots",
                    root_key=HKEY.HKEY_LOCAL_MACHINE,
                )
                if not reg:
                    raise pe
                else:
                    versions = [str(subkey) for subkey in reg.get_subkeys()]
                    versions = ",".join(versions) if len(versions) > 1 else versions[0]
                    plural = "s" if len(versions) > 1 else ""
                    raise InstallError(
                        "Cannot install Windows SDK version %s. "
                        "Version%s %s already present on system. "
                        "Please run `spack external find win-sdk` to use the SDK"
                        % (self.version, plural, versions)
                    )
