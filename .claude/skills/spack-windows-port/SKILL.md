---
name: spack-windows-port
description: Add a new Spack package, or port an existing one to build natively on Windows with MSVC or clang-cl. Use this for EVERY request to add, create, or write a new Spack package.py recipe, including bare requests like "add a package for libfoo" or "we need X in spack", because Windows support must be assessed as part of adding any package rather than bolted on later. Do not wait for the user to mention Windows, MSVC, or any Windows tool; they usually will not, and this skill decides how much Windows work is warranted. Also use it whenever Spack package work touches Windows, MSVC, cl.exe, nmake, MSBuild, .lib/.dll/import libraries, dllexport, or LNK/C1083 build errors; when a Windows build fails with unresolved externals or a missing import library; or when deciding whether a package needs a Windows-specific build system, variant, or conflict. Trigger even if the user never says "Spack" or "Windows", so long as the working tree is a Spack package repository.
---

# Spack: add a package, port it to Windows

Windows support is part of what "adding a package" means here, not a follow-up someone has to
remember to request. So this skill runs on every new-package request, assesses how much Windows
work is actually warranted, and does that much — no more.

The counterweight matters as much as the rule: **effort must be proportionate to difficulty.**
Most packages are either free on Windows or hopeless on Windows, and both verdicts are cheap to
reach. Phase 0 exists to reach them cheaply. A skill that turns a routine `py-foo` addition into a
porting project will get routed around, and then nothing gets ported.

## The five non-negotiables

Every decision downstream follows from these, so they come first.

1. **Build from source.** Binary downloads only where genuinely impossible — MSVC itself, vendor
   SDKs. A prebuilt library that *could* be compiled is not an acceptable shortcut; it defeats the
   point of Spack.
2. **Never degrade Linux, FreeBSD, or macOS.** Refactor freely; remove nothing. If a package has
   an Autotools build, *add* the CMake or NMake path beside it — never swap it out. Existing users
   have pinned specs that must keep concretizing and building identically.
3. **Native toolchain only.** MSVC or clang-cl for C/C++, oneAPI or flang for Fortran. MSYS and
   Cygwin are not compilers we target.
4. **Prefer the project's own build system.** Carrying a patched-in build system means maintaining
   it forever. Only do it if the whole thing fits in roughly 300 lines. Past that, the honest
   answer is that the package is not portable — say so.
5. **Dependencies first, bottom-up.** A port attempted before its dependencies build is wasted
   work, and the failures it produces are misleading.

## Entry points

**Existing package** → read the current recipe first. Inventory what already works, what is
already Windows-aware, and what is missing. Then go to Phase 0.

**New package** → scaffold with `spack create <url>`, which infers the build system and fills in
versions. Then go to Phase 0.

Both paths converge immediately; the rest of the workflow is shared.

---

## Phase 0 — Windows feasibility triage

Always runs. This is what makes triggering on every package safe: it sizes the Windows work before
any is done. Classification is cheap — it comes from the language, the build system, and a scan for
POSIX-only dependencies.

| Bucket | Signals | What to do |
|---|---|---|
| **Free** | Pure Python with no compiled extension, pure script, header-only, or an existing all-platform CMake build | Windows already works. Add nothing — no guards, no conflicts, no tag. Note it in a sentence and go to Phase 6. |
| **Likely** | CMake present, or a `win32/`-style native build, or upstream CI has a Windows job; dependencies already build on Windows | Run Phases 1–6. |
| **Contingent** | A native Windows build path exists, but one or more dependencies are unported | Name the blocking dependencies, say what porting them entails, and let the user choose the scope before you start climbing the tree. |
| **Infeasible** | Hard POSIX dependency (fork/exec, POSIX-only syscalls, `dl`, X11-only), or no native build system and no viable patch under ~300 lines | Write the recipe for the other platforms, add a commented `conflicts("platform=windows")` recording *why*, and report it. Do not attempt the port. |

