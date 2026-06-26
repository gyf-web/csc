# Progress Log

## Stage 0 - Project initialization

Status: completed  
Date: 2026-06-25  
Inputs: None.  
Outputs: Project directory structure; `config/config.yaml`; `README.md`; `TASK_PLAN.md`; `docs/data_dictionary.md`; `docs/method_notes.md`; reserved placeholder files under `gee/`, `scripts/`, and `src/`; conda environment `csc`.  
Checks: Project directories were created; configuration file exists; progress log exists; planned stage script filenames were reserved; Python environment `csc` was created with required base packages; package imports succeeded; `outputs/` contains no generated result files; no remote sensing outputs, rasters, random data, or test rasters were generated.  
Problems: Existing project root contains unrelated pre-existing files and folders; they were left untouched. During the sandboxed import check, Matplotlib could not write its cache under the user home directory, but the import succeeded.  
Next stage: Stage 1 may prepare study area and forest type data after the user explicitly starts that stage.

## Stage 1 - Study area and forest type data preparation

Status: failed  
Date: 2026-06-25  
Inputs: `config/config.yaml`; Hainan ROI asset configured as `projects/ee-gyf/assets/hainan`; Global Natural and Planted Forests 2021 community dataset planned from `projects/sat-io/open-datasets/GLOBAL-NATURAL-PLANTED-FORESTS`; Hansen loss planned from `UMD/hansen/global_forest_change_2025_v1_13` for loss years 2021-2024; Dynamic World planned from `GOOGLE/DYNAMICWORLD/V1` for 2021-2024 modal water/built/bare masking.  
Outputs: Implemented `gee/stage01_export_forest_type.py`; wrote `outputs/tables/table_forest_type_asset_manifest.csv` with `dry_run_not_submitted` status for the two required Earth Engine Asset targets. `outputs/tables/table_forest_type_area.csv` was not generated because area statistics require an online Earth Engine reducer result.  
Checks: GEEMu local environment gate failed for online execution: default `python` cannot import `ee` or `geemap`; `D:\anaconda\envs\csc\python.exe` can import `ee` but cannot import `geemap`; no `EE_PROJECT`, `GOOGLE_CLOUD_PROJECT`, or `EE_PROJECT_ID` environment variable is set. Because online Earth Engine initialization was not possible, the following required Stage 1 checks could not be completed: Hainan boundary loading, natural/planted spatial reasonability, non-forest exclusion, area statistics, Asset 30 m export, Asset alignment, exported code validation, mask validation, and final Earth Engine export completion. Static script checks confirm the script reads `config/config.yaml`, uses Python Earth Engine API, defaults to dry-run, requires `--project` for online work, exports only to Earth Engine Asset when `--export` is passed, writes only CSV tables locally, and does not download `ForestType_30m_clean.tif` or `ForestMask_30m.tif`.  
Problems: Earth Engine Cloud Project ID is missing and geemap is unavailable in the checked project environment, so export tasks were not submitted and the area table was not computed. To avoid fabricated or placeholder science results, no area statistics were written. GEEMu run-folder artifacts were not created because this Stage 1 request explicitly allowed modification of only four project paths.  
Next stage: Rerun Stage 1 online after setting `EE_PROJECT` or passing `--project PROJECT_ID`, installing/activating a geemap-capable environment if desired, and confirming the Asset folders `users/gyf/forest_csc_alphaearth` and `users/gyf/forest_csc_alphaearth/stage01_forest_type` exist in Earth Engine. Use `D:\anaconda\envs\csc\python.exe gee/stage01_export_forest_type.py --project PROJECT_ID --export` to submit the two Asset exports and generate the area table.

## Stage 1 - Study area and forest type data preparation rerun

