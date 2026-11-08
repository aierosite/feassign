# Fresh-source local reproduction

## Guided startup

The [judge handoff](../JUDGING.md) gives a small native first look and a complete
review. With Python 3.10+, `cc`, Linux x86-64 and glibc >= 2.39:

```sh
python3 tools/review.py native --download
python3 tools/review.py full --download
```

The first command needs only the pinned Fe asset. The second also needs
Anvil/cast and invokes the same 11-stage reproduction described below.
`--download` opts into official, checksum-verified GitHub releases in
`.cache/reviewer-tools`; it does not install packages or change PATH globally.
Without it, pass `--fe`, `--anvil` and `--cast` paths as needed, or use the
verified local cache/PATH. Wrong tool bytes are rejected before executing them.
Each invocation keeps a fresh output directory and a `review.json` with the
actual result; a failed review exits nonzero and preserves its logs.

Run in WSL rather than Windows Python on a Windows host. An unsupported
architecture/libc, missing `cc` or disabled Python assertions stops preflight.
If a download fails, check outbound access to the official release URL or
provide an already downloaded asset after checking its SHA in toolchain.json.
An existing wrong cache is not silently replaced. Choose another verified tool
path. For an already-used `--out`, omit that option to get a fresh directory.

## Manual tool setup and complete scope

Requirements are Linux x86-64 (WSL works), Python3.10+, a C compiler named cc,
the exact official Fe26.5.1 Linux asset and Foundry Anvil/cast1.8.7. Exact
commits/asset hashes are in [toolchain.json](../toolchain.json). Download
[Fe26.5.1](https://github.com/argotorg/fe/releases/tag/v26.5.1)'s
`fe_linux_amd64` executable and
[Foundry1.8.7](https://github.com/foundry-rs/foundry/releases/tag/v1.8.7)'s
`foundry_v1.8.7_linux_amd64.tar.gz`; extract `anvil` and `cast` from that archive.
Compare SHA-256 for the Fe binary, Foundry archive and both extracted binaries
with their Linux fields in toolchain.json. Give the three binaries executable
permission and keep them in a separate tool directory. The command below takes
their absolute paths. The workflow uses Python's standard library and local
processes; keep tool binaries outside the source package. The runners need
readable `/proc/net/tcp` and `/proc/<owned-child-pid>/fd` to check listener
ownership before local RPC; environment proxies are bypassed.

The tested environment is Ubuntu24.04 x86-64 under WSL, glibc2.39,
Python3.12.3 and GCC13.3. The pinned Fe executable requires GLIBC_2.39 symbols.
These GNU/Linux assets use /lib64/ld-linux-x86-64.so.2 and the libc/libm/libgcc
runtime libraries; cast also needs libudev.so.1. Ensure those existing binary
dependencies are available in the build environment. The ELF requirements and
this tested environment do not establish compatibility with every Linux image.

From a fresh extraction/check-out of this source:

```sh
python3 tools/reproduce.py --fe "/absolute/path/to/fe" --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --out target/repro-01
```

The output directory must be new. Inside the source tree, use target/; other
locations there are rejected before directory creation. The script creates fresh
outputs, temporary files and caches without deleting an older run. It checks the compiler bytes,
executes the8 model and46 API functions on each native/EVM backend,2 EVM board
functions and5 intended compiler rejections. It builds/runs the complete demo,
then2906 actual native certificate/verify roundtrips,43 classified negatives,
descriptor/I/O tests, the15-transaction full32 campaign and40-transaction ABI
edge campaign. All owned localhost nodes must stop. Source bytes must remain
unchanged. Logs include commands, exit codes, versions, hashes, receipt/status,
state and observed limits. Local success is not a remotely executed CI result.
Each owned node defaults to a fresh OS-selected loopback port, avoiding reuse
of a fixed port still reserved after a preceding process has stopped.

For a smaller first look, run only the command in DEMO.md. Individual test/build
commands are in README.md. Advanced protocol checks can use that demo's actual
artifacts without a second optimizer:

The [external-certificate replay](INTEROPERABILITY.md) uses the same checker
with `--certificate`, validating a supplied witness before starting its node.
The default and `--abi-edges` commands below retain their original scenarios.

```sh
python3 tools/check-board.py --build-dir target/demo-01/board --executable target/demo-01/native/feassign --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --evidence target/full32-01
python3 tools/check-board.py --build-dir target/demo-01/board --executable target/demo-01/native/feassign --anvil "/absolute/path/to/anvil" --cast "/absolute/path/to/cast" --evidence target/abi-01 --abi-edges
```

The protocol checker matches compiler metadata source content to the current
assignment/board files before accepting artifacts. It records deployed code
including immutables, not just emitted runtime. The metadata is not treated as
proof of transaction success; receipts and relevant getters/state establish it.

For an exported immutable source snapshot, a SOURCE_COMMIT file may contain its
full40-hex Git SHA; reproduce.json records it and all source-file hashes. The
snapshot/archive digest, full commit and evidence directory must be recorded
by the packaging step. An output/cache-fresh run from the development directory
alone is not relabelled as a fresh-source extraction.

Current evidence remains checkpoint-specific. Owner review was reported complete
with no issues on November 8, 2026, before the reviewer-startup changes. The
previous submitted commit passed registration/deadline checks; technical review,
the exact replacement submission and the later scheduled freeze are separate facts.
Publication is not performed by these scripts. The demo's loopback-only node
and test accounts never connect a wallet, remote RPC or real-fund network.