State the bucket and its justification as a one-line verdict, not a report. If someone asked for a
Linux package and it lands in Free or Infeasible, the Windows dimension cost them one sentence.

Never expand a routine package addition into a porting project without saying so and getting
agreement first.

Full classification signals and worked examples: `references/triage.md`.

---

## Phase 1 — Dependencies first

Walk `depends_on` bottom-up. For each dependency establish three things: does it exist in this
repo, does it build on Windows today, and is it even *needed* on Windows. That third question
matters most — Windows dependency sets often differ substantially, and porting a dependency the
Windows build never uses is pure waste.

Produce an ordered work list before touching the target package.

→ `references/triage.md`

## Phase 2 — Upstream recon

Start where the project documents itself: `BUILD.md`, `INSTALL.md`, `README`. Then look for a
`win32/`, `msvc/`, or `windows/` subdirectory — that is where Windows port code and build systems
usually live.

The highest-yield single move is mining upstream CI for a Windows job. A green `windows-latest`
job is a working recipe someone already debugged; mimic it for the first pass and build out from
there.

→ `references/triage.md`

## Phase 3 — Choose the build system

The decision tree ends in exactly one of: reuse the existing CMake build, add a CMake build
alongside what exists, `NMakePackage`, `MSBuildPackage`, generic `Package`, or *report as not
portable*.

→ `references/build-systems.md`

## Phase 4 — Write the recipe

Multi-build-system class layout, `build_system()` with `conditional(...)`, shared builder mixins,
variant modeling, and dependency divergence. The recurring trap here is shared-vs-static: CMake on
Windows uses the Ninja generator, which produces static *or* shared per configure, never both.

Also verify the build is not fetching or vendoring its own dependencies on Windows — that is
common in Windows build paths specifically, since upstreams assume no package manager is present.

→ `references/modeling.md`

## Phase 5 — Build and iterate

```
spack solve <spec>        # concretizes? if not, fix modeling before building
spack install <spec>      # then read spack-build-out.txt on failure
```

When a link step fails, check symbol visibility **first**. MSVC hides symbols by default and the
linker emits no import library for a DLL that exports nothing, so a missing `foo.lib` is usually
not a build-order problem — it is a dependency that exported nothing. This misdirects more time
than any other failure mode on Windows.

→ `references/symbols.md` for the visibility fix ladder
→ `references/debug.md` for the error → cause → fix table and log locations

## Phase 6 — Verify no regression, then land

1. Confirm non-Windows behavior is untouched: `spack solve` a Linux spec and compare, then read
   the diff specifically asking "could this change what another platform does?"
2. `.ci/style_check.sh --fix develop` (needs a `spack-core/` clone in the repo root)
3. `spack audit packages`, filtered to the packages you changed
4. Add `tags = [..., "windows"]` only where the package genuinely supports Windows

For the commit, draft-PR, and CI-wait workflow, follow `.github/skills/package-update.md`
Phases 4–8 — it is already written and this skill does not duplicate it.

---

## Concluding a package is not portable

This is a valid, complete outcome — not a failure to work around. Reach it deliberately rather
than by exhaustion, and record the evidence:

- what was tried for symbol visibility (the full ladder in `references/symbols.md`)
- why no native build system fits, or why the patch to add one would exceed ~300 lines
- which dependency is POSIX-only and unfixable, if that is the blocker

Then write the recipe for the platforms that do work, with a commented
`conflicts("platform=windows")` stating the reason. That comment is the deliverable: it stops the
next person from repeating the whole investigation.

## Reference files

| File | Read it for |
|---|---|
| `references/triage.md` | Phase 0 bucket signals; upstream recon; dependency-tree walk |
| `references/build-systems.md` | Choosing and wiring CMake / NMake / MSBuild; multi-build-system layout |
| `references/modeling.md` | shared vs static, variants, dependency divergence, devendoring |
| `references/symbols.md` | dllexport, import libraries — the highest-cost failure class |
| `references/debug.md` | MSVC error → root cause → fix; logs and iteration commands |
