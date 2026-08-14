# Recipe modeling: variants, dependencies, devendoring

Contents:
- [Shared vs static](#shared-vs-static)
- [Windows dependency divergence](#windows-dependency-divergence)
- [Devendoring](#devendoring)
- [Conflicts and version gating](#conflicts-and-version-gating)
- [Language dependencies and Fortran](#language-dependencies-and-fortran)
- [Tags](#tags)

---

## Shared vs static

### The constraint

CMake on Windows uses the Ninja generator (see `build-systems.md`), and a single CMake configure
produces **either** static **or** shared libraries — `BUILD_SHARED_LIBS` is one boolean per
configure. Most Autotools builds, by contrast, happily produce both in one pass via libtool.

So a package that models static and shared as simultaneously available is expressing something
that cannot be satisfied by one Windows CMake configure.

### Which variant style is in play

**Boolean `variant("shared", default=True)`** — the common case, and it is already sound. One
value per build, maps directly to `BUILD_SHARED_LIBS`:

```python
variant("shared", default=True, description="Build shared library")
...
self.define_from_variant("BUILD_SHARED_LIBS", "shared")
```

Nothing Windows-specific is needed. `libxml2` uses exactly this.

**Multi-valued `variant("libs", default="shared,static", values=("shared", "static"), multi=True)`**
— this is the one that needs attention. `libs=shared,static` asks for both in one install. On
Windows with a CMake build, that requires either a second configure pass or an explicit conflict.

Two sound resolutions:

```python
# Option A — declare the limitation. Simple, honest, no build complexity.
conflicts(
    "libs=shared,static",
    when="platform=windows",
    msg="CMake/Ninja on Windows builds either shared or static per configure; pick one",
)
```

```python
# Option B — two configure passes. Only worth it if consumers really need both.
#            Requires a custom builder that runs cmake twice with different
#            BUILD_SHARED_LIBS values into separate build directories.
```

Prefer Option A unless there is a concrete consumer requiring both. It costs users one explicit
choice and costs maintainers nothing.

**The non-regression rule:** whichever you choose, the *default* variant value must not change on
other platforms. A `conflicts` scoped to `when="platform=windows"` leaves POSIX untouched; changing
`default=` does not.

> No package in this repo currently expresses this conflict, so there is no local pattern to copy —
> get the modeling right from first principles rather than looking for precedent.

### Verifying it built what you asked for

A Windows build that "succeeds" but produces no `.dll` is usually a static configure, or a shared
configure that exported no symbols (see `symbols.md`). Check `prefix/lib` and `prefix/bin` for the
artifacts you expect before declaring success.

---

## Windows dependency divergence

Windows dependency sets are frequently smaller and sometimes disjoint. Two idioms:

### `with when("platform=windows"):`

Groups Windows-only directives — variants as well as dependencies. From `openssl/package.py`:

```python
variant("shared", default=True, description="Build shared library version")
with when("platform=windows"):
    variant("dynamic", default=False, description="Link with MSVC's dynamic runtime library")

depends_on("nasm", when="platform=windows")
```

Two things worth copying here. The `dynamic` variant exists *only* on Windows, so it cannot
clutter the variant space on other platforms — that is what a CRT choice (`/MD` vs `/MT`) should
look like when a package needs to expose one. And `nasm` is pulled in only on Windows, because
that is the only platform where openssl's build needs an external assembler.

### Gating a POSIX dependency by naming the platforms that need it

The inverse idiom — rather than excluding Windows, name the platforms that require the dependency.
Also from `openssl`:

```python
depends_on("gmake", type="build", when="platform=linux")
depends_on("gmake", type="build", when="platform=darwin")
```

This is more robust than `when="platform=windows"` negation: a new platform does not silently
inherit a dependency it may not need.

### `when="build_system=<windows-builder>"`

When the build system is already Windows-conditional, gating on it is cleaner than gating on the
platform — it says *why* the dependency differs rather than merely *where*. `libxml2` does this and
comments the reasoning:

```python
depends_on("pkgconfig", type="build", when="build_system=autotools")
# conditional on non Windows, but rather than specify for each platform
# specify for non Windows builder, which has equivalent effect
depends_on("iconv", when="build_system=autotools")
```

Use this when the dependency belongs to the build system rather than to the platform — Autotools
needs `pkgconfig`; nmake does not, regardless of platform.

See `triage.md` for the tables of commonly-unneeded and Windows-only dependencies.

---

## Devendoring

Upstream Windows build paths vendor and download dependencies far more often than POSIX ones,
because they assume no system package manager exists. Spack must supply those dependencies
instead — otherwise the build silently ignores the versions Spack concretized, and the resulting
install is unreproducible.

### Detecting it

| Signal | Where |
|---|---|
| `FetchContent_Declare` / `FetchContent_MakeAvailable` | `CMakeLists.txt` |
| `ExternalProject_Add` with a `URL`/`GIT_REPOSITORY` | `CMakeLists.txt` |
| `third_party/`, `external/`, `deps/`, `vendor/` with checked-in sources | source tree |
| `packages.config`, `*.nupkg`, NuGet restore steps | Windows/MSBuild projects |
| `vcpkg.json`, `vcpkg_installed/` | Windows CMake projects |
| `git submodule` init in the Windows build script | `win32/build.bat` and friends |
| Network access during the build | `spack-build-out.txt` showing downloads |

### Stopping it

```python
# CMake FetchContent
args.append(self.define("FETCHCONTENT_FULLY_DISCONNECTED", True))

# Common upstream switches — names vary, read the CMakeLists
args.append(self.define("USE_SYSTEM_ZLIB", True))
args.append(self.define("<PKG>_USE_EXTERNAL_<DEP>", True))

# Point discovery at the Spack prefix
args.append(self.define("ZLIB_ROOT", self.spec["zlib-api"].prefix))
```

Where no switch exists, a patch removing the fetch and substituting `find_package` is appropriate
and encouraged — it is exactly the kind of contained Windows-specific patch that is worth carrying.

Then add the real `depends_on` for whatever was being vendored.

### The narrow exemption

A vendored dependency may stay only when it genuinely cannot be replaced:

- a proprietary binary that cannot be built from source
- a POSIX-only component that could not run on Windows even under the future POSIX build
  environment

"It is inconvenient to package" is not an exemption. Note the exemption in a comment so the next
person knows it was a decision rather than an oversight.

---

## Conflicts and version gating

When upstream changes its build system and Spack has not caught up, gate by version rather than
dropping Windows support wholesale. From `libxml2`:

```python
# Build system changed in 2.14, and isn't yet implemented in Spack.
conflicts("@2.14: platform=windows")
```

This keeps the versions that do work on Windows working, and states plainly why the newer ones do
not. Always include the explanatory comment — a bare `conflicts` line is an unexplained dead end.

For Windows-specific patches, gate them the same way (from `netcdf_c`):

```python
patch("4.8.1-win-hdf5-with-zlib.patch", when="@4.8.1:4.9.2 platform=windows")
```

Windows-specific patches to source and build systems are encouraged. Keep them narrow and gated so
they cannot affect other platforms.

---

## Language dependencies and Fortran

Declare language dependencies explicitly:

```python
depends_on("c", type="build")
depends_on("cxx", type="build")
depends_on("fortran", type="build")
```

Fortran on Windows is the awkward case. Spack currently models `msvc` as supplying the
Fortran compiler in some configurations, even though MSVC has no Fortran — a modeling artifact
noted in `build_systems/cmake.py`, where a `depends_on("cmake@4.1:", when="%cxx=msvc %fortran=msvc")`
line sits commented out for that reason. Real Fortran on Windows means oneAPI (`ifx`) or flang.

If a package is Fortran-heavy, confirm the toolchain story before promising a Windows port; this
is a legitimate reason to land in the Contingent bucket.

---

## Tags

```python
tags = ["core-packages", "windows"]
```

Add `"windows"` only when the package genuinely builds and works on Windows. It is a discovery
signal for other people doing Windows work, so a speculative tag is actively misleading. Used
in-repo by `openssl`, `hdf5`, `curl`, `cmake`, and ~23 others.
