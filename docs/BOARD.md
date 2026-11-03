# Immutable assignment board and semantic ABI, version 1

The Fe AssignmentBoard accepts one certificate for a fixed complete assignment
problem and records the shared verifier's recomputed total and chosen columns.
The board has no funds, caller authority, owner, setter, external Call or upgrade.
Constructor arguments are `(uint8 rows,uint8 columns,uint256 commitment)` with
1 <= rows <= columns <= 32. These three fields are immutable. Any commitment
word is accepted; a wrong or unavailable problem may leave the board Open.

The commitment is Ethereum Keccak-256 of standard Solidity ABI encoding of:

```text
(uint256 domain,uint32 version,uint32 objective,uint8 rows,uint8 columns,int64[] costs)
domain    = 0x464541535349474e5f50524f424c454d00000000000000000000000000000000
version   = 1
objective = 1  (minimum total sum)
```

Domain bytes spell `FEASSIGN_PROBLEM` followed by zero bytes. Costs are exactly
rows*columns logical signed values in row-major order. The tuple has six head
words; its array offset is192, followed by the length and sign-extended words.
Both dimensions are included. This is not internal packed matrix storage,
packed encoding, an immutable compiler tail, raw calldata or NIST SHA3-256.
`tools/board_abi.py` supplies a host reference encoder and uses Foundry cast for
Keccak through stdin; it is not an assignment optimizer.

For rows2,columns3,costs `[4,1,8,2,6,3]`, the digest observed independently by the
host encoder and an accepted real board submission is:

```text
0x8a230a08ac8d5db31c948b48071f96adcb6c448685e8f2bb16bfa19d3b8af7cf
```

Public messages are:

- `details()` -> `(uint8 rows,uint8 columns,uint256 commitment,bool solved)`.
- `submit(int64[] costs,uint8[] selected,int128[] u,int128[] v)` -> `int128 total`.
- `totalCost()` -> `int128`; reverts before Solved.
- `selectedColumn(uint8 row)` -> `uint8`; reverts before Solved or outside rows.

Submit requires Open, exact costs/selected/u/v lengths r*c/r/r/c and valid narrow
ABI values. It reads each element into the bounded model/certificate. Sequential
ProblemBuilder construction avoids the large redundant matrix staging array.
`problem_digest` independently reads every cost after its shape/length guards.
For static `i64`, the pinned decoder/constructors retain exactly one length word
and one32-byte word per element. A successful typed read checks that each word
is the unique canonical sign extension. The validated tail can therefore be
copied directly into the fresh semantic tuple and hashed; no second array
allocation/zeroing/re-encoding is needed. Tuple encoding fixes the outer offset.
This argument is specific to static `i64`, not dynamic/nested arrays. Matching the immutable digest precedes the
shared pure verifier. Every mathematical condition must pass before any storage
write. Then the board records p and total and marks Solved. Repeats revert.
The submitted message contains no objective value to trust.

Dirty upper bits/sign extension, bad bounds and invalid lengths reject. Some
ABI element checks are lazy; explicit reads prevent them being bypassed by a
verbatim span hash. Nonminimal offsets, gaps, reordered tails and ignored suffix
bytes can encode the same values; accepted variants bind the same digest.
The transaction campaign accepted a 32-byte-gap/14-byte-suffix submission and
simulated reordered tails with the same result. These wire bytes are deliberately
different from canonical encoding. Decoder allocation/copy can precede our
application length guards, so the core32 bound is not a universal malformed-wire
memory bound. Decoder reverts may have empty data; mathematical rejection gives
`invalid certificate`, and a semantic mismatch gives `wrong problem`.

Actual ordinary-limit protocol evidence uses Anvil1.8.7 with Osaka and
`--enable-tx-gas-limit`, a30,000,000 block gas limit and declared16,777,216 per
transaction. The above-cap control was rejected. Every claimed deployment,
successful submit and failed-state check has a receipt/status plus readback.
Rejection transactions used less than the declared limit; they are not labelled
mathematical rejection on the strength of an out-of-gas result.

The initial O1 board emitted27,695 runtime bytes and exceeded EIP-170; O2 and
size optimization still exceeded it. Initializing the1024 staging array from a
runtime value worsened size to32,408bytes. Those artifacts remain evidence.
The pure sequential builder removed the staging array while preserving all
full-i64/full32 values. Current O1 emitted runtime is23,498bytes; actual deployed
code is23,594bytes including96bytes of immutable data, below24,576. Creation
code is23,985bytes; total initcode including96bytes of constructor ABI arguments
is24,081, below49,152. Runtime has982bytes of current headroom, so later changes
must recheck actual code size. A first test-harness assertion mistakenly equated
emitted and deployed runtime, then assumed an ABI-shaped immutable tail. Those
two harness failures are preserved; actual getters and emitted-prefix comparison
now establish the constructor values without treating internal layout as ABI.

Observed deployments used5,054,840gas. Three full32×32 submissions had36,100
canonical calldata bytes each:

| Actual case | Stored total | Receipt gasUsed |
| --- | ---: | ---: |
| zero-delta/augmentation chain |31|2,407,387|
| all i64-min | -295147905179352825856 |2,737,558|
| one min-cost column, other costs i64-max |276701161105643274209|2,503,728|

These are specific measurements, not a universal gas bound. The same three
full32 payloads used84,791 less gas each than before the static-tail change;
this comparison is limited to these inputs under the same pinned Osaka setup. All32 stored indices matched the actual Fe
CLI certificate. Repeat and malformed/invalid submissions preserved mutable
slots0..33 (solved,total,chosen32), with relevant public-state checks. The ABI
edge campaign observed40 transactions:28 expected failures and12 successes,
including successful deployments. It covered dirty signed/unsigned words,
length/bounds errors, full-i128 gauge, hostile wide sum, two independent
rectangular sign/unused-column counterexamples, alternate optimum, changed
domain/version/objective/dimensions and invalid constructors.

Current core/model/API checks are8+46 functions on each native/EVM backend,
plus2 EVM board functions and5 intended external compiler rejections. The
2,906-result native independent certificate/I/O campaign passed again after
the builder change. `docs/evidence/board.json` retains the original builder checkpoint and its old
source/size/gas scope. The later static-tail revision has unchanged core/CLI
sources and ABI,2 EVM board function passes,60 receipted demo/protocol checks,
and a separate existing mixed-full-i64 case with3 receipts and32 getter checks.
Its helper-isolation control rejects both dirty signed words independently of
other Submit checks; omitting only the typed-read loop makes them return. These
controls are temporary research copies, not added product APIs or test cases.
The current candidate manifest binds the revised source and evidence; earlier
checkpoint JSON and whole-suite counts remain historical.

This board proves an optimum for its committed integer matrix. It does not
authenticate resources, certify true costs, dispatch jobs or prove work delivery.
An identical problem's certificate may be reused on another board legitimately;
there is no spending authorization. Publish demo data for availability without
claiming on-chain availability guarantees. The local demo and fresh-source workflow are described in
[DEMO.md](DEMO.md) and [REPRODUCE.md](REPRODUCE.md).
Actual human review and final freeze remain future requirements.
