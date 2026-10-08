# e3nn/e3nn

## Notes summary

The longest observed gap is January 21 to June 13, 2024 (144 days), with no commit-message or PR evidence establishing why work paused. The post-gap activity added compile-compatible tensor-product functionality and was led by a different contributor from the last nearby pre-gap work, with continued feature and optimization commits through September 29, 2025; the project is **Active** at the requested cutoff.

## Reflection

The gap has clear dates but is hard to interpret causally: pre-gap messages concern packaging, CI caching, and changelog work, while the first post-gap burst is focused feature development. PR #436 introduced `FullTensorProductv2` for `torch.compile(..., fullgraph=True)` and points to continuing development, but neither the PR nor the sampled issues/README evidence explains the intervening interval. The nearby pre-gap work is associated with `Saurav Maheshkar`, while the post-gap feature is associated with `Mit Kotak`; later contributors also appear. This supports a change in the active contributor set, not a proven reason for the gap.

## Status at the requested cutoff

- Latest commit on or before 2025-09-30: **2025-09-29**.
- **Currentstatus: Active**.
- Most recent sampled themes: **Feature development** (Irreps filtering and slicing); **Bug fixes** (filter/slice corrections). Version changes and merges are secondary.

## Evidence

- [Pre-gap CI and packaging commit](https://github.com/e3nn/e3nn/commit/ac3528f7fb5fe1a8838f1df087d2eefe60d91ea8)
- [PR #436: FullTensorProductv2 for torch.compile](https://github.com/e3nn/e3nn/pull/436)
- [Merged implementation commit](https://github.com/e3nn/e3nn/commit/19dca23bf9ca2de6a13bf8d466d2952a5bc9f060)
- [September 2025 feature commit](https://github.com/e3nn/e3nn/commit/92c87a53631bd79fe31d27e7e57a0367db9708fb)
