# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


import os
import re

from spack_repo.builtin.build_systems.generic import Package
from spack_repo.builtin.packages.win_sdk.package import check_kit_files, install_kit_from_layout

from spack.package import *


class WinWdk(Package):
    """
    Windows Driver Kit development package
    """

    homepage = "https://learn.microsoft.com/en-us/windows-hardware/drivers/"
    tags = ["windows", "windows-system"]

    redistribute(source=False, binary=False)
    license("https://aka.ms/WDKLicense")

    # The wdk has many libraries and executables. Record one for detection purposes
    libraries = ["mmos.lib"]

    version(
        "10.0.26100",
        sha256="cc3c968aca86e8ef72e178e100dc5be1290449df724139ffa94eebb99f840149",
        url="https://download.microsoft.com/download/7e94e645-61e3-479b-811b-981b4c514d5d/KIT_BUNDLE_WDK_MEDIACREATION/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.22621",
        sha256="a891543c0eaf610757ee7852f515c5ce89d0202f22a15dfa31c4d49f2bafdf27",
        url="https://download.microsoft.com/download/7/b/f/7bfc8dbe-00cb-47de-b856-70e696ef4f46/wdk/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.19041",
        sha256="5f4ea0c55af099f97cb569a927c3a290c211f17edcfc65009f5b9253b9827925",
        url="https://download.microsoft.com/download/c/f/8/cf80b955-d578-4635-825c-2801911f9d79/wdk/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.18362",
        sha256="c35057cb294096c63bbea093e5024a5fb4120103b20c13fa755c92f227b644e5",
        url="https://download.microsoft.com/download/2/9/3/29376990-B744-43C5-AE5C-99405068D58B/WDK/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.17763",
        sha256="e6e5a57bf0a58242363cd6ca4762f44739f19351efc06cad382cca944b097235",
        url="https://download.microsoft.com/download/1/4/0/140EBDB7-F631-4191-9DC0-31C8ECB8A11F/wdk/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.17134",
        sha256="48e636117bb7bfe66b1ade793cc8e885c42c880fadaee471782d31b5c4d13e9b",
        url="https://download.microsoft.com/download/B/5/8/B58D625D-17D6-47A8-B3D3-668670B6D1EB/wdk/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.16299",
        sha256="14efbcc849e5977417e962f1cd68357d21abf27393110b9d95983ad03fc22ef4",
        url="https://download.microsoft.com/download/7/D/D/7DD48DE6-8BDA-47C0-854A-539A800FAA90/wdk/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.15063",
        sha256="489b497111bc791d9021b3573bfd93086a28b598c7325ab255e81c6f5d80a820",
        url="https://download.microsoft.com/download/4/E/0/4E07EAAD-E394-4EA8-B2B8-D46E46A409C5/wdk/wdksetup.exe",
        expand=False,
    )
    version(
        "10.0.14393",
        sha256="0bfb2ac9db446e0d98c29ef7341a8c8e8e7aa24bc72b00c5704a88b13f48b3cb",
        url="https://download.microsoft.com/download/8/1/6/816FE939-15C7-4185-9767-42ED05524A95/wdk/wdksetup.exe",
        expand=False,
    )

    variant(
        "plat", values=("x64", "x86", "arm", "arm64"), default="x64", description="Toolchain arch"
    )

    # need one to one dep on SDK per https://github.com/MicrosoftDocs/windows-driver-docs/issues/1550
    # additionally, the WDK needs to be paired with a version of the Windows SDK
    # as per https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk#download-icon-step-2-install-windows-11-version-22h2-sdk
    depends_on("win-sdk@10.0.26100", when="@10.0.26100")
    depends_on("win-sdk@10.0.22621", when="@10.0.22621")
    depends_on("win-sdk@10.0.19041", when="@10.0.19041")
    depends_on("win-sdk@10.0.18362", when="@10.0.18362")
    depends_on("win-sdk@10.0.17763", when="@10.0.17763")
    depends_on("win-sdk@10.0.17134", when="@10.0.17134")
    depends_on("win-sdk@10.0.16299", when="@10.0.16299")
    depends_on("win-sdk@10.0.15063", when="@10.0.15063")
    depends_on("win-sdk@10.0.14393", when="@10.0.14393")

    for plat in ["linux", "darwin"]:
        conflicts("platform=%s" % plat)

    @classmethod
    def determine_version(cls, lib):
        """
        WDK is a set of drivers that we would like to
        be discoverable externally by Spack.
        The lib does not provide the WDK
        version so we derive from the lib path
        """
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

    def setup_dependent_build_environment(
        self, env: EnvironmentModifications, dependent_spec: Spec
    ) -> None:
        # This points to all core build extensions needed to build
        # drivers on Windows
        root = self.prefix if self.spec.external else self.kits_root + os.sep
        env.set("WDKContentRoot", root)

    @property
    def kits_root(self):
        """Equivalent of the system's KitsRoot10 for this WDK"""
        return os.path.join(self.prefix, "Windows Kits", "10")

    def install(self, spec, prefix):
        install_kit_from_layout(self, "wdksetup.exe", ["+"])

        ver = f"{self.version}.0"
        plat = spec.variants["plat"].value
        check_kit_files(
            self.kits_root,
            [
                os.path.join("Include", ver, "km", "ntddk.h"),
                os.path.join("Lib", ver, "km", plat, "ntoskrnl.lib"),
            ],
        )
