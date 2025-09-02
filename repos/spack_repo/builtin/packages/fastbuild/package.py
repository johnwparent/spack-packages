# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import itertools
import os
import re
import sys
from subprocess import Popen

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator
from spack_repo.builtin.build_systems.cuda import CudaPackage
from spack_repo.builtin.build_systems.rocm import ROCmPackage

from spack.package import *



class FastBuild(Package):
    """High performance build system for Windows, OSX and Linux.
    Supporting caching, network distribution and more."""

    homepage = "https://fastbuild.org"
    url = "https://github.com/fastbuild/fastbuild/archive/refs/tags/v1.15.tar.gz"


    depends_on("c", type="build")
    depends_on("cxx", type="build")

    depends_on("lz4")
    depends_on("zstd")
    depends_on("python", type="build")
