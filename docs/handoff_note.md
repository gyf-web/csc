# Project Handoff Note

## 1. Current Handoff

- current_machine: DESKTOP-MP8LE18
- handoff_time: 2026-06-26 10:55:56 +08:00
- operator: gyf
- reason: continue Stage 4/5 workflow on another computer

## 2. Git State

- is_git_repo: yes
- current_branch: main
- remote_url: origin https://github.com/gyf-web/csc.git
- latest_local_base_before_this_handoff: `c3726b1 Pause Stage 3 and prepare cross-machine handoff`
- local_changes_to_commit: Stage 4 script, Stage 4 local outputs, `docs/progress_log.md`, and this handoff note
- unrelated_local_untracked_files_not_to_commit:
  - `Claude-项目文献对标与论文可行性评估.md`
  - `literature_summary.md`
  - `tools/`

## 3. Project Progress

- completed_stages: Stage 0, Stage 1, Stage 2, Stage 3, Stage 4 local workflow and export submission
- current_stage: Stage 4
- current_stage_status: local Stage 4 outputs complete; GEE EQI_func exports submitted/queued
- next_stage: Stage 5
- blocked_by: Stage 4 GEE Asset export tasks not fully completed
- do_not_run_next_stage_until:
  - `users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000` through `EQI_func_2024` all exist as IMAGE assets
  - `outputs/tables/table_annual_eqi_stats.csv` is present and complete
  - `outputs/tables/table_stage04_eqi_asset_manifest.csv` is present and reviewed

## 4. Stage 4 Model Summary

- model: `NIRv ~ FVC + DEM + Slope + Precip + Temp`
- model_type: `unified_residual_model`
- simplified_model: false
- ForestType_in_model: false
- sample_design: stratified by ForestType, 10,000 natural forest pixels and 10,000 plantation forest pixels per year
- sample_years: 2000-2024
- cleaned_sample_rows: 500,000
- DEM_source: `USGS/SRTMGL1_003`
- Slope_source: derived from DEM in Earth Engine
- climate_source: `ECMWF/ERA5_LAND/MONTHLY_AGGR`
- precip_units: annual meters from monthly `total_precipitation_sum`
- temp_units: degree C from monthly mean `temperature_2m`

Model diagnostics:

| metric | value |
|---|---:|
| R2 | 0.77283639 |
| RMSE | 0.03034619 |
| MAE | 0.02316444 |
| Bias | 0.0 |
| sample_count | 500000 |

Coefficients:

| term | coefficient |
|---|---:|
| Intercept | 0.09412783499 |
| FVC | 0.207347648675 |
| DEM | -0.000056633975 |
| Slope | -0.000071600707 |
| Precip | -0.001811573899 |
| Temp | 0.000186252721 |

## 5. Stage 4 GEE Task Status

Latest check time: 2026-06-26 10:55 +08:00

Summary:

| state | count |
|---|---:|
| COMPLETED | 1 |
| RUNNING | 3 |
| READY | 21 |
| FAILED | 0 |

Asset summary:

| asset_type | count |
|---|---:|
| IMAGE | 1 |
| missing_or_not_yet_available | 24 |

Completed / available as IMAGE:

| year | asset_id | status |
|---|---|---|
| 2000 | `users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000` | IMAGE / COMPLETED |

Running tasks:

| year | asset_id | task_state |
|---|---|---|
| 2001 | `users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2001` | RUNNING |
| 2002 | `users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2002` | RUNNING |
| 2003 | `users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2003` | RUNNING |

Ready / queued tasks:

| years | task_state |
|---|---|
| 2004-2024 | READY |

Failed tasks:

- none found in the latest check

## 6. Stage 4 Local Outputs

| file_path | exists | notes |
|---|---|---|
| `gee/stage04_build_eqi_model.py` | yes | Stage 4 runnable Python Earth Engine workflow |
| `outputs/stage04_eqi/EQI_regression_samples.csv` | yes | 500,000 cleaned sample rows |
| `outputs/tables/table_eqi_regression_coefficients.csv` | yes | 6 model terms |
| `outputs/tables/table_eqi_regression_diagnostics.csv` | yes | R2/RMSE/MAE/Bias/sample_count |
| `outputs/tables/table_annual_eqi_stats.csv` | yes | 75 rows: 25 years x 3 forest groups |
| `outputs/tables/table_stage04_eqi_asset_manifest.csv` | yes | 25 EQI_func target assets/tasks |
| `outputs/figures/fig03_eqi_timeseries_by_forest_type.png` | yes | EQI_func time series by forest type |
| `docs/progress_log.md` | yes | Stage 4 appended |

Local GeoTIFF check:

- `outputs/` contains no `.tif` or `.tiff` files from Stage 4.

## 7. Files To Commit For This Handoff

Commit these:

```text
gee/stage04_build_eqi_model.py
docs/progress_log.md
docs/handoff_note.md
outputs/stage04_eqi/EQI_regression_samples.csv
outputs/tables/table_eqi_regression_coefficients.csv
outputs/tables/table_eqi_regression_diagnostics.csv
outputs/tables/table_annual_eqi_stats.csv
outputs/tables/table_stage04_eqi_asset_manifest.csv
outputs/figures/fig03_eqi_timeseries_by_forest_type.png
```

Do not commit these local-only/unrelated files unless intentionally requested later:

```text
Claude-项目文献对标与论文可行性评估.md
literature_summary.md
tools/
```

## 8. Recovery Steps On Another Computer

1. Pull the latest GitHub repository state from `https://github.com/gyf-web/csc`.
2. Read `AGENTS.md`, `docs/progress_log.md`, and this `docs/handoff_note.md`.
3. Activate the project Python environment with Earth Engine access.
4. Check Stage 4 task completion and Asset availability before Stage 5.
5. Do not run Stage 5 until every target below exists as an IMAGE asset:

```text
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000
...
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2024
```

## 9. Suggested Next Codex Prompt

```text
Please do not execute any new analysis stage yet.

Read:
1. AGENTS.md
2. docs/progress_log.md
3. docs/handoff_note.md

The project is paused after Stage 4. Stage 4 local outputs are complete, and
EQI_func_2000-2024 export tasks have been submitted to Earth Engine, but the
handoff check found only EQI_func_2000 available as an IMAGE asset; years
2001-2003 were RUNNING and 2004-2024 were READY.

First check:
1. whether all Stage 4 GEE tasks completed successfully;
2. whether users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000 through
   EQI_func_2024 all exist as IMAGE assets;
3. whether outputs/tables/table_annual_eqi_stats.csv is complete;
4. whether outputs/tables/table_stage04_eqi_asset_manifest.csv is complete.

If Stage 4 is not fully complete, only list missing years, missing EQI_func
assets, and failed tasks. Do not execute Stage 5.

If Stage 4 is fully complete, suggest the next Codex command for Stage 5.
```
