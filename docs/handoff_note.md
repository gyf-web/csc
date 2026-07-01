# Project Handoff Note

## 1. Current Handoff

- current_machine: DESKTOP-MP8LE18
- handoff_time: 2026-07-01 17:28:26 +08:00
- operator: gyf
- reason: continue the workflow on another computer after Stage 5 completion
- current_stage: Stage 5 completed
- next_stage: Stage 6 decoupling analysis
- explicit_pause: Stage 6 has not been executed

## 2. Git State

- repository: `https://github.com/gyf-web/csc.git`
- branch: `main`
- remote: `origin`
- remote_main_before_handoff: `a9f4914 Complete Stage 4 EQI handoff`
- local_stage05_commit_before_handoff_note: `8eead9c stage05`
- local_status_before_handoff_note: `main` was one commit ahead of `origin/main`
- intended_sync: commit this handoff-note update and push `main` to `origin`

Important scope note:

- Commit `8eead9c` contains all Stage 5 code and outputs.
- It also contains the previously local literature files
  `Claude-项目文献对标与论文可行性评估.md`,
  `literature_summary.md`, and three scripts under `tools/`.
- Those additional files were already part of the existing local commit before
  this handoff update. They were not added or modified by the Stage 5 handoff
  operation.

## 3. Project Progress

- completed_stages: Stage 0, Stage 1, Stage 2, Stage 3, Stage 4, Stage 5
- Stage 4 status: complete; all `EQI_func_2000` through `EQI_func_2024`
  assets exist as Earth Engine IMAGE assets
- Stage 5 status: complete
- blocked_by: none
- next_authorized_action: none; do not run Stage 6 unless the user explicitly
  requests it on the next computer

Stage 5 used:

- period: 2000-2024
- resolution: 30 m
- study mask: `ForestMask_30m`
- main trend estimator: per-pixel Sen's slope
- significance test: Kendall tau followed by a two-sided asymptotic
  Mann-Kendall normal-approximation p value
- significance threshold: `p < 0.05`

## 4. Stage 5 Earth Engine Assets

All four target exports completed successfully and exist as IMAGE assets:

| asset_name | asset_id | band | status |
|---|---|---|---|
| FVC_SenSlope_30m | `users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m` | `FVC_SenSlope` | IMAGE / COMPLETED |
| FVC_pvalue_30m | `users/gyf/forest_csc_alphaearth/stage05_trend/FVC_pvalue_30m` | `FVC_pvalue` | IMAGE / COMPLETED |
| EQI_SenSlope_30m | `users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m` | `EQI_SenSlope` | IMAGE / COMPLETED |
| EQI_pvalue_30m | `users/gyf/forest_csc_alphaearth/stage05_trend/EQI_pvalue_30m` | `EQI_pvalue` | IMAGE / COMPLETED |

Final successful task IDs:

| asset_name | task_id |
|---|---|
| FVC_SenSlope_30m | `EYQS5OXLEQFQIGUGP2EI7DNY` |
| FVC_pvalue_30m | `DMZGICS7WQWL22AIUSOMHCU5` |
| EQI_SenSlope_30m | `6ANS2NH2V6WIWM42EGQGI2PQ` |
| EQI_pvalue_30m | `AJ2K6LE6ZZWRZKH2R5C2YPQJ` |

All final assets have:

- CRS: `EPSG:4326`
- scale property: 30
- start year: 2000
- end year: 2024
- project property: `hainan_forest_greening_quality`

Exported p-value ranges:

| asset | minimum | maximum |
|---|---:|---:|
| FVC_pvalue_30m | 1.659317128e-11 | 1.0 |
| EQI_pvalue_30m | 6.176981149e-11 | 1.0 |

## 5. Stage 5 Method Correction

Earth Engine's direct `p-value` output from
`ee.Reducer.kendallsCorrelation(2)` was masked/NaN for these annual image
series. The two initial invalid p-value export tasks were cancelled before
creating assets:

| description | cancelled_task_id | final_state |
|---|---|---|
| FVC_pvalue_30m | `XXCGPVWRTFZWMF54ICXK6DDE` | CANCELLED |
| EQI_pvalue_30m | `LSWQWNWDD7MLFERFSZBA6I3C` | CANCELLED |

