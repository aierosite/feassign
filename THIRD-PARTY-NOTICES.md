# Source, tools and attribution

Original FeAssign source, C bridge, scripts, examples and documentation use the
MIT license in LICENSE. No Hungarian/JV implementation or other assignment
engine is vendored. Hungarian algorithms and assignment duality are classical;
OR-Tools/SciPy/KACTL were research references, not runtime engines or copied code.

Later comparison runs used OR-Tools, HiGHS and NetworkX outside this product.
The two external-certificate examples contain our illustrative integer problem
and numeric witness data from HiGHS 1.15.1, with provenance and the exact
preprocessing described in docs/INTEROPERABILITY.md. The pinned research source
is [HiGHS 04024d7](https://github.com/ERGO-Code/HiGHS/tree/04024d701f79feb8e2f18bc3df0dffc04ef05088),
which provides an MIT license. No HiGHS, OR-Tools or NetworkX code or binaries
are redistributed or required by these examples.

Fe26.5.1 and its core/std libraries are external toolchain dependencies. Their
pinned repository contains [Apache-2.0](https://github.com/fe-lang/fe/blob/149c758503563ebd6ad7237b85e28a94dca6e22a/LICENSE-APACHE).
FeAssign imports their APIs; it does not present std implementation as original
source. Compiler metadata generated in the observed board build embeds only
our assignment and board sources. Compiler/library binaries are not distributed
in this source package. The unchanged pinned Fe license is retained at
licenses/Fe-APACHE-2.0.txt for locally generated artifacts that incorporate
compiler-library code; the original source license above applies to our code.

Foundry Anvil/cast1.8.7 are external local test tools. The pinned repository
provides [Apache-2.0](https://github.com/foundry-rs/foundry/blob/985eeea031d79922cd654d4e94e6c3701e1c7d73/LICENSE-APACHE)
and [MIT](https://github.com/foundry-rs/foundry/blob/985eeea031d79922cd654d4e94e6c3701e1c7d73/LICENSE-MIT)
license files. Foundry source/binaries are not included in this source package.
Python and the system C compiler/libc remain environment prerequisites.

The child-only cc wrapper approach derives from a disclosed pre-window
experiment with unchanged official sources. Product code and tests were
authored after opening; preparation is not relabelled as a contest contribution.
See docs/PROVENANCE.md for AI assistance, selection/timing and known failures.
No public repository, final submission, independent audit or human acceptance
is claimed by this notice.
