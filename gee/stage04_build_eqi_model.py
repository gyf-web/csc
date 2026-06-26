"""Stage 4: build annual EQI_func images from unified NIRv residuals.

This script reads Stage 3 FVC and NIRv Earth Engine Assets, samples forest
pixels with environmental covariates, fits one pooled regression model in
Python, and exports annual EQI_func residual rasters back to Earth Engine
Assets.

Local outputs are limited to:
1. outputs/stage04_eqi/EQI_regression_samples.csv
2. outputs/tables/table_eqi_regression_coefficients.csv
3. outputs/tables/table_eqi_regression_diagnostics.csv
4. outputs/tables/table_annual_eqi_stats.csv
5. outputs/tables/table_stage04_eqi_asset_manifest.csv
6. outputs/figures/fig03_eqi_timeseries_by_forest_type.png

No annual EQI_func GeoTIFFs are downloaded locally.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

try:
    import ee
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "The earthengine-api package is required. Activate the project "
        "environment or install earthengine-api before running Stage 4."
    ) from exc

try:
    import geemap  # type: ignore
except ImportError:  # pragma: no cover - optional GEEMu fallback
    geemap = None


PROJECT_NAME = "hainan_forest_greening_quality"
DEFAULT_HAINAN_ROI = "projects/ee-gyf/assets/Hainan-Island-Boundary"
DEFAULT_FOREST_MASK_ASSET = (
    "users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m"
)
DEFAULT_FOREST_TYPE_ASSET = (
    "users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean"
)
DEFAULT_INDICES_ASSET_ROOT = "users/gyf/forest_csc_alphaearth/stage03_indices"
DEFAULT_EQI_ASSET_ROOT = "users/gyf/forest_csc_alphaearth/stage04_eqi"
MODEL_TYPE = "unified_residual_model"
MODEL_TERMS = ["FVC", "DEM", "Slope", "Precip", "Temp"]
FOREST_TYPES = [
    ("all_forest", None),
    ("natural_forest", 1),
    ("plantation_forest", 2),
]
SAMPLE_FIELDNAMES = [
    "year",
    "longitude",
    "latitude",
    "NIRv",
    "FVC",
    "DEM",
    "Slope",
    "Precip",
    "Temp",
    "ForestType",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and export Stage 4 EQI_func annual residual images."
    )
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--project",
        default=os.environ.get("EE_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("EE_PROJECT_ID"),
        help="Earth Engine Cloud Project ID. Required for online EE work.",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Start Earth Engine Asset export tasks. Default is dry run.",
    )
    parser.add_argument(
        "--hainan-roi",
        default=None,
        help="Optional Hainan ROI asset override. The config is still read first.",
    )
    parser.add_argument("--forest-mask-asset", default=None)
    parser.add_argument("--forest-type-asset", default=None)
    parser.add_argument("--indices-asset-root", default=None)
    parser.add_argument("--eqi-asset-root", default=None)
    parser.add_argument("--stage-dir", default="outputs/stage04_eqi")
    parser.add_argument("--tables-dir", default="outputs/tables")
    parser.add_argument("--figures-dir", default="outputs/figures")
    parser.add_argument("--tile-scale", type=int, default=4)
    parser.add_argument(
        "--samples-per-class",
        type=int,
        default=10000,
        help="ForestType-stratified sample count per class per year.",
    )
    parser.add_argument(
        "--overwrite-samples",
        action="store_true",
        help="Rebuild the local regression sample CSV.",
    )
    parser.add_argument(
        "--skip-stats",
        action="store_true",
        help="Skip reducer-based annual EQI statistics and figure generation.",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError(f"Invalid YAML config: {config_path}")
    return config


def get_config_value(config: dict[str, Any], *keys: str) -> Any:
    node: Any = config
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def initialize_ee(project: str | None) -> None:
    if not project:
        raise RuntimeError(
            "Earth Engine Cloud Project ID is required for online Stage 4 work. "
            "Pass --project PROJECT_ID or set EE_PROJECT."
        )
    if geemap is not None:
        geemap.ee_initialize(project=project)
    else:
        ee.Initialize(project=project)
    ee.data.setDefaultWorkloadTag("hainan-stage04-eqi")


def require_asset(asset_id: str, expected_type: str | None = None) -> dict[str, Any]:
    try:
        asset = ee.data.getAsset(asset_id)
    except Exception as exc:  # pragma: no cover - online EE guard
        raise RuntimeError(
            f"Required Earth Engine Asset is missing or inaccessible: {asset_id}"
        ) from exc
    if expected_type and asset.get("type") != expected_type:
        raise RuntimeError(
            f"Unexpected asset type for {asset_id}: "
            f"expected {expected_type}, got {asset.get('type')}"
        )
    return asset


def existing_asset_type(asset_id: str) -> str | None:
    try:
        return str(ee.data.getAsset(asset_id).get("type"))
    except Exception:
        return None


def task_status_by_description() -> dict[str, dict[str, Any]]:
    tasks = ee.data.getTaskList()
    status: dict[str, dict[str, Any]] = {}
    priority = {"RUNNING": 4, "READY": 3, "COMPLETED": 2, "FAILED": 1, "CANCELLED": 0}
    for task in tasks:
        description = task.get("description")
        state = task.get("state")
        if not description or not state:
            continue
        old = status.get(description)
        if old is None or priority.get(state, -1) > priority.get(old.get("state"), -1):
            status[description] = task
    return status


def index_asset_id(root: str, index_name: str, year: int) -> str:
    return f"{root.rstrip('/')}/{index_name}_{year}"


def eqi_asset_id(root: str, year: int) -> str:
    return f"{root.rstrip('/')}/EQI_func_{year}"


def load_fvc_nirv(
    indices_root: str,
    year: int,
    forest_mask: "ee.Image",
    hainan: "ee.FeatureCollection",
) -> tuple["ee.Image", "ee.Image"]:
    fvc = (
        ee.Image(index_asset_id(indices_root, "FVC", year))
        .select("FVC")
        .updateMask(forest_mask)
        .clip(hainan)
    )
    nirv = (
        ee.Image(index_asset_id(indices_root, "NIRv", year))
        .select("NIRv")
        .updateMask(forest_mask)
        .clip(hainan)
    )
    return fvc, nirv


def build_dem_slope(hainan: "ee.FeatureCollection") -> tuple["ee.Image", "ee.Image"]:
    dem = (
        ee.Image("USGS/SRTMGL1_003")
        .select("elevation")
        .rename("DEM")
        .clip(hainan)
    )
    slope = ee.Terrain.slope(dem).rename("Slope").clip(hainan)
    return dem, slope


def get_annual_climate(year: int, hainan: "ee.FeatureCollection") -> "ee.Image":
    start = f"{year}-01-01"
    end = f"{year + 1}-01-01"
    era5 = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterDate(start, end)
        .filterBounds(hainan.geometry().bounds())
    )
    precip = era5.select("total_precipitation_sum").sum().rename("Precip").clip(hainan)
    temp = (
        era5.select("temperature_2m")
        .mean()
        .subtract(273.15)
        .rename("Temp")
        .clip(hainan)
    )
    return precip.addBands(temp)


def sample_image_for_year(
    year: int,
    indices_root: str,
    forest_mask: "ee.Image",
    forest_type: "ee.Image",
    dem: "ee.Image",
    slope: "ee.Image",
    hainan: "ee.FeatureCollection",
) -> "ee.Image":
    fvc, nirv = load_fvc_nirv(indices_root, year, forest_mask, hainan)
    year_band = ee.Image.constant(year).rename("year").toInt16()
    lonlat = ee.Image.pixelLonLat().select(["longitude", "latitude"])
    return (
        nirv.addBands(fvc)
        .addBands(dem)
        .addBands(slope)
        .addBands(get_annual_climate(year, hainan))
        .addBands(forest_type.rename("ForestType").toByte())
        .addBands(year_band)
        .addBands(lonlat)
        .updateMask(forest_mask)
        .clip(hainan)
    )


def sample_year(
    year: int,
    sample_img: "ee.Image",
    hainan: "ee.FeatureCollection",
    samples_per_class: int,
    random_seed: int,
    scale: int,
    tile_scale: int,
) -> list[dict[str, Any]]:
    samples = sample_img.stratifiedSample(
        numPoints=samples_per_class,
        classBand="ForestType",
        classValues=[1, 2],
        classPoints=[samples_per_class, samples_per_class],
        region=hainan.geometry(),
        scale=scale,
        seed=random_seed + year,
        tileScale=tile_scale,
        dropNulls=True,
        geometries=False,
    )
    sample_df = ee.data.computeFeatures(
        {
            "expression": samples,
            "fileFormat": "PANDAS_DATAFRAME",
        }
    )
    if sample_df.empty:
        return []
    features = sample_df.to_dict("records")
    rows: list[dict[str, Any]] = []
    for props in features:
        row = {field: props.get(field) for field in SAMPLE_FIELDNAMES}
        if all(row.get(field) is not None for field in SAMPLE_FIELDNAMES):
            rows.append(row)
    return rows


def sample_years_present(samples_csv: Path) -> set[int]:
    if not samples_csv.exists():
        return set()
    years = set()
    with samples_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("year"):
                years.add(int(float(row["year"])))
    return years


def append_sample_rows(samples_csv: Path, rows: list[dict[str, Any]], write_header: bool) -> None:
    samples_csv.parent.mkdir(parents=True, exist_ok=True)
    with samples_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def build_or_load_samples(
    samples_csv: Path,
    years: list[int],
    indices_root: str,
    forest_mask: "ee.Image",
    forest_type: "ee.Image",
    dem: "ee.Image",
    slope: "ee.Image",
    hainan: "ee.FeatureCollection",
    samples_per_class: int,
    random_seed: int,
    scale: int,
    tile_scale: int,
    overwrite_samples: bool,
) -> pd.DataFrame:
    if overwrite_samples and samples_csv.exists():
        samples_csv.unlink()
    done_years = sample_years_present(samples_csv)
    if done_years:
        print(f"Using existing sample rows for years: {sorted(done_years)}")
    for year in years:
        if year in done_years:
            continue
        sample_img = sample_image_for_year(
            year, indices_root, forest_mask, forest_type, dem, slope, hainan
        )
        rows = sample_year(
            year,
            sample_img,
            hainan,
            samples_per_class,
            random_seed,
            scale,
            tile_scale,
        )
        if len(rows) < samples_per_class:
            raise RuntimeError(
                f"Too few Stage 4 samples for {year}: {len(rows)} rows. "
                "Check FVC/NIRv masks and ForestType classes."
            )
        append_sample_rows(samples_csv, rows, write_header=not samples_csv.exists())
        print(f"Sampled {year}: {len(rows)} rows")
    df = pd.read_csv(samples_csv)
    return clean_sample_dataframe(df)


def clean_sample_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required = ["year", "longitude", "latitude", "NIRv", *MODEL_TERMS, "ForestType"]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise RuntimeError(f"Regression sample CSV is missing columns: {missing}")
    df = df[required].copy()
    for column in required:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    df = df[df["ForestType"].isin([1, 2])]
    if df.empty:
        raise RuntimeError("No valid regression sample rows remain after cleaning.")
    return df


def fit_unified_model(df: pd.DataFrame) -> Any:
    x = sm.add_constant(df[MODEL_TERMS], has_constant="add")
    y = df["NIRv"]
    model = sm.OLS(y, x, missing="drop")
    return model.fit()


def write_coefficients(path: Path, result: Any) -> None:
    rows = []
    for term in ["const", *MODEL_TERMS]:
        rows.append(
            {
                "term": "Intercept" if term == "const" else term,
                "coefficient": round(float(result.params[term]), 12),
                "std_error": round(float(result.bse[term]), 12),
                "t_value": round(float(result.tvalues[term]), 6),
                "p_value": round(float(result.pvalues[term]), 12),
                "model_type": MODEL_TYPE,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term",
                "coefficient",
                "std_error",
                "t_value",
                "p_value",
                "model_type",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_diagnostics(path: Path, df: pd.DataFrame, result: Any) -> dict[str, float]:
    pred = result.predict(sm.add_constant(df[MODEL_TERMS], has_constant="add"))
    residual = df["NIRv"] - pred
    rmse = math.sqrt(float(np.mean(np.square(residual))))
    mae = float(np.mean(np.abs(residual)))
    bias = float(np.mean(residual))
    diagnostics = {
        "R2": round(float(result.rsquared), 8),
        "RMSE": round(rmse, 8),
        "MAE": round(mae, 8),
        "Bias": round(bias, 12),
        "sample_count": int(len(df)),
        "model_type": MODEL_TYPE,
        "simplified_model": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(diagnostics))
        writer.writeheader()
        writer.writerow(diagnostics)
    return diagnostics


def model_coefficients(result: Any) -> dict[str, float]:
    return {
        "Intercept": float(result.params["const"]),
        "FVC": float(result.params["FVC"]),
        "DEM": float(result.params["DEM"]),
        "Slope": float(result.params["Slope"]),
        "Precip": float(result.params["Precip"]),
        "Temp": float(result.params["Temp"]),
    }


def build_eqi_image(
    year: int,
    indices_root: str,
    forest_mask: "ee.Image",
    dem: "ee.Image",
    slope: "ee.Image",
    hainan: "ee.FeatureCollection",
    coefs: dict[str, float],
    scale: int,
) -> "ee.Image":
    fvc, nirv = load_fvc_nirv(indices_root, year, forest_mask, hainan)
    climate = get_annual_climate(year, hainan)
    precip = climate.select("Precip")
    temp = climate.select("Temp")
    nirv_pred = (
        ee.Image.constant(coefs["Intercept"])
        .add(fvc.multiply(coefs["FVC"]))
        .add(dem.multiply(coefs["DEM"]))
        .add(slope.multiply(coefs["Slope"]))
        .add(precip.multiply(coefs["Precip"]))
        .add(temp.multiply(coefs["Temp"]))
        .rename("NIRv_predicted")
    )
    return (
        nirv.subtract(nirv_pred)
        .rename("EQI_func")
        .updateMask(forest_mask)
        .clip(hainan)
        .set(
            {
                "year": year,
                "index_name": "EQI_func",
                "model_type": MODEL_TYPE,
                "simplified_model": False,
                "source": "NIRv residual after FVC and environmental correction",
                "scale": scale,
                "project": PROJECT_NAME,
                "precip_units": "m year-1 from ERA5-Land monthly total_precipitation_sum",
                "temp_units": "degree C from ERA5-Land monthly mean temperature_2m",
            }
        )
    )


def metric_stats(
    image: "ee.Image",
    mask: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> dict[str, Any]:
    reducer = (
        ee.Reducer.mean()
        .combine(ee.Reducer.median(), sharedInputs=True)
        .combine(ee.Reducer.stdDev(), sharedInputs=True)
        .combine(ee.Reducer.percentile([25, 75]), sharedInputs=True)
        .combine(ee.Reducer.count(), sharedInputs=True)
    )
    result = (
        image.updateMask(mask)
        .reduceRegion(
            reducer=reducer,
            geometry=hainan.geometry(),
            scale=scale,
            crs="EPSG:4326",
            maxPixels=1e13,
            tileScale=tile_scale,
        )
        .getInfo()
    )
    return result or {}


def safe_float(value: Any) -> float | str:
    if value is None:
        return ""
    return round(float(value), 8)


def annual_eqi_stats_row(
    year: int,
    forest_type_name: str,
    forest_type_code: int | None,
    eqi: "ee.Image",
    forest_mask: "ee.Image",
    forest_type: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> dict[str, Any]:
    mask = forest_mask if forest_type_code is None else forest_type.eq(forest_type_code).selfMask()
    stats = metric_stats(eqi, mask, hainan, scale, tile_scale)
    valid_pixel_count = int(stats.get("EQI_func_count") or 0)
    valid_area_km2 = valid_pixel_count * scale * scale / 1_000_000
    return {
        "year": year,
        "forest_type": forest_type_name,
        "EQI_mean": safe_float(stats.get("EQI_func_mean")),
        "EQI_median": safe_float(stats.get("EQI_func_median")),
        "EQI_std": safe_float(stats.get("EQI_func_stdDev")),
        "EQI_q25": safe_float(stats.get("EQI_func_p25")),
        "EQI_q75": safe_float(stats.get("EQI_func_p75")),
        "valid_pixel_count": valid_pixel_count,
        "valid_area_km2": round(valid_area_km2, 6),
    }


def write_eqi_stats(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "year",
        "forest_type",
        "EQI_mean",
        "EQI_median",
        "EQI_std",
        "EQI_q25",
        "EQI_q75",
        "valid_pixel_count",
        "valid_area_km2",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "year",
        "asset_id",
        "export_description",
        "export_status",
        "scale",
        "crs",
        "model_type",
        "simplified_model",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_manifest(path: Path) -> dict[int, dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {int(row["year"]): row for row in rows}


def export_image_to_asset(
    image: "ee.Image",
    asset_id: str,
    description: str,
    hainan: "ee.FeatureCollection",
    scale: int,
) -> Any:
    task = ee.batch.Export.image.toAsset(
        image=image.toFloat(),
        description=description,
        assetId=asset_id,
        region=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
    )
    task.start()
    return task


def plot_eqi_timeseries(stats_csv: Path, figure_path: Path) -> None:
    df = pd.read_csv(stats_csv)
    keep = ["all_forest", "natural_forest", "plantation_forest"]
    df = df[df["forest_type"].isin(keep)].copy()
    labels = {
        "all_forest": "All forest",
        "natural_forest": "Natural forest",
        "plantation_forest": "Plantation forest",
    }
    colors = {
        "all_forest": "#333333",
        "natural_forest": "#1b8a5a",
        "plantation_forest": "#c7832b",
    }
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for forest_type_name in keep:
        sub = df[df["forest_type"] == forest_type_name]
        ax.plot(
            sub["year"],
            sub["EQI_mean"],
            marker="o",
            linewidth=1.8,
            markersize=3,
            label=labels[forest_type_name],
            color=colors[forest_type_name],
        )
    ax.axhline(0, color="#8c8c8c", linewidth=0.8)
    ax.set_ylabel("Mean EQI_func")
    ax.set_xlabel("Year")
    ax.grid(True, color="#d9d9d9", linewidth=0.6, alpha=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="best")
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=300)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))

    scale = int(get_config_value(config, "project", "target_scale") or 30)
    start_year = int(get_config_value(config, "project", "start_year") or 2000)
    end_year = int(get_config_value(config, "project", "end_year") or 2024)
    crs = str(get_config_value(config, "project", "crs") or "EPSG:4326")
    random_seed = int(get_config_value(config, "analysis", "random_seed") or 2026)
    years = list(range(start_year, end_year + 1))

    if scale != 30 or crs != "EPSG:4326":
        raise RuntimeError(f"Stage 4 is fixed at 30 m EPSG:4326, got scale={scale}, crs={crs}.")
    if start_year != 2000 or end_year != 2024:
        raise RuntimeError(f"Stage 4 is fixed to 2000-2024, got {start_year}-{end_year}.")
    if args.samples_per_class < 10000:
        raise RuntimeError("Stage 4 requires at least 10,000 samples per forest class per year.")

    hainan_asset = (
        args.hainan_roi
        or get_config_value(config, "gee_assets", "hainan_roi")
        or DEFAULT_HAINAN_ROI
    )
    if not hainan_asset or str(hainan_asset).endswith("/hainan"):
        hainan_asset = DEFAULT_HAINAN_ROI
    forest_mask_asset = (
        args.forest_mask_asset
        or get_config_value(config, "gee_assets", "forest_mask_asset")
        or DEFAULT_FOREST_MASK_ASSET
    )
    forest_type_asset = (
        args.forest_type_asset
        or get_config_value(config, "gee_assets", "forest_type_asset")
        or DEFAULT_FOREST_TYPE_ASSET
    )
    indices_root = (
        args.indices_asset_root
        or get_config_value(config, "gee_assets", "indices_asset_root")
        or DEFAULT_INDICES_ASSET_ROOT
    )
    eqi_root = (
        args.eqi_asset_root
        or get_config_value(config, "gee_assets", "eqi_asset_root")
        or DEFAULT_EQI_ASSET_ROOT
    )

    stage_dir = Path(args.stage_dir)
    tables_dir = Path(args.tables_dir)
    figures_dir = Path(args.figures_dir)
    samples_csv = stage_dir / "EQI_regression_samples.csv"
    coefficients_csv = tables_dir / "table_eqi_regression_coefficients.csv"
    diagnostics_csv = tables_dir / "table_eqi_regression_diagnostics.csv"
    stats_csv = tables_dir / "table_annual_eqi_stats.csv"
    manifest_csv = tables_dir / "table_stage04_eqi_asset_manifest.csv"
    figure_path = figures_dir / "fig03_eqi_timeseries_by_forest_type.png"

    resolved = {
        "mode": "export" if args.export else "dry_run",
        "project": args.project or "MISSING",
        "hainan_roi": hainan_asset,
        "forest_mask_asset": forest_mask_asset,
        "forest_type_asset": forest_type_asset,
        "indices_asset_root": indices_root,
        "eqi_asset_root": eqi_root,
        "years": f"{start_year}-{end_year}",
        "scale": scale,
        "crs": crs,
        "samples_per_class_per_year": args.samples_per_class,
        "model": "NIRv ~ FVC + DEM + Slope + Precip + Temp",
        "simplified_model": False,
        "samples_csv": str(samples_csv),
        "coefficients_csv": str(coefficients_csv),
        "diagnostics_csv": str(diagnostics_csv),
        "stats_csv": str(stats_csv),
        "manifest_csv": str(manifest_csv),
        "figure_path": str(figure_path),
    }
    print(json.dumps(resolved, indent=2, ensure_ascii=False))

    initialize_ee(args.project)
    require_asset(str(hainan_asset), expected_type="TABLE")
    require_asset(str(forest_mask_asset), expected_type="IMAGE")
    require_asset(str(forest_type_asset), expected_type="IMAGE")
    require_asset(str(indices_root), expected_type="FOLDER")
    require_asset(str(eqi_root), expected_type="FOLDER")
    require_asset("USGS/SRTMGL1_003", expected_type="IMAGE")

    for year in years:
        require_asset(index_asset_id(str(indices_root), "FVC", year), expected_type="IMAGE")
        require_asset(index_asset_id(str(indices_root), "NIRv", year), expected_type="IMAGE")

    # Force a small metadata request so climate band problems fail before sampling.
    climate_bands = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterDate("2024-01-01", "2025-01-01")
        .select(["total_precipitation_sum", "temperature_2m"])
        .first()
        .bandNames()
        .getInfo()
    )
    if set(climate_bands) != {"total_precipitation_sum", "temperature_2m"}:
        raise RuntimeError(f"Unexpected ERA5-Land climate bands: {climate_bands}")

    hainan = ee.FeatureCollection(str(hainan_asset))
    forest_mask = ee.Image(str(forest_mask_asset)).eq(1).selfMask()
    forest_type = ee.Image(str(forest_type_asset))
    dem, slope = build_dem_slope(hainan)

    samples = build_or_load_samples(
        samples_csv,
        years,
        str(indices_root),
        forest_mask,
        forest_type,
        dem,
        slope,
        hainan,
        args.samples_per_class,
        random_seed,
        scale,
        args.tile_scale,
        args.overwrite_samples,
    )
    print(f"Regression sample rows after cleaning: {len(samples)}")

    result = fit_unified_model(samples)
    write_coefficients(coefficients_csv, result)
    diagnostics = write_diagnostics(diagnostics_csv, samples, result)
    coefs = model_coefficients(result)
    print(f"Wrote {coefficients_csv}")
    print(f"Wrote {diagnostics_csv}")
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))

    eqi_by_year: dict[int, ee.Image] = {}
    if not args.skip_stats:
        stats_rows: list[dict[str, Any]] = []
    manifest_by_year = load_manifest(manifest_csv)
    existing_tasks = task_status_by_description() if args.export else {}
    manifest_rows: list[dict[str, Any]] = []
    submitted_tasks: list[dict[str, Any]] = []

    for year in years:
        eqi = build_eqi_image(year, str(indices_root), forest_mask, dem, slope, hainan, coefs, scale)
        eqi_by_year[year] = eqi

        if not args.skip_stats:
            for forest_type_name, forest_type_code in FOREST_TYPES:
                stats_rows.append(
                    annual_eqi_stats_row(
                        year,
                        forest_type_name,
                        forest_type_code,
                        eqi,
                        forest_mask,
                        forest_type,
                        hainan,
                        scale,
                        args.tile_scale,
                    )
                )
            write_eqi_stats(stats_csv, stats_rows)
            print(f"Annual EQI statistics complete for {year}")

        asset_id = eqi_asset_id(str(eqi_root), year)
        description = f"EQI_func_{year}"
        old = manifest_by_year.get(year, {})
        export_status = old.get("export_status") or "not_submitted"
        notes = old.get("notes") or "No export requested."
        if args.export:
            asset_type = existing_asset_type(asset_id)
            existing_task = existing_tasks.get(description)
            existing_state = existing_task.get("state") if existing_task else None
            if asset_type == "IMAGE":
                export_status = "existing_asset"
                notes = "Asset already exists; export was not resubmitted."
            elif existing_state in {"READY", "RUNNING", "COMPLETED"}:
                export_status = f"existing_task_{str(existing_state).lower()}"
                notes = f"Existing task ID: {existing_task.get('id')}"
            else:
                task = export_image_to_asset(eqi, asset_id, description, hainan, scale)
                export_status = "submitted"
                notes = f"Submitted task ID: {task.id}"
                submitted_tasks.append({"year": year, "task_id": task.id})
        manifest_rows.append(
            {
                "year": year,
                "asset_id": asset_id,
                "export_description": description,
                "export_status": export_status,
                "scale": scale,
                "crs": crs,
                "model_type": MODEL_TYPE,
                "simplified_model": False,
                "notes": notes,
            }
        )
        write_manifest(manifest_csv, manifest_rows)
        print(f"Manifest updated through {year}: {export_status}")

    if not args.skip_stats:
        print(f"Wrote {stats_csv}")
        plot_eqi_timeseries(stats_csv, figure_path)
        print(f"Wrote {figure_path}")
    print(f"Wrote {manifest_csv}")
    if submitted_tasks:
        print("Submitted Earth Engine tasks:")
        print(json.dumps(submitted_tasks, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
