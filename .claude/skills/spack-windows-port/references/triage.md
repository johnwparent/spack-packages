# Triage: feasibility buckets, upstream recon, dependency walk

Contents:
- [Phase 0 — bucket classification](#phase-0--bucket-classification)
- [Upstream recon](#upstream-recon)
- [Mining upstream CI](#mining-upstream-ci)
- [The dependency walk](#the-dependency-walk)

---

## Phase 0 — bucket classification

The point of this phase is to spend a few minutes deciding how many hours the package deserves.
Classify, state the verdict in one line, act accordingly.

### Free — Windows already works, add nothing

Signals:

- `PythonPackage` with no compiled extension. Check `pyproject.toml` / `setup.py` for
  `ext_modules`, `cffi`, `Extension(...)`, or a `build-backend` like `setuptools` with no C.
  Pure-Python wheels install identically everywhere.
- Header-only C++ library — no compiled artifacts means no linker, no symbol visibility, no
  import libraries. Most of what makes Windows hard does not apply.
- An existing CMake build with no platform guards excluding Windows, and no POSIX-only
  dependencies.
- Pure script/data packages.

Action: say Windows works, add no guards, no `conflicts`, no `windows` tag, and go to Phase 6.
Adding Windows machinery to a package that does not need it is a net negative — it implies a
constraint that is not real and someone will maintain it forever.

### Likely — run the full workflow

Signals:

- `CMakeLists.txt` at the root, especially with `if(WIN32)` / `if(MSVC)` branches that *add*
  Windows handling rather than error out.
- A `win32/`, `msvc/`, `windows/`, or `build/windows/` subdirectory.
- Upstream CI has a Windows job (see below).
- The dependency set is small and already ported.

Action: Phases 1 through 6.

### Contingent — dependencies block it

Signals: the package itself looks portable, but `depends_on` names one or more packages that do
not build on Windows today.

Action: name the blockers explicitly, estimate what each involves, and let the user pick the
scope. Do not silently start porting a five-deep dependency chain — that is a different and much
larger piece of work than what was asked for.

### Infeasible — record why, do not attempt

Signals:

- Hard POSIX process model: `fork()`, `exec*()`, `wait()`, POSIX signals used structurally rather
  than incidentally. These have no native Windows equivalent, and shimming them is a rewrite.
- POSIX-only syscalls: `mmap` with fork semantics, `dlopen`/`dlsym` as the core mechanism,
  `termios`, `sys/socket.h` used without an abstraction layer.
- X11-only, or depends on an X11-only package with no Windows backend.
- Autotools-only with no native build system, where writing one would exceed ~300 lines.
- The upstream explicitly documents Windows as unsupported and the code confirms it.

Action: write the recipe for the working platforms, add a commented `conflicts` recording the
reason, report the finding. For example:

```python
# fork()/exec() based process supervision has no native Windows equivalent;
# upstream targets POSIX only. See src/supervisor.c.
conflicts("platform=windows")
```

The comment is what makes this a deliverable rather than a dead end.

---

## Upstream recon

### Read the project's own docs first

`BUILD.md`, `INSTALL.md`, `README.md`, `docs/building.rst`. Windows instructions, when they exist,
are usually explicit about which toolchain and which build file. This is faster and more reliable
than inferring intent from the source tree.

### Where Windows build code hides

| Path / file | What it means |
|---|---|
| `win32/`, `win/`, `windows/`, `msvc/` | Dedicated Windows port directory — the first place to look |
| `build/windows/`, `contrib/vs/` | Same, less common layouts |
| `*.sln`, `*.vcxproj` | Visual Studio solution → `MSBuildPackage` |
| `Makefile.msvc`, `Makefile.vc`, `makefile.msc`, `nmakefile` | nmake makefile → `NMakePackage` |
| `configure.js`, `configure.bat`, `*.ps1` | Script-driven configure step preceding nmake (libxml2 does this) |
| `CMakeLists.txt` | Possibly usable directly — verify it is Windows-clean, not just Windows-guarded |
| `meson.build` | Meson supports MSVC natively; may work with little effort |

A `win32/` directory that only contains a stale VS6 project is worse than nothing — check whether
it is maintained before committing to it.

### Verifying a CMake build is actually Windows-clean

The presence of `CMakeLists.txt` is not sufficient. Look for:

- `if(UNIX)` blocks with no `else()` — functionality silently missing on Windows
- `find_package` for POSIX-only libraries without a Windows alternative
- Hardcoded `/usr/...` paths, `pkg_check_modules` as the only discovery path
- `target_link_libraries(... dl pthread m)` unguarded — those do not exist on Windows
- Symbol visibility handled only via `-fvisibility=hidden` with no `__declspec` equivalent —
  see `symbols.md`, this predicts a missing-import-library failure

---

## Mining upstream CI

This is the highest-yield single move in the whole workflow. A green Windows CI job is a working
build recipe someone already debugged, including the exact flags and dependency versions.

Where to look:

| File | Look for |
|---|---|
| `.github/workflows/*.yml` | `runs-on: windows-latest`, `windows-2022`, matrix entries with `os: windows` |
| `appveyor.yml` | AppVeyor is Windows-first; the whole file is usually relevant |
| `azure-pipelines.yml` | `vmImage: 'windows-latest'` |
| `.gitlab-ci.yml` | `tags:` naming a Windows runner |

What to extract and translate into Spack:

- The configure command and its full flag list → `cmake_args()` / `nmake_args()`
- Which dependencies are installed in the job (vcpkg, chocolatey, or manual) → the real Windows
  `depends_on` set, which is often smaller than the POSIX one
- Whether it builds shared or static, and whether it builds both → informs variant modeling
- Any `set CL=` / `set LINK=` environment fiddling → likely needed in `setup_build_environment`

If CI installs a dependency via vcpkg, that dependency is required on Windows and needs a Spack
package. If CI *skips* a dependency on Windows that POSIX builds require, that is a strong signal
to gate it with `when=` rather than porting it.

---

## The dependency walk

Work bottom-up. For each entry in `depends_on`, answer three questions in this order:

**1. Is it needed on Windows at all?**

Commonly *not* needed on Windows:

| Dependency | Why |
|---|---|
| `pkgconfig` | Windows builds rarely use pkg-config discovery; CMake/nmake find deps directly |
| `libtool`, `autoconf`, `automake`, `m4` | Autotools machinery; irrelevant to CMake/NMake paths |
| `dl`, `libdl` | `dlopen` is POSIX; Windows uses `LoadLibrary` |
| `pthread` | Windows threads or the CRT provide this |
| X11 stack (`libx11`, `libxext`, ...) | No X11 on native Windows |
| `iconv` | Often replaceable with the Win32 API; libxml2 passes `iconv=no` on Windows |
| `readline`, `ncurses` | POSIX terminal handling |

Commonly needed *only* on Windows:

| Dependency | Why |
|---|---|
| `win-sdk` | Windows SDK headers and libraries |
| `win-wdk` | Driver kit, for packages needing it |
| `wgl` | OpenGL on Windows |
| `msmpi` | MPI implementation on Windows |
| `nasm` | Assembler; openssl needs it on Windows specifically |
| `winbison`, `win-flex` | Windows builds of the parser generators |

**2. Does it exist in this repo?** `ls repos/spack_repo/builtin/packages/<name>` — note that
directory names use underscores while Spack names use hyphens (`py_numpy` ↔ `py-numpy`).

**3. Does it build on Windows today?** Check for `conflicts("platform=windows")`, a
`tags = [..., "windows"]` marker, or Windows-specific handling in its recipe. `spack solve` on a
Windows spec is the definitive test.

Record the answers as an ordered work list — deepest unported dependency first — and confirm the
scope with the user before starting on it if the list is longer than one or two entries.