Status: completed  
Date: 2026-06-25  
Inputs: Earth Engine Cloud Project `ee-gyf`; corrected Hainan boundary asset `projects/ee-gyf/assets/Hainan-Island-Boundary`; Global Natural and Planted Forests 2021 image collection `projects/sat-io/open-datasets/GLOBAL-NATURAL-PLANTED-FORESTS`; Hansen loss image `UMD/hansen/global_forest_change_2025_v1_13` using loss years 2021-2024; Dynamic World image collection `GOOGLE/DYNAMICWORLD/V1` using 2021-2024 modal labels to remove water, built-up, and bare areas. The configured `projects/ee-gyf/assets/hainan` asset was checked and found unsuitable for this stage because it has 137 features and geometry area 0 km2; it was not used for the final run.  
Outputs: Updated `gee/stage01_export_forest_type.py` with a `--hainan-roi` override while still reading `config/config.yaml`; generated `outputs/tables/table_forest_type_area.csv`; generated `outputs/tables/table_forest_type_asset_manifest.csv`; submitted Earth Engine Asset export tasks for `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean` and `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m`.  
Checks: Earth Engine initialized successfully with project `ee-gyf`; target Asset folders `users/gyf/forest_csc_alphaearth` and `users/gyf/forest_csc_alphaearth/stage01_forest_type` exist; corrected Hainan boundary has 1 feature, area 33,897.787969 km2, and bounds 108.6163-111.0387 E / 18.1609-20.1653 N; final frequency checks found `ForestType_30m_clean` contains only classes 0, 1, and 2 and `ForestMask_30m` contains only 0 and 1; area statistics are non-forest/uncertain 9,216.928261 km2, natural forest 13,814.013707 km2 (56.204348% of forest), plantation forest 10,764.180381 km2 (43.795652% of forest); exports are configured at 30 m, EPSG:4326, clipped to the corrected Hainan boundary, and submitted to the required Asset folder; local `outputs/stage01_forest_type/` contains no files and no local `ForestType_30m_clean.tif` or `ForestMask_30m.tif` was generated. The first run used the unsuitable configured ROI and produced too-small area statistics; its two Earth Engine tasks `63YUPOVKNAVWLEA3TWPMGQV3` and `2A2NS7BJCIMOCKOL7WMVMSOE` were cancel-requested before rerunning with the corrected boundary.  
Problems: `geemap` is not installed in `D:\anaconda\envs\csc`, so initialization used the GEEMu-allowed equivalent `ee.Initialize(project="ee-gyf")`. Earth Engine exports are asynchronous; at the latest check, corrected tasks `XK6G7DC7R2NCCK6TMCLBLIN7` and `DQKVVJV7LXDXPBSBZFJ2R6OV` were RUNNING, so final Asset completion should be checked in Earth Engine Tasks before Stage 2.  
Next stage: After both Stage 1 export tasks finish successfully in Earth Engine, proceed to Stage 2 using `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean` and `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m`.

## Stage 2 - Landsat annual 30 m surface reflectance composites

