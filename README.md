# CAISO Paper Record

**FX:** [Daily](data/fx/daily.csv) · [Weekly](data/fx/weekly.csv) · [Monthly](data/fx/monthly.csv) · [Summary](data/fx/summary.csv)

**F_BROAD:** [Daily](data/f-broad/daily.csv) · [Weekly](data/f-broad/weekly.csv) · [Monthly](data/f-broad/monthly.csv) · [Summary](data/f-broad/summary.csv)

Daily hypothetical results from **2024-01-01**, using the PTP record's folder layout and exact CSV columns. FX and F_BROAD are alternative portfolios; do not add them together. No executed trades or capital-return claim.

**Start with `timestamped_from_2026-10-11`, the first summary row, and [Status](STATUS.md).** It counts every prospective calendar day, including pending results. Its financial metrics use identified observations only; full-cohort cash bounds and coverage are shown in Status. A few days cannot establish profitability or a reliable Sharpe. `full_displayed_history` combines research versions and is not the live track record.

**The frozen FX decision monitor is currently blocked by October 14's unresolved award.** It suppresses economic kill and confidence calculations while any included FX day is unresolved. Its ONGOING label is not evidence that those checks passed. A reporting/freshness check succeeding does not establish a functioning trading-risk verdict. The public records preserve this uncertainty; no new bid-price policy or decision amendment has been adopted.

Through September 2026: post-selection legacy research, with earlier eligibility and sizing, including fractional pocket allocations. Simulated fills use the original strict-price convention; bid-price ties are assumed unfilled, not observed CAISO awards. This is not a restatement of today's executable A4 book. October 1–10: independently checked, retrospective reconstruction using frozen A4 rules and dated official price, eligibility and market-award reports. These reconstructed orders have no contemporaneous timestamp proof. From October 11: the unchanged A4 timestamped paper programme. All reconstructed history remains development evidence.

The development/selection window was July 2023–June 2025; this repository displays its January 2024–June 2025 slice. July 2025–September 2026 had also been examined before final selection and is not an untouched holdout. Separate summary rows identify those legacy slices and the October 1–10 reconstruction.

USD `pnl` deducts the frozen **$0.50/cleared leg-MWh plus modeled uplift**. Coordinator costs remain unquoted; no own-impact, capacity, financing or collateral model is included. `_mw` columns hold **leg-MWh**, following PTP's names. Awards and fills are simulated. The source anchors report modeled uplift and version boundaries.

Unknown observations are blank, never zero. In the A4 period, bids exactly equal to the day-ahead price remain `execution_pending`: public historical prices cannot determine the counterfactual award of an unsubmitted order. FX October 7 has five such order-hours; October 14 has one, confirmed by refreshed official reports. Their verified fixed-price net P&L ranges are **−$5,005.70 to −$4,018.64** and **−$1,048.97 to −$743.40**, respectively, under the frozen fee and uplift model. Point estimates remain blank. These are award bounds, not confidence intervals or executed results.

Period statistics use known financial days; `settled_days` counts them. Volume totals sum known quantities; incomplete fill rates stay blank. Cumulative P&L, drawdown and ratios describe available observations across the stated versions, not a complete continuously executable history. The source anchors' `verified_model_net_range` includes bounded pending losses in aggregate cash; if another date lacks bounds, the complete-history range stays null. Do not treat the known-observation cash sum as the complete history's cash. Ratios use sample daily-dollar SD and √365; `pnl_es10` averages the worst ceil(10%) observations. Year/half-year drawdowns restart at zero.

Check hashes, arithmetic and timestamp tokens: `python3 scripts/verify.py`; add `--require-current` for freshness. These checks do not independently verify private orders, financial truth or economic-monitor usability. Historical proof IDs are reconstruction hashes. Independent pre-09:55 Pacific decision proofs begin with bid day October 10; tokens and pinned public certificates are in `proof/private_anchor.json`. Import timestamps do not prove earlier GitHub posting. Orders and alpha remain private. The GCP publisher appends corrections in Git history; prior rows, assumptions and version boundaries remain auditable.

[Status](STATUS.md) · [FX source](data/fx/source_anchor.json) · [F_BROAD source](data/f-broad/source_anchor.json)
