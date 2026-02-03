# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class Vxl(CMakePackage):
    """
    VXL (the Vision-something-Libraries) is a collection of C++
    libraries designed for computer vision research and implementation.
    """

    homepage = "https://vxl.github.io/"
    url = "https://github.com/vxl/vxl/archive/refs/tags/v3.3.2.tar.gz"

    maintainers("johnwparent")

    license("")

    version("3.3.2", sha256="95ecde4b02bbe00aec0d656fd2c43373de2a5d41487a68135f0b565254919411")
    version("3.3.0", sha256="90a2d8e30737e3ef09d85aca442548636e35d30a9396fa8bb82920f4ee2b7427")
    version("2.0.2", sha256="f0553daa287754e6b5d17bf3466fdab1f94fb4cbd8155ae20a35197090048fe0")
    version("1.18.0", sha256="25e3b39669482c92afa0a4af925feee11b460e94b07f8f24a1ce7ece65035710")

    variant("ffmpeg", default=True, description="Build with ffmpeg support")
    variant("rpl", default=False, description="Build the rpl subproject")
    variant("brl", default=False, description="Build the brl subproject")
    variant("mul", default=False, description="Build the mul subproject")
    variant("prip", default=False, description="Build the prip subproject")

    depends_on("zlib-api")
    depends_on("libjpeg-turbo")
    depends_on("libtiff")
    depends_on("libgeotiff")
    depends_on("libpng")
    depends_on("bz2")

    def cmake_args(self):
        args = [
            self.define("BUILD_EXAMPLES", False),
            self.define("BUILD_TESTING", False),
            self.define("BUILD_CONTRIB", True),
            self.define("BUILD_FOR_VXL_DASHBOARD", True),
            self.define("BUILD_CORE_PROBABILITY", True),
            self.define("BUILD_CORE_GEOMETRY", True),
            self.define("BUILD_CORE_NUMERICS", True),
            self.define("BUILD_CORE_IMAGING", True),
            self.define("BUILD_CORE_SERIALISATION", True),
            self.define("BUILD_CORE_VIDEO", True),
            self.define("GEOTIFF_INCLUDE_DIR", self.spec["libgeotiff"].headers),
            self.define("GEOTIFF_LIBRARY", self.spec["libgeotiff"].libraries)
            self.define_from_variant("BUILD_RPL", "rpl"),
            self.define_from_variant("BUILD_BRL", "brl"),
            self.define_from_variant("BUILD_MUL_TOOLS", "mul"),
            self.define_from_variant("BUILD_PRIP", "prip"),
        ]