Status: completed  
Date: 2026-06-25  
Inputs: `config/config.yaml`; Earth Engine Cloud Project `ee-gyf`; corrected Hainan boundary override `projects/ee-gyf/assets/Hainan-Island-Boundary`; Stage 1 assets `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m` and `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean`; Landsat Collection 2 Level-2 collections `LANDSAT/LT05/C02/T1_L2`, `LANDSAT/LE07/C02/T1_L2`, `LANDSAT/LC08/C02/T1_L2`, and `LANDSAT/LC09/C02/T1_L2`.  
Outputs: Updated `gee/stage02_export_landsat_annual.py`; generated `outputs/tables/table_landsat_valid_pixels_by_year.csv`; generated `outputs/tables/table_landsat_asset_manifest.csv`; submitted annual composite exports to `users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000` through `users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024`.  
Checks: Earth Engine initialized successfully with project `ee-gyf`; Stage 1 ForestMask and ForestType assets and the Stage 2 output Asset folder were accessible; all 25 years from 2000-2024 were submitted or already active in Earth Engine Tasks; all manifest Asset IDs use the required `users/gyf/forest_csc_alphaearth/stage02_landsat/` folder; every composite is built with the six unified bands `Blue;Green;Red;NIR;SWIR1;SWIR2`; Landsat DN values are converted to surface reflectance using `DN * 0.0000275 - 0.2`; QA masks remove fill, dilated cloud, cloud, cloud shadow, snow, and saturated pixels using `QA_PIXEL` and `QA_RADSAT`; `ForestMask_30m` is applied before annual median compositing and export. The valid-pixel table has 25 rows, image counts are nonzero for every year, and valid forest coverage ranges from 99.468652% to 100.000000%, so no missing year or obvious Landsat 7 SLC-off coverage anomaly was flagged by the quantitative coverage check. Coarse 300 m p1/p99 reflectance checks were within plausible surface-reflectance ranges across all years: Blue about 0.013-0.101, Green about 0.026-0.132, Red about 0.017-0.147, NIR about 0.181-0.443, SWIR1 about 0.091-0.318, and SWIR2 about 0.037-0.226. Local `outputs/stage02_landsat/` contains no files and no local annual GeoTIFF was generated. The Stage 2 script passed `py_compile`. Latest task status check: 2000-2007 completed, 2008-2009 running, and 2010-2024 ready/queued in Earth Engine.  
Problems: `geemap` is not installed in `D:\anaconda\envs\csc`, so initialization used the GEEMu-allowed equivalent `ee.Initialize(project="ee-gyf")`. The configured `gee_assets.hainan_roi` still points to the unsuitable `projects/ee-gyf/assets/hainan`, so this run used the corrected Hainan boundary override. Earth Engine exports are asynchronous; final Asset completion and visual striping inspection should be checked in Earth Engine after queued tasks finish. A first long online run timed out after submitting early years, so the script was made resumable and avoids duplicate task submission by checking existing tasks/assets.  
Next stage: After all Stage 2 Earth Engine export tasks complete successfully, proceed to Stage 3 using the 25 LandsatComposite assets under `users/gyf/forest_csc_alphaearth/stage02_landsat/`.

## Handoff update: Stage 2 paused

- time: 2026-06-25 17:16:44 +08:00
- current_stage: Stage 2 Landsat annual composites
- status: GEE export tasks submitted, not all completed
- task_status_summary: 2000-2011 COMPLETED and available as IMAGE assets; 2012-2013 RUNNING and not yet available as assets; 2014-2024 READY and not yet available as assets; no FAILED Stage 2 task was found in the latest check.
- next_action: check Stage 2 GEE task completion and Asset availability before Stage 3
- do_not_run_next_stage_until:
  - LandsatComposite_2000-2024 all exist as GEE Assets
  - `outputs/tables/table_landsat_valid_pixels_by_year.csv` is complete
  - `outputs/tables/table_landsat_asset_manifest.csv` is present and reviewed
- explicit_pause: Do not execute Stage 3 or any later stage during this handoff. Do not submit new Earth Engine tasks, cancel existing Stage 2 tasks, download full-resolution GeoTIFFs, or generate local Landsat composites.
- handoff_note: See `docs/handoff_note.md` for the year-by-year task table, Asset status table, Git sync notes, ignored local files, and laptop recovery prompt.

## Environment setup - csc conda environment

Status: completed  
Date: 2026-06-25  
Inputs: `AGENTS.md`; existing Anaconda installation at `D:\Annaconda3`; existing geemap-capable `GEE` environment; Earth Engine Cloud Project `ee-gyf`.  
Outputs: Conda environment `csc` created at `D:\Annaconda3\envs\csc`; no remote sensing outputs, rasters, notebooks, or temporary project-root scripts were generated.  
Checks: `conda info --envs` lists `csc`; `D:\Annaconda3\envs\csc\python.exe -s` imports all checked project packages successfully: `ee`, `geemap`, `geopandas`, `rasterio`, `rioxarray`, `xarray`, `numpy`, `pandas`, `scipy`, `sklearn`, `statsmodels`, `matplotlib`, `seaborn`, `yaml`, `tqdm`, `joblib`, `pyarrow`, `openpyxl`, `folium`, `shapely`, `pyproj`, `fiona`, `pyogrio`, `geedim`, `cartopy`, `pymannkendall`, `semopy`, and `python-box`; key installed versions include `earthengine-api 1.6.15`, `geemap 0.36.6`, `pyogrio 0.11.1`, `pymannkendall 1.4.3`, and `semopy 2.3.11`; `geemap.ee_initialize(project="ee-gyf")` succeeded; `ee.data.getAssetRoots()` returned 52 roots; `ee.FeatureCollection("projects/ee-gyf/assets/hainan").size().getInfo()` returned 137.  
Problems: The first from-scratch conda solve timed out, so the existing verified `GEE` environment was cloned to `csc` and then upgraded in place. Base Anaconda required a temporary `PATH` fix for `D:\Annaconda3\Library\bin` so SSL could load. Pip reports a lingering warning for an invalid `-ython-box` distribution metadata entry, but `import box` succeeds and `python-box 7.3.2` is installed inside `csc`. Some pre-existing optional package dependency warnings remain from the cloned broad geospatial environment; the required project imports and GEE initialization passed.  
Next stage: Keep Stage 2 paused until all Stage 2 Earth Engine export tasks complete; use `conda activate csc` or `D:\Annaconda3\envs\csc\python.exe` for future project commands.

