# Ryugraph Extension Server ARM64 Issue - Investigation Report

**Date:** 2025-12-15
**Status:** Resolved
**Affected:** E2E tests for native algorithms (PageRank, WCC, SCC, Louvain, K-Core) and NetworkX algorithms

## Executive Summary

The Ryugraph wrapper E2E tests fail on ARM64 hosts (Apple Silicon Macs) because the Predictable Labs extension server (`ghcr.io/predictable-labs/extension-repo:latest`) contains incorrectly packaged ARM64 binaries. The `linux_arm64` directory actually contains x86-64 (AMD64) ELF binaries.

**Solution:** Build and run all E2E test containers as AMD64 (linux/amd64). On ARM64 Macs, these run via Rosetta 2 (Apple's fast binary translation). This has been verified to work.

## Background

### KuzuDB vs Ryugraph

| Feature | KuzuDB v0.11.3 | Ryugraph v25.9.2 |
|---------|---------------|------------------|
| Status | Archived (Oct 2025) | Active fork by Predictable Labs |
| Algo extension | Pre-installed, pre-loaded | Requires extension server |
| Extension server | `ghcr.io/kuzudb/extension-repo` | `ghcr.io/predictable-labs/extension-repo` |
| Version scheme | 0.x.x | 25.x.x |

### Extension Loading Mechanism

1. **INSTALL** downloads the extension binary from the extension server
2. **LOAD** loads the extension into the current connection
3. Extensions are connection-scoped (must reload per connection)

```cypher
-- Install from extension server (downloads binary)
INSTALL algo FROM 'http://extension-server:80/';

-- Load into current connection
LOAD algo;
```

## Root Cause Analysis

### Problem Discovery

When running E2E tests on an Apple Silicon Mac with k3d/OrbStack:

```
RuntimeError: IO exception: Failed to load library:
/home/wrapper/.ryu/extension/25.9.0/linux_arm64/algo/libalgo.ryu_extension
Error: cannot open shared object file: No such file or directory.
```

The file exists (453,888 bytes) but cannot be loaded as a shared library.

### Binary Architecture Verification

Inspected the ELF header of the downloaded extension:

```bash
# Check magic bytes at position 18 (machine type)
head -c 20 libalgo.ryu_extension | xxd

00000000: 7f45 4c46 0201 0103 0000 0000 0000 0000  .ELF............
00000010: 0300 3e00                                ..>.
```

- `7f45 4c46` = ELF magic number (correct)
- `0300 3e00` at position 18 = machine type `0x003e` = **x86-64 (AMD64)**
- ARM64 should be `0xb7` = 183

**Conclusion:** The extension server's `linux_arm64` directory contains x86-64 binaries, not ARM64 binaries.

### Extension Server Contents Verification

```bash
# Verified on extension server container
/usr/share/nginx/html/v25.9.0/
├── linux_amd64/algo/libalgo.ryu_extension  # x86-64 binary
├── linux_arm64/algo/libalgo.ryu_extension  # x86-64 binary (WRONG!)
├── osx_amd64/algo/libalgo.ryu_extension
├── osx_arm64/algo/libalgo.ryu_extension
└── win_amd64/algo/libalgo.ryu_extension
```

## Platform-Specific Behavior

### macOS (Apple Silicon)

```python
# Works without extension server!
conn.execute('LOAD algo')  # SUCCESS
```

The macOS Python wheel appears to bundle the algo extension, or uses a different loading mechanism.

### Linux AMD64

```python
# Works with extension server
conn.execute("INSTALL algo FROM 'http://extension-server/'")  # SUCCESS
conn.execute('LOAD algo')  # SUCCESS
```

### Linux ARM64

```python
# INSTALL succeeds (downloads file)
conn.execute("INSTALL algo FROM 'http://extension-server/'")  # SUCCESS

# LOAD fails (wrong binary architecture)
conn.execute('LOAD algo')  # FAILS - cannot load x86-64 on ARM64
```

## Solution

### Why Emulation is Required

The fundamental constraint: **You cannot load an x86-64 shared library (`.so`) into an ARM64 process**. This is an OS-level restriction, not something we can work around in code.

When Ryugraph calls `dlopen()` on the algo extension:
- The extension binary must match the CPU architecture of the running process
- Extension server serves x86-64 binaries for `linux_arm64` (the bug)
- An ARM64 Ryugraph process cannot load x86-64 code

Therefore, we must run Ryugraph itself as x86-64, which requires the entire container to be x86-64.

### Implemented: AMD64 Container Build

Modified `tests/e2e/conftest.py` to build all containers for `linux/amd64`:

```python
@pytest.fixture(scope="session")
def docker_images_built(monorepo_root: Path) -> dict[str, str]:
    """Build Docker images for the stack.

    Builds for linux/amd64 platform to ensure compatibility with the
    Ryugraph extension server (which provides x86-64 binaries only).
    On ARM hosts (Apple Silicon), images run via Rosetta 2.
    """
    # Build with: docker buildx build --platform linux/amd64 --load
    ...
```

Also updated `deployed_extension_server` fixture to pull AMD64 image:

```python
# Pull AMD64 version of extension server (ARM64 binaries are broken)
subprocess.run(
    ["docker", "pull", "--platform", "linux/amd64", extension_image],
    check=True,
)
```

### Rosetta 2 vs QEMU

On Apple Silicon Macs with OrbStack or Docker Desktop:
- **Rosetta 2**: Apple's binary translation layer, very fast (~80-90% native speed)
- **QEMU**: Software emulation, much slower (~10-20% native speed)

OrbStack and modern Docker Desktop use Rosetta 2 automatically for AMD64 containers, so runtime performance is acceptable. However, **building** AMD64 images on ARM64 is still slower than native builds.

### Verification

Manual test in k3d cluster with AMD64 images:

```
Ryugraph version: 25.9.2
Platform: x86_64 (should be x86_64)
Extension server: http://extension-server.test-e2e.svc.cluster.local:80
Running: INSTALL algo FROM 'http://extension-server.../'
SUCCESS: INSTALL algo
Running: LOAD algo
SUCCESS: LOAD algo
SUCCESS: page_rank!
Results:
  ['Alice', 0.07500000000000001]
  ['Bob', 0.13875]

=== ALL AMD64 TESTS PASSED ===
```

## Resolution

### Bug Fix: AttributeError in Algorithm Routers

The 500 Internal Server Error was caused by a bug in `routers/algo.py` and `routers/networkx.py`:

```python
# Bug: algorithm_type is already a string (Pydantic converts enum to str)
algorithm_type=execution.algorithm_type.value,  # AttributeError: 'str' has no attribute 'value'

# Fix: Remove .value call
algorithm_type=execution.algorithm_type,
```

The `AlgorithmExecution` model defines `algorithm_type: str`, so Pydantic automatically converts the enum value to a string. The router code incorrectly assumed it was still an enum.

### Final Test Results

```
======================== 40 passed in 259.53s (0:04:19) ========================
```

All tests passing:
- **12 deployment tests:** Cluster health, control plane, namespace isolation
- **10 query tests:** Cypher queries, schema, mutations blocked
- **8 native algorithm tests:** PageRank, WCC, SCC, SCC-Kosaraju, Louvain, K-Core
- **5 NetworkX algorithm tests:** Betweenness, closeness, degree centrality
- **5 other tests:** Locking, result persistence, API endpoints

## Solution Options Comparison

| Option | Emulation Required? | Build Speed | Runtime Speed | Complexity | Recommended? |
|--------|---------------------|-------------|---------------|------------|--------------|
| AMD64 + Rosetta 2 (current) | Yes (fast) | Slow first build | ~90% native | Low | **Yes - CI & local** |
| Pre-built images from registry | Yes (fast) | N/A (pull only) | ~90% native | Medium | **Yes - local only** |
| Skip algo tests on ARM64 | No | Native | Native | Low | Acceptable |
| Fix extension server upstream | No | Native | Native | N/A | Best long-term |
| Build custom ARM64 extensions | No | Native | Native | High | Not recommended |

### Option 1: AMD64 + Rosetta 2 (Implemented)

Build all containers as `linux/amd64`. On ARM64 Macs, Rosetta 2 provides fast binary translation.

**Pros:** Works everywhere, single approach for CI and local
**Cons:** First build is slow (~5-10 min), subsequent builds use cache

**Best for:** CI (GitHub Actions runs AMD64 natively) and local development

### Option 2: Pre-built Images from Registry

Build AMD64 images in CI, push to container registry, pull for local testing.

```bash
# In CI (runs natively on AMD64)
docker buildx build --platform linux/amd64 -t ghcr.io/org/wrapper:e2e --push .

# On local ARM64 Mac (fast pull, fast runtime via Rosetta 2)
docker pull ghcr.io/org/wrapper:e2e
```

**Pros:** No local build overhead, fast iteration
**Cons:** Requires CI pipeline and registry setup

**Best for:** Teams with CI/CD infrastructure

### Option 3: Skip Algorithm Tests on ARM64

Mark algorithm E2E tests to skip on ARM64. Run full suite only in CI.

```python
import platform

@pytest.mark.skipif(
    platform.machine() in ('arm64', 'aarch64'),
    reason="Ryugraph extension server ARM64 binaries are broken"
)
class TestNativeAlgorithms:
    ...
```

**Pros:** Fast local development, no emulation overhead
**Cons:** Algorithm tests only run in CI, not locally

**Best for:** Developers who primarily work on non-algorithm features

### Option 4: Report Bug to Predictable Labs

File issue at https://github.com/predictable-labs/ryugraph requesting proper ARM64 binaries.

**Pros:** Fixes root cause for everyone
**Cons:** Unknown timeline, dependency on external maintainers

**Status:** Should be done regardless of other solutions

### Option 5: Build Custom ARM64 Extension Server

Compile the algo extension from Ryugraph source for ARM64 Linux, host in custom extension server.

**Pros:** Full native ARM64 support
**Cons:** Complex build process, ongoing maintenance burden, must track upstream changes

**Not recommended** unless ARM64 performance is critical

## Files Modified

1. `tests/e2e/conftest.py`
   - `docker_images_built`: Added `--platform linux/amd64` to buildx commands
   - `deployed_extension_server`: Added explicit AMD64 pull before k3d import

2. `src/wrapper/routers/algo.py`
   - Lines 101, 154: Removed `.value` call on `algorithm_type` (already a string)

3. `src/wrapper/routers/networkx.py`
   - Line 127: Removed `.value` call on `algorithm_type` (already a string)

## References

- KuzuDB Extension Docs: https://docs.kuzudb.com/extensions/
- Ryugraph Docs: https://github.com/predictable-labs/ryugraph-docs
- Extension Server Image: `ghcr.io/predictable-labs/extension-repo:latest`
- ELF Machine Types: https://en.wikipedia.org/wiki/Executable_and_Linkable_Format

## Appendix: Native Algorithms Requiring Algo Extension

| Algorithm | Function | Description |
|-----------|----------|-------------|
| PageRank | `page_rank()` | Node importance ranking |
| WCC | `weakly_connected_components()` | Connected components (undirected) |
| SCC | `strongly_connected_components()` | Connected components (directed) |
| SCC Kosaraju | `strongly_connected_components_kosaraju()` | DFS-based SCC |
| Louvain | `louvain()` | Community detection |
| K-Core | `k_core_decomposition()` | Core decomposition |

All require:
1. `project_graph()` to create projected graph
2. Algorithm function call
3. `drop_projected_graph()` to clean up
