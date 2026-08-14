# Symbol visibility and import libraries

This is the failure class that costs the most time on Windows ports, because the error it produces
points somewhere other than the actual problem. Read this before spending time on a missing `.lib`.

## Why it happens

On ELF platforms, every non-static symbol is exported by default. On Windows, **nothing is
exported unless you say so** — via `__declspec(dllexport)`, a `.def` file, or
`CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS`.

The consequence that misleads people: **the linker produces an import library (`foo.lib`) only if
the DLL exports at least one symbol.** A DLL exporting nothing produces `foo.dll` and no `foo.lib`
at all.

So when a dependent build fails with:

```
LINK : fatal error LNK1181: cannot open input file 'foo.lib'
```

the usual cause is not a build-order problem, not a missing install step, and not a path problem.
It is that `foo` was built as a DLL that exported no symbols. The file was never created.

Libraries that are normally built static, or that were ported to Windows without attention to
visibility, hit this constantly.

## Diagnose first

Before changing anything, confirm the diagnosis:

```powershell
# Does the DLL exist, and does it export anything?
dumpbin /exports <prefix>\bin\foo.dll

# Is there an import library at all, and what is in it?
dumpbin /symbols <prefix>\lib\foo.lib
lib /list <prefix>\lib\foo.lib
```

A `foo.dll` that exists with an empty exports table confirms it. If the DLL itself is missing, the
problem is upstream of this — check whether the build configured static-only (`modeling.md`).

`dumpbin` and `lib` come from the MSVC toolchain; run them inside the build environment:

```
spack build-env <spec> -- dumpbin /exports path\to\foo.dll
```

## Fix ladder

Work down in order. Each step is cheaper than the one after it.

### 1. CMake: export everything automatically

```python
args.append(self.define("CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS", True))
```

or, if patching the project's CMake, the per-target form:

```cmake
set_target_properties(foo PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)
```

This makes CMake generate a `.def` file listing the symbols, which restores approximately ELF
behavior.

**Its real limitation:** it exports functions, not **data** symbols. A library exporting global
variables still needs `__declspec(dllexport)` on those specifically. If the link error names a
variable rather than a function, this flag will not fix it and you should go to step 2.

> There are currently zero uses of this in this repo — it is the correct first move, not an
> established local pattern. Do not go looking for an example to copy.

### 2. Find the project's existing visibility macro

Many projects already have the machinery and simply fail to activate it on this build path. Grep
the headers for:

```
FOO_API, FOO_EXPORT, FOO_PUBLIC, FOO_DECLSPEC
__declspec(dllexport), __declspec(dllimport)
__attribute__((visibility("default")))
```

The usual shape:

```c
#if defined(_WIN32)
#  if defined(FOO_BUILDING_DLL)
#    define FOO_API __declspec(dllexport)
#  else
#    define FOO_API __declspec(dllimport)
#  endif
#else
#  define FOO_API __attribute__((visibility("default")))
#endif
```

When this exists but symbols still are not exported, the cause is nearly always that
`FOO_BUILDING_DLL` (or its equivalent) is not defined while compiling the library. Fix it in the
build arguments:

```python
args.append(self.define("CMAKE_C_FLAGS", "-DFOO_BUILDING_DLL"))
# or, better, patch the CMakeLists to use target_compile_definitions(foo PRIVATE FOO_BUILDING_DLL)
```

The mirror-image failure — the library links but *consumers* get `LNK2019 unresolved external` —
means consumers are not getting the `dllimport` side. Check that the macro resolves correctly when
`FOO_BUILDING_DLL` is absent.

### 3. Patch in the visibility control

If the project has no visibility machinery at all, adding it is acceptable and encouraged when the
change is contained — a header defining the macro, plus annotations on the public API. Gate the
patch with `when="platform=windows"` so other platforms are untouched.

This is worth doing for a library with a small, well-defined public API. It is not worth doing for
one exporting hundreds of symbols across many headers — that is upstream's work, and attempting it
produces an unmaintainable patch.

### 4. Conclude it is broken for Windows shared builds

If none of the above applies, the project does not support shared builds on Windows. That is a
legitimate finding. Two acceptable outcomes:

- **Static-only on Windows.** If consumers can use a static library, model it:
  `conflicts("+shared", when="platform=windows")` with a comment explaining why. This is often the
  right interim answer.
- **Report as not portable.** If shared is required, follow the stop condition in SKILL.md and
  record what was tried.

Either way, state explicitly which rungs of this ladder you tried. "It does not build" is not a
finding; "it exports no symbols, has no visibility macros, and annotating its 200-function API is
upstream's work" is.
