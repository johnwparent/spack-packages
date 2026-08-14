# Choosing and wiring a Windows build system

Contents:
- [Decision tree](#decision-tree)
- [CMake on Windows](#cmake-on-windows)
- [NMakePackage](#nmakepackage)
- [MSBuildPackage](#msbuildpackage)
- [Multi-build-system class layout](#multi-build-system-class-layout)
- [Paths with spaces: windows_sfn](#paths-with-spaces-windows_sfn)
- [POSIX-on-Windows fallback](#posix-on-windows-fallback)

---

## Decision tree

Work down this list and stop at the first match.

1. **Root `CMakeLists.txt` that is genuinely Windows-clean** → reuse it. `CMakePackage` already
   works on Windows; you may need Windows-specific `cmake_args()` but not a new build system.
2. **Root `CMakeLists.txt` that is Windows-*guarded* (excludes rather than supports)** → assess
   whether the gaps are small. Patching a few `if(UNIX)` blocks is fine; rewriting the build is
   not.
3. **`*.sln` / `*.vcxproj` present and maintained** → `MSBuildPackage`.
4. **`Makefile.msvc` / `makefile.msc` / `Makefile.vc` present** → `NMakePackage`, possibly with a
   script-driven configure phase first.
5. **No native build system, but the project is small and modern** → consider adding a CMake
   build, only if it stays under roughly 300 lines. Beyond that the maintenance cost exceeds the
   value; see the non-negotiables.
6. **Build steps are simple and imperative (copy headers, run a compiler, install)** → generic
   `Package` with a hand-written `install()`.
7. **None of the above** → report as not portable. See the stop condition in SKILL.md.

Whichever you pick, adding it must not change what any other platform does.

---

## CMake on Windows

**The generator is Ninja, not Visual Studio.** `CMakeBuilder.std_args` in
`repos/spack_repo/builtin/build_systems/cmake.py` sets
`default_generator = "Ninja" if sys.platform == "win32" else "Unix Makefiles"`.

Consequences that matter:

- Ninja is a **single-config generator**, so `CMAKE_BUILD_TYPE` applies normally (no
  `--config Release` needed, no multi-config layout).
- One configure produces **either** static **or** shared libraries, never both. If the package
  models static and shared as simultaneously buildable, that modeling is wrong on Windows — see
  `modeling.md`.
- Do not write `cmake_args()` that assume a Visual Studio generator (`CMAKE_CONFIGURATION_TYPES`,
  per-config output subdirectories).

Common Windows-specific `cmake_args()` additions:

```python
def cmake_args(self):
    args = [...]
    if self.spec.satisfies("platform=windows"):
        # export all symbols when upstream lacks __declspec annotations
        args.append(self.define("CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS", True))
    return args
```

See `symbols.md` before reaching for that flag — it has real limitations.

---

## NMakePackage

Defined in `repos/spack_repo/builtin/build_systems/nmake.py`. It declares
`conflicts("platform=linux")` and `conflicts("platform=darwin")` scoped to `build_system=nmake`,
so it can coexist with POSIX build systems in the same class.

Phases are `("build", "install")` — add `"configure"` yourself if the project needs one.

| Override | Purpose |
|---|---|
| `makefile_name` | Passed as `/F<name>`. Needed when several makefiles share a directory (e.g. `Makefile.msvc`). |
| `makefile_root` | Directory containing the makefile; `build_directory` derives from it. |
| `build_directory` | Directly override if `makefile_root` is not enough. Already wrapped in `windows_sfn`. |
| `nmake_args()` | Build-phase arguments. Use `self.define("KEY", value)` → `KEY=value`. |
| `nmake_install_args()` | Extra install-phase arguments. `PREFIX=<prefix>` is appended automatically. |
| `build_targets` / `install_targets` | Default install target is `["INSTALL"]`. |
| `ignore_quotes` | Set `True` when arguments legitimately contain quotes or spaces, to suppress Spack's warning. |
| `override_env(var, val)` | Formats `/E<var>=<val>` for overriding environment variables on the nmake command line. |
| `std_nmake_args` | `/NOLOGO` by default. |

Worked example — `repos/spack_repo/builtin/packages/libxml2/package.py`, which adds a `configure`
phase driving a JScript configure script before nmake:

```python
class NMakeBuilder(AnyBuilder, nmake.NMakeBuilder):
    phases = ("configure", "build", "install")

    @property
    def makefile_name(self):
        return "Makefile.msvc"

    @property
    def build_directory(self):
        return windows_sfn(os.path.join(self.stage.source_path, "win32"))

    def configure(self, pkg, spec, prefix):
        with working_dir(self.build_directory):
            opts = [
                "prefix=%s" % windows_sfn(prefix),
                "compiler=msvc",
                "iconv=no",
                "lib=%s" % ";".join((...)),
            ]
            cscript("configure.js", *opts)
```

Note the shape: dependency prefixes are passed as semicolon-joined `lib=` and `include=` lists,
because nmake makefiles do not do dependency discovery.

For a Perl-driven configure instead of JScript, see `openssl/package.py`, which calls
`Executable("perl")("Configure", *args, ignore_quotes=True)` and selects the `VC-WIN64A` target.

---

## MSBuildPackage

Defined in `repos/spack_repo/builtin/build_systems/msbuild.py`. Conflicts with linux, darwin, and
freebsd, scoped to `build_system=msbuild`.

Phases are `("build", "install")`.

| Override | Purpose |
|---|---|
| `build_directory` | Directory containing the `.sln`/`.vcxproj`. Defaults to the source root, `windows_sfn`-wrapped. |
| `msbuild_args()` | Build arguments. `self.define("Key", value)` → `/p:Key=value`. |
| `msbuild_install_args()` | Defaults to `msbuild_args()`. |
| `build_targets` / `install_targets` | Formatted by `define_targets()` into `/target:A;B`. Install default is `["INSTALL"]`. |
| `toolchain_version` | Defaults to `"v" + spec["msvc"].package.platform_toolset_ver`. Override to pin a toolset. |
| `std_msbuild_args` | Supplies `PlatformToolset` automatically — do not set it again in `msbuild_args()`. |

**Expect to override `install`.** Visual Studio solutions rarely define an `INSTALL` target, and
the default install phase will fail if none exists. A hand-written `install()` that copies the
built artifacts into `prefix.lib`, `prefix.bin`, and `prefix.include` is the norm.

---

## Multi-build-system class layout

This is how a package gains a Windows build without losing its POSIX one. The canonical example is
`libxml2`, which carries three:

```python
class Libxml2(AutotoolsPackage, CMakePackage, NMakePackage):
    ...
    build_system(
        conditional("nmake", when="platform=windows"), "cmake", "autotools", default="autotools"
    )
```

Two things make this non-regressing:

- `conditional("nmake", when="platform=windows")` means the nmake value does not even exist as an
  option off Windows, so it cannot be selected accidentally.
- `default="autotools"` is unchanged from before the port. **Never change the default to
  accommodate Windows.** If Windows needs a different build system, express that with
  `conditional(...)`, not by moving the default.

### Sharing logic across builders

Define a mixin and inherit it into each builder, so post-install steps and shared helpers are
written once:

```python
class AnyBuilder(BaseBuilder):
    @run_after("install")
    @on_package_attributes(run_tests=True)
    def import_module_test(self):
        ...

class AutotoolsBuilder(AnyBuilder, autotools.AutotoolsBuilder): ...
class CMakeBuilder(AnyBuilder, cmake.CMakeBuilder): ...
class NMakeBuilder(AnyBuilder, nmake.NMakeBuilder): ...
```

Import the builder modules alongside the package classes:

```python
from spack_repo.builtin.build_systems import autotools, cmake, nmake
from spack_repo.builtin.build_systems.autotools import AutotoolsPackage
from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.nmake import NMakePackage
```

---

## Paths with spaces: `windows_sfn`

`windows_sfn()` converts a path to its 8.3 short form. Use it when passing paths to tools that
split arguments on whitespace — nmake makefiles, JScript/Perl configure scripts, and anything
invoked through a shell that does not quote reliably. `NMakeBuilder.build_directory` and
`MSBuildBuilder.build_directory` already apply it; prefixes and dependency paths you pass yourself
usually need it too.

Spaces in paths get fixed in code — short names, correct quoting, `ignore_quotes` where
appropriate. Telling a user to reinstall somewhere without spaces is not a fix.

Used in-repo by `libxml2`, `curl`, and `perl`.

---

## POSIX-on-Windows fallback

> **Not available on `develop` today.** A Spack-based, Windows-native POSIX build environment is in
> progress. Until it lands, a package with no native Windows build path and no viable patch is
> **Infeasible** — write the recipe for the other platforms with a commented
> `conflicts("platform=windows")` and report it.
>
> When that environment lands, this section is where its guidance goes: which build-system class
> to inherit, how to declare the tool dependencies, and the criteria for choosing it over a native
> port. It is deliberately self-contained so it can be replaced wholesale.
>
> The criterion for when it *would* apply: the project has a working Autotools (or similar POSIX)
> build, no native Windows build system exists, and patching one in would exceed the ~300-line
> budget. It does **not** apply to packages that have a native path — those stay native, per
> non-negotiable #4.
