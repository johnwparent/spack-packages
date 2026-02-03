# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class Shapelib(CMakePackage):
    """The Shapefile C Library provides the ability to write simple C programs
    for reading, writing and updating (to a limited extent) ESRI Shapefiles,
    and the associated attribute file (.dbf).
    """

    homepage = "http://shapelib.maptools.org/"
    url = "https://github.com/OSGeo/shapelib/archive/v1.5.0.tar.gz"

    license("LGPL-2.0-only OR MIT")

    version("1.6.2", sha256="d1e4dac2ac20a77be19f2f43525d3271fe62aea2a332526479f83f7ab8adde27")
    version("1.6.1", sha256="72a30ed408edee0dc9eaa81255e634af6706f9192b5ed5b536013f1cc4b327c4")
    version("1.6.0", sha256="0bfd1eab9616ca3c420a5ad674b0d07c7c5018620d6ab6ae43917daa18ff0d1e")
    version("1.5.0", sha256="48de3a6a8691b0b111b909c0b908af4627635c75322b3a501c0c0885f3558cad")

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated
