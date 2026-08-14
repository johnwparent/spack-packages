# Debugging Windows builds

Contents:
- [Error → cause → fix](#error--cause--fix)
- [Where the logs are](#where-the-logs-are)
- [Iterating without rebuilding everything](#iterating-without-rebuilding-everything)
- [Reproducing a failure by hand](#reproducing-a-failure-by-hand)

---

## Error → cause → fix

| Symptom | Usual cause | Where to go |
|---|---|---|
| `LNK1181: cannot open input file 'foo.lib'` | The dependency exported no symbols, so no import library was ever generated. Almost never a path or ordering problem. | `symbols.md` — run the fix ladder |
| `LNK2019: unresolved external symbol` naming a dependency's function | Consumers are not getting the `dllimport` side of the visibility macro, or the library genuinely did not export it | `symbols.md` steps 2–3 |
| `LNK2019` naming a CRT or Win32 function (`__imp_...`) | A required system library is not being linked (`ws2_32`, `advapi32`, `shell32`, ...) | Add to the link line; upstream POSIX builds never needed it |
| `LNK2038: mismatch detected for 'RuntimeLibrary'` | Mixed `/MD` (dynamic CRT) and `/MT` (static CRT) across the dependency graph | Align the CRT choice across every package in the DAG. `openssl` models this explicitly with a Windows-only `+dynamic` variant — see `modeling.md` |
| `LNK2005: symbol already defined` | A symbol exported from two places — often a vendored copy of a dependency alongside the real one | `modeling.md` § devendoring |
| `C1083: Cannot open include file 'foo.h'` | Include directory not propagated to the compile line | Check `include=`/`-I` wiring; nmake builds need explicit `include=` lists |
| `C1083` naming a *flag* rather than a file (e.g. `/MD`) | A POSIX compatibility layer path-converted a slash-flag into a filename | POSIX-env section of `build-systems.md`; not applicable to native builds |
| `C2065`/`C4013` on POSIX functions (`strcasecmp`, `ssize_t`, `unistd.h`) | Code assumes POSIX headers | Small Windows patch, or the package may be Infeasible if pervasive |
| Build succeeds but produces no `.dll` | Static-only configure, or a shared configure that exported nothing | `modeling.md` § shared vs static, then `symbols.md` |
| Build downloads things from the network | Upstream is vendoring dependencies | `modeling.md` § devendoring |
| `fatal error C1041` / PDB write conflicts | Parallel compilation writing one PDB | `/FS`, or reduce jobs for that package |
| Command line too long / path length errors | Windows `MAX_PATH` or command-line limits | Shorter stage path, response files, `windows_sfn` |

When several of these appear at once, fix in dependency order — a broken dependency produces
misleading errors in its dependents.

---

## Where the logs are

| File | Contents |
|---|---|
| `spack-build-out.txt` | Full build output. The first error matters, not the last. |
| `spack-build-env.txt` | The environment the build ran in — check `PATH`, `INCLUDE`, `LIB`, `CL` |
| `spack-configure-args.txt` | Exact arguments passed to the configure step |
| `spack-build-<hash>/` | The build directory itself, inside the stage |

Reach them with:

```
spack cd -b <spec>      # build directory
spack location -b <spec>
```

Read `spack-build-out.txt` from the top. MSVC emits a great deal of output after the first fatal
error, and the tail is usually just the build system unwinding.

---

## Iterating without rebuilding everything

```powershell
# keep the stage so you can inspect and re-run after a failure
spack install --keep-stage <spec>

# stop after a phase — useful to inspect a configure result before building
spack install -u configure <spec>
spack install --until build <spec>

# verbose output when the failure is not in the log
spack install --verbose <spec>

# force a rebuild of just this package
spack install --overwrite <spec>
```

`-u` / `--until` takes a phase name (`configure`, `build`, `install`) and stops after it. Combine
with `--keep-stage` to examine what a configure step actually produced before spending time on a
full build.

For a package you are actively editing, `spack dev-build` also accepts `-u`/`--until` and builds
from a local source directory.

---

## Reproducing a failure by hand

The fastest loop for a stubborn compile or link error is to enter the build environment and run
the failing command directly:

```powershell
# drop into the exact environment Spack used
spack build-env <spec> -- powershell

# or run one command in it
spack build-env <spec> -- cl /c foo.c
spack build-env <spec> -- dumpbin /exports path\to\foo.dll
spack build-env <spec> -- ninja -v
```

This is how to check symbol exports, test a flag, or confirm a header is reachable without waiting
for a full `spack install` cycle.

`ninja -v` is particularly useful — it prints the full command line for each step, which makes it
obvious whether a define or include path actually reached the compiler.

## Checking modeling before building at all

Many Windows failures are modeling errors that never need a compiler to diagnose:

```powershell
spack solve <spec>                 # does it concretize? what did it choose?
spack spec -I <spec>               # what is already installed vs to be built
spack audit packages               # semantic errors in the recipe
```

If `spack solve` hangs rather than erroring, suspect a dependency cycle — the solver's acyclicity
constraint makes cycles unsolvable rather than reportable.
