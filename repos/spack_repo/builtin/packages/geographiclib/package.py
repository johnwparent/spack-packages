# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class Geographiclib(CMakePackage):
    """Geographic lib is a small C++ library for geographic data operations"""

    homepage = "https://geographiclib.sourceforge.io/"
    url = "https://github.com/geographiclib/geographiclib"

    
    maintainers("johnwparent")

    license("MIT", checked_by="johnwparent")



    variant("shared", default=True, description="Build shared libs")
    variant("boost", default=False, description="Build with Boost support for NearestNeighbor")

    resource(
        name="geoid-data",
        url="",
        sha256="",
        placement=join_path("share-geoid")
    )
    resource(
        name="gravity-data",
        url="",
        sha256="",
        placement=join_path("share-geoid")
    )
    resource(
        name="magnetic-data",
        url="",
        sha256="",
        placement=join_path("share-geoid")
    )