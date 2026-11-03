# Initial full32 representation gate

Observed November 3, 2026, after the actual contest opening, with Fe26.5.1
commit `149c758503563ebd6ad7237b85e28a94dca6e22a`.

The single directed test initializes all 1,024 row-major i64 cells, moves owned
storage into a private-field Problem, reads through shared references, checks
offsets above255 and both i64 endpoints, and sums the complete matrix in i256.
The independently derived expected sum is -512. It is a representation test;
it does not optimize an assignment or verify a dual certificate.

| Profile | Observed outcome |
|---|---|
| EVM / sonatina `-O 0` | Runtime StackOverflow; failure preserved |
| EVM / sonatina `-O 1` | One test passed; repeated once to capture emitted code |
| Linux native `-O 0` | One test passed |
| Linux native `-O 1` | One test passed |

An earlier compile attempt rejected a lossy usize-to-i64 cast in test-data
construction. It was replaced with a checked narrowing. That compile failure
and the separate EVM runtime failure remain in the dated execution records.
The optimization-dependent StackOverflow has not been diagnosed as a specific
compiler defect or repaired in the compiler. The supported measured EVM profile
here is `-O 1`; the full problem domain has not been reduced.

Inspected EVM IR retains `[i64;1024]` storage, runtime fill/read loops, shared
object-reference access, widened index multiplication and sign extension to
i256. This rules out reporting only an entirely folded scalar checksum as the
representation observation. It does not prove all future host-input paths.

The EVM test report contains20,887 runtime bytes and20,902 initcode bytes.
Native test ELF sizes are278,552 bytes atO0 and167,688 bytes atO1. These include
test code/harness and fixture initialization; they are not production library,
CLI or AssignmentBoard sizes or universal bounds. No board transaction/gas,
ordinary deployment-limit or full-size certificate result is established here.

The EVM debug report's target-only IR export says the library runtime package
has no root objects. Per-test IR/code and the successful test result exist
separately. The diagnostic is preserved rather than presented as a successful
production contract build. Debug reports are observed for evidence only;
objects/executables are not extracted as the normal product build route.

Machine-readable observations are in [the evidence record](evidence/representation-gate.json).
Full raw logs, emitted IR and original debug archives remain in the surrounding
task workspace under `logs/feassign-fa01-attempt01` through the named attempt06
directory. All source, syntax and API acceptance beyond this first entry gate
remain work in progress: invalid dimensions/counts/indices, external-consumer
privacy and ownership paths, certificate model and actual optimizer/verifier.
