# Actual native consumer and independent certificate checkpoint

On November 3, 2026 after opening, the pinned Fe 26.5.1 Linux x86-64 release
compiled the real CLI at native -O 1. The compiler itself invokes cc; a scoped
child PATH wrapper adds our C bridge to the normal executable link. It resolves
the real compiler before the prepend. No object extraction, compiler patch,
global environment change or host optimizer is involved. The pure assignment
source remains SHA256
`19235c78e12d400b6f2443ae2cba98a85a09596ee66d549efa05ac101364660a`.

`tools/check-native.py` launches this executable and inspects actual exported
selected columns and row/column potentials. Python arbitrary integers check
shape, index range, injectivity, all dual inequalities, selected-edge tightness,
nonpositive column potentials, zero unused-column potentials, selected cost and
full primal/dual equality. Each of the 2,906 primary solved envelopes also goes
through the real Fe verify command:

- 2,252 entries from the nine finite spaces in oracle-cases.json. Python
  independently enumerates distinct-column injections for exact minima.
- 528 separable examples cover every permitted shape, with closed-form minima.
- 96 seed-20261103 matrices include full i64 endpoints, ties, square/rectangular
  cases and larger/full32 shapes. Tiny seeded cases additionally enumerate.
- 20 metamorphic cases: five bases, row offsets, a uniform column offset and
  row/column reindexing. Expected changes are checked, input i64 ranges guarded
  and repeated base output checked for pinned-solver determinism.
- 10 directed cases include the documented rectangle, singleton endpoints,
  extreme-delta augmentation, full32 constant endpoints and a zero-delta chain.

These are 2,906 corpus entries with 2,899 unique logical matrices; they are not
an exhaustive full-domain proof. No host Hungarian/JV produces the solution.
The existing common 44 API/solver/verifier/oracle test functions also passed
again on native and EVM -O 1 after adding the CLI workspace member. The eight
model checks and three intended compiler rejections remain in the earlier
matching-kernel evidence. No changed kernel semantics were needed for this CLI.

The runtime campaign additionally checks 39 classified rejection cases,
argument counts/help, exact 128 KiB acceptance and overflow rejection, ASCII
policy, signed endpoints, full hostile i128 proof inputs and inconsistent total.
A valid extreme i128 square gauge is accepted. Actual Linux /dev/full, a pipe
without a reader and directory-as-stdin exercise final flush, SIGPIPE policy and
read-error-versus-EOF. The separate descriptor campaign covers byte-at-a-time
input, a complete prefix followed by an extra token, EAGAIN before/after a
prefix, handled non-restarted EINTR before/after a prefix, large output failure
and stderr flush failure. The EINTR helper only installs a test signal handler;
the production Fe binary, bridge and libc I/O remain real.

No success is emitted before complete input. Writing can fail after a partial
output; final status then reports I/O failure. Parsing uses bounded arrays and
one-character lookahead; formatting uses wide negation and 40-byte scratch.
There are no explicit Fe heap owners; this is not whole-process zero-allocation,
leak, durability or abrupt-kill cleanup evidence. Linux/WSL is the tested target.

Three failed build attempts are retained with exact source snapshots: generic
AsBytes does not accept long DynString literals, extern calls need matching
labels, Result.unwrap needs an ABI-encodable error, and a generic result-return
helper must own its argument. Splitting static text, explicit scalar-result
matching and ownership repaired these without changing the model. These are
actual compiler diagnostics, not unexplained solver counterexamples. No runtime
solver mismatch occurred in this campaign, so no minimized solver failure is
invented.

`docs/evidence/native.json` records source/binary hashes and executed evidence
references. Commands for fresh evidence are in README.md. The normal builder
checks exact compiler asset bytes. This is FA04/FA05/FA06 acceptance evidence,
not FA07/FA08, a fresh-source complete-project rehearsal, a human review or final
freeze. The board, semantic commitment/signed ABI, real full32 transaction
receipt/state/gas, final demo and remaining adversarial/package gates still
require work. The persistent build goal remains active through the actual
review/freeze requirements.
