"""Earth Engine helpers for Stage 5 non-parametric trend analysis."""

from __future__ import annotations

import math
from typing import Any

import ee


def build_annual_time_series(
    asset_root: str,
    asset_prefix: str,
    source_band: str,
    years: range,
    forest_mask: "ee.Image",
) -> "ee.ImageCollection":
    """Build a two-band (year, value) annual Earth Engine collection."""
    images: list[ee.Image] = []
    for year in years:
        value = (
            ee.Image(f"{asset_root.rstrip('/')}/{asset_prefix}_{year}")
            .select(source_band)
            .rename("value")
            .toFloat()
            .updateMask(forest_mask)
        )
        time = (
            ee.Image.constant(year)
            .rename("year")
            .toFloat()
            .updateMask(value.mask())
        )
        images.append(
            time.addBands(value)
            .set("year", year)
            .set("system:time_start", ee.Date.fromYMD(year, 1, 1).millis())
        )
    return ee.ImageCollection.fromImages(images)


def calculate_sen_slope(
    time_series: "ee.ImageCollection",
    output_band: str,
    forest_mask: "ee.Image",
    region: "ee.Geometry",
) -> "ee.Image":
    """Calculate per-pixel Sen's slope with year as the time variable."""
    return (
        time_series.select(["year", "value"])
        .reduce(ee.Reducer.sensSlope())
        .select("slope")
        .rename(output_band)
        .toFloat()
        .updateMask(forest_mask)
        .clip(region)
    )


def calculate_mann_kendall_pvalue(
    time_series: "ee.ImageCollection",
    output_band: str,
    forest_mask: "ee.Image",
    region: "ee.Geometry",
) -> tuple["ee.Image", "ee.Image"]:
    """Return Kendall tau and a two-sided normal-approximation p value.

    With year as the first input and the annual value as the second input,
    ``ee.Reducer.kendallsCorrelation(2)`` supplies per-pixel Kendall tau.
    Earth Engine currently returns a masked/NaN ``p-value`` output for these
    image-series inputs, so significance is calculated from tau and the valid
    observation count using the asymptotic Mann-Kendall normal approximation:

    var(tau) = 2 * (2n + 5) / (9n(n - 1))
    p = 2 * (1 - Phi(abs(tau) / sqrt(var(tau))))

    This is AGENTS.md Stage 5 option B (Kendall tau followed by an approximate
    p value). The result is explicitly clamped to 0--1 and requires n >= 3.
    """
    result = time_series.select(["year", "value"]).reduce(
        ee.Reducer.kendallsCorrelation(2)
    )
    tau = (
        result.select("tau")
        .rename(output_band.replace("pvalue", "tau"))
        .toFloat()
        .updateMask(forest_mask)
        .clip(region)
    )
    count = time_series.select("value").count().toFloat()
    variance_tau = (
        count.multiply(2)
        .add(5)
        .multiply(2)
        .divide(count.multiply(count.subtract(1)).multiply(9))
    )
    z_score = tau.abs().divide(variance_tau.sqrt())
    pvalue = (
        ee.Image.constant(1)
        .subtract(z_score.divide(math.sqrt(2)).erf())
        .clamp(0, 1)
        .rename(output_band)
        .toFloat()
        .updateMask(count.gte(3))
        .updateMask(forest_mask)
        .clip(region)
    )
    return tau, pvalue


def add_trend_properties(
    image: "ee.Image",
    *,
    variable: str,
    method: str,
    start_year: int,
    end_year: int,
    scale: int,
    project_name: str,
) -> "ee.Image":
    """Attach the Stage 5 provenance properties required by AGENTS.md."""
    properties: dict[str, Any] = {
        "variable": variable,
        "method": method,
        "start_year": start_year,
        "end_year": end_year,
        "scale": scale,
        "project": project_name,
    }
    return image.set(properties)
