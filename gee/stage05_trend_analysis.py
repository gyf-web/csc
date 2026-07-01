"""Stage 5: 30 m FVC and EQI_func non-parametric trend analysis.

The workflow reads annual Earth Engine Assets, calculates per-pixel Sen's
slope and Mann-Kendall significance, exports four 30 m trend images to Earth
Engine Assets, and writes only CSV summaries and PNG previews locally.

No full-resolution GeoTIFF is downloaded or generated.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests
from PIL import Image

try:
    import ee
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "earthengine-api is required. Activate the project csc environment."
    ) from exc

try:
    import geemap
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "geemap is required by the GEEMu environment gate."
    ) from exc

from src.io_utils import load_yaml_config, write_csv_rows
from src.trend_utils import (
    add_trend_properties,
    build_annual_time_series,
    calculate_mann_kendall_pvalue,
    calculate_sen_slope,
)


FOREST_TYPES = [
    ("all_forest", None),
    ("natural_forest", 1),
    ("plantation_forest", 2),
]
TREND_OUTPUTS = [
    ("FVC_SenSlope_30m", "FVC", "SenSlope", "FVC_SenSlope"),
    ("FVC_pvalue_30m", "FVC", "pvalue", "FVC_pvalue"),
    ("EQI_SenSlope_30m", "EQI_func", "SenSlope", "EQI_SenSlope"),
    ("EQI_pvalue_30m", "EQI_func", "pvalue", "EQI_pvalue"),
]
MANIFEST_FIELDS = [
    "asset_name",
    "asset_id",
    "variable",
    "metric",
    "export_description",
    "export_status",
    "scale",
    "crs",
    "notes",
]
STATS_FIELDS = [
    "forest_type",
    "FVC_slope_mean",
    "FVC_slope_median",
    "EQI_slope_mean",
    "EQI_slope_median",
    "FVC_positive_area_km2",
    "FVC_negative_area_km2",
    "EQI_positive_area_km2",
    "EQI_negative_area_km2",
    "FVC_significant_positive_area_km2",
    "FVC_significant_negative_area_km2",
    "EQI_significant_positive_area_km2",
    "EQI_significant_negative_area_km2",
]
CHECK_FIELDS = ["check_item", "result", "value", "notes"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Stage 5 FVC and EQI_func trend analysis."
    )
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument(
        "--project",
        default=os.environ.get("EE_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("EE_PROJECT_ID"),
        help="Earth Engine Cloud Project ID; required for --export.",
    )
    parser.add_argument("--hainan-roi", default=None)
    parser.add_argument("--forest-mask-asset", default=None)
    parser.add_argument("--forest-type-asset", default=None)
    parser.add_argument("--indices-asset-root", default=None)
    parser.add_argument("--eqi-asset-root", default=None)
    parser.add_argument("--trend-asset-root", default=None)
    parser.add_argument("--tables-dir", default=None)
    parser.add_argument("--figures-dir", default=None)
    parser.add_argument("--tile-scale", type=int, default=8)
    parser.add_argument(
        "--export",
        action="store_true",
        help="Execute online reducers and start Asset exports. Default is dry run.",
    )
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip PNG map preview generation.",
    )
    return parser.parse_args()


def require_text(value: Any, label: str) -> str:
    if value is None or not str(value).strip():
        raise ValueError(
            f"Missing {label}. Add it to config/config.yaml or pass its CLI override."
        )
    return str(value).strip().rstrip("/")


def resolve_parameters(args: argparse.Namespace) -> dict[str, Any]:
    config_path = Path(args.config)
    config = load_yaml_config(config_path)
    project = config.get("project", {})
    paths = config.get("paths", {})
    gee_assets = config.get("gee_assets", {})
    analysis = config.get("analysis", {})

    params = {
        "config_path": str(config_path),
        "project_id": args.project,
        "project_name": require_text(project.get("name"), "project.name"),
        "crs": require_text(project.get("crs"), "project.crs"),
        "scale": int(project.get("target_scale")),
        "start_year": int(project.get("start_year")),
        "end_year": int(project.get("end_year")),
        "pvalue_threshold": float(analysis.get("trend_pvalue_threshold", 0.05)),
        "hainan_roi": args.hainan_roi or gee_assets.get("hainan_roi"),
        "forest_mask_asset": args.forest_mask_asset
        or gee_assets.get("forest_mask_asset"),
        "forest_type_asset": args.forest_type_asset
        or gee_assets.get("forest_type_asset"),
        "indices_asset_root": args.indices_asset_root
        or gee_assets.get("indices_asset_root"),
        "eqi_asset_root": args.eqi_asset_root
        or gee_assets.get("eqi_asset_root"),
        "trend_asset_root": args.trend_asset_root
        or gee_assets.get("trend_asset_root"),
        "tables_dir": args.tables_dir or paths.get("tables"),
        "figures_dir": args.figures_dir or paths.get("figures"),
        "tile_scale": int(args.tile_scale),
    }
    for key in (
        "hainan_roi",
        "forest_mask_asset",
        "forest_type_asset",
        "indices_asset_root",
        "eqi_asset_root",
        "trend_asset_root",
        "tables_dir",
        "figures_dir",
    ):
        params[key] = require_text(params[key], key)

    if params["start_year"] > params["end_year"]:
        raise ValueError("project.start_year must not exceed project.end_year")
    if params["scale"] != 30:
        raise ValueError("Stage 5 main analysis must use target_scale = 30")
    if not 0 < params["pvalue_threshold"] < 1:
        raise ValueError("analysis.trend_pvalue_threshold must be between 0 and 1")
    return params


def initialize_ee(project_id: str | None) -> None:
    if not project_id:
        raise RuntimeError(
            "Earth Engine Cloud Project ID is required. Pass --project or set EE_PROJECT."
        )
    geemap.ee_initialize(project=project_id)
    ee.data.setDefaultWorkloadTag("hainan-stage05-trend")


def require_asset(asset_id: str, expected_type: str) -> dict[str, Any]:
    try:
        asset = ee.data.getAsset(asset_id)
    except Exception as exc:
        raise RuntimeError(
            f"Required Earth Engine Asset is missing or inaccessible: {asset_id}"
        ) from exc
    if asset.get("type") != expected_type:
        raise RuntimeError(
            f"Unexpected type for {asset_id}: expected {expected_type}, "
            f"got {asset.get('type')}"
        )
    return asset


def require_image_band(asset_id: str, band_name: str) -> None:
    require_asset(asset_id, "IMAGE")
    bands = ee.Image(asset_id).bandNames().getInfo()
    if band_name not in bands:
        raise RuntimeError(
            f"Required band {band_name!r} is missing from {asset_id}: {bands}"
        )


def active_task_by_description() -> dict[str, dict[str, Any]]:
    priority = {"RUNNING": 4, "READY": 3, "COMPLETED": 2}
    found: dict[str, dict[str, Any]] = {}
    for task in ee.data.getTaskList():
        description = task.get("description")
        state = task.get("state")
        if not description or state not in priority:
            continue
        old = found.get(description)
        if old is None or priority[state] > priority.get(str(old.get("state")), -1):
            found[description] = task
    return found


def existing_asset_type(asset_id: str) -> str | None:
    try:
        return str(ee.data.getAsset(asset_id).get("type"))
    except Exception:
        return None


def build_products(
    params: dict[str, Any],
    forest_mask: "ee.Image",
    region: "ee.Geometry",
) -> tuple[dict[str, "ee.Image"], dict[str, "ee.Image"]]:
    years = range(params["start_year"], params["end_year"] + 1)
    fvc_ts = build_annual_time_series(
        params["indices_asset_root"], "FVC", "FVC", years, forest_mask
    )
    eqi_ts = build_annual_time_series(
        params["eqi_asset_root"], "EQI_func", "EQI_func", years, forest_mask
    )

    fvc_slope = calculate_sen_slope(
        fvc_ts, "FVC_SenSlope", forest_mask, region
    )
    eqi_slope = calculate_sen_slope(
        eqi_ts, "EQI_SenSlope", forest_mask, region
    )
    fvc_tau, fvc_pvalue = calculate_mann_kendall_pvalue(
        fvc_ts, "FVC_pvalue", forest_mask, region
    )
    eqi_tau, eqi_pvalue = calculate_mann_kendall_pvalue(
        eqi_ts, "EQI_pvalue", forest_mask, region
    )

    common = {
        "start_year": params["start_year"],
        "end_year": params["end_year"],
        "scale": params["scale"],
        "project_name": params["project_name"],
    }
    products = {
        "FVC_SenSlope_30m": add_trend_properties(
            fvc_slope, variable="FVC", method="Sen slope", **common
        ),
        "FVC_pvalue_30m": add_trend_properties(
            fvc_pvalue,
            variable="FVC",
            method="Mann-Kendall (Kendall tau normal-approximation p-value)",
            **common,
        ),
        "EQI_SenSlope_30m": add_trend_properties(
            eqi_slope, variable="EQI_func", method="Sen slope", **common
        ),
        "EQI_pvalue_30m": add_trend_properties(
            eqi_pvalue,
            variable="EQI_func",
            method="Mann-Kendall (Kendall tau normal-approximation p-value)",
            **common,
        ),
    }
    diagnostics = {"FVC_tau": fvc_tau, "EQI_tau": eqi_tau}
    return products, diagnostics


def submit_or_reuse_exports(
    products: dict[str, "ee.Image"],
    params: dict[str, Any],
    region: "ee.Geometry",
) -> list[dict[str, Any]]:
    tasks = active_task_by_description()
    rows: list[dict[str, Any]] = []
    definitions = {name: (variable, metric, band) for name, variable, metric, band in TREND_OUTPUTS}

    for asset_name, image in products.items():
        variable, metric, _ = definitions[asset_name]
        asset_id = f"{params['trend_asset_root']}/{asset_name}"
        description = asset_name
        asset_type = existing_asset_type(asset_id)
        existing_task = tasks.get(description)

        if asset_type == "IMAGE":
            status = "completed"
            notes = "Target IMAGE exists; no task submitted."
        elif existing_task is not None:
            state = str(existing_task.get("state", "")).lower()
            status = f"existing_task_{state}"
            notes = f"Existing task ID: {existing_task.get('id')}"
        else:
            task = ee.batch.Export.image.toAsset(
                image=image.toFloat(),
                description=description,
                assetId=asset_id,
                region=region,
                scale=params["scale"],
                crs=params["crs"],
                maxPixels=1e13,
            )
            task.start()
            status = "submitted"
            notes = f"Submitted task ID: {task.id}"

        rows.append(
            {
                "asset_name": asset_name,
                "asset_id": asset_id,
                "variable": variable,
                "metric": metric,
                "export_description": description,
                "export_status": status,
                "scale": params["scale"],
                "crs": params["crs"],
                "notes": notes,
            }
        )
    return rows


def masked_for_forest_type(
    image: "ee.Image",
    forest_type: "ee.Image",
    class_id: int | None,
) -> "ee.Image":
    if class_id is None:
        return image
    return image.updateMask(forest_type.eq(class_id))


def safe_number(value: Any) -> float:
    if value is None:
        return float("nan")
    return float(value)


def calculate_statistics(
    products: dict[str, "ee.Image"],
    forest_type: "ee.Image",
    region: "ee.Geometry",
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    fvc_slope = products["FVC_SenSlope_30m"]
    eqi_slope = products["EQI_SenSlope_30m"]
    fvc_pvalue = products["FVC_pvalue_30m"]
    eqi_pvalue = products["EQI_pvalue_30m"]
    threshold = params["pvalue_threshold"]
    pixel_area = ee.Image.pixelArea().divide(1e6)

    rows: list[dict[str, Any]] = []
    for label, class_id in FOREST_TYPES:
        slope_image = masked_for_forest_type(
            fvc_slope.addBands(eqi_slope), forest_type, class_id
        )
        slope_stats = (
            slope_image.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.median(), sharedInputs=True
                ),
                geometry=region,
                scale=params["scale"],
                maxPixels=1e13,
                tileScale=params["tile_scale"],
            )
            .getInfo()
        )

        areas = ee.Image.cat(
            [
                pixel_area.updateMask(fvc_slope.gt(0)).rename(
                    "FVC_positive_area_km2"
                ),
                pixel_area.updateMask(fvc_slope.lt(0)).rename(
                    "FVC_negative_area_km2"
                ),
                pixel_area.updateMask(eqi_slope.gt(0)).rename(
                    "EQI_positive_area_km2"
                ),
                pixel_area.updateMask(eqi_slope.lt(0)).rename(
                    "EQI_negative_area_km2"
                ),
                pixel_area.updateMask(
                    fvc_slope.gt(0).And(fvc_pvalue.lt(threshold))
                ).rename("FVC_significant_positive_area_km2"),
                pixel_area.updateMask(
                    fvc_slope.lt(0).And(fvc_pvalue.lt(threshold))
                ).rename("FVC_significant_negative_area_km2"),
                pixel_area.updateMask(
                    eqi_slope.gt(0).And(eqi_pvalue.lt(threshold))
                ).rename("EQI_significant_positive_area_km2"),
                pixel_area.updateMask(
                    eqi_slope.lt(0).And(eqi_pvalue.lt(threshold))
                ).rename("EQI_significant_negative_area_km2"),
            ]
        )
        areas = masked_for_forest_type(areas, forest_type, class_id)
        area_stats = (
            areas.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=params["scale"],
                maxPixels=1e13,
                tileScale=params["tile_scale"],
            )
            .getInfo()
        )

        row = {
            "forest_type": label,
            "FVC_slope_mean": safe_number(slope_stats.get("FVC_SenSlope_mean")),
            "FVC_slope_median": safe_number(
                slope_stats.get("FVC_SenSlope_median")
            ),
            "EQI_slope_mean": safe_number(slope_stats.get("EQI_SenSlope_mean")),
            "EQI_slope_median": safe_number(
                slope_stats.get("EQI_SenSlope_median")
            ),
        }
        for field in STATS_FIELDS[5:]:
            row[field] = safe_number(area_stats.get(field))
        rows.append(row)
    return rows


def calculate_checks(
    products: dict[str, "ee.Image"],
    raw_forest_mask: "ee.Image",
    region: "ee.Geometry",
    params: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    combined = ee.Image.cat(list(products.values()))
    ranges = (
        combined.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=region,
            scale=params["scale"],
            maxPixels=1e13,
            tileScale=params["tile_scale"],
        )
        .getInfo()
    )

    pixel_area = ee.Image.pixelArea().divide(1e6)
    valid_areas = (
        ee.Image.cat(
            [
                pixel_area.updateMask(
                    products["FVC_SenSlope_30m"].mask()
                ).rename("FVC_valid_area_km2"),
                pixel_area.updateMask(
                    products["EQI_SenSlope_30m"].mask()
                ).rename("EQI_valid_area_km2"),
            ]
        )
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=params["scale"],
            maxPixels=1e13,
            tileScale=params["tile_scale"],
        )
        .getInfo()
    )

    off_forest = (
        ee.Image.cat(
            [
                products["FVC_SenSlope_30m"]
                .mask()
                .updateMask(raw_forest_mask.neq(1))
                .rename("FVC_off_forest"),
                products["EQI_SenSlope_30m"]
                .mask()
                .updateMask(raw_forest_mask.neq(1))
                .rename("EQI_off_forest"),
            ]
        )
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region,
            scale=params["scale"],
            maxPixels=1e13,
            tileScale=params["tile_scale"],
        )
        .getInfo()
    )
    fvc_off = safe_number(off_forest.get("FVC_off_forest", 0))
    eqi_off = safe_number(off_forest.get("EQI_off_forest", 0))

    numeric = {key: safe_number(value) for key, value in ranges.items()}
    numeric.update({key: safe_number(value) for key, value in valid_areas.items()})
    numeric["FVC_off_forest_pixel_sum"] = fvc_off
    numeric["EQI_off_forest_pixel_sum"] = eqi_off

    fvc_min = numeric["FVC_SenSlope_min"]
    fvc_max = numeric["FVC_SenSlope_max"]
    eqi_min = numeric["EQI_SenSlope_min"]
    eqi_max = numeric["EQI_SenSlope_max"]
    fvc_pmin = numeric["FVC_pvalue_min"]
    fvc_pmax = numeric["FVC_pvalue_max"]
    eqi_pmin = numeric["EQI_pvalue_min"]
    eqi_pmax = numeric["EQI_pvalue_max"]

    rows = [
        {
            "check_item": "FVC_SenSlope 是否存在正负值",
            "result": "pass" if fvc_min < 0 < fvc_max else "fail",
            "value": f"min={fvc_min:.10g}; max={fvc_max:.10g}",
            "notes": "Sen slope units: FVC/year.",
        },
        {
            "check_item": "EQI_SenSlope 是否存在正负值",
            "result": "pass" if eqi_min < 0 < eqi_max else "fail",
            "value": f"min={eqi_min:.10g}; max={eqi_max:.10g}",
            "notes": "Sen slope units: EQI/year.",
        },
        {
            "check_item": "FVC_pvalue 是否在 0—1",
            "result": "pass" if 0 <= fvc_pmin <= fvc_pmax <= 1 else "fail",
            "value": f"min={fvc_pmin:.10g}; max={fvc_pmax:.10g}",
            "notes": "Two-sided normal-approximation p value from Kendall tau.",
        },
        {
            "check_item": "EQI_pvalue 是否在 0—1",
            "result": "pass" if 0 <= eqi_pmin <= eqi_pmax <= 1 else "fail",
            "value": f"min={eqi_pmin:.10g}; max={eqi_pmax:.10g}",
            "notes": "Two-sided normal-approximation p value from Kendall tau.",
        },
        {
            "check_item": "FVC 有效森林像元面积",
            "result": "pass"
            if numeric["FVC_valid_area_km2"] > 0
            else "fail",
            "value": f"{numeric['FVC_valid_area_km2']:.6f}",
            "notes": "km2 from ee.Image.pixelArea(), not pixel-count approximation.",
        },
        {
            "check_item": "EQI 有效森林像元面积",
            "result": "pass"
            if numeric["EQI_valid_area_km2"] > 0
            else "fail",
            "value": f"{numeric['EQI_valid_area_km2']:.6f}",
            "notes": "km2 from ee.Image.pixelArea(), not pixel-count approximation.",
        },
        {
            "check_item": "趋势结果是否只覆盖森林区",
            "result": "pass" if fvc_off == 0 and eqi_off == 0 else "fail",
            "value": f"FVC_off={fvc_off:.0f}; EQI_off={eqi_off:.0f}",
            "notes": "Sum of valid trend-mask pixels outside ForestMask_30m.",
        },
    ]
    return rows, numeric


def robust_visual_range(
    image: "ee.Image",
    band: str,
    region: "ee.Geometry",
    params: dict[str, Any],
) -> tuple[float, float]:
    values = (
        image.reduceRegion(
            reducer=ee.Reducer.percentile([2, 98]),
            geometry=region,
            scale=max(300, params["scale"]),
            bestEffort=True,
            maxPixels=1e9,
            tileScale=params["tile_scale"],
        )
        .getInfo()
    )
    low = safe_number(values.get(f"{band}_p2"))
    high = safe_number(values.get(f"{band}_p98"))
    limit = max(abs(low), abs(high))
    if not limit > 0:
        raise RuntimeError(f"Cannot derive a nonzero map range for {band}")
    return -limit, limit


def make_map_figure(
    image: "ee.Image",
    band: str,
    region: "ee.Geometry",
    output_path: Path,
    title: str,
    units: str,
    params: dict[str, Any],
) -> None:
    vmin, vmax = robust_visual_range(image, band, region, params)
    palette = ["#7f0000", "#d73027", "#f7f7f7", "#4575b4", "#053061"]
    url = image.select(band).getThumbURL(
        {
            "region": region,
            "dimensions": 1200,
            "format": "png",
            "min": vmin,
            "max": vmax,
            "palette": palette,
        }
    )
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    thumbnail = Image.open(io.BytesIO(response.content)).convert("RGBA")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 8.0), dpi=180)
    ax.imshow(thumbnail)
    ax.set_axis_off()
    ax.set_title(title, fontsize=13, pad=12)
    scalar = plt.cm.ScalarMappable(
        norm=plt.Normalize(vmin=vmin, vmax=vmax),
        cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
            "trend_diverging", palette
        ),
    )
    colorbar = fig.colorbar(
        scalar, ax=ax, orientation="horizontal", fraction=0.045, pad=0.035
    )
    colorbar.set_label(units)
    fig.text(
        0.5,
        0.015,
        "2000–2024 Sen’s slope; preview rendered from Earth Engine (final raster: 30 m Asset)",
        ha="center",
        fontsize=8,
        color="#444444",
    )
    fig.savefig(output_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def validate_local_outputs(
    stats_path: Path,
    manifest_path: Path,
    checks_path: Path,
    figure_paths: list[Path],
) -> dict[str, Any]:
    stats = pd.read_csv(stats_path)
    manifest = pd.read_csv(manifest_path)
    checks = pd.read_csv(checks_path)
    expected_groups = {item[0] for item in FOREST_TYPES}
    result = {
        "stats_rows": int(len(stats)),
        "stats_groups": sorted(stats["forest_type"].tolist()),
        "manifest_rows": int(len(manifest)),
        "manifest_assets": sorted(manifest["asset_name"].tolist()),
        "check_rows": int(len(checks)),
        "failed_checks": checks.loc[
            checks["result"].str.lower() != "pass", "check_item"
        ].tolist(),
        "figures": {
            str(path): path.exists() and path.stat().st_size > 0
            for path in figure_paths
        },
        "local_geotiffs": [
            str(path)
            for path in (ROOT / "outputs").rglob("*")
            if path.suffix.lower() in {".tif", ".tiff"}
        ],
    }
    if set(stats["forest_type"]) != expected_groups or len(stats) != 3:
        raise RuntimeError(f"Incomplete trend statistics: {result}")
    if len(manifest) != 4 or set(manifest["asset_name"]) != {
        item[0] for item in TREND_OUTPUTS
    }:
        raise RuntimeError(f"Incomplete Stage 5 manifest: {result}")
    if result["failed_checks"]:
        raise RuntimeError(f"Stage 5 checks failed: {result}")
    if not all(result["figures"].values()):
        raise RuntimeError(f"Missing Stage 5 figure: {result}")
    if result["local_geotiffs"]:
        raise RuntimeError(f"Local GeoTIFFs are prohibited: {result}")
    return result


def main() -> None:
    args = parse_args()
    params = resolve_parameters(args)
    print("Resolved Stage 5 plan:")
    print(json.dumps(params, indent=2, ensure_ascii=False))
    print(
        "Method: Sen's slope + Mann-Kendall significance via Kendall tau "
        "and a two-sided asymptotic normal p-value."
    )
    print("Output: four 30 m Earth Engine Assets; local CSV/PNG only.")

    if not args.export:
        print("Dry run only. Re-run with --export to execute online work.")
        return

    initialize_ee(params["project_id"])
    require_asset(params["hainan_roi"], "TABLE")
    require_asset(params["forest_mask_asset"], "IMAGE")
    require_asset(params["forest_type_asset"], "IMAGE")
    require_asset(params["indices_asset_root"], "FOLDER")
    require_asset(params["eqi_asset_root"], "FOLDER")
    require_asset(params["trend_asset_root"], "FOLDER")

    years = range(params["start_year"], params["end_year"] + 1)
    for year in years:
        require_image_band(
            f"{params['indices_asset_root']}/FVC_{year}", "FVC"
        )
        require_image_band(
            f"{params['eqi_asset_root']}/EQI_func_{year}", "EQI_func"
        )
    print(f"Input gate passed: {len(years) * 2} annual IMAGE assets.")

    hainan = ee.FeatureCollection(params["hainan_roi"])
    region = hainan.geometry()
    raw_forest_mask = ee.Image(params["forest_mask_asset"]).eq(1)
    forest_mask = raw_forest_mask.selfMask()
    forest_type = ee.Image(params["forest_type_asset"]).updateMask(forest_mask)
    products, _ = build_products(params, forest_mask, region)

    tables_dir = ROOT / params["tables_dir"]
    figures_dir = ROOT / params["figures_dir"]
    manifest_path = tables_dir / "table_stage05_trend_asset_manifest.csv"
    stats_path = tables_dir / "table_trend_stats_by_forest_type.csv"
    checks_path = tables_dir / "table_stage05_trend_checks.csv"
    figure_paths = [
        figures_dir / "fig04_fvc_trend_map.png",
        figures_dir / "fig05_eqi_trend_map.png",
    ]

    manifest_rows = submit_or_reuse_exports(products, params, region)
    write_csv_rows(manifest_path, MANIFEST_FIELDS, manifest_rows)
    print(f"Wrote manifest: {manifest_path}")

    stats_rows = calculate_statistics(products, forest_type, region, params)
    write_csv_rows(stats_path, STATS_FIELDS, stats_rows)
    print(f"Wrote trend statistics: {stats_path}")

    check_rows, numeric_checks = calculate_checks(
        products, raw_forest_mask, region, params
    )
    write_csv_rows(checks_path, CHECK_FIELDS, check_rows)
    print(f"Wrote trend checks: {checks_path}")
    print(json.dumps(numeric_checks, indent=2, ensure_ascii=False))

    if args.skip_figures:
        raise RuntimeError(
            "Stage 5 requires both map figures; do not use --skip-figures for completion."
        )
    make_map_figure(
        products["FVC_SenSlope_30m"],
        "FVC_SenSlope",
        region,
        figure_paths[0],
        "Hainan forest FVC trend",
        "FVC per year",
        params,
    )
    make_map_figure(
        products["EQI_SenSlope_30m"],
        "EQI_SenSlope",
        region,
        figure_paths[1],
        "Hainan forest EQI_func trend",
        "EQI_func per year",
        params,
    )
    print(f"Wrote figures: {figure_paths[0]}, {figure_paths[1]}")

    validation = validate_local_outputs(
        stats_path, manifest_path, checks_path, figure_paths
    )
    print("Stage 5 local validation:")
    print(json.dumps(validation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
