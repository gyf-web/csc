"""Stage 1: prepare Hainan natural/planted forest type assets.

This script uses the Earth Engine Python API to:

1. Load the configured Hainan ROI.
2. Read the Global Natural and Planted Forests 2021 community dataset.
3. Recode it to this project's canonical classes:
   0 = non-forest or uncertain, 1 = natural forest, 2 = plantation forest.
4. Remove obvious 2021-2024 changes using Hansen loss and Dynamic World
   water/built/bare labels.
5. Export the cleaned forest type image and forest mask to Earth Engine Assets.
6. Write local CSV tables for area statistics and the asset manifest.

Exports are opt-in. A plain run performs a dry run and starts no Earth Engine
tasks. Use --export after confirming the resolved parameters.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:
    import ee
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "The earthengine-api package is required. Activate the project "
        "environment or install earthengine-api before running Stage 1."
    ) from exc

try:
    import geemap  # type: ignore
except ImportError:  # pragma: no cover - optional fallback
    geemap = None


PROJECT_NAME = "hainan_forest_greening_quality"
DEFAULT_FOREST_SOURCE = (
    "projects/sat-io/open-datasets/GLOBAL-NATURAL-PLANTED-FORESTS"
)
DEFAULT_HANSEN_ASSET = "UMD/hansen/global_forest_change_2025_v1_13"
DEFAULT_DYNAMIC_WORLD_ASSET = "GOOGLE/DYNAMICWORLD/V1"
DEFAULT_OUTPUT_ASSET_ROOT = "users/gyf/forest_csc_alphaearth"
STAGE_FOLDER = "stage01_forest_type"
FOREST_TYPE_NAME = "ForestType_30m_clean"
FOREST_MASK_NAME = "ForestMask_30m"
CLASS_ROWS = [
    (0, "non_forest_or_uncertain"),
    (1, "natural_forest"),
    (2, "plantation_forest"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Stage 1 Hainan forest type assets."
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
        "--skip-area-stats",
        action="store_true",
        help="Skip area reducers and do not write the area CSV.",
    )
    parser.add_argument("--forest-source", default=DEFAULT_FOREST_SOURCE)
    parser.add_argument(
        "--hainan-roi",
        default=None,
        help="Optional Hainan ROI asset override. The config is still read first.",
    )
    parser.add_argument("--hansen-asset", default=DEFAULT_HANSEN_ASSET)
    parser.add_argument("--dynamic-world-asset", default=DEFAULT_DYNAMIC_WORLD_ASSET)
    parser.add_argument("--output-asset-root", default=DEFAULT_OUTPUT_ASSET_ROOT)
    parser.add_argument("--tables-dir", default="outputs/tables")
    parser.add_argument("--tile-scale", type=int, default=4)
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
            "Earth Engine Cloud Project ID is required for online Stage 1 work. "
            "Pass --project PROJECT_ID or set EE_PROJECT."
        )
    if geemap is not None:
        geemap.ee_initialize(project=project)
    else:
        ee.Initialize(project=project)
    ee.data.setDefaultWorkloadTag("hainan-stage01-forest-type")


def require_asset_folder(asset_id: str) -> None:
    try:
        asset = ee.data.getAsset(asset_id)
    except Exception as exc:  # pragma: no cover - online EE guard
        raise RuntimeError(
            f"Required Earth Engine Asset folder does not exist or is not "
            f"accessible: {asset_id}. Create it before running --export."
        ) from exc
    if asset.get("type") != "FOLDER":
        raise RuntimeError(f"Expected a FOLDER asset, got {asset.get('type')}: {asset_id}")


def stage_asset_ids(output_asset_root: str) -> tuple[str, str, str]:
    stage_root = f"{output_asset_root.rstrip('/')}/{STAGE_FOLDER}"
    forest_type_asset_id = f"{stage_root}/{FOREST_TYPE_NAME}"
    forest_mask_asset_id = f"{stage_root}/{FOREST_MASK_NAME}"
    return stage_root, forest_type_asset_id, forest_mask_asset_id


def build_forest_type_images(
    hainan: "ee.FeatureCollection",
    forest_source: str,
    hansen_asset: str,
    dynamic_world_asset: str,
    scale: int,
) -> dict[str, "ee.Image"]:
    roi = hainan.geometry()

    raw = ee.ImageCollection(forest_source).mosaic().select(["b1", "b2", "b3"])
    red = raw.select("b1")
    green = raw.select("b2")
    blue = raw.select("b3")

    # The source is an RGB-coded 2021 map: green = natural forest,
    # yellow = planted forest, gray = non-forest/background.
    natural = red.eq(0).And(green.eq(127)).And(blue.eq(0))
    plantation = red.eq(127).And(green.eq(127)).And(blue.eq(0))

    forest_type_initial = (
        ee.Image(0)
        .where(natural, 1)
        .where(plantation, 2)
        .rename("forest_type")
        .toByte()
        .clip(roi)
        .unmask(0)
    )

    hansen = ee.Image(hansen_asset).select("lossyear")
    recent_loss = hansen.gte(21).And(hansen.lte(24))

    dynamic_world = (
        ee.ImageCollection(dynamic_world_asset)
        .filterDate("2021-01-01", "2024-12-31")
        .filterBounds(roi)
        .select("label")
        .mode()
        .rename("dw_label_mode")
        .clip(roi)
    )
    latest_water_built_bare = (
        dynamic_world.eq(0).Or(dynamic_world.eq(6)).Or(dynamic_world.eq(7))
    )

    remove_recent_change = recent_loss.Or(latest_water_built_bare).rename(
        "remove_recent_change"
    )
    forest_type_clean = (
        forest_type_initial.where(remove_recent_change, 0)
        .rename("forest_type")
        .toByte()
        .clip(roi)
        .unmask(0)
        .set(
            {
                "project": PROJECT_NAME,
                "stage": "stage01_forest_type",
                "source_dataset": forest_source,
                "source_year": 2021,
                "class_values": "0=non_forest_or_uncertain;1=natural_forest;2=plantation_forest",
                "recent_change_mask": "Hansen loss year 2021-2024 OR Dynamic World 2021-2024 modal water/built/bare",
                "scale": scale,
            }
        )
    )

    forest_mask = (
        forest_type_clean.gt(0)
        .rename("forest_mask")
        .toByte()
        .clip(roi)
        .unmask(0)
        .set(
            {
                "project": PROJECT_NAME,
                "stage": "stage01_forest_type",
                "source": FOREST_TYPE_NAME,
                "class_values": "0=other;1=forest",
                "scale": scale,
            }
        )
    )

    return {
        "forest_type_initial": forest_type_initial,
        "forest_type_clean": forest_type_clean,
        "forest_mask": forest_mask,
        "recent_loss": recent_loss,
        "latest_water_built_bare": latest_water_built_bare,
        "remove_recent_change": remove_recent_change,
    }


def reduce_area_by_class(
    forest_type_clean: "ee.Image",
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> pd.DataFrame:
    area_image = (
        ee.Image.pixelArea()
        .divide(1_000_000)
        .rename("area_km2")
        .addBands(forest_type_clean.rename("class_id"))
    )
    grouped = area_image.reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName="class_id"),
        geometry=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
        tileScale=tile_scale,
    )
    groups = grouped.get("groups").getInfo() or []
    area_lookup = {int(row["class_id"]): float(row["sum"]) for row in groups}
    forest_total = area_lookup.get(1, 0.0) + area_lookup.get(2, 0.0)

    rows: list[dict[str, Any]] = []
    for class_id, class_name in CLASS_ROWS:
        area_km2 = area_lookup.get(class_id, 0.0)
        percentage = (
            (area_km2 / forest_total * 100.0)
            if class_id in (1, 2) and forest_total > 0
            else None
        )
        rows.append(
            {
                "class_id": class_id,
                "class_name": class_name,
                "area_km2": round(area_km2, 6),
                "percentage_of_forest": (
                    round(percentage, 6) if percentage is not None else ""
                ),
            }
        )
    return pd.DataFrame(rows)


def frequency_histogram(
    image: "ee.Image",
    band_name: str,
    hainan: "ee.FeatureCollection",
    scale: int,
    tile_scale: int,
) -> dict[str, Any]:
    result = image.select(band_name).reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
        tileScale=tile_scale,
    )
    histogram = result.get(band_name).getInfo()
    return histogram or {}


def export_image_to_asset(
    image: "ee.Image",
    asset_id: str,
    description: str,
    hainan: "ee.FeatureCollection",
    scale: int,
) -> Any:
    task = ee.batch.Export.image.toAsset(
        image=image.toByte(),
        description=description,
        assetId=asset_id,
        region=hainan.geometry(),
        scale=scale,
        crs="EPSG:4326",
        maxPixels=1e13,
    )
    task.start()
    return task


def write_manifest(
    path: Path,
    forest_type_asset_id: str,
    forest_mask_asset_id: str,
    forest_type_status: str,
    forest_mask_status: str,
    notes: str,
) -> None:
    rows = [
        {
            "asset_name": FOREST_TYPE_NAME,
            "asset_id": forest_type_asset_id,
            "description": "Canonical natural/planted forest type map; 0 non-forest/uncertain, 1 natural, 2 plantation.",
            "scale": 30,
            "crs": "EPSG:4326",
            "export_status": forest_type_status,
            "notes": notes,
        },
        {
            "asset_name": FOREST_MASK_NAME,
            "asset_id": forest_mask_asset_id,
            "description": "Forest analysis mask derived from cleaned forest type; 1 forest, 0 other.",
            "scale": 30,
            "crs": "EPSG:4326",
            "export_status": forest_mask_status,
            "notes": notes,
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "asset_name",
                "asset_id",
                "description",
                "scale",
                "crs",
                "export_status",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    tables_dir = Path(args.tables_dir)
    config = load_config(config_path)

    hainan_asset = args.hainan_roi or get_config_value(config, "gee_assets", "hainan_roi")
    if not hainan_asset or "your_username" in str(hainan_asset):
        raise RuntimeError(
            "config/config.yaml must contain a real gee_assets.hainan_roi asset ID."
        )

    scale = int(get_config_value(config, "project", "target_scale") or 30)
    crs = str(get_config_value(config, "project", "crs") or "EPSG:4326")
    if scale != 30 or crs != "EPSG:4326":
        raise RuntimeError(
            f"Stage 1 is fixed at 30 m EPSG:4326, got scale={scale}, crs={crs}."
        )

    stage_root, forest_type_asset_id, forest_mask_asset_id = stage_asset_ids(
        args.output_asset_root
    )
    area_csv = tables_dir / "table_forest_type_area.csv"
    manifest_csv = tables_dir / "table_forest_type_asset_manifest.csv"

    resolved = {
        "mode": "export" if args.export else "dry_run",
        "project": args.project or "MISSING",
        "hainan_roi": hainan_asset,
        "forest_source": args.forest_source,
        "hansen_asset": args.hansen_asset,
        "dynamic_world_asset": args.dynamic_world_asset,
        "stage_asset_folder": stage_root,
        "forest_type_asset_id": forest_type_asset_id,
        "forest_mask_asset_id": forest_mask_asset_id,
        "scale": scale,
        "crs": crs,
        "area_csv": str(area_csv),
        "manifest_csv": str(manifest_csv),
    }

    print(json.dumps(resolved, indent=2, ensure_ascii=False))
    if not args.export and args.skip_area_stats:
        write_manifest(
            manifest_csv,
            forest_type_asset_id,
            forest_mask_asset_id,
            "dry_run_not_submitted",
            "dry_run_not_submitted",
            "Dry run only; rerun with --project PROJECT_ID --export to submit tasks.",
        )
        return 0

    initialize_ee(args.project)
    if args.export:
        require_asset_folder(args.output_asset_root.rstrip("/"))
        require_asset_folder(stage_root)

    hainan = ee.FeatureCollection(hainan_asset)
    images = build_forest_type_images(
        hainan=hainan,
        forest_source=args.forest_source,
        hansen_asset=args.hansen_asset,
        dynamic_world_asset=args.dynamic_world_asset,
        scale=scale,
    )

    validation = {
        "hainan_feature_count": hainan.size().getInfo(),
        "forest_type_unique_codes": frequency_histogram(
            images["forest_type_clean"], "forest_type", hainan, scale, args.tile_scale
        ),
        "forest_mask_unique_codes": frequency_histogram(
            images["forest_mask"], "forest_mask", hainan, scale, args.tile_scale
        ),
    }
    print(json.dumps(validation, indent=2, ensure_ascii=False))

    if not args.skip_area_stats:
        area_df = reduce_area_by_class(
            images["forest_type_clean"], hainan, scale, args.tile_scale
        )
        area_csv.parent.mkdir(parents=True, exist_ok=True)
        area_df.to_csv(area_csv, index=False, encoding="utf-8")
        print(f"Wrote {area_csv}")

    if args.export:
        forest_type_task = export_image_to_asset(
            images["forest_type_clean"],
            forest_type_asset_id,
            FOREST_TYPE_NAME,
            hainan,
            scale,
        )
        forest_mask_task = export_image_to_asset(
            images["forest_mask"], forest_mask_asset_id, FOREST_MASK_NAME, hainan, scale
        )
        notes = (
            f"Submitted task IDs: {forest_type_task.id}, {forest_mask_task.id}. "
            "Check Earth Engine Tasks for final completion."
        )
        write_manifest(
            manifest_csv,
            forest_type_asset_id,
            forest_mask_asset_id,
            "submitted",
            "submitted",
            notes,
        )
    else:
        write_manifest(
            manifest_csv,
            forest_type_asset_id,
            forest_mask_asset_id,
            "not_submitted",
            "not_submitted",
            "Online validation/statistics ran, but --export was not passed.",
        )
    print(f"Wrote {manifest_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