## Stage 3 - NDVI, FVC, and NIRv calculation

Status: completed  
Date: 2026-06-25  
Inputs: `config/config.yaml`; Earth Engine Cloud Project `ee-gyf`; corrected Hainan boundary asset `projects/ee-gyf/assets/Hainan-Island-Boundary`; Stage 1 assets `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m` and `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean`; Stage 2 assets `users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000` through `users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024`.  
Outputs: Created `gee/stage03_export_indices.py`; generated `outputs/tables/table_fvc_thresholds.csv`; generated `outputs/tables/table_annual_fvc_nirv_stats.csv`; generated `outputs/tables/table_stage03_indices_asset_manifest.csv`; generated `outputs/figures/fig02_annual_fvc_nirv_timeseries.png`; submitted annual NDVI, FVC, and NIRv exports to `users/gyf/forest_csc_alphaearth/stage03_indices/`.  
Checks: Earth Engine initialized successfully with project `ee-gyf`; Stage 1 ForestMask and ForestType assets, the Stage 2 Landsat asset folder, and the Stage 3 output Asset folder were accessible; all 25 Stage 2 LandsatComposite image assets from 2000-2024 exist and contain the required six bands `Blue`, `Green`, `Red`, `NIR`, `SWIR1`, and `SWIR2`; unified FVC thresholds were computed from Earth Engine fixed histograms over all 2000-2024 forest pixels, with NDVI_soil 0.494750, NDVI_veg 0.872750, and histogram count 726,415,224; the annual statistics table has 75 rows for 25 years and three forest groups (`all_forest`, `natural_forest`, `plantation_forest`); table-level checks found mean NDVI range 0.584897-0.831641, mean FVC range 0.298411-0.885637, and mean NIRv range 0.150265-0.266127; the Asset manifest has 75 submitted rows for NDVI, FVC, and NIRv; latest task status check found 2 RUNNING, 73 READY, and 0 FAILED Stage 3 export tasks; `gee/stage03_export_indices.py` passed `py_compile`; local `outputs/` contains no `.tif` or `.tiff` files.  
Problems: The configured `gee_assets.hainan_roi` still points to the unsuitable `projects/ee-gyf/assets/hainan`, so this run used the corrected Hainan boundary override already documented in prior stages. Earth Engine exports are asynchronous; at the latest check, Stage 3 index Asset exports had been submitted but had not yet materialized as IMAGE assets. A pandas optional dependency warning reported `numexpr` below the preferred pandas version, but the CSV and figure outputs were written successfully.  
Next stage: Do not proceed to Stage 4 until all Stage 3 Earth Engine export tasks complete successfully and `NDVI_2000-2024`, `FVC_2000-2024`, and `NIRv_2000-2024` exist under `users/gyf/forest_csc_alphaearth/stage03_indices/`.

## Handoff update: Stage 3 paused

