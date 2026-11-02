# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems import autotools, cmake
from spack_repo.builtin.build_systems.autotools import AutotoolsPackage
from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class Fltk(CMakePackage, AutotoolsPackage):
    """FLTK (pronounced "fulltick") is a cross-platform C++ GUI toolkit for
    UNIX/Linux (X11), Microsoft Windows, and MacOS X. FLTK provides
    modern GUI functionality without the bloat and supports 3D
    graphics via OpenGL and its built-in GLUT emulation.

    FLTK is designed to be small and modular enough to be statically
    linked, but works fine as a shared library. FLTK also includes an
    excellent UI builder called FLUID that can be used to create
    applications in minutes.

    """

    homepage = "https://www.fltk.org/"
    url = "https://github.com/fltk/fltk/archive/refs/tags/release-1.3.3.tar.gz"
    git = "https://github.com/fltk/fltk.git"

    version("master", branch="master")
    version("1.4.4", sha256="cbf5f7846af596206e8e4489e14c9981f98d7b37168110a00dcd26d8d479a669")
    version("1.4.3", sha256="6a11c0bf91b7b193a87a1928c32a953f36d7dd4b65fef3e9d0c40a51882f97a6")
    version("1.3.7", sha256="019f65810fb0ea5acac14c852193e8f374e822e6a3034a3c80ed8676f6f3a090")
    version("1.3.3", sha256="186bdc4234bea74bce4d47f186d41d35bdd47d48dbe5f829513a2183fbf8f3b2")

    # 1.3.x CMakeLists require CMake < 3.5 policies and use different option names;
    # autotools support was removed after 1.4
    build_system(
        conditional("cmake", when="@1.4:"), conditional("autotools", when="@:1.4"), default="cmake"
    )

    depends_on("c", type="build")
    depends_on("cxx", type="build")

    with when("build_system=cmake"):
        depends_on("cmake@3.15:", type="build")

    with when("build_system=autotools"):
        depends_on("autoconf", type="build")
        depends_on("automake", type="build", when="@:1.3")
        depends_on("pkgconfig", type="build", when="@1.3.7")

    for plat in ["linux", "freebsd"]:
        depends_on("libx11", when=f"platform={plat}")
    depends_on("freetype", when="@1.4.3:")

    patch("font.patch", when="@1.3.3")

    # https://github.com/fltk/fltk/commits/master/src/Fl_Tree_Item.cxx
    #  -Fix return value test, as pointed out by Albrecht.
    patch("fix_compare_val.patch", when="@:1.3.3")
    # https://github.com/fltk/fltk/commits/master/test/menubar.cxx
    # -Allow compilation with -std=c++11
    # -Add missing cast (part of patch for STR #2813).
    patch("type_cast.patch", when="@:1.3.3")

    variant("shared", default=True, description="Enables the build of shared libraries")

    variant("gl", default=True, description="Enables opengl support")

    variant("xft", default=False, description="Enables Anti-Aliased Fonts")

    # FLTK 1.4 enables a hybrid Wayland/X11 backend by default on Linux whenever the
    # Wayland libraries are found; keep it opt-in so builds are reproducible.
    variant(
        "wayland",
        default=False,
        when="@1.4: platform=linux",
        description="Build the hybrid Wayland/X11 backend",
    )

    # variant dependencies
    depends_on("gl", when="+gl")

    depends_on("libxft", when="+xft")

    with when("+wayland"):
        # The Wayland backend forces Xft, Pango and Cairo on, and with X11 present it
        # requires all of the X11 extension libraries.
        requires("+xft", msg="FLTK's Wayland backend always uses Xft")
        depends_on("pkgconfig", type="build")
        depends_on("wayland@1.18:")
        depends_on("wayland-protocols@1.15:", type="build")
        depends_on("libxkbcommon")
        depends_on("pango+X")
        depends_on("cairo+X")
        depends_on("libxcursor")
        depends_on("libxfixes")
        depends_on("libxinerama")
        depends_on("libxrender")
        depends_on("egl", when="+gl")
        depends_on("glu", when="+gl")


class CMakeBuilder(cmake.CMakeBuilder):
    def cmake_args(self):
        return [
            self.define_from_variant("FLTK_BUILD_SHARED_LIBS", "shared"),
            self.define_from_variant("FLTK_BUILD_GL", "gl"),
            self.define_from_variant("FLTK_USE_XFT", "xft"),
            self.define_from_variant("FLTK_USE_XRENDER", "xft"),
            self.define("FLTK_BACKEND_WAYLAND", self.spec.satisfies("+wayland")),
            # Match the autotools build: use the bundled image/compression libraries
            self.define("FLTK_USE_SYSTEM_LIBJPEG", False),
            self.define("FLTK_USE_SYSTEM_LIBPNG", False),
            self.define("FLTK_USE_SYSTEM_ZLIB", False),
            # Don't let FindX11 pick up optional extensions from the system
            self.define("FLTK_USE_XCURSOR", False),
            self.define("FLTK_USE_XFIXES", False),
            self.define("FLTK_USE_XINERAMA", False),
            # Wayland extras with no Spack equivalent; use the bundled libdecor
            self.define("FLTK_USE_SYSTEM_LIBDECOR", False),
            self.define("FLTK_USE_LIBDECOR_GTK", False),
            self.define("FLTK_USE_DBUS", False),
            self.define("FLTK_BUILD_TEST", False),
            self.define("FLTK_BUILD_EXAMPLES", False),
            self.define("FLTK_BUILD_HTML_DOCS", False),
            self.define("FLTK_BUILD_PDF_DOCS", False),
        ]


class AutotoolsBuilder(autotools.AutotoolsBuilder):
    def autoreconf(self, pkg, spec, prefix):
        with working_dir(self.configure_directory):
            Executable("./autogen.sh")(extra_env={"NOCONFIGURE": "1"})

    @run_after("autoreconf")
    def filter_nvhpc_flags(self):
        # Remove flags not recognized by the NVIDIA compiler
        if not self.spec.satisfies("%nvhpc"):
            return
        with working_dir(self.configure_directory):
            filter_file(
                'OPTIM="-Wall -Wunused -Wno-format-y2k $OPTIM"',
                'OPTIM="-Wall $OPTIM"',
                "configure",
                string=True,
            )
            filter_file('OPTIM="-Os $OPTIM"', 'OPTIM="-O2 $OPTIM"', "configure", string=True)
            filter_file(
                'CXXFLAGS="$CXXFLAGS -fvisibility=hidden"',
                'CXXFLAGS="$CXXFLAGS"',
                "configure",
                string=True,
            )
            filter_file(
                'OPTIM="$OPTIM -fvisibility=hidden"', 'OPTIM="$OPTIM"', "configure", string=True
            )

    def configure_args(self):
        args = ["--enable-localjpeg", "--enable-localpng", "--enable-localzlib"]
        args += self.enable_or_disable("shared")
        args += self.enable_or_disable("gl")
        # https://www.fltk.org/articles.php?L374+I0+TFAQ+P1+Q
        args += self.enable_or_disable("xft")
        if self.spec.satisfies("@1.4: platform=linux"):
            args += self.enable_or_disable("wayland")
        return args
