# Skill: Windows Support for New and Existing Packages

Add a new Spack package, or port an existing one to build natively on Windows with MSVC or
clang-cl. Covers feasibility triage, dependency divergence, build-system selection, symbol
visibility, and the build-and-iterate loop.

**Windows feasibility is assessed for every new package, not only when Windows is mentioned.**
Windows support is part of what adding a package means, not a follow-up someone has to remember to
request. The assessment is cheap — most packages are either free on Windows or clearly infeasible,
and both verdicts cost about a sentence.

Read [`package-update`](package-update.md) for the shared commit, draft-PR, and CI conventions;
this skill does not duplicate them.

## Usage

```
Add a package for libfoo
Port libtiff to build on Windows
Why is this failing with LNK1181: cannot open input file 'zlib.lib'
```

## The five non-negotiables

1. **Build from source.** Binary downloads only where genuinely impossible (MSVC itself, vendor
   SDKs).
2. **Never degrade Linux, FreeBSD, or macOS.** Refactor freely; remove nothing. Add a CMake or
   NMake path beside an existing Autotools build — never swap it out.
3. **Native toolchain only.** MSVC or clang-cl for C/C++, oneAPI or flang for Fortran. Not MSYS or
   Cygwin.
4. **Prefer the project's own build system.** Only carry a patched-in build system if it fits in
   roughly 300 lines; past that, report the package as not portable.
5. **Dependencies first, bottom-up.** A port attempted before its dependencies build is wasted
   work.

## Phases

**Phase 0 — Feasibility triage.** Always runs; sizes the work before any is done.

| Bucket | Signals | Action |
|---|---|---|
| Free | Pure Python (no compiled ext), header-only, existing all-platform CMake | Add nothing; skip to Phase 6 |
| Likely | CMake or `win32/` build present; deps already ported | Run Phases 1–6 |
| Contingent | Native path exists but deps are unported | Name the blockers, confirm scope with the user |
| Infeasible | Hard POSIX dependency, or no native build system and no viable patch | Recipe for other platforms + commented `conflicts("platform=windows")` |

Effort must stay proportionate to difficulty. Never expand a routine package addition into a
porting project without agreement.

**Phase 1 — Dependencies first.** Walk `depends_on` bottom-up: does it exist here, does it build on
Windows, is it even needed on Windows.

**Phase 2 — Upstream recon.** Read `BUILD.md`/`INSTALL.md`/`README`, check for `win32/`, and mine
upstream CI for a Windows job — a green `windows-latest` job is a recipe someone already debugged.

**Phase 3 — Choose the build system.** Existing CMake, added CMake, `NMakePackage`,
`MSBuildPackage`, generic `Package`, or report as not portable.

**Phase 4 — Write the recipe.** Multi-build-system layout via
`build_system(conditional("nmake", when="platform=windows"), ...)` without changing the default on
other platforms. Watch shared-vs-static: CMake uses the Ninja generator on Windows, so one
configure yields static *or* shared, never both. Verify the build is not vendoring dependencies.

**Phase 5 — Build and iterate.** `spack solve` → `spack install` → read `spack-build-out.txt`.
Check symbol visibility first on link failures: MSVC hides symbols by default, and no import
library is emitted for a DLL that exports nothing, so a missing `foo.lib` usually means `foo`
exported nothing.

**Phase 6 — Verify no regression, then land.** Confirm non-Windows concretization is unchanged, run
`.ci/style_check.sh --fix develop` and `spack audit packages`, add the `windows` tag only where
Windows genuinely works. Then follow [`package-update`](package-update.md) Phases 4–8.

## Full detail

The complete skill, including the MSVC error → cause → fix table and the symbol-visibility fix
ladder, lives at `.claude/skills/spack-windows-port/`:

| File | Covers |
|---|---|
| `SKILL.md` | Workflow and phase detail |
| `references/triage.md` | Bucket signals, upstream recon, dependency walk |
| `references/build-systems.md` | CMake / NMake / MSBuild wiring, multi-build-system layout |
| `references/modeling.md` | shared vs static, dependency divergence, devendoring |
| `references/symbols.md` | dllexport and import libraries |
| `references/debug.md` | Error → cause → fix, logs, iteration commands |