- time: 2026-06-25 22:12:00 +08:00
- current_stage: Stage 3 NDVI/FVC/NIRv
- status: GEE export tasks submitted, not all completed
- task_status_summary: 7 COMPLETED, 2 RUNNING, 66 READY, 0 FAILED, 0 CANCELLED
- asset_status_summary: 7 target assets exist as IMAGE, 68 target assets remain export_pending
- failed_tasks: none found in the latest check
- next_action: check Stage 3 GEE task completion and Asset availability before Stage 4
- do_not_run_next_stage_until:
  - NDVI_2000-2024 all exist as GEE Assets
  - FVC_2000-2024 all exist as GEE Assets
  - NIRv_2000-2024 all exist as GEE Assets
  - `outputs/tables/table_fvc_thresholds.csv` is complete
  - `outputs/tables/table_annual_fvc_nirv_stats.csv` is complete
  - `outputs/tables/table_stage03_indices_asset_manifest.csv` is updated
- explicit_pause: Do not execute Stage 4 or any later stage during this handoff. Do not submit new Earth Engine tasks, cancel existing Stage 3 tasks, rerun Stage 3, download full-resolution GeoTIFFs, or delete existing results.
- handoff_note: See `docs/handoff_note.md` for the year-by-year Stage 3 task table, target Asset status table, local output checks, Git sync notes, ignored local files, and office-computer recovery prompt.

## Stage 4 - EQI_func construction

Status: completed  
Date: 2026-06-26  
Inputs: `config/config.yaml`; Earth Engine Cloud Project `ee-gyf`; corrected Hainan boundary asset `projects/ee-gyf/assets/Hainan-Island-Boundary`; Stage 1 assets `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m` and `users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean`; Stage 3 assets `users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000` through `FVC_2024` and `users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000` through `NIRv_2024`; Earth Engine public datasets `USGS/SRTMGL1_003` and `ECMWF/ERA5_LAND/MONTHLY_AGGR`.  
Outputs: Created `gee/stage04_build_eqi_model.py`; generated `outputs/stage04_eqi/EQI_regression_samples.csv`; generated `outputs/tables/table_eqi_regression_coefficients.csv`; generated `outputs/tables/table_eqi_regression_diagnostics.csv`; generated `outputs/tables/table_annual_eqi_stats.csv`; generated `outputs/tables/table_stage04_eqi_asset_manifest.csv`; generated `outputs/figures/fig03_eqi_timeseries_by_forest_type.png`; submitted or reused annual EQI_func exports under `users/gyf/forest_csc_alphaearth/stage04_eqi/`.  
Checks: Earth Engine initialized successfully with project `ee-gyf`; all 25 FVC and 25 NIRv Stage 3 input IMAGE assets were accessible; Stage 1 ForestMask and ForestType assets were accessible; DEM and Slope were generated from `USGS/SRTMGL1_003`; annual climate controls were generated from ERA5-Land monthly `total_precipitation_sum` and `temperature_2m`, with precipitation retained as annual meters and temperature converted from K to degrees C; simplified_model = false; the unified pooled model used `NIRv ~ FVC + DEM + Slope + Precip + Temp` and did not include ForestType; regression samples were stratified by natural forest and plantation forest with 10,000 points per class per year, producing 500,000 cleaned sample rows; model diagnostics were R2 = 0.77283639, RMSE = 0.03034619, MAE = 0.02316444, and Bias = 0.0; annual EQI statistics contain 75 rows for 25 years and three forest groups (`all_forest`, `natural_forest`, `plantation_forest`); EQI_mean ranges from -0.01065756 to 0.0096903 and EQI_std ranges from 0.02114004 to 0.0415534; the Stage 4 manifest has 25 rows; latest GEE status check found 1 target EQI_func IMAGE asset already present, 3 RUNNING tasks, 21 READY tasks, and 0 FAILED tasks; local `outputs/` contains no `.tif` or `.tiff` files.  
Problems: Earth Engine exports are asynchronous; at the latest check, 24 of 25 Stage 4 target EQI_func assets had not yet materialized as IMAGE assets, although their export tasks were RUNNING or READY and no FAILED task was found. A first long run timed out after completing the sample table and part of the annual statistics, so the resumable script was rerun without overwriting samples; it reused the complete 500,000-row sample table, avoided duplicate export submissions for existing tasks/assets, and completed all local Stage 4 outputs.  
Next stage: Do not proceed to Stage 5 until all Stage 4 Earth Engine export tasks complete successfully and `EQI_func_2000` through `EQI_func_2024` exist under `users/gyf/forest_csc_alphaearth/stage04_eqi/`.
