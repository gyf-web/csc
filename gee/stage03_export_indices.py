"""Stage 3: export annual NDVI, FVC, and NIRv index images to EE Assets.

This script reads Stage 2 Landsat annual composites from Earth Engine Assets,
computes NDVI, a fixed-threshold FVC, and NIRv for 2000-2024, then exports the
annual index rasters back to Earth Engine Assets.

Local outputs are limited to:
1. outputs/tables/table_fvc_thresholds.csv
2. outputs/tables/table_annual_fvc_nirv_stats.csv
3. outputs/tables/table_stage03_indices_asset_manifest.csv
4. outputs/figures/fig02_annual_fvc_nirv_timeseries.png

No annual index GeoTIFFs are downloaded locally.
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
import pandas as pd
import yaml

try:
    import ee
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "The earthengine-api package is required. Activate the project "
        "environment or install earthengine-api before running Stage 3."
    ) from exc

try:
    import geemap  # type: ignore
except ImportError:  # pragma: no cover - optional GEEMu fallback
    geemap = None


PROJECT_NAME = "hainan_forest_greening_quality"
DEFAULT_OUTPUT_ASSET_ROOT = "users/gyf/forest_csc_alphaearth"
DEFAULT_HAINAN_ROI = "projects/ee-gyf/assets/Hainan-Island-Boundary"
DEFAULT_FOREST_MASK_ASSET = (
    "users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m"
)
DEFAULT_FOREST_TYPE_ASSET = (
    "users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean"
)
DEFAULT_LANDSAT_ASSET_ROOT = (
    "users/gyf/forest_csc_alphaearth/stage02_landsat"
)
DEFAULT_INDICES_ASSET_ROOT = (
    "users/gyf/forest_csc_alphaearth/stage03_indices"
)
LANDSAT_PREFIX = "LandsatComposite"
INDEX_NAMES = ["NDVI", "FVC", "NIRv"]
LANDSAT_BANDS = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]
FOREST_TYPES = [
    ("all_forest", None),
    ("natural_forest", 1),
    ("plantation_forest", 2),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Stage 3 NDVI/FVC/NIRv annual index images to EE Assets."
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
    parser.add_argument("--landsat-asset-root", default=None)
    parser.add_argument("--indices-asset-root", default=None)
    parser.add_argument("--tables-dir", default="outputs/tables")
    parser.add_argument("--figures-dir", default="outputs/figures")
    parser.add_argument("--tile-scale", type=int, default=4)
    parser.add_argument("--histogram-bins", type=int, default=4000)
    parser.add_argument(
        "--skip-stats",
        action="store_true",
        help="Skip reducer-based annual statistics and figure generation.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recompute existing local Stage 3 CSV outputs.",
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
            "Earth Engine Cloud Project ID is required for online Stage 3 work. "
            "Pass --project PROJECT_ID or set EE_PROJECT."
        )
    if geemap is not None:
        geemap.ee_initialize(project=project)
    else:
        ee.Initialize(project=project)
    ee.data.setDefaultWorkloadTag("hainan-stage03-indices")


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


def landsat_asset_id(root: str, year: int) -> str:
    return f"{root.rstrip('/')}/{LANDSAT_PREFIX}_{year}"


def index_asset_id(root: str, index_name: str, year: int) -> str:
    return f"{root.rstrip('/')}/{index_name}_{year}"


def load_landsat(root: str, year: int, forest_mask: "ee.Image", hainan: "ee.FeatureCollection") -> "ee.Image":
    return (
        ee.Image(landsat_asset_id(root, year))
        .select(LANDSAT_BANDS)
        .updateMask(forest_mask)
        .clip(hainan)
    )


def calculate_ndvi(landsat: "ee.Image", forest_mask: "ee.Image", hainan: "ee.FeatureCollection") -> "ee.Image":
    return (
        landsat.normalizedDifference(["NIR", "Red"])
        .rename("NDVI")
        .updateMask(forest_mask)
        .clip(hainan)
    )


def calculate_fvc(
    ndvi: "ee.Image",
    ndvi_soil: float,
    ndvi_veg: float,
    forest_mask: "ee.Image",
    hainan: "ee.FeatureCollection",
) -> "ee.Image":
    return (
        ndvi.subtract(ndvi_soil)
        .divide(ndvi_veg - ndvi_soil)
        .clamp(0, 1)
        .rename("FVC")
        .updateMask(forest_mask)
        .clip(hainan)
    )


def calculate_nirv(
    ndvi: "ee.Image",
    landsat: "ee.Image",
    forest_mask: "ee.Image",
    hainan: "ee.FeatureCollection",
) -> "ee.Image":
    return (
        ndvi.subtract(0.08)
        .multiply(landsat.select("NIR"))
        .rename("NIRv")
        .updateMask(forest_mask)
        .clip(hainan)
    )


def set_index_properties(image: "ee.Image", year: int, index_name: str, scale: int) -> "ee.Image":
    return image.set(
        {
            "year": year,
            "index_name": index_name,
            "source": "Landsat annual median composite",
            "scale": scale,
            "project": PROJECT_NAME,
        }
    )


def ndvi_histogram(
    ndvi: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
    bins: int,
) -> list[list[float]]:
    result = ndvi.reduceRegion(
        reducer=ee.Reducer.fixedHistogram(-1, 1, bins),
        geometry=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
        tileScale=tile_scale,
    )
    raw = result.get("NDVI").getInfo()
    return raw or []


def parse_histogram_rows(rows: list[list[float]], bins: int) -> list[tuple[float, float]]:
    parsed: list[tuple[float, float]] = []
    bin_width = 2.0 / bins
    for row in rows:
        if len(row) < 2:
            continue
        low = float(row[0])
        count = float(row[-1])
        if count <= 0 or not math.isfinite(count):
            continue
        value = low + bin_width / 2.0
        parsed.append((value, count))
    return parsed


def weighted_percentile(values_counts: list[tuple[float, float]], percentile: float) -> float:
    if not values_counts:
        raise RuntimeError("Cannot calculate percentile from an empty NDVI histogram.")
    values_counts = sorted(values_counts, key=lambda item: item[0])
    total = sum(count for _, count in values_counts)
    if total <= 0:
        raise RuntimeError("Cannot calculate percentile from a zero-count NDVI histogram.")
    target = total * percentile / 100.0
    cumulative = 0.0
    for value, count in values_counts:
        cumulative += count
        if cumulative >= target:
            return value
    return values_counts[-1][0]


def write_thresholds(
    path: Path,
    soil_percentile: int,
    veg_percentile: int,
    ndvi_soil: float,
    ndvi_veg: float,
    total_count: float,
    bins: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "ndvi_soil_percentile": soil_percentile,
            "ndvi_veg_percentile": veg_percentile,
            "ndvi_soil_value": round(ndvi_soil, 6),
            "ndvi_veg_value": round(ndvi_veg, 6),
            "method": f"Earth Engine fixedHistogram -1 to 1 with {bins} bins, combined across 2000-2024 forest pixels",
            "sample_or_histogram_count": int(round(total_count)),
        }
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_thresholds(path: Path) -> tuple[float, float]:
    with path.open("r", encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    return float(row["ndvi_soil_value"]), float(row["ndvi_veg_value"])


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
    return round(float(value), 6)


def annual_stats_row(
    year: int,
    forest_type_name: str,
    forest_type_code: int | None,
    indices: "ee.Image",
    forest_mask: "ee.Image",
    forest_type: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> dict[str, Any]:
    mask = forest_mask if forest_type_code is None else forest_type.eq(forest_type_code).selfMask()
    stats = metric_stats(indices, mask, hainan, scale, tile_scale)
    valid_pixel_count = int(stats.get("NDVI_count") or 0)
    valid_area_km2 = valid_pixel_count * scale * scale / 1_000_000
    return {
        "year": year,
        "forest_type": forest_type_name,
        "NDVI_mean": safe_float(stats.get("NDVI_mean")),
        "NDVI_median": safe_float(stats.get("NDVI_median")),
        "FVC_mean": safe_float(stats.get("FVC_mean")),
        "FVC_median": safe_float(stats.get("FVC_median")),
        "FVC_std": safe_float(stats.get("FVC_stdDev")),
        "NIRv_mean": safe_float(stats.get("NIRv_mean")),
        "NIRv_median": safe_float(stats.get("NIRv_median")),
        "NIRv_std": safe_float(stats.get("NIRv_stdDev")),
        "valid_pixel_count": valid_pixel_count,
        "valid_area_km2": round(valid_area_km2, 6),
    }


def write_stats(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "year",
        "forest_type",
        "NDVI_mean",
        "NDVI_median",
        "FVC_mean",
        "FVC_median",
        "FVC_std",
        "NIRv_mean",
        "NIRv_median",
        "NIRv_std",
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
        "index_name",
        "asset_id",
        "export_description",
        "export_status",
        "scale",
        "crs",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_manifest(path: Path) -> dict[tuple[int, str], dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    result = {}
    for row in rows:
        result[(int(row["year"]), row["index_name"])] = row
    return result


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


def plot_timeseries(stats_csv: Path, figure_path: Path) -> None:
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

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for forest_type_name in keep:
        sub = df[df["forest_type"] == forest_type_name]
        axes[0].plot(
            sub["year"],
            sub["FVC_mean"],
            marker="o",
            linewidth=1.8,
            markersize=3,
            label=labels[forest_type_name],
            color=colors[forest_type_name],
        )
        axes[1].plot(
            sub["year"],
            sub["NIRv_mean"],
            marker="o",
            linewidth=1.8,
            markersize=3,
            label=labels[forest_type_name],
            color=colors[forest_type_name],
        )
    axes[0].set_ylabel("Mean FVC")
    axes[1].set_ylabel("Mean NIRv")
    axes[1].set_xlabel("Year")
    for ax in axes:
        ax.grid(True, color="#d9d9d9", linewidth=0.6, alpha=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].legend(frameon=False, ncol=3, loc="best")
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
    soil_percentile = int(get_config_value(config, "analysis", "fvc_ndvi_soil_percentile") or 5)
    veg_percentile = int(get_config_value(config, "analysis", "fvc_ndvi_veg_percentile") or 95)

    if scale != 30 or crs != "EPSG:4326":
        raise RuntimeError(f"Stage 3 is fixed at 30 m EPSG:4326, got scale={scale}, crs={crs}.")
    if start_year != 2000 or end_year != 2024:
        raise RuntimeError(f"Stage 3 is fixed to 2000-2024, got {start_year}-{end_year}.")
    if soil_percentile >= veg_percentile:
        raise RuntimeError("FVC soil percentile must be lower than vegetation percentile.")

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
    landsat_root = (
        args.landsat_asset_root
        or get_config_value(config, "gee_assets", "landsat_asset_root")
        or DEFAULT_LANDSAT_ASSET_ROOT
    )
    indices_root = (
        args.indices_asset_root
        or get_config_value(config, "gee_assets", "indices_asset_root")
        or DEFAULT_INDICES_ASSET_ROOT
    )

    years = list(range(start_year, end_year + 1))
    tables_dir = Path(args.tables_dir)
    figures_dir = Path(args.figures_dir)
    thresholds_csv = tables_dir / "table_fvc_thresholds.csv"
    stats_csv = tables_dir / "table_annual_fvc_nirv_stats.csv"
    manifest_csv = tables_dir / "table_stage03_indices_asset_manifest.csv"
    figure_path = figures_dir / "fig02_annual_fvc_nirv_timeseries.png"

    resolved = {
        "mode": "export" if args.export else "dry_run",
        "project": args.project or "MISSING",
        "hainan_roi": hainan_asset,
        "forest_mask_asset": forest_mask_asset,
        "forest_type_asset": forest_type_asset,
        "landsat_asset_root": landsat_root,
        "indices_asset_root": indices_root,
        "years": f"{start_year}-{end_year}",
        "scale": scale,
        "crs": crs,
        "thresholds_csv": str(thresholds_csv),
        "stats_csv": str(stats_csv),
        "manifest_csv": str(manifest_csv),
        "figure_path": str(figure_path),
    }
    print(json.dumps(resolved, indent=2, ensure_ascii=False))

    initialize_ee(args.project)
    require_asset(str(hainan_asset), expected_type="TABLE")
    require_asset(str(forest_mask_asset), expected_type="IMAGE")
    require_asset(str(forest_type_asset), expected_type="IMAGE")
    require_asset(str(landsat_root), expected_type="FOLDER")
    require_asset(str(indices_root), expected_type="FOLDER")

    for year in years:
        require_asset(landsat_asset_id(str(landsat_root), year), expected_type="IMAGE")

    hainan = ee.FeatureCollection(str(hainan_asset))
    forest_mask = ee.Image(str(forest_mask_asset)).eq(1).selfMask()
    forest_type = ee.Image(str(forest_type_asset))

    ndvi_by_year: dict[int, ee.Image] = {}
    landsat_by_year: dict[int, ee.Image] = {}
    for year in years:
        landsat = load_landsat(str(landsat_root), year, forest_mask, hainan)
        band_names = landsat.bandNames().getInfo()
        missing_bands = sorted(set(LANDSAT_BANDS) - set(band_names))
        if missing_bands:
            raise RuntimeError(
                f"{landsat_asset_id(str(landsat_root), year)} is missing bands: {missing_bands}"
            )
        landsat_by_year[year] = landsat
        ndvi_by_year[year] = calculate_ndvi(landsat, forest_mask, hainan)

    if thresholds_csv.exists() and not args.overwrite:
        ndvi_soil, ndvi_veg = read_thresholds(thresholds_csv)
        print(f"Using existing thresholds from {thresholds_csv}: {ndvi_soil}, {ndvi_veg}")
    else:
        combined_hist: list[tuple[float, float]] = []
        for year in years:
            rows = ndvi_histogram(
                ndvi_by_year[year],
                hainan,
                scale,
                args.tile_scale,
                args.histogram_bins,
            )
            parsed = parse_histogram_rows(rows, args.histogram_bins)
            if not parsed:
                raise RuntimeError(f"Empty NDVI histogram for {year}.")
            combined_hist.extend(parsed)
            print(f"Histogram complete for {year}: {int(sum(c for _, c in parsed))} values")
        total_count = sum(count for _, count in combined_hist)
        ndvi_soil = weighted_percentile(combined_hist, soil_percentile)
        ndvi_veg = weighted_percentile(combined_hist, veg_percentile)
        if ndvi_veg <= ndvi_soil:
            raise RuntimeError(
                f"Invalid FVC thresholds: ndvi_soil={ndvi_soil}, ndvi_veg={ndvi_veg}"
            )
        write_thresholds(
            thresholds_csv,
            soil_percentile,
            veg_percentile,
            ndvi_soil,
            ndvi_veg,
            total_count,
            args.histogram_bins,
        )
        print(f"Wrote {thresholds_csv}")

    indices_by_year: dict[int, dict[str, ee.Image]] = {}
    for year in years:
        ndvi = set_index_properties(ndvi_by_year[year], year, "NDVI", scale)
        fvc = set_index_properties(
            calculate_fvc(ndvi_by_year[year], ndvi_soil, ndvi_veg, forest_mask, hainan),
            year,
            "FVC",
            scale,
        )
        nirv = set_index_properties(
            calculate_nirv(ndvi_by_year[year], landsat_by_year[year], forest_mask, hainan),
            year,
            "NIRv",
            scale,
        )
        indices_by_year[year] = {"NDVI": ndvi, "FVC": fvc, "NIRv": nirv}

    if not args.skip_stats and (args.overwrite or not stats_csv.exists()):
        stats_rows: list[dict[str, Any]] = []
        for year in years:
            combined = (
                indices_by_year[year]["NDVI"]
                .addBands(indices_by_year[year]["FVC"])
                .addBands(indices_by_year[year]["NIRv"])
            )
            for forest_type_name, forest_type_code in FOREST_TYPES:
                row = annual_stats_row(
                    year,
                    forest_type_name,
                    forest_type_code,
                    combined,
                    forest_mask,
                    forest_type,
                    hainan,
                    scale,
                    args.tile_scale,
                )
                stats_rows.append(row)
            write_stats(stats_csv, stats_rows)
            print(f"Annual statistics complete for {year}")
        plot_timeseries(stats_csv, figure_path)
        print(f"Wrote {stats_csv}")
        print(f"Wrote {figure_path}")
    elif not args.skip_stats and stats_csv.exists():
        print(f"Using existing annual statistics from {stats_csv}")
        plot_timeseries(stats_csv, figure_path)
        print(f"Wrote {figure_path}")

    manifest_by_key = load_manifest(manifest_csv)
    existing_tasks = task_status_by_description() if args.export else {}
    manifest_rows: list[dict[str, Any]] = []
    submitted_tasks: list[dict[str, Any]] = []
    for year in years:
        for index_name in INDEX_NAMES:
            asset_id = index_asset_id(str(indices_root), index_name, year)
            description = f"{index_name}_{year}"
            old = manifest_by_key.get((year, index_name), {})
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
                    task = export_image_to_asset(
                        indices_by_year[year][index_name],
                        asset_id,
                        description,
                        hainan,
                        scale,
                    )
                    export_status = "submitted"
                    notes = f"Submitted task ID: {task.id}"
                    submitted_tasks.append({"year": year, "index_name": index_name, "task_id": task.id})
            manifest_rows.append(
                {
                    "year": year,
                    "index_name": index_name,
                    "asset_id": asset_id,
                    "export_description": description,
                    "export_status": export_status,
                    "scale": scale,
                    "crs": crs,
                    "notes": notes,
                }
            )
        write_manifest(manifest_csv, manifest_rows)
        print(f"Manifest updated through {year}")

    print(f"Wrote {manifest_csv}")
    if submitted_tasks:
        print("Submitted Earth Engine tasks:")
        print(json.dumps(submitted_tasks, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
