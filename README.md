# Hainan Forest Greening-Quality Project

This project studies whether vegetation greenness increases consistently across Hainan Island forests, whether higher FVC necessarily indicates better ecological quality, and whether forest structure helps explain differences between natural forests and plantations.

## Core Indicators

- Greenness: FVC
- Photosynthetic function proxy: NIRv
- Ecological quality: FVC-corrected NIRv residual, `EQI_func`
- Forest type: natural forest / plantation forest
- Forest structure: GEDI-derived 30 m FHD
- Robustness structure metric: CSC
- Stability: NIRv stability or CV_NIRv

## Workflow

1. Stage 0 - Project initialization
2. Stage 1 - Study area and forest type data preparation
3. Stage 2 - Landsat annual 30 m composites
4. Stage 3 - NDVI, FVC, and NIRv calculation
5. Stage 4 - Build EQI_func
6. Stage 5 - Trend analysis
7. Stage 6 - Greening-quality decoupling
8. Stage 7 - Train FHD models
9. Stage 8 - Select final FHD model
10. Stage 9 - Generate FHD maps
11. Stage 10 - Forest type comparison
12. Stage 11 - Regression and SEM analysis
13. Stage 12 - Stability analysis
14. Stage 13 - Robustness analysis
15. Stage 14 - Final figures and tables

## Environment

Use the `csc` conda environment for command-line execution:

```powershell
conda activate csc
```

All scripts must read project settings from `config/config.yaml`.
