# CAISO Paper Record

**FX:** [Daily](data/fx/daily.csv) · [Weekly](data/fx/weekly.csv) · [Monthly](data/fx/monthly.csv) · [Summary](data/fx/summary.csv)

**F_BROAD:** [Daily](data/f-broad/daily.csv) · [Weekly](data/f-broad/weekly.csv) · [Monthly](data/f-broad/monthly.csv) · [Summary](data/f-broad/summary.csv)

Daily hypothetical results from **2024-01-01**, using the PTP record's folder layout and exact CSV columns. FX and F_BROAD are alternative portfolios; do not add them together. No executed trades or capital-return claim.

Through September 2026: post-selection legacy research, with earlier eligibility and sizing, including fractional pocket allocations. Simulated fills use the original strict-price convention; bid-price ties are assumed unfilled, not observed CAISO awards. This is not a restatement of today's executable A4 book. October 1–10 has no verified record and stays blank. From October 11: the unchanged A4 timestamped paper programme. All historical results remain development evidence.

USD `pnl` deducts the frozen **$0.50/cleared leg-MWh plus modeled uplift**. Coordinator costs remain unquoted; no own-impact, capacity, financing or collateral model is included. `_mw` columns hold **leg-MWh**, following PTP's names. Awards and fills are simulated. The source anchors report modeled uplift and version boundaries.

Unknown observations are blank, never zero. Period statistics use known financial days; `settled_days` counts them. Volume totals sum known quantities; incomplete fill rates stay blank. Cumulative P&L, drawdown and ratios describe available observations across the stated versions, not a complete continuously executable history. Ratios use sample daily-dollar SD and √365; `pnl_es10` averages the worst ceil(10%) observations. Year/half-year drawdowns restart at zero.

Check hashes, arithmetic and timestamp tokens: `python3 scripts/verify.py`; add `--require-current` for freshness. These checks do not independently verify private orders or financial truth. Historical proof IDs are reconstruction hashes. Independent pre-09:55 Pacific decision proofs begin with bid day October 10; tokens and pinned public certificates are in `proof/private_anchor.json`. Import timestamps do not prove earlier GitHub posting. Orders and alpha remain private. The GCP publisher retains score corrections in Git history.

[Status](STATUS.md) · [FX source](data/fx/source_anchor.json) · [F_BROAD source](data/f-broad/source_anchor.json)
