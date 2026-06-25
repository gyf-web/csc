"""Stage 2: export annual Landsat surface-reflectance composites to EE Assets.

This script builds 2000-2024 annual median Landsat Collection 2 Level-2
surface-reflectance composites over the Hainan forest mask prepared in Stage 1.

Local outputs are limited to:
1. outputs/tables/table_landsat_valid_pixels_by_year.csv
2. outputs/tables/table_landsat_asset_manifest.csv

Full-resolution annual composites are exported only to Earth Engine Assets.
Exports are opt-in: use --export after checking the resolved parameters.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:
    import ee
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "The earthengine-api package is required. Activate the project "
        "environment or install earthengine-api before running Stage 2."
    ) from exc

try:
    import geemap  # type: ignore
except ImportError:  # pragma: no cover - optional GEEMu fallback
    geemap = None


PROJECT_NAME = "hainan_forest_greening_quality"
DEFAULT_OUTPUT_ASSET_ROOT = "users/gyf/forest_csc_alphaearth"
DEFAULT_FOREST_MASK_ASSET = (
    "users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m"
)
DEFAULT_FOREST_TYPE_ASSET = (
    "users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean"
)
STAGE_FOLDER = "stage02_landsat"
COMPOSITE_PREFIX = "LandsatComposite"
OUTPUT_BANDS = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]
LANDSAT57_BANDS = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]
LANDSAT89_BANDS = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
LANDSAT_COLLECTIONS = {
    "LT05": "LANDSAT/LT05/C02/T1_L2",
    "LE07": "LANDSAT/LE07/C02/T1_L2",
    "LC08": "LANDSAT/LC08/C02/T1_L2",
    "LC09": "LANDSAT/LC09/C02/T1_L2",
}
SR_SCALE = 0.0000275
SR_OFFSET = -0.2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Stage 2 Landsat annual median composites to EE Assets."
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
    parser.add_argument(
        "--forest-mask-asset",
        default=None,
        help="Optional Stage 1 ForestMask_30m asset override.",
    )
    parser.add_argument(
        "--forest-type-asset",
        default=None,
        help="Optional Stage 1 ForestType_30m_clean asset override for validation.",
    )
    parser.add_argument(
        "--output-asset-root",
        default=None,
        help="Asset root containing stage02_landsat.",
    )
    parser.add_argument("--tables-dir", default="outputs/tables")
    parser.add_argument("--tile-scale", type=int, default=4)
    parser.add_argument(
        "--skip-stats",
        action="store_true",
        help="Skip reducer-based valid-pixel statistics.",
    )
    parser.add_argument(
        "--overwrite-stats",
        action="store_true",
        help="Recompute the valid-pixel statistics even if the CSV already exists.",
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
            "Earth Engine Cloud Project ID is required for online Stage 2 work. "
            "Pass --project PROJECT_ID or set EE_PROJECT."
        )
    if geemap is not None:
        geemap.ee_initialize(project=project)
    else:
        ee.Initialize(project=project)
    ee.data.setDefaultWorkloadTag("hainan-stage02-landsat")


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


def stage_asset_root(output_asset_root: str) -> str:
    return f"{output_asset_root.rstrip('/')}/{STAGE_FOLDER}"


def composite_asset_id(stage_root: str, year: int) -> str:
    return f"{stage_root}/{COMPOSITE_PREFIX}_{year}"


def qa_clear_mask(image: "ee.Image") -> "ee.Image":
    qa = image.select("QA_PIXEL")
    clear = (
        qa.bitwiseAnd(1 << 0)
        .eq(0)
        .And(qa.bitwiseAnd(1 << 1).eq(0))
        .And(qa.bitwiseAnd(1 << 3).eq(0))
        .And(qa.bitwiseAnd(1 << 4).eq(0))
        .And(qa.bitwiseAnd(1 << 5).eq(0))
    )
    saturated = image.select("QA_RADSAT").eq(0)
    return clear.And(saturated)


def preprocess_landsat57(
    image: "ee.Image",
    hainan: "ee.FeatureCollection",
    forest_mask: "ee.Image",
) -> "ee.Image":
    sr = (
        image.select(LANDSAT57_BANDS)
        .multiply(SR_SCALE)
        .add(SR_OFFSET)
        .rename(OUTPUT_BANDS)
    )
    return (
        sr.updateMask(qa_clear_mask(image))
        .updateMask(forest_mask)
        .clip(hainan)
        .copyProperties(image, ["system:time_start", "SPACECRAFT_ID"])
    )


def preprocess_landsat89(
    image: "ee.Image",
    hainan: "ee.FeatureCollection",
    forest_mask: "ee.Image",
) -> "ee.Image":
    sr = (
        image.select(LANDSAT89_BANDS)
        .multiply(SR_SCALE)
        .add(SR_OFFSET)
        .rename(OUTPUT_BANDS)
    )
    return (
        sr.updateMask(qa_clear_mask(image))
        .updateMask(forest_mask)
        .clip(hainan)
        .copyProperties(image, ["system:time_start", "SPACECRAFT_ID"])
    )


def raw_annual_collection(year: int, hainan: "ee.FeatureCollection") -> "ee.ImageCollection":
    start = f"{year}-01-01"
    end = f"{year + 1}-01-01"
    bounds = hainan.geometry().bounds()
    collections = [
        ee.ImageCollection(asset_id).filterDate(start, end).filterBounds(bounds)
        for asset_id in LANDSAT_COLLECTIONS.values()
    ]
    merged = collections[0]
    for collection in collections[1:]:
        merged = merged.merge(collection)
    return merged


def preprocessed_annual_collection(
    year: int,
    hainan: "ee.FeatureCollection",
    forest_mask: "ee.Image",
) -> "ee.ImageCollection":
    start = f"{year}-01-01"
    end = f"{year + 1}-01-01"
    bounds = hainan.geometry().bounds()
    lt05 = (
        ee.ImageCollection(LANDSAT_COLLECTIONS["LT05"])
        .filterDate(start, end)
        .filterBounds(bounds)
        .map(lambda image: preprocess_landsat57(image, hainan, forest_mask))
    )
    le07 = (
        ee.ImageCollection(LANDSAT_COLLECTIONS["LE07"])
        .filterDate(start, end)
        .filterBounds(bounds)
        .map(lambda image: preprocess_landsat57(image, hainan, forest_mask))
    )
    lc08 = (
        ee.ImageCollection(LANDSAT_COLLECTIONS["LC08"])
        .filterDate(start, end)
        .filterBounds(bounds)
        .map(lambda image: preprocess_landsat89(image, hainan, forest_mask))
    )
    lc09 = (
        ee.ImageCollection(LANDSAT_COLLECTIONS["LC09"])
        .filterDate(start, end)
        .filterBounds(bounds)
        .map(lambda image: preprocess_landsat89(image, hainan, forest_mask))
    )
    return lt05.merge(le07).merge(lc08).merge(lc09)


def build_annual_composite(
    year: int,
    hainan: "ee.FeatureCollection",
    forest_mask: "ee.Image",
    scale: int,
) -> "ee.Image":
    collection = preprocessed_annual_collection(year, hainan, forest_mask)
    sensors = ee.List(collection.aggregate_array("SPACECRAFT_ID")).distinct().sort()
    return (
        collection.median()
        .select(OUTPUT_BANDS)
        .updateMask(forest_mask)
        .clip(hainan)
        .set(
            {
                "year": year,
                "sensor_group": sensors.join(";"),
                "composite_method": "annual_median",
                "scale": scale,
                "project": PROJECT_NAME,
                "source": "Landsat Collection 2 Tier 1 Level-2 surface reflectance",
                "sr_scale_factor": SR_SCALE,
                "sr_offset": SR_OFFSET,
                "masking": "QA_PIXEL fill/dilated cloud/cloud/cloud shadow/snow and QA_RADSAT==0; ForestMask_30m applied",
            }
        )
    )


def forest_area_km2(
    forest_mask: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> float:
    forest_pixels = ee.Image.constant(1).rename("forest").updateMask(forest_mask)
    result = forest_pixels.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
        tileScale=tile_scale,
    )
    pixel_count = int(result.get("forest").getInfo() or 0)
    return pixel_count * scale * scale / 1_000_000


def valid_pixel_count(
    composite: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> int:
    valid = ee.Image.constant(1).rename("valid").updateMask(composite.select("NIR").mask())
    result = valid.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
        tileScale=tile_scale,
    )
    value = result.get("valid").getInfo()
    return int(value or 0)


def band_range_summary(
    composite: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> dict[str, float | None]:
    check_scale = max(scale, 300)
    reducer = ee.Reducer.percentile([1, 99])
    result = composite.select(OUTPUT_BANDS).reduceRegion(
        reducer=reducer,
        geometry=hainan.geometry(),
        scale=check_scale,
        crs="EPSG:4326",
        maxPixels=1e13,
        tileScale=tile_scale,
    )
    values = result.getInfo() or {}
    return {key: (float(value) if value is not None else None) for key, value in values.items()}


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "year",
        "asset_id",
        "export_description",
        "export_status",
        "band_names",
        "scale",
        "crs",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_stats(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = [
        "year",
        "valid_pixel_count",
        "valid_area_km2",
        "forest_area_km2",
        "valid_percentage",
        "image_count_before_mask",
        "image_count_after_mask",
        "asset_id",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_existing_rows(path: Path, key: str) -> dict[int, dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    existing: dict[int, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if value in (None, ""):
            continue
        existing[int(value)] = row
    return existing


def task_status_by_description() -> dict[str, dict[str, Any]]:
    tasks = ee.data.getTaskList()
    status: dict[str, dict[str, Any]] = {}
    for task in tasks:
        description = task.get("description")
        state = task.get("state")
        if not description or not state:
            continue
        if description not in status or state in {"RUNNING", "READY", "COMPLETED"}:
            status[description] = task
    return status


def existing_asset_type(asset_id: str) -> str | None:
    try:
        return str(ee.data.getAsset(asset_id).get("type"))
    except Exception:
        return None


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


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    tables_dir = Path(args.tables_dir)

    hainan_asset = args.hainan_roi or get_config_value(config, "gee_assets", "hainan_roi")
    if not hainan_asset or "your_username" in str(hainan_asset):
        raise RuntimeError(
            "config/config.yaml must contain a real gee_assets.hainan_roi asset ID, "
            "or pass --hainan-roi."
        )

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
    output_asset_root = (
        args.output_asset_root
        or get_config_value(config, "gee_assets", "output_asset_root")
        or DEFAULT_OUTPUT_ASSET_ROOT
    )
    stage_root = stage_asset_root(str(output_asset_root))

    scale = int(get_config_value(config, "project", "target_scale") or 30)
    start_year = int(get_config_value(config, "project", "start_year") or 2000)
    end_year = int(get_config_value(config, "project", "end_year") or 2024)
    random_seed = int(get_config_value(config, "analysis", "random_seed") or 2026)
    crs = str(get_config_value(config, "project", "crs") or "EPSG:4326")
    years = list(range(start_year, end_year + 1))

    if scale != 30 or crs != "EPSG:4326":
        raise RuntimeError(
            f"Stage 2 is fixed at 30 m EPSG:4326, got scale={scale}, crs={crs}."
        )
    if start_year != 2000 or end_year != 2024:
        raise RuntimeError(
            f"Stage 2 is fixed to 2000-2024, got {start_year}-{end_year}."
        )

    valid_pixels_csv = tables_dir / "table_landsat_valid_pixels_by_year.csv"
    manifest_csv = tables_dir / "table_landsat_asset_manifest.csv"

    resolved = {
        "mode": "export" if args.export else "dry_run",
        "project": args.project or "MISSING",
        "hainan_roi": hainan_asset,
        "forest_mask_asset": forest_mask_asset,
        "forest_type_asset": forest_type_asset,
        "output_asset_folder": stage_root,
        "years": f"{start_year}-{end_year}",
        "scale": scale,
        "crs": crs,
        "random_seed": random_seed,
        "valid_pixels_csv": str(valid_pixels_csv),
        "manifest_csv": str(manifest_csv),
    }
    print(json.dumps(resolved, indent=2, ensure_ascii=False))

    if not args.export and args.skip_stats:
        rows = [
            {
                "year": year,
                "asset_id": composite_asset_id(stage_root, year),
                "export_description": f"{COMPOSITE_PREFIX}_{year}",
                "export_status": "dry_run_not_submitted",
                "band_names": ";".join(OUTPUT_BANDS),
                "scale": scale,
                "crs": crs,
                "notes": "Dry run only; no Earth Engine tasks submitted.",
            }
            for year in years
        ]
        write_manifest(manifest_csv, rows)
        print(f"Wrote {manifest_csv}")
        return 0

    initialize_ee(args.project)
    require_asset(str(output_asset_root).rstrip("/"), expected_type="FOLDER")
    require_asset(stage_root, expected_type="FOLDER")
    require_asset(str(forest_mask_asset), expected_type="IMAGE")
    require_asset(str(forest_type_asset), expected_type="IMAGE")

    hainan = ee.FeatureCollection(str(hainan_asset))
    forest_mask = ee.Image(str(forest_mask_asset)).eq(1).selfMask()

    hainan_count = hainan.size().getInfo()
    if int(hainan_count or 0) <= 0:
        raise RuntimeError(f"Hainan ROI has no features: {hainan_asset}")

    forest_total_km2 = 0.0 if args.skip_stats else forest_area_km2(
        forest_mask, hainan, scale, args.tile_scale
    )
    if not args.skip_stats and forest_total_km2 <= 0:
        raise RuntimeError(
            f"ForestMask_30m has zero valid forest area: {forest_mask_asset}"
        )

    stats_by_year = (
        {} if args.overwrite_stats else load_existing_rows(valid_pixels_csv, "year")
    )
    manifest_by_year = load_existing_rows(manifest_csv, "year")
    range_checks: dict[int, dict[str, float | None]] = {}
    tasks: list[tuple[int, str]] = []
    existing_tasks = task_status_by_description() if args.export else {}

    for year in years:
        raw_collection = raw_annual_collection(year, hainan)
        processed_collection = preprocessed_annual_collection(year, hainan, forest_mask)
        raw_count = int(raw_collection.size().getInfo() or 0)
        processed_count = int(processed_collection.size().getInfo() or 0)
        if raw_count <= 0 or processed_count <= 0:
            raise RuntimeError(f"No Landsat images found for {year}.")

        composite = build_annual_composite(year, hainan, forest_mask, scale)
        asset_id = composite_asset_id(stage_root, year)

        if not args.skip_stats and year not in stats_by_year:
            valid_count = valid_pixel_count(composite, hainan, scale, args.tile_scale)
            valid_area_km2 = valid_count * scale * scale / 1_000_000
            valid_percentage = (
                valid_area_km2 / forest_total_km2 * 100 if forest_total_km2 > 0 else 0
            )
            stats_by_year[year] = {
                "year": year,
                "valid_pixel_count": valid_count,
                "valid_area_km2": round(valid_area_km2, 6),
                "forest_area_km2": round(forest_total_km2, 6),
                "valid_percentage": round(valid_percentage, 6),
                "image_count_before_mask": raw_count,
                "image_count_after_mask": processed_count,
                "asset_id": asset_id,
            }
            write_stats(
                valid_pixels_csv,
                [stats_by_year[y] for y in sorted(stats_by_year)],
            )
            range_checks[year] = band_range_summary(
                composite, hainan, scale, args.tile_scale
            )

        existing_manifest = manifest_by_year.get(year, {})
        export_status = existing_manifest.get("export_status") or "not_submitted"
        task_note = existing_manifest.get("notes") or "No export requested."
        if not args.export and export_status == "dry_run_not_submitted":
            export_status = "not_submitted"
            task_note = "No export requested."
        if args.export:
            description = f"{COMPOSITE_PREFIX}_{year}"
            asset_type = existing_asset_type(asset_id)
            existing_task = existing_tasks.get(description)
            existing_state = existing_task.get("state") if existing_task else None
            if asset_type == "IMAGE":
                export_status = "existing_asset"
                task_note = "Asset already exists; export was not resubmitted."
            elif existing_state in {"READY", "RUNNING", "COMPLETED"}:
                export_status = f"existing_task_{str(existing_state).lower()}"
                task_note = f"Existing task ID: {existing_task.get('id')}"
            else:
                task = export_image_to_asset(
                    composite, asset_id, description, hainan, scale
                )
                tasks.append((year, task.id))
                export_status = "submitted"
                task_note = f"Submitted task ID: {task.id}"

        manifest_by_year[year] = {
            "year": year,
            "asset_id": asset_id,
            "export_description": f"{COMPOSITE_PREFIX}_{year}",
            "export_status": export_status,
            "band_names": ";".join(OUTPUT_BANDS),
            "scale": scale,
            "crs": crs,
            "notes": task_note,
        }
        write_manifest(
            manifest_csv,
            [manifest_by_year[y] for y in sorted(manifest_by_year)],
        )
        print(
            f"Processed {year}: raw_images={raw_count}, "
            f"processed_images={processed_count}, export_status={export_status}",
            flush=True,
        )

    if not args.skip_stats:
        print(f"Wrote {valid_pixels_csv}")
    print(f"Wrote {manifest_csv}")

    if range_checks:
        print("Reflectance percentile checks at 300 m check scale (p1/p99 by band):")
        print(json.dumps(range_checks, indent=2, ensure_ascii=False))
    if tasks:
        print("Submitted Earth Engine tasks:")
        print(json.dumps([{"year": year, "task_id": task_id} for year, task_id in tasks], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
