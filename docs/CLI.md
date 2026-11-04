# Native text interface (version 1)

Initial platform: Linux x86-64, including WSL. Run:

```sh
python3 tools/build-native.py --fe "/absolute/path/to/fe-26.5.1"
```

The builder requires a new output directory and checks the pinned compiler hash.
The default executable is `target/native/feassign`; use --out-dir for another run.
The build uses the pinned official compiler and a child-only `cc` wrapper to add
`native/io.c`; it does not alter global PATH, the compiler or the pure kernel.
This link route reuses a preparation experiment; the product bridge is new.

Both commands require the exact `FEASSIGN 1` header. `feassign solve` then reads
two unsigned dimensions, rows then columns, followed by
exactly rows*columns signed i64 costs in row-major order. Require
1 <= rows <= columns <= 32. Example:

```text
FEASSIGN 1
2 3
1 2 9
1 100 3
```

Output is a versioned certificate envelope, consumed unchanged by
`feassign verify`:

```text
FEASSIGN 1
2 3
1 2 9
1 100 3
1 0
2 2
-1 0 0
TOTAL 3
```

After the header and dimensions come the row-major costs, exactly rows selected
zero-based column indices (unsigned bytes), rows signed i128 row potentials,
columns signed i128 column potentials, then `TOTAL` and one signed i128 total.
Line breaks are for readability. The redundant total is checked against the
shared verifier's recomputation from matrix values; it is never trusted by the
kernel. Any valid optimum is accepted, not just this solver's tie choice.
Successful verification prints `VALID <recomputed total>` and a newline.

Only ASCII space, tab, LF, vertical tab, form feed and CR separate tokens.
Leading/trailing whitespace is accepted. Numeric tokens are decimal digits,
optionally preceded by one minus for signed fields; no plus, fractions,
exponents or Unicode whitespace. Leading zeros and negative zero are accepted.
Header/version tokens are exactly `FEASSIGN` and `1`. Reject missing/extra tokens,
NUL, control/non-ASCII token bytes and values outside their documented types.
Input accepts at most 131072 bytes including whitespace. At the boundary one
additional read may establish EOF or reject an oversized stream; no whole-input
buffer is retained. This is a size bound, not an input deadline.

Exit statuses: 0 success, 2 syntax/type/dimension error, 3 input size limit,
4 mathematically invalid certificate or inconsistent total, 5 I/O failure,
6 internal invariant failure, 64 usage error. Diagnostics use fixed stderr text
without reproducing hostile input. A valid prefix followed by bad input produces
no success output. A late write failure may leave partial output and no diagnostic;
its exit status is 5. Treat the exit status as authoritative.

The kernel checks a successful solve certificate. Its private CLI formatter sums
selected costs in the existing selected-index loop using i256, then checked i128
narrowing. External verify recomputes total while checking the whole certificate.

All parsing, numeric formatting, solve and proof checks are Fe code. A streaming
cursor uses one character of lookahead, checked magnitude accumulation and
widening before signed negation. Output uses logical literal lengths and a
40-byte decimal scratch array, including full i128 minima. Fe's official Args
view requires one unsafe native-entry constructor; the pure kernel has none.
There are no explicit Fe heap owners to release here; libc may allocate buffers.

The scalar C bridge distinguishes EOF from ferror, retains write failure,
checks final stdout/stderr flush, and installs a checked standalone-process
SIGPIPE-ignore policy. It does not parse, optimize, inspect certificates or
expose FILE pointers to Fe. EINTR/nonblocking failures are explicit I/O errors;
there is no unbounded retry or durability/fsync promise. The pure library does
not change signal policy. Build and runtime evidence are tracked separately;
this interface document does not by itself establish any acceptance gate.
Observed execution and remaining project gates are in NATIVE-CHECKPOINT.md.