The final p-value assets use the Stage 5 option-B method allowed by
`AGENTS.md`: Kendall tau plus a two-sided asymptotic normal approximation.
Values are clamped to 0-1 and require at least three valid annual observations.
The approximation does not implement an explicit per-pixel tie correction;
retain this limitation in downstream interpretation and robustness analysis.

## 6. Stage 5 Local Outputs

| file_path | status | notes |
|---|---|---|
| `gee/stage05_trend_analysis.py` | complete | Runnable Python Earth Engine Stage 5 workflow |
| `src/trend_utils.py` | complete | Time-series, Sen slope, and p-value helpers |
| `src/io_utils.py` | complete | YAML and CSV helpers |
| `outputs/tables/table_trend_stats_by_forest_type.csv` | complete | Three forest groups |
| `outputs/tables/table_stage05_trend_asset_manifest.csv` | complete | Four assets, all marked completed |
| `outputs/tables/table_stage05_trend_checks.csv` | complete | Seven checks, all passed |
| `outputs/figures/fig04_fvc_trend_map.png` | complete | Visually inspected |
| `outputs/figures/fig05_eqi_trend_map.png` | complete | Visually inspected |
| `docs/progress_log.md` | complete | Stage 5 completion entry appended |

Key validation results:

- FVC slope range: -0.04765588418 to 0.05502215773 per year
- EQI_func slope range: -0.009519957006 to 0.01053539477 per year
- FVC valid trend area: 24,578.194088 km2
- EQI_func valid trend area: 23,987.777560 km2
- off-forest valid trend-mask sums: zero for both variables
- local GeoTIFF files under `outputs/`: none
- Stage 6 files or decoupling products generated: none

## 7. Configuration Caveat

`config/config.yaml` still has:

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: null
  rubber_mask_asset: null
```

The configured Hainan ROI is not the corrected island-only boundary, and the
Stage 1/3/4/5 asset roots are not stored in the config. Stage 5 therefore read
years, scale, CRS, output paths, and the p-value threshold from the config but
used explicit command-line overrides for:

```text
projects/ee-gyf/assets/Hainan-Island-Boundary
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
users/gyf/forest_csc_alphaearth/stage03_indices
users/gyf/forest_csc_alphaearth/stage04_eqi
users/gyf/forest_csc_alphaearth/stage05_trend
```

Do not silently edit `config/config.yaml` as part of Stage 6. Configuration
maintenance should be a separately authorized action or explicitly included in
the next-stage request.

## 8. Recovery Steps On Another Computer

1. Pull the latest `main` branch:

   ```powershell
   git pull origin main
   ```

2. Read:

   ```text
   AGENTS.md
   docs/progress_log.md
   docs/handoff_note.md
   ```

3. Activate the Earth Engine environment:

   ```powershell
   conda activate csc
   ```

   Known working interpreter on the source computer:

   ```text
   D:\anaconda\envs\csc\python.exe
   ```

4. Confirm Earth Engine access using Cloud Project `ee-gyf`.
5. Before Stage 6, perform a read-only check that the four Stage 5 assets in
   section 4 exist as IMAGE assets with the expected bands.
6. Do not rerun Stage 5, resubmit its exports, download full-resolution
   GeoTIFFs, or generate Stage 6 outputs unless explicitly requested.

## 9. Suggested Next Codex Prompt

```text
Read:
1. AGENTS.md
2. docs/progress_log.md
3. docs/handoff_note.md

The project is paused after successful completion of Stage 5.

First perform read-only checks:
1. confirm these four Earth Engine assets exist as IMAGE assets:
   - users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m
   - users/gyf/forest_csc_alphaearth/stage05_trend/FVC_pvalue_30m
   - users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m
   - users/gyf/forest_csc_alphaearth/stage05_trend/EQI_pvalue_30m
2. confirm their expected bands, EPSG:4326 metadata, 30 m scale property, and
   p-value ranges within 0-1;
3. confirm the three Stage 5 tables and two Stage 5 figures are present;
4. confirm outputs/ contains no local GeoTIFF.

Do not rerun Stage 5 and do not execute Stage 6 yet.

If all checks pass, report that Stage 5 is ready for Stage 6 and provide the
next Codex prompt for Stage 6. If anything is missing, list only the missing or
failed items.
```
