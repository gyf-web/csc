# 海南岛天然林/人工林绿量—生态质量脱钩与森林结构调节作用项目 AGENTS.md

## 0. Codex 总执行原则

### 0.1 项目目标

本项目以海南岛为研究区，基于 30 m 遥感数据研究：

1. 海南岛植被覆盖度是否持续提高；
2. 植被覆盖度提高是否必然代表生态质量改善；
3. 是否存在“FVC 提高但生态质量下降”的绿量—绿质脱钩区；
4. 脱钩区是否主要分布于人工林区域；
5. 森林垂直结构复杂性是否解释天然林与人工林之间的生态质量差异。

### 0.2 核心指标

本项目固定使用以下主指标：

- 绿量指标：FVC；
- 光合功能代理：NIRv；
- 生态质量主指标：FVC 校正后的 NIRv 残差，记为 `EQI_func`；
- 森林类型变量：天然林 / 人工林；
- 森林结构变量：GEDI FHD 外推得到的 30 m FHD；
- 结构稳健性变量：CSC 综合结构指数；
- 稳定性指标：NIRv stability 或 CV_NIRv。

### 0.3 分辨率和年份

- 主分析分辨率：30 m；
- 生态质量长时序：2000—2024 年；
- 森林结构外推：2019—2024 年；
- 结构主图：2019—2024 年平均 FHD；
- 森林类型主图：优先采用 2020/2021 年 30 m 天然林/人工林数据，并剔除 2021—2024 年明显变化区域。

### 0.4 Codex 必须遵守的硬性规则

1. 每次只执行一个阶段，不允许跨阶段提前生成后续代码。
2. 每个阶段完成后必须更新 `docs/progress_log.md`。
3. 每个阶段必须输出固定文件，不能只输出临时结果。
4. 不允许在项目根目录堆放临时脚本、测试脚本或无用 notebook。
5. 所有脚本必须放入 `scripts/` 或 `src/`。
6. 所有输出必须放入 `outputs/` 下对应阶段文件夹。
7. 所有中间数据必须写入 `data/interim/` 或 `data/processed/`。
8. 所有最终图表必须写入 `outputs/figures/`。
9. 所有表格必须写入 `outputs/tables/`。
10. 每个阶段结束后必须删除无用临时文件，或将其移动到 `archive/` 并在日志中说明。
11. 不允许把旧版本代码留在同一目录中造成混乱。若需要保留旧版本，放入 `archive/stageXX/`。
12. 所有脚本必须可以从命令行运行。
13. 所有脚本必须读取 `config/config.yaml`，不要在脚本中硬编码绝对路径。
14. 每个阶段必须有可验证的检查结果。
15. 如果某阶段缺少必要输入，必须停止并在日志中说明，不得编造数据继续执行。
16. 不得为了让流程通过而生成伪数据、随机数据或占位结果。
17. 每个阶段完成后必须列出：新增文件、修改文件、检查结果、遗留问题和下一阶段建议。
18. 若修改已有脚本，必须保持原有阶段边界，不得把多个阶段逻辑混写到一个脚本中。

---

## 1. 推荐项目目录结构

Codex 初始化项目时，应创建如下结构：

```text
project_root/
├── AGENTS.md
├── TASK_PLAN.md
├── README.md
├── config/
│   └── config.yaml
├── docs/
│   ├── progress_log.md
│   ├── data_dictionary.md
│   └── method_notes.md
├── gee/  # Python 端 Earth Engine API 导出脚本
│   ├── stage01_export_forest_type.py
│   ├── stage02_export_landsat_annual.py
│   ├── stage03_export_gedi_samples.py
│   └── stage04_export_alphaearth_samples.py
├── scripts/
│   ├── stage00_check_environment.py
│   ├── stage03_indices.py
│   ├── stage04_build_eqi_model.py
│   ├── stage05_trend_analysis.py
│   ├── stage06_decoupling.py
│   ├── stage07_train_fhd_models.py
│   ├── stage08_select_final_fhd.py
│   ├── stage09_generate_fhd_maps.py
│   ├── stage10_forest_type_analysis.py
│   ├── stage11_regression_sem.py
│   ├── stage12_stability_analysis.py
│   ├── stage13_robustness.py
│   └── stage14_make_figures_tables.py
├── src/
│   ├── __init__.py
│   ├── io_utils.py
│   ├── raster_utils.py
│   ├── stats_utils.py
│   ├── model_utils.py
│   ├── trend_utils.py
│   ├── plotting_utils.py
│   └── validation_utils.py
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── outputs/
│   ├── stage01_forest_type/
│   ├── stage02_landsat/
│   ├── stage03_indices/
│   ├── stage04_eqi/
│   ├── stage05_trend/
│   ├── stage06_decoupling/
│   ├── stage07_gedi/
│   ├── stage08_fhd_model/
│   ├── stage09_fhd_maps/
│   ├── stage10_forest_comparison/
│   ├── stage11_models/
│   ├── stage12_stability/
│   ├── stage13_robustness/
│   ├── figures/
│   └── tables/
└── archive/
```

---

## 2. 基础配置文件要求

创建 `config/config.yaml`，至少包含：

```yaml
project:
  name: hainan_forest_greening_quality
  crs: EPSG:4326
  target_scale: 30
  start_year: 2000
  end_year: 2024
  structure_start_year: 2019
  structure_end_year: 2024

paths:
  data_raw: data/raw
  data_interim: data/interim
  data_processed: data/processed
  outputs: outputs
  figures: outputs/figures
  tables: outputs/tables

gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: null
  rubber_mask_asset: null

analysis:
  fvc_ndvi_soil_percentile: 5
  fvc_ndvi_veg_percentile: 95
  trend_pvalue_threshold: 0.05
  random_seed: 2026
  spatial_block_km: 20
  cv_folds: 5
```

如果用户尚未替换 `projects/your_username/assets/Hainan_ROI`，Codex 必须停止并提示用户修改配置，不得自行猜测 Earth Engine 资产路径。

---

## 3. 进度日志规范

创建 `docs/progress_log.md`，模板如下：

```markdown
# Progress Log

## Stage 0 - Project initialization

Status: pending / running / completed / failed  
Date:  
Inputs:  
Outputs:  
Checks:  
Problems:  
Next stage:
```

每个阶段结束时必须追加一段日志，不允许覆盖旧日志。

---

# Stage 0：项目结构初始化

## 目标

创建规范项目结构，保证后续代码、数据和结果不会混乱。

## 输入

无。

## 允许创建或修改的文件

```text
AGENTS.md
TASK_PLAN.md
README.md
config/config.yaml
docs/progress_log.md
docs/data_dictionary.md
docs/method_notes.md
gee/
scripts/
src/
data/
outputs/
archive/
```

## 具体任务

1. 创建推荐目录结构。
2. 创建 `config/config.yaml`。
3. 创建 `docs/progress_log.md`。
4. 创建空的工具模块文件：
   - `src/io_utils.py`
   - `src/raster_utils.py`
   - `src/stats_utils.py`
   - `src/model_utils.py`
   - `src/trend_utils.py`
   - `src/plotting_utils.py`
   - `src/validation_utils.py`
5. 创建空的阶段脚本文件。
6. 创建基础 `README.md`，写明项目目标和阶段顺序。
7. 更新 `docs/progress_log.md`。

## 输出

```text
config/config.yaml
docs/progress_log.md
README.md
完整项目目录结构
```

## 检查标准

阶段完成后必须满足：

- 项目目录结构完整；
- `config/config.yaml` 存在；
- `docs/progress_log.md` 存在；
- 所有阶段脚本文件名已预留；
- 不产生任何遥感处理结果。

## 禁止事项

- 不允许在此阶段写完整分析代码；
- 不允许创建未经规划的目录；
- 不允许生成测试栅格或随机数据。

---

# Stage 1：研究区与森林类型数据准备

## 目标

准备海南岛边界、天然林/人工林类型图、森林分析掩膜，并输出统一 30 m 森林类型数据。

## 输入数据

必须准备海南岛边界矢量。

森林类型数据为：

Global Natural and Planted Forests 2021；


## 允许创建或修改的文件

```text
gee/stage01_export_forest_type.py
outputs/tables/table_forest_type_area.csv
outputs/tables/table_forest_type_asset_manifest.csv
docs/progress_log.md
```

## 具体任务

### 1. 加载海南边界

使用 Python 端 Earth Engine API 加载：

```python
import ee

ee.Initialize()

hainan = ee.FeatureCollection("projects/ee-gyf/assets/hainan")
```

检查是否成功显示海南岛。

### 2. 加载森林类型产品

优先加载已有 30 m 天然林/人工林图。

如果使用 Global Natural and Planted Forests：

```python
forest_type_raw = (
    ee.ImageCollection("projects/sat-io/open-datasets/GLOBAL-NATURAL-PLANTED-FORESTS")
    .mosaic()
    .clip(hainan)
)
```

### 3. 统一分类编码

将不同来源的森林类型数据重分类为：

```text
0 = 非森林或不确定
1 = 天然林
2 = 人工林
```


### 4. 剔除近期变化区

如果森林类型图年份为 2020 或 2021，需要剔除 2021—2024 年明显变化区域。

剔除规则：

- Hansen forest loss 发生在 2021—2024 年；
- 或 2021—2024 年 FVC 明显下降；
- 或被最新土地覆盖数据识别为建设用地、水体、裸地。

剔除后重新编码为 0。

### 5. 输出森林类型图和森林掩膜

本阶段不将森林类型图和森林掩膜下载为本地 GeoTIFF，而是使用 Python 端 Earth Engine API 导出到 Earth Engine Asset。

导出到：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
```

其中：

```text
ForestType_30m_clean:
0 = 非森林或不确定
1 = 天然林
2 = 人工林
```


森林掩膜定义为：

```text
ForestMask_30m:
1 = 天然林或人工林
0 = 其他区域
```

Python 端 Earth Engine 导出示例：

```python
forest_type_asset_id = (
    "users/gyf/forest_csc_alphaearth/"
    "stage01_forest_type/ForestType_30m_clean"
)

forest_mask_asset_id = (
    "users/gyf/forest_csc_alphaearth/"
    "stage01_forest_type/ForestMask_30m"
)

task_forest_type = ee.batch.Export.image.toAsset(
    image=forest_type_clean.toByte(),
    description="ForestType_30m_clean",
    assetId=forest_type_asset_id,
    region=hainan.geometry(),
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13
)

task_forest_mask = ee.batch.Export.image.toAsset(
    image=forest_mask.toByte(),
    description="ForestMask_30m",
    assetId=forest_mask_asset_id,
    region=hainan.geometry(),
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13
)

task_forest_type.start()
task_forest_mask.start()
```

---

### 6. 面积统计

本地仅输出 CSV 表格：

```text
outputs/tables/table_forest_type_area.csv
```

字段：

```text
class_id
class_name
area_km2
percentage_of_forest
```

其中：

```text
class_id
```

对应统一后的森林类型编码。

```text
area_km2
```

使用 Earth Engine 中的 `ee.Image.pixelArea()` 计算，不允许用像元数量粗略估算。

---

### 7. Asset 清单

本地输出：

```text
outputs/tables/table_forest_type_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
description
scale
crs
export_status
notes
```

内容示例：

```text
ForestType_30m_clean,users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean,统一编码后的天然林/人工林类型图,30,EPSG:4326,submitted,
ForestMask_30m,users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m,森林分析掩膜,30,EPSG:4326,submitted,
```

---

## 检查标准

必须检查：

1. 海南边界是否正确；
2. 天然林和人工林是否位于合理区域；
3. 非森林区域是否被剔除；
4. 面积统计是否合理；
5. 导出 Asset 是否为 30 m；
6. 导出 Asset 是否与海南边界对齐；
7. `ForestType_30m_clean` 是否只包含统一编码；
8. `ForestMask_30m` 是否只包含森林区；
9. 影像是否成功导出到：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/
```

10. 本地是否只保存 CSV 表格，不保存森林类型图和森林掩膜 GeoTIFF。

---

## 禁止事项

* 不允许把原始森林类型数据直接用于分析，必须统一编码；
* 不允许把水体、建设用地、裸地保留为森林；
* 不允许在未说明的情况下混用多个森林类型产品；
* 不允许直接声称森林类型是 2024 年，除非使用的确实是 2024 年数据；
* 不允许将 `ForestType_30m_clean.tif` 和 `ForestMask_30m.tif` 下载到本地；
* 不允许在 `outputs/stage01_forest_type/` 中保存大体量 GeoTIFF；
* 不允许导出到 Google Drive 作为主方案；
* 不允许使用 JavaScript 端 GEE 代码。


# Stage 2：Landsat 年度 30 m 合成影像

## 目标

生成 2000—2024 年海南岛森林区 Landsat 年度 30 m 地表反射率合成影像。

由于 2000—2024 年共 25 期 30 m 合成影像直接下载到本地数据量过大，本阶段不再将年度合成影像导出为本地 GeoTIFF，而是使用 Python 端 Earth Engine API 将每年合成影像导出到 Earth Engine Asset。

本阶段本地仅保存：

1. 年度有效像元统计表；
2. 年度合成影像 Asset 清单；
3. 进度日志。

年度合成影像统一导出到：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/
```

每年影像命名为：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000
...
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024
```

---

## 输入数据

Earth Engine 数据集：

```text
LANDSAT/LT05/C02/T1_L2
LANDSAT/LE07/C02/T1_L2
LANDSAT/LC08/C02/T1_L2
LANDSAT/LC09/C02/T1_L2
```

上一阶段输出：

```text
ForestMask_30m
ForestType_30m_clean
```

说明：

上一阶段森林类型图和森林掩膜如果已经导出到 Earth Engine Asset，则 Stage 2 直接从 Asset 读取。

推荐路径示例：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

如果上一阶段仍为本地 GeoTIFF，则需要先上传到 Earth Engine Asset 后再执行本阶段。

---

## 允许创建或修改的文件

```text
gee/stage02_export_landsat_annual.py
outputs/tables/table_landsat_valid_pixels_by_year.csv
outputs/tables/table_landsat_asset_manifest.csv
docs/progress_log.md
```

本阶段不再创建：

```text
outputs/stage02_landsat/LandsatComposite_2000.tif
...
outputs/stage02_landsat/LandsatComposite_2024.tif
```

年度合成影像改为输出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000
...
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage02_export_landsat_annual.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 设置基础参数

在脚本中读取 `config/config.yaml`。

必须从配置文件读取：

```text
hainan_roi
target_scale
start_year
end_year
random_seed
```

本阶段新增或使用以下 Asset 根目录：

```text
users/gyf/forest_csc_alphaearth
```

推荐在配置文件中加入：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  output_asset_root: users/gyf/forest_csc_alphaearth
```

如果 `output_asset_root` 不存在，Codex 必须停止并提示用户先在 Earth Engine Asset 中创建：

```text
users/gyf/forest_csc_alphaearth
```

如果子文件夹不存在，也需要先创建：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat
```

---

### 3. 加载海南边界和森林掩膜

Python 端写法：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_mask = ee.Image(config["gee_assets"]["forest_mask_asset"]).eq(1).selfMask()
```

检查：

```text
hainan 是否能正常加载；
forest_mask 是否为 1/无效值 掩膜；
forest_mask 是否覆盖海南主要森林区。
```

---

### 4. 编写 Landsat 预处理函数

函数必须完成：

1. 云掩膜；
2. 云影掩膜；
3. 饱和像元剔除；
4. 地表反射率尺度因子转换；
5. 波段统一命名；
6. 裁剪到海南；
7. 应用森林掩膜。

Collection 2 Level-2 地表反射率尺度因子：

```text
SR = DN * 0.0000275 - 0.2
```

QA 掩膜至少剔除：

```text
Fill
Dilated Cloud
Cloud
Cloud Shadow
Snow
```

饱和像元使用：

```text
QA_RADSAT == 0
```

---

### 5. 统一波段名称

统一输出：

```text
Blue
Green
Red
NIR
SWIR1
SWIR2
```

Landsat 5/7：

```text
Blue  = SR_B1
Green = SR_B2
Red   = SR_B3
NIR   = SR_B4
SWIR1 = SR_B5
SWIR2 = SR_B7
```

Landsat 8/9：

```text
Blue  = SR_B2
Green = SR_B3
Red   = SR_B4
NIR   = SR_B5
SWIR1 = SR_B6
SWIR2 = SR_B7
```

---

### 6. 年度合成

对每一年执行：

```text
filterDate(year-01-01, year-12-31)
filterBounds(hainan)
map(preprocess)
median()
clip(hainan)
updateMask(ForestMask)
```

主合成方法：

```text
全年 median
```

稳健性备用方法：

```text
4—11 月 median
```

本阶段只实现全年 median，备用方法在稳健性阶段再实现。

---

### 7. 导出年度合成影像到 Earth Engine Asset

每年导出到：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000
...
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024
```

Python 端导出示例：

```python
asset_id = f"users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_{year}"

task = ee.batch.Export.image.toAsset(
    image=composite.toFloat(),
    description=f"LandsatComposite_{year}",
    assetId=asset_id,
    region=hainan.geometry(),
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13
)

task.start()
```

导出影像必须包含以下 6 个波段：

```text
Blue
Green
Red
NIR
SWIR1
SWIR2
```

影像属性必须写入：

```text
year
sensor_group
composite_method
scale
```

例如：

```python
composite = composite.set({
    "year": year,
    "composite_method": "annual_median",
    "scale": 30,
    "project": "hainan_forest_greening_quality"
})
```

---

### 8. 输出 Asset 清单

本地输出：

```text
outputs/tables/table_landsat_asset_manifest.csv
```

字段：

```text
year
asset_id
export_description
export_status
band_names
scale
crs
notes
```

示例：

```text
2000,users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000,LandsatComposite_2000,submitted,"Blue;Green;Red;NIR;SWIR1;SWIR2",30,EPSG:4326,
```

---

### 9. 输出质量统计表

本地输出：

```text
outputs/tables/table_landsat_valid_pixels_by_year.csv
```

字段：

```text
year
valid_pixel_count
valid_area_km2
forest_area_km2
valid_percentage
image_count_before_mask
image_count_after_mask
asset_id
```

其中：

```text
valid_pixel_count
```

为年度合成影像中森林区有效像元数量。

```text
valid_area_km2 = valid_pixel_count * 30 * 30 / 1,000,000
```

```text
forest_area_km2
```

为 ForestMask 对应森林总面积。

```text
valid_percentage = valid_area_km2 / forest_area_km2 * 100
```

---

## 检查标准

必须检查：

1. 2000—2024 年是否全部提交导出任务；
2. 每年 Asset ID 是否正确；
3. 每年合成影像是否包含 6 个统一波段；
4. 每年有效像元比例是否合理；
5. 2000—2024 年是否有明显缺失年份；
6. Landsat 7 SLC-off 年份是否存在异常条带；
7. 波段值是否在合理地表反射率范围；
8. 影像是否应用 ForestMask；
9. 导出的 Asset 是否位于：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/
```

10. 本地是否只保存统计表和 Asset 清单，不保存年度 GeoTIFF。

---

## 禁止事项

* 不允许直接使用 DN 值计算指数；
* 不允许混用未统一波段名的 Landsat 影像；
* 不允许把云和云影保留在合成影像中；
* 不允许把 Stage 3 的指数计算写进本阶段脚本；
* 不允许将 2000—2024 年年度合成影像下载为本地 GeoTIFF；
* 不允许在 `outputs/stage02_landsat/` 中堆放大体量 `.tif` 文件；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许导出到 Google Drive 作为主方案；
* 不允许在 Asset 路径中混用多个根目录。


# Stage 3：NDVI、FVC 和 NIRv 计算

## 目标

基于 Stage 2 已导出到 Earth Engine Asset 的年度 Landsat 合成影像，计算 2000—2024 年海南岛森林区 NDVI、FVC 和 NIRv。

本阶段不下载年度 NDVI、FVC 和 NIRv 栅格到本地，而是使用 Python 端 Earth Engine API 直接读取 GEE Asset，完成指数计算后再导出到 Earth Engine Asset。

本地仅保存：

1. FVC 固定阈值统计表；
2. 年度 NDVI/FVC/NIRv 统计表；
3. 指数影像 Asset 清单；
4. 时间序列图；
5. 进度日志。

---

## 输入数据

Stage 2 年度 Landsat 合成影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000
...
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024
```

Stage 1 森林类型图和森林掩膜，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

如果上述 Asset 不存在，Codex 必须停止，并在 `docs/progress_log.md` 中说明缺少的 Asset ID，不得改为读取本地 GeoTIFF，也不得编造数据继续执行。

---

## 允许创建或修改的文件

```text
gee/stage03_export_indices.py
src/io_utils.py
outputs/tables/table_fvc_thresholds.csv
outputs/tables/table_annual_fvc_nirv_stats.csv
outputs/tables/table_stage03_indices_asset_manifest.csv
outputs/figures/fig02_annual_fvc_nirv_timeseries.png
docs/progress_log.md
```

本阶段不再创建本地 GeoTIFF：

```text
outputs/stage03_indices/NDVI_2000.tif
...
outputs/stage03_indices/NDVI_2024.tif
outputs/stage03_indices/FVC_2000.tif
...
outputs/stage03_indices/FVC_2024.tif
outputs/stage03_indices/NIRv_2000.tif
...
outputs/stage03_indices/NIRv_2024.tif
```

指数影像统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2024

users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2024

users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage03_export_indices.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 加载基础 Asset

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  landsat_asset_root: users/gyf/forest_csc_alphaearth/stage02_landsat
  indices_asset_root: users/gyf/forest_csc_alphaearth/stage03_indices
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_mask = (
    ee.Image(config["gee_assets"]["forest_mask_asset"])
    .eq(1)
    .selfMask()
)

forest_type = ee.Image(config["gee_assets"]["forest_type_asset"])
```

年度 Landsat 合成影像按年份循环读取：

```python
landsat_asset_id = (
    f"{config['gee_assets']['landsat_asset_root']}/"
    f"LandsatComposite_{year}"
)

landsat = ee.Image(landsat_asset_id)
```

---

### 3. 计算 NDVI

公式：

```text
NDVI = (NIR - Red) / (NIR + Red)
```

Python 端 Earth Engine 写法示例：

```python
ndvi = (
    landsat.normalizedDifference(["NIR", "Red"])
    .rename("NDVI")
    .updateMask(forest_mask)
    .clip(hainan)
)
```

年度 NDVI 不导出到本地，统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2024
```

---

### 4. 计算固定 FVC 分位数

FVC 阈值必须使用 2000—2024 年全部森林区 NDVI 的统一分位数，不允许每年单独计算阈值作为主方案。

阈值定义：

```text
NDVI_soil = 5% percentile
NDVI_veg  = 95% percentile
```

由于不下载年度 NDVI 栅格到本地，阈值计算采用以下流程：

1. 在 Earth Engine 端对 2000—2024 年年度 NDVI 影像进行森林区统计；
2. 每年计算 NDVI 直方图或抽样分布；
3. 将每年 NDVI 分布统计结果取回 Python；
4. 在 Python 端合并 2000—2024 年 NDVI 分布；
5. 在 Python 端计算统一的 5% 和 95% 分位数；
6. 将最终阈值写入本地 CSV。

输出：

```text
outputs/tables/table_fvc_thresholds.csv
```

字段：

```text
ndvi_soil_percentile
ndvi_veg_percentile
ndvi_soil_value
ndvi_veg_value
method
sample_or_histogram_count
```

推荐方法：

```text
Earth Engine 端按年份统计 NDVI fixedHistogram；
Python 端合并 25 年直方图并计算 5% / 95% 分位数。
```

如果使用随机抽样代替直方图，必须：

```text
每年至少抽样 50,000 个森林像元；
天然林和人工林都必须包含；
固定 random_seed = 2026；
在日志中说明使用 sample 方法而非 histogram 方法。
```

---

### 5. 计算 FVC

公式：

```text
FVC = (NDVI - NDVI_soil) / (NDVI_veg - NDVI_soil)
```

然后限制到 0—1：

```text
FVC < 0 → 0
FVC > 1 → 1
```

Python 端 Earth Engine 写法示例：

```python
fvc = (
    ndvi.subtract(ndvi_soil)
    .divide(ndvi_veg - ndvi_soil)
    .clamp(0, 1)
    .rename("FVC")
    .updateMask(forest_mask)
    .clip(hainan)
)
```

年度 FVC 不导出到本地，统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2024
```

---

### 6. 计算 NIRv

公式：

```text
NIRv = (NDVI - 0.08) * NIR
```

Python 端 Earth Engine 写法示例：

```python
nirv = (
    ndvi.subtract(0.08)
    .multiply(landsat.select("NIR"))
    .rename("NIRv")
    .updateMask(forest_mask)
    .clip(hainan)
)
```

若森林区出现负值，可保留原值用于统计检查，但主分析可将极端负值掩膜或设为 0。具体处理方式必须写入 `docs/progress_log.md`。

年度 NIRv 不导出到本地，统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024
```

---

### 7. 导出 NDVI、FVC 和 NIRv 到 Earth Engine Asset

每一年需要分别提交 3 个导出任务：

```text
NDVI_YYYY
FVC_YYYY
NIRv_YYYY
```

Python 端导出示例：

```python
def export_image_to_asset(image, asset_id, description, hainan):
    task = ee.batch.Export.image.toAsset(
        image=image.toFloat(),
        description=description,
        assetId=asset_id,
        region=hainan.geometry(),
        scale=30,
        crs="EPSG:4326",
        maxPixels=1e13
    )
    task.start()
    return task
```

示例：

```python
ndvi_asset_id = f"users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_{year}"
fvc_asset_id = f"users/gyf/forest_csc_alphaearth/stage03_indices/FVC_{year}"
nirv_asset_id = f"users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_{year}"

export_image_to_asset(ndvi, ndvi_asset_id, f"NDVI_{year}", hainan)
export_image_to_asset(fvc, fvc_asset_id, f"FVC_{year}", hainan)
export_image_to_asset(nirv, nirv_asset_id, f"NIRv_{year}", hainan)
```

影像属性必须写入：

```text
year
index_name
source
scale
project
```

例如：

```python
ndvi = ndvi.set({
    "year": year,
    "index_name": "NDVI",
    "source": "Landsat annual median composite",
    "scale": 30,
    "project": "hainan_forest_greening_quality"
})
```

---

### 8. 输出指数 Asset 清单

本地输出：

```text
outputs/tables/table_stage03_indices_asset_manifest.csv
```

字段：

```text
year
index_name
asset_id
export_description
export_status
scale
crs
notes
```

示例：

```text
2000,NDVI,users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2000,NDVI_2000,submitted,30,EPSG:4326,
2000,FVC,users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000,FVC_2000,submitted,30,EPSG:4326,
2000,NIRv,users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000,NIRv_2000,submitted,30,EPSG:4326,
```

---

### 9. 输出年度统计表

年度统计表必须在 Python 端生成，并存入本地。

统计过程：

1. 在 Earth Engine 端对每年 NDVI、FVC 和 NIRv 按森林类型进行区域统计；
2. 使用 `reduceRegion` 或 `reduceRegions` 获取统计结果；
3. 使用 Python 将结果整理为 `pandas.DataFrame`；
4. 写出本地 CSV。

输出：

```text
outputs/tables/table_annual_fvc_nirv_stats.csv
```

字段：

```text
year
forest_type
NDVI_mean
NDVI_median
FVC_mean
FVC_median
FVC_std
NIRv_mean
NIRv_median
NIRv_std
valid_pixel_count
valid_area_km2
```

森林类型字段统一为：

```text
all_forest
natural_forest
plantation_forest
rubber_forest
other_plantation
```

其中：

* 如果没有橡胶林分类，则不输出 `rubber_forest` 和 `other_plantation`；
* 如果森林类型图只有天然林/人工林，则仅输出 `all_forest`、`natural_forest`、`plantation_forest`。

---

### 10. 输出时间序列图

根据本地统计表生成时间序列图：

```text
outputs/figures/fig02_annual_fvc_nirv_timeseries.png
```

内容：

* 全岛森林平均 FVC 时间序列；
* 天然林 FVC 时间序列；
* 人工林 FVC 时间序列；
* 全岛森林 NIRv 时间序列；
* 天然林 NIRv 时间序列；
* 人工林 NIRv 时间序列。

图件使用 Python 端 `pandas` 和 `matplotlib` 生成，不从 GEE 下载栅格。

---

## 检查标准

必须检查：

1. 2000—2024 年 LandsatComposite Asset 是否全部存在；
2. 2000—2024 年 NDVI、FVC、NIRv 是否全部提交导出到 Asset；
3. NDVI 是否主要位于 -1—1；
4. FVC 是否严格位于 0—1；
5. NIRv 是否空间分布合理；
6. 天然林和人工林时间序列是否没有明显异常跳变；
7. FVC 阈值是否为 2000—2024 年统一阈值；
8. 本地是否只保存 CSV 表格和时间序列图，不保存年度指数 GeoTIFF；
9. 所有指数 Asset 是否位于：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/
```

---

## 禁止事项

* 不允许每一年单独计算 FVC 分位数作为主方案；
* 不允许使用未转换反射率的 NIR 波段计算 NIRv；
* 不允许在本阶段做趋势分析；
* 不允许在本阶段构建 EQI_func；
* 不允许将 NDVI、FVC、NIRv 年度栅格下载为本地 GeoTIFF；
* 不允许在 `outputs/stage03_indices/` 中保存大体量 `.tif` 文件；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许导出到 Google Drive 作为主方案；
* 不允许在统计表中混用未统一编码的森林类型。


# Stage 4：构建生态质量指标 EQI_func

## 目标

通过统一回归模型扣除 FVC 和环境因子的影响，构建 FVC 校正后的 NIRv 残差指标 `EQI_func`。

本阶段输入数据主要来自 Earth Engine Asset 和 Earth Engine 公共数据集，不再读取本地 GeoTIFF。

其中：

1. FVC 和 NIRv 来自 Stage 3 已导出的 Earth Engine Asset；
2. ForestMask 和 ForestType 来自 Stage 1 已导出的 Earth Engine Asset；
3. DEM 使用 Earth Engine 公共数据；
4. Slope 在 Earth Engine 端由 DEM 计算；
5. Annual precipitation 和 Annual mean temperature 使用 Earth Engine 气候数据在 GEE 端逐年生成；
6. EQI_func 年度栅格不下载到本地，统一导出到 Earth Engine Asset；
7. 回归样本表、模型系数表、诊断表、年度统计表和图件在 Python 端生成并保存到本地。

---

## 输入数据

Stage 3 指数影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2024

users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024
```

Stage 1 森林掩膜和森林类型图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

Earth Engine 公共数据：

```text
USGS/SRTMGL1_003
ECMWF/ERA5_LAND/MONTHLY_AGGR
```

说明：

* `USGS/SRTMGL1_003` 用于 DEM；
* Slope 由 DEM 在 Earth Engine 端计算；
* `ECMWF/ERA5_LAND/MONTHLY_AGGR` 用于逐年降水和逐年平均气温；
* 气候数据为空间分辨率较粗的数据，只作为环境控制变量使用，不解释为 30 m 精细气候格局。

如果气候数据暂未接入，本阶段可先执行简化模型：

```text
NIRv ~ FVC
```

但必须在 `docs/progress_log.md` 中标记：

```text
simplified_model = true
```

---

## 允许创建或修改的文件

```text
gee/stage04_build_eqi_model.py
src/stats_utils.py
src/io_utils.py
outputs/stage04_eqi/EQI_regression_samples.csv
outputs/tables/table_eqi_regression_coefficients.csv
outputs/tables/table_eqi_regression_diagnostics.csv
outputs/tables/table_annual_eqi_stats.csv
outputs/tables/table_stage04_eqi_asset_manifest.csv
outputs/figures/fig03_eqi_timeseries_by_forest_type.png
docs/progress_log.md
```

本阶段不再创建本地 GeoTIFF：

```text
outputs/stage04_eqi/EQI_func_2000.tif
...
outputs/stage04_eqi/EQI_func_2024.tif
```

年度 EQI_func 栅格统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000
...
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2024
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage04_build_eqi_model.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  indices_asset_root: users/gyf/forest_csc_alphaearth/stage03_indices
  eqi_asset_root: users/gyf/forest_csc_alphaearth/stage04_eqi
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_mask = (
    ee.Image(config["gee_assets"]["forest_mask_asset"])
    .eq(1)
    .selfMask()
)

forest_type = ee.Image(config["gee_assets"]["forest_type_asset"])
```

年度 FVC 和 NIRv 按年份循环读取：

```python
fvc_asset_id = (
    f"{config['gee_assets']['indices_asset_root']}/"
    f"FVC_{year}"
)

nirv_asset_id = (
    f"{config['gee_assets']['indices_asset_root']}/"
    f"NIRv_{year}"
)

fvc = ee.Image(fvc_asset_id).select("FVC")
nirv = ee.Image(nirv_asset_id).select("NIRv")
```

如果任一年 FVC 或 NIRv Asset 不存在，Codex 必须停止，并在日志中记录缺失 Asset ID，不得改为读取本地 GeoTIFF，也不得编造数据继续执行。

---

### 3. 准备环境控制变量

DEM 使用 Earth Engine 数据：

```text
USGS/SRTMGL1_003
```

Python 端 Earth Engine 写法：

```python
dem = (
    ee.Image("USGS/SRTMGL1_003")
    .select("elevation")
    .rename("DEM")
    .clip(hainan)
)

slope = (
    ee.Terrain.slope(dem)
    .rename("Slope")
    .clip(hainan)
)
```

年度气候数据使用：

```text
ECMWF/ERA5_LAND/MONTHLY_AGGR
```

每一年计算：

```text
Annual precipitation = sum(total_precipitation_sum)
Annual mean temperature = mean(temperature_2m)
```

示例写法：

```python
def get_annual_climate(year):
    start = f"{year}-01-01"
    end = f"{year + 1}-01-01"

    era5 = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterDate(start, end)
        .filterBounds(hainan)
    )

    precip = (
        era5.select("total_precipitation_sum")
        .sum()
        .rename("Precip")
        .clip(hainan)
    )

    temp = (
        era5.select("temperature_2m")
        .mean()
        .subtract(273.15)
        .rename("Temp")
        .clip(hainan)
    )

    return precip.addBands(temp)
```

注意：

* `temperature_2m` 需要从 K 转为 ℃；
* `total_precipitation_sum` 的单位必须在日志中说明；
* 气候数据不下载到本地；
* 气候数据只作为环境控制变量，不作为 30 m 精细结果解释。

---

### 4. 抽样构建回归训练表

从每一年森林区随机抽样。

建议：

```text
每年 20,000—50,000 个像元
天然林和人工林分层抽样
固定随机种子 2026
```

每年构建用于抽样的多波段影像：

```text
NIRv
FVC
DEM
Slope
Precip
Temp
ForestType
year
```

样本字段：

```text
year
longitude
latitude
NIRv
FVC
DEM
Slope
Precip
Temp
ForestType
```

Python 端 Earth Engine 示例：

```python
sample_img = (
    nirv.addBands(fvc)
    .addBands(dem)
    .addBands(slope)
    .addBands(get_annual_climate(year))
    .addBands(forest_type.rename("ForestType"))
    .updateMask(forest_mask)
    .clip(hainan)
)
```

抽样结果通过 `getInfo()` 或分批导出表格后读入 Python。

本地输出：

```text
outputs/stage04_eqi/EQI_regression_samples.csv
```

说明：

* 回归模型在 Python 端拟合；
* 训练样本 CSV 是本阶段允许保存到本地的中间表；
* 不得保存大体量年度栅格到本地。

---

### 5. 拟合统一回归模型

主模型：

```text
NIRv ~ FVC + DEM + Slope + Precip + Temp
```

备用简化模型：

```text
NIRv ~ FVC
```

模型必须使用 2000—2024 年合并样本统一拟合，不允许每年单独拟合主模型。

Python 端可使用：

```text
statsmodels
sklearn.linear_model
```

输出模型系数：

```text
outputs/tables/table_eqi_regression_coefficients.csv
```

字段建议：

```text
term
coefficient
std_error
t_value
p_value
model_type
```

输出模型诊断：

```text
outputs/tables/table_eqi_regression_diagnostics.csv
```

诊断字段：

```text
R2
RMSE
MAE
Bias
sample_count
model_type
simplified_model
```

---

### 6. 将 Python 回归系数回写到 Earth Engine 端计算 EQI_func

对每一年整幅影像计算：

```text
NIRv_predicted = a + b*FVC + c*DEM + d*Slope + e*Precip + f*Temp
EQI_func = NIRv_observed - NIRv_predicted
```

其中 `a, b, c, d, e, f` 来自 Python 端拟合结果。

Python 端 Earth Engine 示例：

```python
nirv_pred = (
    ee.Image.constant(intercept)
    .add(fvc.multiply(coef_fvc))
    .add(dem.multiply(coef_dem))
    .add(slope.multiply(coef_slope))
    .add(precip.multiply(coef_precip))
    .add(temp.multiply(coef_temp))
    .rename("NIRv_predicted")
)

eqi = (
    nirv.subtract(nirv_pred)
    .rename("EQI_func")
    .updateMask(forest_mask)
    .clip(hainan)
)
```

如果使用简化模型，则计算：

```python
nirv_pred = (
    ee.Image.constant(intercept)
    .add(fvc.multiply(coef_fvc))
    .rename("NIRv_predicted")
)
```

---

### 7. 导出年度 EQI_func 到 Earth Engine Asset

每年导出：

```text
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000
...
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2024
```

Python 端导出示例：

```python
eqi_asset_id = (
    f"{config['gee_assets']['eqi_asset_root']}/"
    f"EQI_func_{year}"
)

task = ee.batch.Export.image.toAsset(
    image=eqi.toFloat(),
    description=f"EQI_func_{year}",
    assetId=eqi_asset_id,
    region=hainan.geometry(),
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13
)

task.start()
```

影像属性必须写入：

```text
year
index_name
model_type
simplified_model
source
scale
project
```

示例：

```python
eqi = eqi.set({
    "year": year,
    "index_name": "EQI_func",
    "model_type": "unified_residual_model",
    "simplified_model": simplified_model,
    "source": "NIRv residual after FVC and environmental correction",
    "scale": 30,
    "project": "hainan_forest_greening_quality"
})
```

---

### 8. 输出 EQI Asset 清单

本地输出：

```text
outputs/tables/table_stage04_eqi_asset_manifest.csv
```

字段：

```text
year
asset_id
export_description
export_status
scale
crs
model_type
simplified_model
notes
```

示例：

```text
2000,users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000,EQI_func_2000,submitted,30,EPSG:4326,unified_residual_model,false,
```

---

### 9. 统计年度 EQI

年度统计表必须在 Python 端生成，并保存到本地。

统计过程：

1. 在 Earth Engine 端对每年 EQI_func 按森林类型进行区域统计；
2. 使用 `reduceRegion` 或 `reduceRegions` 获取统计结果；
3. 使用 Python 将结果整理为 `pandas.DataFrame`；
4. 写出本地 CSV。

输出：

```text
outputs/tables/table_annual_eqi_stats.csv
```

字段：

```text
year
forest_type
EQI_mean
EQI_median
EQI_std
EQI_q25
EQI_q75
valid_pixel_count
valid_area_km2
```

森林类型字段统一为：

```text
all_forest
natural_forest
plantation_forest
rubber_forest
other_plantation
```

其中：

* 如果没有橡胶林分类，则不输出 `rubber_forest` 和 `other_plantation`；
* 如果森林类型图只有天然林 / 人工林，则仅输出 `all_forest`、`natural_forest`、`plantation_forest`。

---

### 10. 输出图件

根据本地统计表生成时间序列图：

```text
outputs/figures/fig03_eqi_timeseries_by_forest_type.png
```

内容：

* 天然林 EQI_func 年际变化；
* 人工林 EQI_func 年际变化；
* 全岛森林 EQI_func 年际变化。

图件使用 Python 端 `pandas` 和 `matplotlib` 生成，不从 GEE 下载栅格。

---

## 检查标准

必须检查：

1. 2000—2024 年 FVC 和 NIRv Asset 是否全部存在；
2. DEM、Slope、Precip、Temp 是否能从 Earth Engine 正常生成；
3. 回归模型是否正常收敛；
4. 残差均值是否接近 0；
5. EQI_func 是否出现大范围异常值；
6. 天然林和人工林 EQI 分布是否合理；
7. 2000—2024 年 EQI_func 是否全部提交导出到 Asset；
8. 年度统计表是否在 Python 端生成并保存本地；
9. 本地是否只保存 CSV 表格、样本表和图件，不保存年度 EQI GeoTIFF；
10. 所有 EQI_func Asset 是否位于：

```text
users/gyf/forest_csc_alphaearth/stage04_eqi/
```

---

## 禁止事项

* 不允许每年单独拟合作为主模型；
* 不允许把 NIRv 原始值直接命名为生态质量；
* 不允许把 ForestType 放入主 EQI 校正模型，ForestType 应用于后续解释分析；
* 不允许本阶段做脱钩区分类；
* 不允许将 EQI_func 年度栅格下载为本地 GeoTIFF；
* 不允许在 `outputs/stage04_eqi/` 中保存大体量 `.tif` 文件；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许导出到 Google Drive 作为主方案；
* 不允许将气候数据解释为真实 30 m 空间分辨率数据；
* 不允许在气候数据缺失时静默切换到简化模型，必须在日志中明确记录 `simplified_model = true`。


# Stage 5：FVC 与 EQI_func 趋势分析

## 目标

计算每个 30 m 森林像元 2000—2024 年 FVC 和 EQI_func 的变化趋势。

本阶段输入数据全部从 Earth Engine Asset 读取，不再读取本地 GeoTIFF。

本阶段输出中：

1. FVC 和 EQI_func 趋势栅格不下载到本地，统一导出到 Earth Engine Asset；
2. 趋势统计表、趋势 Asset 清单和必要检查表在 Python 端生成并保存到本地；
3. 图件在 Python 端生成并保存到本地；
4. 本阶段不得在 `outputs/stage05_trend/` 中保存大体量 `.tif` 文件。

---

## 输入数据

Stage 3 输出的 FVC 年度影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2024
```

Stage 4 输出的 EQI_func 年度影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000
...
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2024
```

Stage 1 输出的森林掩膜和森林类型图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

如果上述任一 Asset 不存在，Codex 必须停止，并在 `docs/progress_log.md` 中说明缺少的 Asset ID，不得改为读取本地 GeoTIFF，也不得编造数据继续执行。

---

## 允许创建或修改的文件

```text
gee/stage05_trend_analysis.py
src/trend_utils.py
src/io_utils.py
outputs/tables/table_trend_stats_by_forest_type.csv
outputs/tables/table_stage05_trend_asset_manifest.csv
outputs/tables/table_stage05_trend_checks.csv
outputs/figures/fig04_fvc_trend_map.png
outputs/figures/fig05_eqi_trend_map.png
docs/progress_log.md
```

本阶段不再创建本地 GeoTIFF：

```text
outputs/stage05_trend/FVC_SenSlope_30m.tif
outputs/stage05_trend/FVC_pvalue_30m.tif
outputs/stage05_trend/EQI_SenSlope_30m.tif
outputs/stage05_trend/EQI_pvalue_30m.tif
```

趋势栅格统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_pvalue_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_pvalue_30m
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage05_trend_analysis.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  indices_asset_root: users/gyf/forest_csc_alphaearth/stage03_indices
  eqi_asset_root: users/gyf/forest_csc_alphaearth/stage04_eqi
  trend_asset_root: users/gyf/forest_csc_alphaearth/stage05_trend
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_mask = (
    ee.Image(config["gee_assets"]["forest_mask_asset"])
    .eq(1)
    .selfMask()
)

forest_type = ee.Image(config["gee_assets"]["forest_type_asset"])
```

年度 FVC 和 EQI_func 按年份循环读取：

```python
fvc_asset_id = (
    f"{config['gee_assets']['indices_asset_root']}/"
    f"FVC_{year}"
)

eqi_asset_id = (
    f"{config['gee_assets']['eqi_asset_root']}/"
    f"EQI_func_{year}"
)

fvc = ee.Image(fvc_asset_id).select("FVC")
eqi = ee.Image(eqi_asset_id).select("EQI_func")
```

---

### 3. 构建 Earth Engine 端时间序列 ImageCollection

本阶段不在本地构建：

```text
FVC_stack_2000_2024.tif
EQI_stack_2000_2024.tif
```

而是在 Earth Engine 端构建带年份属性的 `ImageCollection`。

FVC 时间序列：

```python
def build_fvc_image(year):
    year = ee.Number(year).toInt()
    image = (
        ee.Image(
            ee.String(config["gee_assets"]["indices_asset_root"])
            .cat("/FVC_")
            .cat(year.format())
        )
        .select("FVC")
        .rename("value")
        .updateMask(forest_mask)
        .set("year", year)
        .set("system:time_start", ee.Date.fromYMD(year, 1, 1).millis())
    )
    time = ee.Image.constant(year).rename("year").toFloat()
    return time.addBands(image).toFloat()

years = ee.List.sequence(
    config["project"]["start_year"],
    config["project"]["end_year"]
)

fvc_ts = ee.ImageCollection(years.map(build_fvc_image))
```

EQI_func 时间序列同理构建：

```python
def build_eqi_image(year):
    year = ee.Number(year).toInt()
    image = (
        ee.Image(
            ee.String(config["gee_assets"]["eqi_asset_root"])
            .cat("/EQI_func_")
            .cat(year.format())
        )
        .select("EQI_func")
        .rename("value")
        .updateMask(forest_mask)
        .set("year", year)
        .set("system:time_start", ee.Date.fromYMD(year, 1, 1).millis())
    )
    time = ee.Image.constant(year).rename("year").toFloat()
    return time.addBands(image).toFloat()

eqi_ts = ee.ImageCollection(years.map(build_eqi_image))
```

---

### 4. 计算 Sen’s slope

在 Earth Engine 端对每个像元计算 Sen’s slope。

```python
fvc_sens = (
    fvc_ts.select(["year", "value"])
    .reduce(ee.Reducer.sensSlope())
)

fvc_slope = (
    fvc_sens.select("slope")
    .rename("FVC_SenSlope")
    .updateMask(forest_mask)
    .clip(hainan)
)

eqi_sens = (
    eqi_ts.select(["year", "value"])
    .reduce(ee.Reducer.sensSlope())
)

eqi_slope = (
    eqi_sens.select("slope")
    .rename("EQI_SenSlope")
    .updateMask(forest_mask)
    .clip(hainan)
)
```

说明：

* 主结果必须使用 Sen’s slope；
* 不允许使用普通线性回归 slope 替代 Sen’s slope 作为主结果；
* 时间变量使用年份数值；
* 输出 slope 的单位分别为 FVC/year 和 EQI/year。

---

### 5. 计算 Mann-Kendall 显著性

计算：

```text
FVC_pvalue
EQI_pvalue
```

优先在 Earth Engine 端实现 Mann-Kendall 显著性检验。

如果直接计算 30 m 全岛逐像元 Mann-Kendall p value 计算量过大，可采用以下策略之一，但必须在日志中说明：

```text
方案 A：Earth Engine 端分块计算；
方案 B：Earth Engine 端先计算 Kendall tau，再近似计算 p value；
方案 C：仅在森林区掩膜内计算，避免非森林区参与；
方案 D：导出 Sen’s slope 主结果，p value 通过分块任务单独导出。
```

最终必须输出：

```text
FVC_pvalue
EQI_pvalue
```

不得忽略显著性结果。

p value 栅格要求：

```text
取值范围必须在 0—1；
无效区必须被掩膜；
波段名必须分别为 FVC_pvalue 和 EQI_pvalue。
```

---

### 6. 输出趋势栅格到 Earth Engine Asset

本阶段趋势栅格不保存为本地 `.tif`，统一导出到 Earth Engine Asset。

导出路径：

```text
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_pvalue_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_pvalue_30m
```

Python 端导出示例：

```python
def export_image_to_asset(image, asset_id, description, hainan):
    task = ee.batch.Export.image.toAsset(
        image=image.toFloat(),
        description=description,
        assetId=asset_id,
        region=hainan.geometry(),
        scale=30,
        crs="EPSG:4326",
        maxPixels=1e13
    )
    task.start()
    return task
```

示例：

```python
trend_root = config["gee_assets"]["trend_asset_root"]

export_image_to_asset(
    fvc_slope,
    f"{trend_root}/FVC_SenSlope_30m",
    "FVC_SenSlope_30m",
    hainan
)

export_image_to_asset(
    fvc_pvalue,
    f"{trend_root}/FVC_pvalue_30m",
    "FVC_pvalue_30m",
    hainan
)

export_image_to_asset(
    eqi_slope,
    f"{trend_root}/EQI_SenSlope_30m",
    "EQI_SenSlope_30m",
    hainan
)

export_image_to_asset(
    eqi_pvalue,
    f"{trend_root}/EQI_pvalue_30m",
    "EQI_pvalue_30m",
    hainan
)
```

导出影像属性必须写入：

```text
variable
method
start_year
end_year
scale
project
```

例如：

```python
fvc_slope = fvc_slope.set({
    "variable": "FVC",
    "method": "Sen slope",
    "start_year": 2000,
    "end_year": 2024,
    "scale": 30,
    "project": "hainan_forest_greening_quality"
})
```

---

### 7. 输出趋势 Asset 清单

本地输出：

```text
outputs/tables/table_stage05_trend_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
variable
metric
export_description
export_status
scale
crs
notes
```

示例：

```text
FVC_SenSlope_30m,users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m,FVC,SenSlope,FVC_SenSlope_30m,submitted,30,EPSG:4326,
FVC_pvalue_30m,users/gyf/forest_csc_alphaearth/stage05_trend/FVC_pvalue_30m,FVC,pvalue,FVC_pvalue_30m,submitted,30,EPSG:4326,
EQI_SenSlope_30m,users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m,EQI_func,SenSlope,EQI_SenSlope_30m,submitted,30,EPSG:4326,
EQI_pvalue_30m,users/gyf/forest_csc_alphaearth/stage05_trend/EQI_pvalue_30m,EQI_func,pvalue,EQI_pvalue_30m,submitted,30,EPSG:4326,
```

---

### 8. 输出统计表

趋势统计表必须在 Python 端生成，并存入本地。

统计过程：

1. 在 Earth Engine 端读取趋势结果影像；
2. 按森林类型进行区域统计；
3. 使用 `reduceRegion` 或 `reduceRegions` 获取统计结果；
4. 使用 Python 将结果整理为 `pandas.DataFrame`；
5. 写出本地 CSV。

输出：

```text
outputs/tables/table_trend_stats_by_forest_type.csv
```

字段：

```text
forest_type
FVC_slope_mean
FVC_slope_median
EQI_slope_mean
EQI_slope_median
FVC_positive_area_km2
FVC_negative_area_km2
EQI_positive_area_km2
EQI_negative_area_km2
FVC_significant_positive_area_km2
FVC_significant_negative_area_km2
EQI_significant_positive_area_km2
EQI_significant_negative_area_km2
```

森林类型字段统一为：

```text
all_forest
natural_forest
plantation_forest
rubber_forest
other_plantation
```

其中：

* 如果没有橡胶林分类，则不输出 `rubber_forest` 和 `other_plantation`；
* 如果森林类型图只有天然林 / 人工林，则仅输出 `all_forest`、`natural_forest`、`plantation_forest`。

---

### 9. 输出趋势检查表

本地输出：

```text
outputs/tables/table_stage05_trend_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
FVC_SenSlope 是否存在正负值
EQI_SenSlope 是否存在正负值
FVC_pvalue 是否在 0—1
EQI_pvalue 是否在 0—1
FVC 有效森林像元面积
EQI 有效森林像元面积
趋势结果是否只覆盖森林区
```

---

### 10. 输出图件

输出：

```text
outputs/figures/fig04_fvc_trend_map.png
outputs/figures/fig05_eqi_trend_map.png
```

图件可通过以下方式生成：

1. 从 Earth Engine 端生成缩略图或低分辨率预览图；
2. 或从 Earth Engine 端按较粗尺度导出小尺寸预览图；
3. 或使用本地统计和抽样结果绘制趋势空间示意图。

要求：

* 图件仅用于论文初步检查和结果展示；
* 不得为了制图而下载 30 m 全分辨率趋势 GeoTIFF；
* 最终 30 m 趋势栅格以 Earth Engine Asset 为准。

---

## 检查标准

必须检查：

1. 2000—2024 年 FVC Asset 是否全部存在；
2. 2000—2024 年 EQI_func Asset 是否全部存在；
3. FVC_SenSlope 是否有合理正负分布；
4. EQI_SenSlope 是否不是全 0；
5. p value 是否在 0—1；
6. 天然林和人工林趋势统计是否正常；
7. 趋势图是否与海南森林空间格局一致；
8. 趋势栅格是否全部导出到 Earth Engine Asset；
9. 本地是否只保存 CSV 表格和图件，不保存趋势 GeoTIFF；
10. 所有趋势 Asset 是否位于：

```text
users/gyf/forest_csc_alphaearth/stage05_trend/
```

---

## 禁止事项

* 不允许在未生成 EQI_func 的情况下直接用 NIRv 趋势替代；
* 不允许使用线性回归 slope 替代 Sen’s slope 作为主结果；
* 不允许忽略显著性结果；
* 不允许在本阶段生成脱钩分类图；
* 不允许将趋势栅格下载为本地 GeoTIFF；
* 不允许在 `outputs/stage05_trend/` 中保存大体量 `.tif` 文件；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许导出到 Google Drive 作为主方案；
* 不允许把本阶段生成的趋势 Asset 路径写错到其他阶段目录；
* 不允许为了降低计算量而改变主分析分辨率，除非在稳健性阶段另行说明。


# Stage 6：绿量—生态质量脱钩区识别

## 目标

识别 FVC 增加但 EQI_func 下降的“量增质减区”，并统计其在天然林和人工林中的分布。

本阶段输入数据全部从 Earth Engine Asset 读取，不再读取本地 GeoTIFF。

本阶段输出中：

1. 脱钩分类栅格不下载到本地，统一导出到 Earth Engine Asset；
2. 显著性筛选版本和无显著性筛选版本都必须导出到 Earth Engine Asset；
3. 面积统计表、森林类型统计表、Asset 清单和检查表在 Python 端生成并保存到本地；
4. 图件在 Python 端生成并保存到本地；
5. 本阶段不得在 `outputs/stage06_decoupling/` 中保存大体量 `.tif` 文件。

---

## 输入数据

Stage 5 输出的趋势结果，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_pvalue_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_pvalue_30m
```

Stage 1 输出的森林掩膜和森林类型图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

如果上述任一 Asset 不存在，Codex 必须停止，并在 `docs/progress_log.md` 中说明缺少的 Asset ID，不得改为读取本地 GeoTIFF，也不得编造数据继续执行。

---

## 允许创建或修改的文件

```text
gee/stage06_decoupling.py
src/stats_utils.py
src/io_utils.py
outputs/tables/table_decoupling_area.csv
outputs/tables/table_decoupling_by_forest_type.csv
outputs/tables/table_stage06_decoupling_asset_manifest.csv
outputs/tables/table_stage06_decoupling_checks.csv
outputs/figures/fig06_decoupling_map.png
outputs/figures/fig07_decoupling_by_forest_type_barplot.png
docs/progress_log.md
```

本阶段不再创建本地 GeoTIFF：

```text
outputs/stage06_decoupling/DecouplingType_30m.tif
outputs/stage06_decoupling/DecouplingType_30m_no_pfilter.tif
```

脱钩分类栅格统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m
users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m_no_pfilter
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage06_decoupling.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  trend_asset_root: users/gyf/forest_csc_alphaearth/stage05_trend
  decoupling_asset_root: users/gyf/forest_csc_alphaearth/stage06_decoupling
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_mask = (
    ee.Image(config["gee_assets"]["forest_mask_asset"])
    .eq(1)
    .selfMask()
)

forest_type = ee.Image(config["gee_assets"]["forest_type_asset"])

trend_root = config["gee_assets"]["trend_asset_root"]

fvc_slope = ee.Image(f"{trend_root}/FVC_SenSlope_30m").select("FVC_SenSlope")
fvc_pvalue = ee.Image(f"{trend_root}/FVC_pvalue_30m").select("FVC_pvalue")
eqi_slope = ee.Image(f"{trend_root}/EQI_SenSlope_30m").select("EQI_SenSlope")
eqi_pvalue = ee.Image(f"{trend_root}/EQI_pvalue_30m").select("EQI_pvalue")
```

---

### 3. 设置分类规则

主分类规则：

```text
0 = 非森林、无效区或趋势不显著
1 = 协同改善区：FVC_slope > 0 且 EQI_slope > 0
2 = 量增质减区：FVC_slope > 0 且 EQI_slope < 0
3 = 量减质增区：FVC_slope < 0 且 EQI_slope > 0
4 = 双退化区：FVC_slope < 0 且 EQI_slope < 0
```

显著性主方案：

```text
FVC_pvalue < 0.05
EQI_pvalue < 0.05
```

如果显著性筛选后有效面积过小，仍必须同时输出无显著性版本：

```text
DecouplingType_30m_no_pfilter
```

---

### 4. 生成无显著性筛选版本

无显著性版本只根据 FVC 和 EQI_func 的 Sen’s slope 正负号分类。

Python 端 Earth Engine 示例：

```python
decoupling_no_pfilter = (
    ee.Image(0)
    .where(fvc_slope.gt(0).And(eqi_slope.gt(0)), 1)
    .where(fvc_slope.gt(0).And(eqi_slope.lt(0)), 2)
    .where(fvc_slope.lt(0).And(eqi_slope.gt(0)), 3)
    .where(fvc_slope.lt(0).And(eqi_slope.lt(0)), 4)
    .updateMask(forest_mask)
    .rename("DecouplingType")
    .clip(hainan)
)
```

---

### 5. 生成显著性筛选版本

显著性筛选掩膜：

```python
sig_mask = (
    fvc_pvalue.lt(0.05)
    .And(eqi_pvalue.lt(0.05))
    .And(forest_mask)
)
```

显著性筛选版本：

```python
decoupling_sig = (
    ee.Image(0)
    .where(fvc_slope.gt(0).And(eqi_slope.gt(0)).And(sig_mask), 1)
    .where(fvc_slope.gt(0).And(eqi_slope.lt(0)).And(sig_mask), 2)
    .where(fvc_slope.lt(0).And(eqi_slope.gt(0)).And(sig_mask), 3)
    .where(fvc_slope.lt(0).And(eqi_slope.lt(0)).And(sig_mask), 4)
    .updateMask(forest_mask)
    .rename("DecouplingType")
    .clip(hainan)
)
```

说明：

* 显著性版本中，趋势不显著的森林像元编码为 0；
* 非森林区必须被掩膜；
* 无显著性版本用于探索对比，不作为主结论。

---

### 6. 导出脱钩分类栅格到 Earth Engine Asset

本阶段脱钩分类栅格不保存为本地 `.tif`，统一导出到 Earth Engine Asset。

导出路径：

```text
users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m
users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m_no_pfilter
```

Python 端导出示例：

```python
def export_image_to_asset(image, asset_id, description, hainan):
    task = ee.batch.Export.image.toAsset(
        image=image.toByte(),
        description=description,
        assetId=asset_id,
        region=hainan.geometry(),
        scale=30,
        crs="EPSG:4326",
        maxPixels=1e13
    )
    task.start()
    return task
```

示例：

```python
decoupling_root = config["gee_assets"]["decoupling_asset_root"]

export_image_to_asset(
    decoupling_sig,
    f"{decoupling_root}/DecouplingType_30m",
    "DecouplingType_30m",
    hainan
)

export_image_to_asset(
    decoupling_no_pfilter,
    f"{decoupling_root}/DecouplingType_30m_no_pfilter",
    "DecouplingType_30m_no_pfilter",
    hainan
)
```

导出影像属性必须写入：

```text
classification_method
pvalue_filter
fvc_pvalue_threshold
eqi_pvalue_threshold
scale
project
```

示例：

```python
decoupling_sig = decoupling_sig.set({
    "classification_method": "FVC_EQI_slope_quadrant",
    "pvalue_filter": "FVC_pvalue_lt_0.05_and_EQI_pvalue_lt_0.05",
    "fvc_pvalue_threshold": 0.05,
    "eqi_pvalue_threshold": 0.05,
    "scale": 30,
    "project": "hainan_forest_greening_quality"
})

decoupling_no_pfilter = decoupling_no_pfilter.set({
    "classification_method": "FVC_EQI_slope_quadrant",
    "pvalue_filter": "none",
    "scale": 30,
    "project": "hainan_forest_greening_quality"
})
```

---

### 7. 输出脱钩 Asset 清单

本地输出：

```text
outputs/tables/table_stage06_decoupling_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
classification_method
pvalue_filter
export_description
export_status
scale
crs
notes
```

示例：

```text
DecouplingType_30m,users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m,FVC_EQI_slope_quadrant,FVC_pvalue<0.05 and EQI_pvalue<0.05,DecouplingType_30m,submitted,30,EPSG:4326,
DecouplingType_30m_no_pfilter,users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m_no_pfilter,FVC_EQI_slope_quadrant,none,DecouplingType_30m_no_pfilter,submitted,30,EPSG:4326,
```

---

### 8. 统计面积

面积统计表必须在 Python 端生成，并保存到本地。

统计过程：

1. 在 Earth Engine 端读取脱钩分类结果；
2. 使用 `ee.Image.pixelArea()` 计算各脱钩类型面积；
3. 通过 `reduceRegion` 或 `reduceRegions` 获取面积结果；
4. 使用 Python 将结果整理为 `pandas.DataFrame`；
5. 写出本地 CSV。

输出：

```text
outputs/tables/table_decoupling_area.csv
```

字段：

```text
version
decoupling_type
decoupling_name
area_km2
percentage_of_forest
```

其中 `version` 取值：

```text
pfilter
no_pfilter
```

脱钩类型名称：

```text
0 = 非森林、无效区或趋势不显著
1 = 协同改善区
2 = 量增质减区
3 = 量减质增区
4 = 双退化区
```

重点检查：

```text
量增质减区面积
量增质减区占森林面积比例
```

---

### 9. 按森林类型统计

森林类型统计表必须在 Python 端生成，并保存到本地。

输出：

```text
outputs/tables/table_decoupling_by_forest_type.csv
```

字段：

```text
version
decoupling_type
decoupling_name
forest_type
area_km2
percentage_within_decoupling_type
percentage_within_forest_type
```

森林类型字段统一为：

```text
all_forest
natural_forest
plantation_forest
rubber_forest
other_plantation
```

其中：

* 如果没有橡胶林分类，则不输出 `rubber_forest` 和 `other_plantation`；
* 如果森林类型图只有天然林 / 人工林，则仅输出 `all_forest`、`natural_forest`、`plantation_forest`。

重点关注：

```text
量增质减区中的人工林面积和占比
```

---

### 10. 输出检查表

本地输出：

```text
outputs/tables/table_stage06_decoupling_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
显著性版本分类值是否仅为 0、1、2、3、4
无显著性版本分类值是否仅为 0、1、2、3、4
量增质减区是否有有效面积
量增质减区是否与人工林空间有重叠
显著性版本和无显著性版本是否都已提交导出
面积统计是否与 ForestMask 总面积一致
本地是否未保存大体量 GeoTIFF
```

---

### 11. 输出图件

输出：

```text
outputs/figures/fig06_decoupling_map.png
outputs/figures/fig07_decoupling_by_forest_type_barplot.png
```

图件生成要求：

1. `fig06_decoupling_map.png` 可使用 Earth Engine 端缩略图、低分辨率预览图或抽样结果生成；
2. 不得为了制图下载 30 m 全分辨率脱钩 GeoTIFF；
3. `fig07_decoupling_by_forest_type_barplot.png` 必须基于本地 CSV 统计表生成；
4. 图例必须明确标注 0、1、2、3、4 各类别含义；
5. 主图优先展示显著性筛选版本，无显著性版本作为补充检查图或日志说明。

---

## 检查标准

必须检查：

1. 输入的 FVC 和 EQI_func 趋势 Asset 是否全部存在；
2. 输入的森林掩膜和森林类型 Asset 是否存在；
3. 分类值是否仅为 0、1、2、3、4；
4. 量增质减区是否有有效面积；
5. 量增质减区是否与人工林空间有重叠；
6. 显著性版本和无显著性版本是否都导出到 Earth Engine Asset；
7. 面积统计是否与 ForestMask 总面积一致；
8. 本地是否只保存 CSV 表格和图件，不保存脱钩分类 GeoTIFF；
9. 所有脱钩分类 Asset 是否位于：

```text
users/gyf/forest_csc_alphaearth/stage06_decoupling/
```

---

## 禁止事项

* 不允许把 NIRv_slope 直接用于主脱钩分类；
* 不允许只输出图不输出栅格；
* 不允许只统计全岛，不按天然林 / 人工林统计；
* 不允许删除无显著性版本，必须保留用于探索对比；
* 不允许将脱钩分类栅格下载为本地 GeoTIFF；
* 不允许在 `outputs/stage06_decoupling/` 中保存大体量 `.tif` 文件；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许导出到 Google Drive 作为主方案；
* 不允许把本阶段生成的脱钩 Asset 路径写错到其他阶段目录；
* 不允许为了让面积统计看起来合理而手动修改分类结果。

# Stage 7：GEDI FHD 训练标签提取

## 目标

从 GEDI 数据中提取 2019—2024 年高质量森林垂直结构训练标签，为 30 m FHD 外推建模准备样本。

本阶段只提取与森林垂直结构复杂性（CSC）相关的 GEDI 特征，不提取 DEM、Slope 等地形变量。

本阶段输出两份训练样点：

1. 本地 CSV 文件，用于 Python 端模型训练和检查；
2. Earth Engine Table Asset，用于后续在 GEE 端与 AlphaEarth 或多源遥感特征进行空间采样。

---

## 输入数据

Earth Engine 数据：

```text
LARSE/GEDI/GEDI02_B_002
或 LARSE/GEDI/GEDI02_B_002_MONTHLY
```

如需提取 RH 指标，可同时使用：

```text
LARSE/GEDI/GEDI02_A_002
或 LARSE/GEDI/GEDI02_A_002_MONTHLY
```

辅助数据仅使用：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

本阶段不使用、不提取：

```text
DEM
Slope
TPI
Precip
Temp
```

---

## 允许创建或修改的文件

```text
gee/stage07_export_gedi_samples.py
src/io_utils.py
outputs/stage07_gedi/GEDI_CSC_labels_2019_2024.csv
outputs/tables/table_gedi_label_summary.csv
outputs/tables/table_stage07_gedi_asset_manifest.csv
outputs/tables/table_stage07_gedi_checks.csv
outputs/figures/fig08_gedi_sample_distribution.png
docs/progress_log.md
```

训练样点同时导出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage07_gedi/GEDI_CSC_labels_2019_2024
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage07_export_gedi_samples.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  gedi_asset_root: users/gyf/forest_csc_alphaearth/stage07_gedi
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_mask = (
    ee.Image(config["gee_assets"]["forest_mask_asset"])
    .eq(1)
    .selfMask()
)

forest_type = ee.Image(config["gee_assets"]["forest_type_asset"])
```

如果森林掩膜或森林类型 Asset 不存在，Codex 必须停止，并在 `docs/progress_log.md` 中说明缺少的 Asset ID，不得改为读取本地 GeoTIFF。

---

### 3. 提取 GEDI L2B 数据

筛选时间：

```text
2019-01-01 至 2024-12-31
```

空间范围：

```text
filterBounds(hainan)
```

优先使用 GEDI L2B：

```text
LARSE/GEDI/GEDI02_B_002_MONTHLY
```

Python 端 Earth Engine 示例：

```python
gedi_l2b = (
    ee.ImageCollection("LARSE/GEDI/GEDI02_B_002_MONTHLY")
    .filterDate("2019-01-01", "2025-01-01")
    .filterBounds(hainan)
)
```

如果需要 RH98、RH25、RH98_RH25 等高度结构变量，可同时读取 GEDI L2A：

```python
gedi_l2a = (
    ee.ImageCollection("LARSE/GEDI/GEDI02_A_002_MONTHLY")
    .filterDate("2019-01-01", "2025-01-01")
    .filterBounds(hainan)
)
```

---

### 4. 质量控制

保留高质量 GEDI 样本：

```text
quality_flag = 1
degrade_flag = 0
sensitivity >= 0.95
ForestMask = 1
```

本阶段不使用：

```text
Slope < 30°
```

原因：

```text
本阶段仅提取 CSC / 垂直结构相关训练标签，不引入 DEM、Slope 等地形变量，避免 Stage 7 与后续地形控制变量混杂。
```

质量控制示例：

```python
def mask_gedi_l2b(img):
    qa = img.select("quality_flag").eq(1)
    degrade = img.select("degrade_flag").eq(0)
    sensitivity = img.select("sensitivity").gte(0.95)

    return (
        img.updateMask(qa)
        .updateMask(degrade)
        .updateMask(sensitivity)
        .updateMask(forest_mask)
        .clip(hainan)
    )

gedi_l2b_clean = gedi_l2b.map(mask_gedi_l2b)
```

---

### 5. 获取 FHD

如果 GEDI L2B 数据中存在：

```text
fhd_normal
```

则直接使用：

```text
FHD = fhd_normal
```

如果没有 `fhd_normal`，则基于 PAVD 垂直剖面计算：

```text
p_i = PAVD_i / sum(PAVD_i)
FHD = -sum(p_i * ln(p_i))
```

输出字段统一命名为：

```text
FHD
```

---

### 6. 提取 CSC 相关结构特征

本阶段只保留 CSC / 垂直结构相关特征。

必须提取：

```text
FHD
cover
ForestType
year
longitude
latitude
```

如果 GEDI 数据中可获得 RH 指标，则同时提取：

```text
RH25
RH50
RH75
RH98
RH98_RH25
```

其中：

```text
RH98_RH25 = RH98 - RH25
```

可选提取：

```text
pai
pai_z
cover_z
```

但必须在 `docs/progress_log.md` 中说明具体使用了哪些 GEDI 字段。

本阶段不提取：

```text
DEM
Slope
TPI
Precip
Temp
AGBD
```

说明：

* `AGBD` 属于生物量 / 碳储量变量，不作为本阶段 CSC 训练标签主字段；
* 如果后续需要 AGBD，可单独设计补充阶段，不混入 FHD 标签提取阶段。

---

### 7. 异常值剔除

剔除：

```text
FHD <= 0
cover < 0
cover > 1
RH98 <= 0
RH98 > 80
RH25 < 0
RH98_RH25 < 0
```

说明：

* 如果未提取 RH 指标，则只执行 FHD 和 cover 的异常值剔除；
* 不得因为缺少 RH 指标而删除有效 FHD 样本；
* 所有异常值剔除规则必须写入 `docs/progress_log.md`。

---

### 8. 构建 GEDI 样点 FeatureCollection

每个样点必须包含字段：

```text
sample_id
longitude
latitude
year
FHD
cover
ForestType
```

如果 RH 指标可用，则增加：

```text
RH25
RH50
RH75
RH98
RH98_RH25
```

最终字段示例：

```text
sample_id
longitude
latitude
year
FHD
cover
RH25
RH50
RH75
RH98
RH98_RH25
ForestType
```

不得包含：

```text
DEM
Slope
TPI
Precip
Temp
AGBD
```

---

### 9. 输出本地训练样本 CSV

本地输出：

```text
outputs/stage07_gedi/GEDI_CSC_labels_2019_2024.csv
```

字段：

```text
sample_id
longitude
latitude
year
FHD
cover
RH25
RH50
RH75
RH98
RH98_RH25
ForestType
```

说明：

* 如果 RH 指标未成功提取，则 RH 字段可以为空或不输出；
* 但必须保留 `FHD`、`cover`、`ForestType`、`year`、`longitude`、`latitude`；
* 本地 CSV 用于 Python 端模型训练、统计检查和可视化。

---

### 10. 同步导出训练样点到 Earth Engine Table Asset

同时将同一份 GEDI CSC 训练样点导出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage07_gedi/GEDI_CSC_labels_2019_2024
```

Python 端导出示例：

```python
gedi_sample_asset_id = (
    "users/gyf/forest_csc_alphaearth/"
    "stage07_gedi/GEDI_CSC_labels_2019_2024"
)

task = ee.batch.Export.table.toAsset(
    collection=gedi_samples,
    description="GEDI_CSC_labels_2019_2024",
    assetId=gedi_sample_asset_id
)

task.start()
```

本地 CSV 与 Earth Engine Table Asset 必须来自同一个 `FeatureCollection`，不得分别生成两套不同样本。

---

### 11. 输出统计表

本地输出：

```text
outputs/tables/table_gedi_label_summary.csv
```

字段：

```text
year
forest_type
sample_count
FHD_mean
FHD_std
cover_mean
cover_std
RH98_mean
RH98_std
RH98_RH25_mean
RH98_RH25_std
```

说明：

* 如果 RH 指标不可用，则 RH 相关字段可以留空；
* 必须至少输出 FHD 和 cover 的年度统计；
* 必须按森林类型统计天然林和人工林样本数量。

---

### 12. 输出 Asset 清单

本地输出：

```text
outputs/tables/table_stage07_gedi_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
asset_type
export_description
export_status
feature_count
fields
notes
```

示例：

```text
GEDI_CSC_labels_2019_2024,users/gyf/forest_csc_alphaearth/stage07_gedi/GEDI_CSC_labels_2019_2024,table,GEDI_CSC_labels_2019_2024,submitted,,sample_id;longitude;latitude;year;FHD;cover;RH25;RH50;RH75;RH98;RH98_RH25;ForestType,
```

---

### 13. 输出检查表

本地输出：

```text
outputs/tables/table_stage07_gedi_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
GEDI 样本是否覆盖海南主要森林区域
天然林和人工林是否都有样本
FHD 值域是否合理
cover 是否在 0—1
RH98 是否没有大量异常值
每年样本数量是否足够
样本坐标是否正确
本地 CSV 是否已保存
Earth Engine Table Asset 是否已提交导出
是否未提取 DEM 和 Slope
是否未提取 AGBD
```

---

### 14. 输出图件

输出：

```text
outputs/figures/fig08_gedi_sample_distribution.png
```

图件内容：

* 海南边界；
* GEDI 样本点分布；
* 天然林样本点；
* 人工林样本点；
* 如有橡胶林分类，则单独显示橡胶林样本点。

图件可使用：

1. 本地 CSV 中的经纬度绘制；
2. 或 Earth Engine 端生成低分辨率预览图；
3. 不得下载任何 GEDI 栅格。

---

## 检查标准

必须检查：

1. GEDI 样本是否覆盖海南主要森林区域；
2. 天然林和人工林是否都有样本；
3. FHD 值域是否合理；
4. cover 是否位于合理范围；
5. RH98 是否没有大量异常值；
6. 每年样本数量是否足够；
7. 样本坐标是否正确；
8. 本地 CSV 是否成功生成；
9. Earth Engine Table Asset 是否提交导出；
10. 本阶段是否未提取 DEM、Slope、AGBD；
11. 输出字段是否只包含 CSC / 垂直结构相关特征和必要标签字段。

---

## 禁止事项

* 不允许把 GEDI footprint 直接栅格化成 30 m 连续图；
* 不允许跳过 GEDI 质量控制；
* 不允许只提取天然林样本或只提取人工林样本；
* 不允许把 AlphaEarth 数据采样写入本阶段；
* 不允许提取 DEM、Slope、TPI、Precip、Temp；
* 不允许提取 AGBD 作为本阶段主字段；
* 不允许在本阶段构建 FHD 外推模型；
* 不允许在本阶段生成 FHD 30 m 空间图；
* 不允许下载 GEDI 栅格到本地；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许本地 CSV 和 Earth Engine Table Asset 使用不同样本来源。

# Stage 8：AlphaEarth 特征采样与 FHD 模型训练

## 目标

优先使用 AlphaEarth 64 维 embedding 作为预测变量，训练 GEDI FHD 外推模型，并用空间交叉验证评估精度。

本阶段承接 Stage 7 的修改：

1. GEDI 训练标签来自 Stage 7 生成的 CSC 训练样点；
2. GEDI 训练标签同时存在本地 CSV 和 Earth Engine Table Asset；
3. AlphaEarth 特征采样优先在 Earth Engine 端完成；
4. AlphaEarth 采样结果同时保存为本地 CSV 和 Earth Engine Table Asset；
5. 模型训练、空间块划分、交叉验证和模型保存均在 Python 本地完成；
6. 本阶段只训练和评估模型，不生成最终 30 m FHD 空间图。

---

## 输入数据

Earth Engine 数据：

```text
GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
```

Stage 7 输出的 GEDI CSC 训练标签，本地 CSV：

```text
outputs/stage07_gedi/GEDI_CSC_labels_2019_2024.csv
```

Stage 7 输出的 GEDI CSC 训练标签，Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage07_gedi/GEDI_CSC_labels_2019_2024
```

说明：

* AlphaEarth 特征采样优先使用 Earth Engine Table Asset；
* 本地 CSV 主要用于训练前检查、字段核对和模型训练；
* 如果 Earth Engine Table Asset 不存在，Codex 必须停止并提示先完成 Stage 7 的 Table Asset 导出，不得仅凭本地 CSV 强行执行 AlphaEarth 采样。

---

## 允许创建或修改的文件

```text
gee/stage08_export_alphaearth_samples.py
scripts/stage08_train_fhd_models.py
src/model_utils.py
src/validation_utils.py
src/io_utils.py
outputs/tables/table_stage08_alphaearth_feature_qc.csv
outputs/tables/table_stage08_alphaearth_feature_correlation.csv
outputs/tables/table_stage08_alphaearth_feature_selection_cv.csv
outputs/tables/table_stage08_alphaearth_feature_set_comparison.csv
outputs/tables/table_stage08_selected_features_final.csv
outputs/stage08_fhd_model/model_alphaearth_only_features.txt
outputs/stage08_fhd_model/model_alphaearth_selected_features.txt
outputs/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples.csv
outputs/stage08_fhd_model/spatial_folds.csv
outputs/stage08_fhd_model/model_alphaearth_only.joblib
outputs/tables/table_fhd_model_alphaearth_cv.csv
outputs/tables/table_stage08_alphaearth_asset_manifest.csv
outputs/tables/table_stage08_alphaearth_sample_summary.csv
outputs/tables/table_stage08_alphaearth_checks.csv
docs/progress_log.md
```

AlphaEarth 采样结果同时导出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage08_export_alphaearth_samples.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/your_username/assets/Hainan_ROI
  gedi_csc_label_asset: users/gyf/forest_csc_alphaearth/stage07_gedi/GEDI_CSC_labels_2019_2024
  alphaearth_dataset: GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
  alphaearth_sample_asset: users/gyf/forest_csc_alphaearth/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

gedi_samples = ee.FeatureCollection(
    config["gee_assets"]["gedi_csc_label_asset"]
)
```

如果 `gedi_csc_label_asset` 不存在，必须停止，并在 `docs/progress_log.md` 中记录缺失 Asset ID。

---

### 3. 加载 AlphaEarth 年度数据

加载：

```text
GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
```

AlphaEarth 波段：

```text
A00, A01, ..., A63
```

Python 端示例：

```python
alphaearth = ee.ImageCollection(
    config["gee_assets"]["alphaearth_dataset"]
).filterBounds(hainan)

ae_bands = [f"A{i:02d}" for i in range(64)]
```

必须检查：

```text
A00—A63 是否全部存在；
AlphaEarth 年份是否覆盖 GEDI 样本年份；
样本 year 字段是否为整数年份。
```

---

### 4. 按 GEDI 样本年份匹配 AlphaEarth 年度影像

对每个 GEDI 样本，根据其 `year` 字段匹配对应年度的 AlphaEarth 影像。

原则：

```text
GEDI 样本 year = 2019 → AlphaEarth 2019 年度影像
GEDI 样本 year = 2020 → AlphaEarth 2020 年度影像
...
GEDI 样本 year = 2024 → AlphaEarth 2024 年度影像
```

如果 AlphaEarth 某一年影像不存在，必须停止并记录缺失年份，不得用相邻年份代替，除非在稳健性阶段另行说明。

---

### 5. AlphaEarth 聚合到 30 m

AlphaEarth 原始为 10 m，本项目统一到 30 m。

处理方式：

```text
对 A00—A63 做 30 m mean 聚合
```

Earth Engine 端可通过导出或采样时设置：

```text
scale = 30
```

如需显式聚合，可使用：

```python
alpha_30m = (
    alpha_img.select(ae_bands)
    .reduceResolution(
        reducer=ee.Reducer.mean(),
        maxPixels=1024
    )
    .reproject(
        crs="EPSG:4326",
        scale=30
    )
)
```

说明：

* 本阶段只进行点位采样，不生成 AlphaEarth 30 m 栅格；
* 不允许导出 AlphaEarth 64 维全岛年度栅格到本地；
* 不允许把 AlphaEarth embedding 直接解释为 FHD。

---

### 6. 在 GEDI 点位采样 AlphaEarth

为每个 GEDI 样本提取：

```text
A00
A01
...
A63
```

同时保留 Stage 7 中的标签字段：

```text
sample_id
longitude
latitude
year
FHD
cover
RH25
RH50
RH75
RH98
RH98_RH25
ForestType
```

如果 Stage 7 未成功提取 RH 指标，则保留：

```text
sample_id
longitude
latitude
year
FHD
cover
ForestType
```

输出字段必须包括：

```text
sample_id
longitude
latitude
year
FHD
cover
ForestType
A00
A01
...
A63
```

推荐按年份分组采样，避免一次性任务过大。

示例逻辑：

```python
def sample_alphaearth_by_year(year):
    year = ee.Number(year).toInt()

    year_samples = gedi_samples.filter(
        ee.Filter.eq("year", year)
    )

    alpha_img = (
        alphaearth
        .filter(ee.Filter.eq("year", year))
        .first()
        .select(ae_bands)
    )

    alpha_30m = (
        alpha_img
        .reduceResolution(
            reducer=ee.Reducer.mean(),
            maxPixels=1024
        )
        .reproject(crs="EPSG:4326", scale=30)
    )

    sampled = alpha_30m.sampleRegions(
        collection=year_samples,
        properties=[
            "sample_id",
            "longitude",
            "latitude",
            "year",
            "FHD",
            "cover",
            "RH25",
            "RH50",
            "RH75",
            "RH98",
            "RH98_RH25",
            "ForestType"
        ],
        scale=30,
        geometries=True
    )

    return sampled
```

如果部分 RH 字段不存在，脚本必须自动仅保留实际存在字段，不得因缺失 RH 字段导致整个阶段失败。

---

### 7. 输出 AlphaEarth 采样结果到 Earth Engine Table Asset

将采样后的 FeatureCollection 导出到：

```text
users/gyf/forest_csc_alphaearth/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples
```

Python 端示例：

```python
task = ee.batch.Export.table.toAsset(
    collection=alphaearth_samples,
    description="GEDI_CSC_AlphaEarth_samples",
    assetId=config["gee_assets"]["alphaearth_sample_asset"]
)

task.start()
```

本地输出 Asset 清单：

```text
outputs/tables/table_stage08_alphaearth_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
asset_type
export_description
export_status
feature_count
fields
notes
```

---

### 8. 输出 AlphaEarth 采样结果到本地 CSV

本地输出：

```text
outputs/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples.csv
```

说明：

* 本地 CSV 必须与 Earth Engine Table Asset 来自同一个采样结果；
* 如果采样结果数量较大，不建议使用单次 `getInfo()`；
* 可采用 Earth Engine 表格导出后再下载，或分年份分批获取；
* 最终必须在本地生成完整 CSV，用于 Python 端模型训练；
* 不得将采样结果仅保存在 GEE Asset 而不生成本地 CSV。

---

### 9. 输出 AlphaEarth 样本统计表

本地输出：

```text
outputs/tables/table_stage08_alphaearth_sample_summary.csv
```

字段：

```text
year
forest_type
sample_count
FHD_mean
FHD_std
cover_mean
RH98_mean
valid_alphaearth_sample_count
missing_alphaearth_sample_count
```

如果 RH 指标不存在，则 RH 字段可留空或不输出。

---

### 10. 构建空间块

使用本地 CSV，根据样本经纬度生成 20 km × 20 km 空间块。

字段：

```text
sample_id
longitude
latitude
block_id
fold_id
```

将空间块分为 5 折。

要求：

```text
同一 block_id 内的样本必须分配到同一 fold_id；
fold_id 取值为 1—5；
固定 random_seed = 2026；
不得使用普通随机划分作为主验证。
```

输出：

```text
outputs/stage08_fhd_model/spatial_folds.csv
```

---

### 11. AlphaEarth 特征质控与特征筛选

在训练 AlphaEarth-only 模型之前，必须对 A00—A63 进行特征质控和可选特征筛选。

需要注意：

```text
AlphaEarth 64 维 embedding 是经过模型学习得到的潜在特征，不是普通光谱波段。
因此不应简单按物理意义删除某些维度，也不应在完整样本上先筛选特征再做交叉验证。
```

本阶段必须至少执行基础特征质控，并输出特征检查结果。

#### 11.1 基础特征质控

对 A00—A63 检查：

```text
缺失值比例
常数列或近似常数列
异常极值
特征分布
特征间相关性
```

删除规则：

```text
缺失率 > 20% 的特征删除；
标准差接近 0 的特征删除；
明显异常且无法解释的特征删除；
```

输出：

```text
outputs/tables/table_stage08_alphaearth_feature_qc.csv
```

字段：

```text
feature
missing_rate
mean
std
min
max
is_constant
drop_by_qc
drop_reason
```

#### 11.2 相关性冗余检查

计算 A00—A63 两两相关系数。

如果存在高度相关特征：

```text
|r| >= 0.95
```

则记录为冗余特征对。

但由于 AlphaEarth embedding 的各维度可能共同编码复杂语义，不要求强制删除所有高相关特征。是否删除必须通过交叉验证结果判断。

输出：

```text
outputs/tables/table_stage08_alphaearth_feature_correlation.csv
```

字段：

```text
feature_1
feature_2
correlation
abs_correlation
highly_correlated
```

#### 11.3 嵌套式特征筛选

特征筛选必须在空间交叉验证内部完成，不能在全部样本上一次性筛选后再做 CV。

每一折执行：

```text
训练集 = fold_id != 当前折
验证集 = fold_id == 当前折
```

在训练集内计算特征重要性，并选择特征。

允许使用以下方法：

```text
Random Forest permutation importance
Random Forest impurity importance
Recursive feature elimination
SelectKBest based on training fold only
```

推荐主方案：

```text
基于 Random Forest permutation importance 的 Top-K 特征筛选
```

候选 K 值：

```text
K = 10
K = 20
K = 30
K = 40
K = 64
```

其中：

```text
K = 64
```

表示使用全部 AlphaEarth 特征，作为基准模型。

输出：

```text
outputs/tables/table_stage08_alphaearth_feature_selection_cv.csv
```

字段：

```text
fold
k_features
selected_features
R2
RMSE
MAE
Bias
Spearman_r
sample_count
```

#### 11.4 全特征模型与筛选模型比较

必须比较两类模型：

```text
AlphaEarth_all64：使用 A00—A63 全部特征
AlphaEarth_selected：使用嵌套交叉验证筛选出的特征
```

输出：

```text
outputs/tables/table_stage08_alphaearth_feature_set_comparison.csv
```

字段：

```text
model_name
feature_selection_method
feature_count
R2_mean
R2_std
RMSE_mean
MAE_mean
Bias_mean
Spearman_mean
selected_as_stage08_model
reason
```

选择规则：

```text
如果筛选模型 R2 比 all64 提高 ≥ 0.03，且 RMSE 更低，则选择筛选模型；
如果筛选模型与 all64 精度差异 < 0.03，则优先选择 all64 模型；
如果筛选模型在天然林或人工林上明显失衡，则不选择筛选模型；
如果筛选结果在不同 fold 中极不稳定，则不选择筛选模型作为主模型。
```

#### 11.5 保存最终特征列表

如果最终选择 all64 模型，保存：

```text
outputs/stage08_fhd_model/model_alphaearth_only_features.txt
```

内容为：

```text
A00
A01
...
A63
```

如果最终选择筛选模型，保存：

```text
outputs/stage08_fhd_model/model_alphaearth_selected_features.txt
```

内容为最终选定的特征列表。

同时输出：

```text
outputs/tables/table_stage08_selected_features_final.csv
```

字段：

```text
feature
selection_frequency
mean_importance
selected_final
notes
```

#### 11.6 防止数据泄漏

禁止：

```text
在全部样本上先计算特征重要性，再用筛选后的特征做空间交叉验证；
在全部样本上先删除低重要性特征，再报告 CV 精度；
用验证集参与特征筛选；
根据测试折表现反复调整特征列表；
只报告筛选后模型，不报告 all64 基准模型。
```

必须在 `docs/progress_log.md` 中记录：

```text
feature_selection_done = true / false
feature_selection_method = ...
all64_model_reported = true
data_leakage_checked = true
```


### 12. 训练 AlphaEarth-only 模型
先训练 AlphaEarth_all64 基准模型，再训练 AlphaEarth_selected 筛选模型。最终 Stage 8 模型由空间交叉验证结果决定，不得只保留筛选后模型。

模型：

```text
FHD ~ A00 + A01 + ... + A63
```

优先使用：

```text
RandomForestRegressor
```

建议初始参数：

```text
n_estimators = 500
random_state = 2026
max_features = "sqrt"
min_samples_leaf = 2
n_jobs = -1
```

可选比较：

```text
XGBoostRegressor
LightGBMRegressor
```

但本阶段主模型必须至少包含 RandomForestRegressor。

训练输入：

```text
outputs/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples.csv
outputs/stage08_fhd_model/spatial_folds.csv
```

不得使用：

```text
DEM
Slope
TPI
Precip
Temp
AGBD
```

作为 AlphaEarth-only 模型特征。

---

### 13. 空间交叉验证

每折输出：

```text
fold
R2
RMSE
MAE
Bias
Spearman_r
sample_count
natural_forest_R2
plantation_forest_R2
natural_forest_RMSE
plantation_forest_RMSE
```

输出：

```text
outputs/tables/table_fhd_model_alphaearth_cv.csv
```

要求：

* 主结果必须报告空间交叉验证；
* 不允许只报告训练集精度；
* 必须比较天然林和人工林分组精度；
* 如果人工林样本量过少，应在表格中标记 `insufficient_samples`，不得隐瞒。

---

### 14. 保存模型

如果 AlphaEarth-only 模型完成训练，保存：

```text
outputs/stage08_fhd_model/model_alphaearth_only.joblib
```

同时建议保存特征列表：

```text
outputs/stage08_fhd_model/model_alphaearth_only_features.txt
```

特征列表必须为：

```text
A00
A01
...
A63
```

不得包含 DEM、Slope、AGBD 等非 AlphaEarth 特征。

---

### 15. 输出检查表

本地输出：

```text
outputs/tables/table_stage08_alphaearth_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
GEDI_CSC_labels Table Asset 是否存在
AlphaEarth 年度数据是否覆盖 2019—2024
A00—A63 是否全部存在
AlphaEarth 采样结果是否成功导出到 Table Asset
AlphaEarth 采样结果是否成功保存到本地 CSV
本地 CSV 与 Table Asset 是否字段一致
空间块是否成功生成
fold_id 是否为 1—5
是否未使用普通随机划分作为主验证
是否未使用 DEM、Slope、AGBD 作为 AlphaEarth-only 特征
是否完成空间交叉验证
是否保存模型文件
```

---

## 检查标准

AlphaEarth-only 模型可接受标准：

```text
R2 >= 0.45
Spearman_r >= 0.60
Bias 接近 0
天然林和人工林验证精度没有严重失衡
```

如果达标，则进入 Stage 10 生成 FHD 图。

如果不达标，则进入 Stage 9 构建多源模型和混合模型。

同时必须检查：

1. AlphaEarth 采样结果是否包含 A00—A63；
2. FHD 标签是否没有异常值；
3. 训练样本是否覆盖 2019—2024 年；
4. 天然林和人工林样本是否都有；
5. 空间交叉验证是否正常执行；
6. 本地 CSV、GEE Table Asset、模型文件和 CV 表格是否均已生成。

---

## 禁止事项

* 不允许把 AlphaEarth 直接当作 FHD；
* 不允许随机划分训练集和测试集作为主验证；
* 不允许跳过空间交叉验证；
* 不允许只报告训练集精度；
* 不允许在本阶段生成最终 FHD 图；
* 不允许在 AlphaEarth-only 模型中加入 DEM、Slope、TPI、Precip、Temp 或 AGBD；
* 不允许下载 AlphaEarth 全岛栅格到本地；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许本地 CSV 与 Earth Engine Table Asset 使用不同采样来源；
* 不允许在 AlphaEarth 年份缺失时静默使用相邻年份替代。


# Stage 9：多源遥感模型和混合模型备选

## 目标

如果 Stage 8 的 AlphaEarth-only 模型精度不足，或需要稳健性对照，则在 Python 端 Earth Engine API 中构建传统多源遥感模型和 AlphaEarth + 多源混合模型，选择最终 FHD 外推模型。

本阶段不使用本地 XGBoost / LightGBM / joblib 作为主流程，而是在 Earth Engine 端完成：

1. 多源特征采样；
2. GEE 回归模型训练；
3. 空间交叉验证；
4. 模型比较；
5. 最终模型选择；
6. 最终模型导出到 Earth Engine Classifier Asset。

本地仅保存：

1. 多源样本 CSV；
2. 空间交叉验证结果 CSV；
3. 模型比较 CSV；
4. 最终模型选择说明表；
5. GEE 模型 Asset 清单；
6. 进度日志。

---

## 执行条件

只有当 Stage 8 的 AlphaEarth-only 模型未达标，或需要稳健性对照时，才执行本阶段。

执行条件包括：

```text
AlphaEarth-only R2 < 0.45
AlphaEarth-only Spearman_r < 0.60
AlphaEarth-only Bias 明显偏离 0
天然林和人工林验证精度严重失衡
或 用户明确要求执行稳健性对照
```

如果 Stage 8 已达标，本阶段可跳过，但必须在 `docs/progress_log.md` 中记录：

```text
Stage 9 skipped because AlphaEarth-only model passed validation.
```

---

## 输入数据

Stage 8 输出的 AlphaEarth 采样样本，本地 CSV：

```text
outputs/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples.csv
```

Stage 8 输出的 AlphaEarth 采样样本，Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples
```

Stage 2 输出的 Landsat 年度合成影像，Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2019
...
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024
```

Stage 3 输出的指数影像，Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2019
...
users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2024

users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2019
...
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2024

users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2019
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024
```

Earth Engine 公共数据：

```text
COPERNICUS/S1_GRD
USGS/SRTMGL1_003
ECMWF/ERA5_LAND/MONTHLY_AGGR
```

辅助 Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

---

## 允许创建或修改的文件

```text
gee/stage09_train_backup_fhd_models.py
src/io_utils.py
src/validation_utils.py
outputs/stage09_fhd_model/GEDI_CSC_multisource_samples.csv
outputs/stage09_fhd_model/GEDI_CSC_hybrid_samples.csv
outputs/tables/table_fhd_model_multisource_cv.csv
outputs/tables/table_fhd_model_hybrid_cv.csv
outputs/tables/table_fhd_model_comparison.csv
outputs/tables/table_stage09_model_asset_manifest.csv
outputs/tables/table_stage09_checks.csv
docs/progress_log.md
```

多源样本和混合样本同时导出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/GEDI_CSC_multisource_samples
users/gyf/forest_csc_alphaearth/stage09_fhd_model/GEDI_CSC_hybrid_samples
```

GEE 模型导出到 Earth Engine Classifier Asset：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_multisource_rf
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_hybrid_rf
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_final_fhd
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage09_train_backup_fhd_models.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 读取配置文件中的 Asset ID

配置文件中应包含：

```yaml
gee_assets:
  hainan_roi: projects/your_username/assets/Hainan_ROI
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  forest_mask_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
  landsat_asset_root: users/gyf/forest_csc_alphaearth/stage02_landsat
  indices_asset_root: users/gyf/forest_csc_alphaearth/stage03_indices
  alphaearth_sample_asset: users/gyf/forest_csc_alphaearth/stage08_fhd_model/GEDI_CSC_AlphaEarth_samples
  stage09_asset_root: users/gyf/forest_csc_alphaearth/stage09_fhd_model
```

---

### 3. 构建传统多源特征

为每个 GEDI 样本提取以下特征。

Landsat 年度合成波段：

```text
Blue
Green
Red
NIR
SWIR1
SWIR2
```

光谱指数：

```text
NDVI
EVI
NIRv
FVC
NDMI
NBR
```

Sentinel-1 年度特征：

```text
VV
VH
VH_div_VV
VH_minus_VV
RVI
```

地形特征：

```text
DEM
Slope
TPI
```

气候控制变量：

```text
Precip
Temp
```

纹理特征：

```text
Texture_NIR_contrast
Texture_NIR_entropy
Texture_NIR_homogeneity
```

说明：

* 本阶段允许使用 DEM、Slope、TPI、气候变量，因为这是备选多源模型；
* Stage 8 的 AlphaEarth-only 模型不得使用这些变量；
* 本阶段多源特征是为了检验 AlphaEarth-only 是否不足。

---

### 4. 在 Earth Engine 端按年份采样多源特征

对每个 GEDI 样本，按其 `year` 字段匹配同一年遥感特征。

输出多源样本字段至少包括：

```text
sample_id
longitude
latitude
year
FHD
cover
RH25
RH50
RH75
RH98
RH98_RH25
ForestType
Blue
Green
Red
NIR
SWIR1
SWIR2
NDVI
EVI
NIRv
FVC
NDMI
NBR
VV
VH
VH_div_VV
VH_minus_VV
RVI
DEM
Slope
TPI
Precip
Temp
Texture_NIR_contrast
Texture_NIR_entropy
Texture_NIR_homogeneity
```

输出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/GEDI_CSC_multisource_samples
```

本地同步保存：

```text
outputs/stage09_fhd_model/GEDI_CSC_multisource_samples.csv
```

---

### 5. 构建混合模型样本

将 Stage 8 的 AlphaEarth 特征与 Stage 9 的多源特征按 `sample_id` 连接。

混合模型字段包括：

```text
FHD
A00—A63
Landsat bands
Spectral indices
Sentinel-1 features
Terrain variables
Climate variables
Texture variables
ForestType
year
longitude
latitude
sample_id
```

输出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/GEDI_CSC_hybrid_samples
```

本地同步保存：

```text
outputs/stage09_fhd_model/GEDI_CSC_hybrid_samples.csv
```

---

### 6. 训练模型 B：多源遥感-only 模型

模型：

```text
FHD ~ Landsat + Sentinel1 + DEM + Climate + Texture
```

GEE 端主模型：

```text
ee.Classifier.smileRandomForest().setOutputMode("REGRESSION")
```

可选 GEE 端对照模型：

```text
ee.Classifier.smileGradientTreeBoost().setOutputMode("REGRESSION")
ee.Classifier.smileCart().setOutputMode("REGRESSION")
```

Python 端 Earth Engine 示例：

```python
multisource_features = [
    "Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2",
    "NDVI", "EVI", "NIRv", "FVC", "NDMI", "NBR",
    "VV", "VH", "VH_div_VV", "VH_minus_VV", "RVI",
    "DEM", "Slope", "TPI", "Precip", "Temp",
    "Texture_NIR_contrast",
    "Texture_NIR_entropy",
    "Texture_NIR_homogeneity"
]

rf_multisource = (
    ee.Classifier.smileRandomForest(
        numberOfTrees=500,
        variablesPerSplit=None,
        minLeafPopulation=2,
        seed=2026
    )
    .setOutputMode("REGRESSION")
    .train(
        features=multisource_training_fc,
        classProperty="FHD",
        inputProperties=multisource_features
    )
)
```

模型导出到：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_multisource_rf
```

---

### 7. 训练模型 C：AlphaEarth + 多源混合模型

模型：

```text
FHD ~ A00—A63 + Landsat + Sentinel1 + DEM + Climate + Texture
```

GEE 端主模型：

```text
ee.Classifier.smileRandomForest().setOutputMode("REGRESSION")
```

输入变量为：

```text
A00—A63
Blue
Green
Red
NIR
SWIR1
SWIR2
NDVI
EVI
NIRv
FVC
NDMI
NBR
VV
VH
VH_div_VV
VH_minus_VV
RVI
DEM
Slope
TPI
Precip
Temp
Texture_NIR_contrast
Texture_NIR_entropy
Texture_NIR_homogeneity
```

模型导出到：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_hybrid_rf
```

---

### 8. 空间交叉验证

空间折叠沿用 Stage 8 的空间块划分结果，不允许重新随机划分。

每折训练时：

```text
训练集 = fold_id != 当前折
验证集 = fold_id == 当前折
```

每个模型输出：

```text
fold
model_name
R2
RMSE
MAE
Bias
Spearman_r
sample_count
natural_forest_R2
plantation_forest_R2
natural_forest_RMSE
plantation_forest_RMSE
```

输出：

```text
outputs/tables/table_fhd_model_multisource_cv.csv
outputs/tables/table_fhd_model_hybrid_cv.csv
```

要求：

* 空间交叉验证在 Python 端调度 Earth Engine 模型训练和验证；
* 验证预测结果可从 Earth Engine 端取回为表格；
* 指标计算在 Python 端完成；
* 不允许只报告训练集精度；
* 不允许用普通随机划分替代空间块交叉验证。

---

### 9. 三模型比较

比较以下模型：

```text
AlphaEarth-only
Multisource-only
AlphaEarth + Multisource hybrid
```

输出：

```text
outputs/tables/table_fhd_model_comparison.csv
```

字段：

```text
model_name
feature_set
training_platform
R2_mean
R2_std
RMSE_mean
MAE_mean
Bias_mean
Spearman_mean
natural_forest_R2_mean
plantation_forest_R2_mean
selected_as_final
final_model_asset_id
reason
```

其中 `training_platform` 固定为：

```text
Python Earth Engine API
```

---

### 10. 选择最终模型

选择最终模型时：

1. 优先选择空间交叉验证 R² 最高的模型；
2. 如果 R² 差异小于 0.03，优先选择变量更少、解释更清晰的模型；
3. 如果 AlphaEarth-only 与混合模型精度接近，AlphaEarth-only 作为主模型，混合模型作为稳健性；
4. 如果 AlphaEarth-only 明显低于多源模型，则使用多源或混合模型作为主模型；
5. 最终模型必须保存为 Earth Engine Classifier Asset；
6. Stage 10 只能读取最终模型 Asset 进行 FHD 制图。

最终模型 Asset 统一命名为：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_final_fhd
```

如果最终模型来自多源模型，则将多源 RF 模型导出为 `model_final_fhd`。

如果最终模型来自混合模型，则将混合 RF 模型导出为 `model_final_fhd`。

---

### 11. 输出模型 Asset 清单

本地输出：

```text
outputs/tables/table_stage09_model_asset_manifest.csv
```

字段：

```text
model_name
model_asset_id
model_type
feature_set
export_status
selected_as_final
notes
```

---

### 12. 输出检查表

本地输出：

```text
outputs/tables/table_stage09_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
是否满足 Stage 9 执行条件
多源样本是否成功生成
混合样本是否成功生成
空间折叠是否沿用 Stage 8
多源模型是否完成空间交叉验证
混合模型是否完成空间交叉验证
是否比较天然林和人工林分组精度
最终模型是否已导出为 GEE 模型 Asset
是否未修改 Stage 8 原始输出
```

---

## 禁止事项

* 不允许重复创建与 Stage 8 相同的无用训练脚本；
* 不允许修改 Stage 8 原始输出；
* 不允许只比较总体精度，不比较天然林和人工林分组精度；
* 不允许选精度差但图好看的模型作为最终模型；
* 不允许使用本地 XGBoost / LightGBM 作为 GEE 主流程模型；
* 不允许只保存本地 `joblib` 而不导出 GEE 模型 Asset；
* 不允许在本阶段生成最终 FHD 图；
* 不允许使用普通随机划分替代空间块交叉验证；
* 不允许把 AlphaEarth-only、多源-only、混合模型的样本来源混乱使用。
# Stage 10：生成 30 m FHD 空间图

## 目标

使用最终选定的 GEE 回归模型生成海南岛 30 m FHD 空间连续分布图。

本阶段全部使用 Python 端 Earth Engine API 执行：

1. 读取最终 FHD 模型 Asset；
2. 读取对应年度预测特征；
3. 在 Earth Engine 端生成 2019—2024 年 30 m FHD 图；
4. 将 FHD 年度图、多年平均图和不确定性图导出到 Earth Engine Asset；
5. 本地仅保存统计表、Asset 清单、检查表和图件；
6. 不下载 30 m 全分辨率 FHD GeoTIFF；
7. 本阶段不构建 CSC 综合结构指数。

---

## 输入数据

最终 FHD 模型 Asset：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_final_fhd
```

最终模型说明表：

```text
outputs/tables/table_fhd_model_comparison.csv
```

如果 Stage 8 的 AlphaEarth-only 模型已达标，并且 Stage 9 被跳过，则最终模型也必须已经被保存为 GEE 模型 Asset：

```text
users/gyf/forest_csc_alphaearth/stage08_fhd_model/model_alphaearth_only
```

或复制 / 记录为：

```text
users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_final_fhd
```

预测特征根据最终模型类型决定。

### 情况 A：最终模型为 AlphaEarth-only

读取：

```text
GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
```

使用特征：

```text
A00—A63
```

### 情况 B：最终模型为 Multisource-only

读取：

```text
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2019
...
users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2024

users/gyf/forest_csc_alphaearth/stage03_indices/NDVI_2019
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024

COPERNICUS/S1_GRD
USGS/SRTMGL1_003
ECMWF/ERA5_LAND/MONTHLY_AGGR
```

使用特征：

```text
Landsat bands
Spectral indices
Sentinel-1 features
Terrain variables
Climate variables
Texture variables
```

### 情况 C：最终模型为 AlphaEarth + Multisource hybrid

同时读取 AlphaEarth 和多源特征。

辅助 Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestMask_30m
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

---

## 允许创建或修改的文件

```text
gee/stage10_generate_fhd_maps.py
src/io_utils.py
outputs/tables/table_fhd_stats_by_forest_type.csv
outputs/tables/table_stage10_fhd_asset_manifest.csv
outputs/tables/table_stage10_checks.csv
outputs/figures/fig09_fhd_map.png
outputs/figures/fig10_fhd_by_forest_type_boxplot.png
docs/progress_log.md
```

本阶段不再创建本地 GeoTIFF：

```text
outputs/stage09_fhd_maps/FHD_30m_2019.tif
...
outputs/stage09_fhd_maps/FHD_30m_2024.tif
outputs/stage09_fhd_maps/FHD_30m_mean_2019_2024.tif
outputs/stage09_fhd_maps/FHD_uncertainty_30m.tif
```

FHD 栅格统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_2019
...
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_2024

users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_mean_2019_2024
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_uncertainty_30m
```

本阶段不输出：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/CSC_30m_mean_2019_2024
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/CSC_proxy_FHD_30m_mean_2019_2024
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage10_generate_fhd_maps.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 读取最终模型 Asset

读取最终模型：

```python
final_model = ee.Classifier.load(
    "users/gyf/forest_csc_alphaearth/stage09_fhd_model/model_final_fhd"
)
```

如果 Stage 9 被跳过，则读取 Stage 8 的 GEE 模型 Asset。

如果没有可读取的 GEE 模型 Asset，Codex 必须停止，并在日志中说明：

```text
Cannot generate FHD map because final FHD model is not available as an Earth Engine classifier asset.
```

不得使用本地 `joblib` 强行在本阶段生成 GEE Asset 图。

---

### 3. 判断最终模型特征集

根据 `table_fhd_model_comparison.csv` 或配置文件确定最终模型类型：

```text
alphaearth_only
multisource_only
alphaearth_multisource_hybrid
```

不同模型必须使用对应特征集。

如果模型需要的特征与预测影像中的波段不一致，必须停止，不得强行预测。

---

### 4. 构建年度预测特征影像

对 2019—2024 年每一年构建预测影像。

### 4.1 AlphaEarth-only 特征影像

使用：

```text
A00—A63
```

AlphaEarth 原始为 10 m，本项目统一到 30 m。

```python
alpha_30m = (
    alpha_img.select(ae_bands)
    .reduceResolution(
        reducer=ee.Reducer.mean(),
        maxPixels=1024
    )
    .reproject(crs="EPSG:4326", scale=30)
    .updateMask(forest_mask)
    .clip(hainan)
)
```

### 4.2 Multisource-only 特征影像

构建：

```text
Blue
Green
Red
NIR
SWIR1
SWIR2
NDVI
EVI
NIRv
FVC
NDMI
NBR
VV
VH
VH_div_VV
VH_minus_VV
RVI
DEM
Slope
TPI
Precip
Temp
Texture_NIR_contrast
Texture_NIR_entropy
Texture_NIR_homogeneity
```

### 4.3 Hybrid 特征影像

拼接：

```text
A00—A63
+
Multisource features
```

要求：

* 波段顺序必须与模型训练时的 `inputProperties` 完全一致；
* 影像必须只在 ForestMask 区域有值；
* 所有特征必须统一到 30 m；
* 不得将缺失波段填 0 后继续预测，除非该处理已在模型训练时使用并记录。

---

### 5. 生成年度 FHD 图

对 2019—2024 年每年预测：

```python
fhd = (
    predictor_image
    .classify(final_model)
    .rename("FHD")
    .updateMask(forest_mask)
    .clip(hainan)
)
```

输出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_2019
...
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_2024
```

导出示例：

```python
task = ee.batch.Export.image.toAsset(
    image=fhd.toFloat(),
    description=f"FHD_30m_{year}",
    assetId=f"users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_{year}",
    region=hainan.geometry(),
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13
)

task.start()
```

---

### 6. 生成多年平均 FHD

在 Earth Engine 端读取 2019—2024 年 FHD 年度图，计算平均：

```text
FHD_30m_mean_2019_2024
```

导出到：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_mean_2019_2024
```

---

### 7. 生成不确定性图

如果模型支持不确定性估计，则输出：

```text
FHD_uncertainty_30m
```

推荐方案：

```text
不同模型预测标准差
```

例如：

```text
AlphaEarth-only 预测
Multisource-only 预测
Hybrid 预测
```

计算它们的像元级标准差作为不确定性近似。

如果只保留单一最终模型，且 GEE 模型无法直接输出各树预测标准差，则可暂不输出不确定性图，但必须在日志中说明：

```text
FHD_uncertainty_30m not generated because only one final GEE model is available and tree-level predictions are not exported.
```

不得生成伪不确定性图。

---

### 8. 不构建 CSC 综合结构指数

本阶段不构建 CSC 综合结构指数。

原因：

```text
当前主流程只可靠外推 FHD，尚未完成 RH98、RH98_RH25、Cover 等多个结构变量的独立外推与精度验证。
同时，当前方案中没有明确文献依据支持使用 mean(z(FHD), z(RH98), z(RH98_RH25), z(Cover)) 作为 CSC 的固定计算公式。
因此，本研究主分析不构建 CSC 综合指数。
```

本阶段主结构变量为：

```text
FHD_30m_mean_2019_2024
```

后续 Stage 11、Stage 12 和 Stage 13 中，统一使用：

```text
FHD_mean
```

作为森林垂直结构复杂性指标。

不得输出或使用：

```text
CSC_30m_mean_2019_2024
CSC_proxy_FHD_30m_mean_2019_2024
CSC_mean
CSC_proxy_FHD
```

如果后续确实需要构建 CSC，必须另设扩展分析或稳健性分析，并满足以下条件：

```text
1. 找到明确可复现的文献公式；
2. 或使用 PCA / 因子分析等数据驱动方法构建结构综合轴；
3. 所有参与构建的结构变量必须完成独立外推和精度验证；
4. 该指标不得与当前主分析的 FHD_mean 混用。
```

必须在 `docs/progress_log.md` 中记录：

```text
CSC was not generated in Stage 10. FHD_mean was used as the main forest vertical structure metric.
```

---

### 9. 统计 FHD

统计表必须在 Python 端生成并保存本地。

输出：

```text
outputs/tables/table_fhd_stats_by_forest_type.csv
```

字段：

```text
forest_type
FHD_mean
FHD_median
FHD_std
FHD_q25
FHD_q75
valid_pixel_count
valid_area_km2
```

森林类型字段统一为：

```text
all_forest
natural_forest
plantation_forest
rubber_forest
other_plantation
```

---

### 10. 输出 FHD Asset 清单

本地输出：

```text
outputs/tables/table_stage10_fhd_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
asset_type
year
model_asset_id
feature_set
export_status
scale
crs
notes
```

不得记录不存在的 CSC Asset。

---

### 11. 输出检查表

本地输出：

```text
outputs/tables/table_stage10_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
最终模型 Asset 是否存在
模型特征集是否明确
预测影像波段是否与模型输入一致
FHD 图是否只在森林区有值
FHD 是否存在大面积异常极值
天然林 FHD 是否总体高于人工林
年度 FHD 是否没有不合理跳变
FHD 年度图是否全部提交导出
FHD 多年平均图是否提交导出
是否未下载全分辨率 FHD GeoTIFF 到本地
是否未构建 CSC 综合指数
```

---

### 12. 输出图件

输出：

```text
outputs/figures/fig09_fhd_map.png
outputs/figures/fig10_fhd_by_forest_type_boxplot.png
```

要求：

* `fig09_fhd_map.png` 可使用 Earth Engine 缩略图或低分辨率预览图生成；
* 不得为了制图下载 30 m 全分辨率 FHD GeoTIFF；
* `fig10_fhd_by_forest_type_boxplot.png` 基于本地统计抽样结果或统计表生成；
* 图件必须区分天然林和人工林。

---

## 检查标准

必须检查：

1. 最终 FHD 模型是否已保存为 Earth Engine 模型 Asset；
2. FHD 图是否只在森林区有值；
3. FHD 空间分布是否与 GEDI 样本和森林类型基本一致；
4. 天然林 FHD 是否总体高于人工林；
5. 是否存在大面积异常极值；
6. 年度 FHD 是否没有不合理跳变；
7. 2019—2024 年 FHD 年度图是否全部导出到 Earth Engine Asset；
8. 本地是否只保存 CSV 表格和图件，不保存 30 m FHD GeoTIFF；
9. 所有 FHD Asset 是否位于：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/
```

10. 是否未生成没有文献依据的 CSC 综合指数。

---

## 禁止事项

* 不允许在模型未通过验证时生成最终 FHD 图；
* 不允许把 AlphaEarth 某个 embedding 波段当作 FHD 图；
* 不允许生成没有空间掩膜的全岛 FHD 图；
* 不允许在 FHD 精度不足时强行构建 CSC 主指标；
* 不允许使用 `mean(z(FHD), z(RH98), z(RH98_RH25), z(Cover))` 构建 CSC，除非后续找到明确文献依据并单独设计扩展分析；
* 不允许将 FHD 命名为 CSC 或 CSC_proxy；
* 不允许输出 `CSC_30m_mean_2019_2024`；
* 不允许输出 `CSC_proxy_FHD_30m_mean_2019_2024`；
* 不允许在后续阶段使用 `CSC_mean` 字段；
* 不允许将 FHD 年度栅格下载为本地 GeoTIFF；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许使用本地 `joblib` 直接生成 GEE 端 FHD Asset；
* 不允许导出到 Google Drive 作为主方案；
* 不允许模型输入特征与预测影像波段不一致时继续执行；
* 不允许生成伪不确定性图。


# Stage 11：天然林与人工林差异分析

## 目标

比较天然林和人工林在 FVC、NIRv、EQI_func、FHD 和稳定性上的差异，重点回答：

```text
同等 FVC 条件下，天然林和人工林的生态质量是否存在显著差异？
```

本阶段输入数据全部从 Earth Engine Asset 读取，不再读取本地 GeoTIFF。

本阶段在 Python 端 Earth Engine API 中完成样本抽取，在 Python 本地完成统计检验和图件绘制。

本地保存：

1. 分析样本 CSV；
2. 天然林与人工林差异检验表；
3. 同等 FVC 分组比较表；
4. 样本 Asset 清单；
5. 检查表；
6. 图件；
7. 进度日志。

---

## 输入数据

Stage 1 输出的森林类型图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

Stage 3 输出的 FVC 和 NIRv 年度影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/FVC_2024

users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024
```

Stage 4 输出的 EQI_func 年度影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2000
...
users/gyf/forest_csc_alphaearth/stage04_eqi/EQI_func_2024
```

Stage 5 输出的趋势结果，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage05_trend/FVC_SenSlope_30m
users/gyf/forest_csc_alphaearth/stage05_trend/EQI_SenSlope_30m
```

Stage 6 输出的脱钩分类结果，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m
users/gyf/forest_csc_alphaearth/stage06_decoupling/DecouplingType_30m_no_pfilter
```

Stage 10 输出的 FHD 多年平均图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_mean_2019_2024
```

如果 CSC 已可靠生成，则读取：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/CSC_30m_mean_2019_2024
```

如果 CSC 未生成，则本阶段仅使用 FHD，不得强行填充 CSC。

环境变量使用 Earth Engine 公共数据：

```text
USGS/SRTMGL1_003
ECMWF/ERA5_LAND/MONTHLY_AGGR
```

其中：

* DEM 使用 `USGS/SRTMGL1_003`；
* Slope 由 DEM 在 Earth Engine 端计算；
* Precip 和 Temp 可使用 2000—2024 年多年平均气候变量；
* 环境变量只作为控制变量，不解释为 30 m 精细气候格局。

---

## 允许创建或修改的文件

```text
gee/stage11_forest_type_analysis.py
src/stats_utils.py
src/plotting_utils.py
src/io_utils.py
outputs/stage11_forest_comparison/Hainan_forest_analysis_samples.csv
outputs/tables/table_natural_vs_plantation_comparison.csv
outputs/tables/table_same_fvc_group_comparison.csv
outputs/tables/table_stage11_sample_asset_manifest.csv
outputs/tables/table_stage11_checks.csv
outputs/figures/fig11_natural_vs_plantation_boxplots.png
outputs/figures/fig12_same_fvc_group_eqi_comparison.png
docs/progress_log.md
```

分析样本表可同步导出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage11_forest_comparison/Hainan_forest_analysis_samples
```

本阶段不创建、不下载任何全分辨率 GeoTIFF。

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage11_forest_type_analysis.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/ee-gyf/assets/hainan
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  indices_asset_root: users/gyf/forest_csc_alphaearth/stage03_indices
  eqi_asset_root: users/gyf/forest_csc_alphaearth/stage04_eqi
  trend_asset_root: users/gyf/forest_csc_alphaearth/stage05_trend
  decoupling_asset_root: users/gyf/forest_csc_alphaearth/stage06_decoupling
  fhd_asset_root: users/gyf/forest_csc_alphaearth/stage10_fhd_maps
  forest_comparison_asset_root: users/gyf/forest_csc_alphaearth/stage11_forest_comparison
```

Python 端加载方式：

```python
hainan = ee.FeatureCollection(config["gee_assets"]["hainan_roi"])

forest_type = ee.Image(config["gee_assets"]["forest_type_asset"])

forest_mask = forest_type.gt(0).selfMask()
```

如果任一必要 Asset 不存在，Codex 必须停止，并在 `docs/progress_log.md` 中说明缺失的 Asset ID，不得改为读取本地 GeoTIFF。

---

### 3. 构建多年平均指标

在 Earth Engine 端构建：

```text
FVC_mean_2000_2024
NIRv_mean_2000_2024
EQI_mean_2000_2024
```

读取 2000—2024 年逐年 Asset 后计算均值：

```python
years = range(2000, 2025)

fvc_collection = ee.ImageCollection([
    ee.Image(
        f"{config['gee_assets']['indices_asset_root']}/FVC_{year}"
    ).select("FVC").rename("FVC")
    for year in years
])

nirv_collection = ee.ImageCollection([
    ee.Image(
        f"{config['gee_assets']['indices_asset_root']}/NIRv_{year}"
    ).select("NIRv").rename("NIRv")
    for year in years
])

eqi_collection = ee.ImageCollection([
    ee.Image(
        f"{config['gee_assets']['eqi_asset_root']}/EQI_func_{year}"
    ).select("EQI_func").rename("EQI")
    for year in years
])

fvc_mean = fvc_collection.mean().rename("FVC_mean")
nirv_mean = nirv_collection.mean().rename("NIRv_mean")
eqi_mean = eqi_collection.mean().rename("EQI_mean")
```

---

### 4. 读取趋势、脱钩和 FHD 结果

读取：

```python
trend_root = config["gee_assets"]["trend_asset_root"]
decoupling_root = config["gee_assets"]["decoupling_asset_root"]
fhd_root = config["gee_assets"]["fhd_asset_root"]

fvc_slope = ee.Image(f"{trend_root}/FVC_SenSlope_30m").select("FVC_SenSlope").rename("FVC_slope")
eqi_slope = ee.Image(f"{trend_root}/EQI_SenSlope_30m").select("EQI_SenSlope").rename("EQI_slope")

decoupling = (
    ee.Image(f"{decoupling_root}/DecouplingType_30m")
    .select("DecouplingType")
    .rename("DecouplingType")
)

fhd_mean = (
    ee.Image(f"{fhd_root}/FHD_30m_mean_2019_2024")
    .select("FHD")
    .rename("FHD_mean")
)
```

如果存在 CSC：

```python
csc_mean = (
    ee.Image(f"{fhd_root}/CSC_30m_mean_2019_2024")
    .select("CSC")
    .rename("CSC_mean")
)
```

如果 CSC 不存在，则不输出 `CSC_mean` 字段，并在日志中说明：

```text
CSC was not available. Stage 11 used FHD_mean as the main forest structure variable.
```

---

### 5. 准备环境控制变量

DEM 使用：

```text
USGS/SRTMGL1_003
```

Slope 在 Earth Engine 端由 DEM 计算。

```python
dem = (
    ee.Image("USGS/SRTMGL1_003")
    .select("elevation")
    .rename("DEM")
    .clip(hainan)
)

slope = (
    ee.Terrain.slope(dem)
    .rename("Slope")
    .clip(hainan)
)
```

多年平均气候变量可使用 2000—2024 年 ERA5-Land：

```python
era5 = (
    ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
    .filterDate("2000-01-01", "2025-01-01")
    .filterBounds(hainan)
)

precip_mean = (
    era5.select("total_precipitation_sum")
    .sum()
    .divide(25)
    .rename("Precip")
    .clip(hainan)
)

temp_mean = (
    era5.select("temperature_2m")
    .mean()
    .subtract(273.15)
    .rename("Temp")
    .clip(hainan)
)
```

---

### 6. 构建分析样本影像

构建用于抽样的多波段影像：

```text
ForestType
FVC_mean
FVC_slope
NIRv_mean
EQI_mean
EQI_slope
FHD_mean
CSC_mean
DecouplingType
DEM
Slope
Precip
Temp
```

注意：

* 原计划中的 `NIRv_slope` 如果 Stage 5 未生成，则不强行使用；
* 如果后续需要 NIRv_slope，可在稳健性阶段单独计算；
* 主分析以 `FVC_slope` 和 `EQI_slope` 为趋势变量。

示例：

```python
sample_img = (
    forest_type.rename("ForestType")
    .addBands(fvc_mean)
    .addBands(fvc_slope)
    .addBands(nirv_mean)
    .addBands(eqi_mean)
    .addBands(eqi_slope)
    .addBands(fhd_mean)
    .addBands(decoupling)
    .addBands(dem)
    .addBands(slope)
    .addBands(precip_mean)
    .addBands(temp_mean)
    .updateMask(forest_mask)
    .clip(hainan)
)
```

如果 CSC 可用，则加入：

```python
sample_img = sample_img.addBands(csc_mean)
```

---

### 7. 构建分析样本表

分层抽样：

```text
天然林 ≥ 20,000 个像元
人工林 ≥ 20,000 个像元
```

如果 ForestType 编码为：

```text
1 = 天然林
2 = 人工林
```

则分别对 `ForestType == 1` 和 `ForestType == 2` 抽样。

如果 ForestType 编码为：

```text
1 = 天然林
2 = 橡胶林
3 = 其他人工林
```

则：

```text
人工林 = 2 和 3 合并
橡胶林和其他人工林可作为附加分组
```

样本字段：

```text
sample_id
longitude
latitude
ForestType
FVC_mean
FVC_slope
NIRv_mean
EQI_mean
EQI_slope
FHD_mean
CSC_mean
DecouplingType
DEM
Slope
Precip
Temp
```

如果 CSC 不存在，则不输出 `CSC_mean` 字段。

本地输出：

```text
outputs/stage11_forest_comparison/Hainan_forest_analysis_samples.csv
```

可选同步导出到 Earth Engine Table Asset：

```text
users/gyf/forest_csc_alphaearth/stage11_forest_comparison/Hainan_forest_analysis_samples
```

本地 CSV 和 Table Asset 必须来自同一个样本结果。

---

### 8. 输出样本 Asset 清单

本地输出：

```text
outputs/tables/table_stage11_sample_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
asset_type
export_description
export_status
feature_count
fields
notes
```

---

### 9. 基础差异检验

在 Python 本地读取：

```text
outputs/stage11_forest_comparison/Hainan_forest_analysis_samples.csv
```

比较天然林和人工林：

```text
FVC_mean
NIRv_mean
EQI_mean
FHD_mean
FVC_slope
EQI_slope
```


使用：

```text
Mann-Whitney U 检验
Cliff's delta 效应量
```

输出：

```text
outputs/tables/table_natural_vs_plantation_comparison.csv
```

字段：

```text
variable
natural_mean
natural_median
plantation_mean
plantation_median
mannwhitney_u
p_value
cliffs_delta
effect_size_interpretation
natural_sample_count
plantation_sample_count
```

---

### 10. 同等 FVC 分组比较

按 FVC_mean 分组：

```text
0.5—0.6
0.6—0.7
0.7—0.8
0.8—0.9
> 0.9
```

在每组内比较：

```text
天然林 EQI_mean vs 人工林 EQI_mean
天然林 FHD_mean vs 人工林 FHD_mean
```



输出：

```text
outputs/tables/table_same_fvc_group_comparison.csv
```

字段：

```text
fvc_group
variable
natural_mean
natural_median
plantation_mean
plantation_median
mannwhitney_u
p_value
cliffs_delta
effect_size_interpretation
natural_sample_count
plantation_sample_count
valid_comparison
notes
```

如果某个 FVC 分组中任一类别样本过少，则：

```text
valid_comparison = false
```

并在 `notes` 中说明样本不足，不得作为主结论。

---

### 11. 输出图件

输出：

```text
outputs/figures/fig11_natural_vs_plantation_boxplots.png
outputs/figures/fig12_same_fvc_group_eqi_comparison.png
```

图件使用 Python 本地的 `pandas`、`matplotlib` 或 `seaborn` 生成。

图件内容：

1. `fig11_natural_vs_plantation_boxplots.png`

   * FVC_mean；
   * NIRv_mean；
   * EQI_mean；
   * FHD_mean；
   * FVC_slope；
   * EQI_slope；


2. `fig12_same_fvc_group_eqi_comparison.png`

   * 横轴为 FVC 分组；
   * 纵轴为 EQI_mean；
   * 按天然林 / 人工林分组显示；
   * 图中标注有效样本量；
   * 不显示样本不足的无效分组，或用灰色标注。

---

### 12. 输出检查表

本地输出：

```text
outputs/tables/table_stage11_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
所有输入 Asset 是否存在
天然林样本量是否 ≥ 20,000
人工林样本量是否 ≥ 20,000
同等 FVC 分组内是否有足够样本
统计检验是否输出 p 值和效应量
图中是否区分天然林和人工林
是否能回答同等 FVC 下生态质量是否不同

```

---

## 检查标准

必须检查：

1. 所有输入 Asset 是否存在；
2. 天然林和人工林样本量是否足够；
3. 同等 FVC 分组内是否每组都有足够样本；
4. 统计检验是否输出 p 值和效应量；
5. 图中是否区分天然林和人工林；
6. 是否能直接回答“同等 FVC 下生态质量是否不同”；
7. 本地是否只保存 CSV 表格和图件；
8. 是否没有下载任何全分辨率 GeoTIFF。

---

## 禁止事项

* 不允许只比较全局均值而不做同等 FVC 分组；
* 不允许只输出 p 值不输出效应量；
* 不允许把样本严重不平衡的比较作为主结论；
* 不允许在没有 ForestType 的像元上做比较；
* 不允许读取本地 GeoTIFF 作为主输入；
* 不允许下载全分辨率 FVC、EQI、FHD 或脱钩 GeoTIFF；
* 不允许把 CSC 缺失时强行填 0；
* 不允许把 NIRv 原始值替代 EQI_func 作为主生态质量指标；
* 不允许使用 JavaScript 端 GEE 代码。


# Stage 12：回归模型、交互效应和 SEM

## 目标

检验森林结构是否调节 FVC 对生态质量的作用，并检验森林类型是否通过 FHD 影响 EQI_func。

本阶段不处理全分辨率栅格，不读取本地 GeoTIFF，也不生成新的 GEE 栅格 Asset。

本阶段使用 Stage 11 生成的分析样本表，在 Python 本地完成：

1. 回归模型；
2. FVC × FHD 交互效应检验；
3. SEM 路径分析；
4. 回归结果表；
5. SEM 路径系数表；
6. 交互效应图；
7. SEM 路径图。

---

## 输入数据

Stage 11 输出的本地分析样本表：

```text
outputs/stage11_forest_comparison/Hainan_forest_analysis_samples.csv
```

如果 Stage 11 同步导出了 Earth Engine Table Asset，也可作为备份输入：

```text
users/gyf/forest_csc_alphaearth/stage11_forest_comparison/Hainan_forest_analysis_samples
```

但本阶段主分析使用本地 CSV，避免对统计建模过程反复请求 Earth Engine。

---

## 允许创建或修改的文件

```text
scripts/stage12_regression_sem.py
src/stats_utils.py
src/model_utils.py
src/plotting_utils.py
src/io_utils.py
outputs/tables/table_regression_results.csv
outputs/tables/table_sem_path_coefficients.csv
outputs/tables/table_stage12_model_diagnostics.csv
outputs/tables/table_stage12_checks.csv
outputs/figures/fig13_fvc_fhd_interaction.png
outputs/figures/fig14_sem_path_diagram.png
docs/progress_log.md
```

本阶段不创建：

```text
任何新的 .tif 栅格
任何新的 GEE Image Asset
```

---

## 具体任务

### 1. 读取分析样本表

读取：

```text
outputs/stage11_forest_comparison/Hainan_forest_analysis_samples.csv
```

必须检查字段是否包含：

```text
sample_id
longitude
latitude
ForestType
FVC_mean
EQI_mean
FHD_mean
DEM
Slope
Precip
Temp
```

可选字段：

```text
DecouplingType
FVC_slope
EQI_slope
NIRv_mean
```

如果缺少 `FHD_mean` 或 `EQI_mean`，必须停止执行，并在 `docs/progress_log.md` 中说明缺少字段，不得用 NIRv_mean 替代 EQI_mean。

---

### 2. 数据预处理

执行以下处理：

1. 删除关键变量缺失样本；
2. 删除 FVC_mean、EQI_mean、FHD_mean 的极端异常值；
3. 将 ForestType 转换为分类变量；
4. 对连续变量进行标准化，用于比较效应大小；
5. 如样本量过大，可进行空间块或分层抽样，避免空间样本过密导致显著性虚高。

推荐保留两套样本：

```text
full_sample：用于描述性统计
model_sample：用于回归和 SEM
```

如果进行抽样，必须固定：

```text
random_seed = 2026
```

---

### 3. 基础回归模型

模型 1：

```text
EQI_mean ~ FVC_mean + DEM + Slope + Precip + Temp
```

模型 2：

```text
EQI_mean ~ FVC_mean + ForestType + DEM + Slope + Precip + Temp
```

模型 3：

```text
EQI_mean ~ FVC_mean + ForestType + FHD_mean + DEM + Slope + Precip + Temp
```

模型 4：

```text
EQI_mean ~ FVC_mean + ForestType + FHD_mean
           + FVC_mean:FHD_mean
           + FVC_mean:ForestType
           + DEM + Slope + Precip + Temp
```

模型建议使用：

```text
statsmodels OLS
```

如果存在明显空间聚集，可补充：

```text
空间块聚类稳健标准误
或 block_id cluster robust standard errors
```

如果 Stage 11 样本表中没有 `block_id`，可根据经纬度生成 20 km × 20 km 空间块。

---

### 4. 输出回归结果

输出：

```text
outputs/tables/table_regression_results.csv
```

字段：

```text
model_id
dependent_variable
term
coefficient
standardized_coefficient
std_error
p_value
r2
adj_r2
aic
bic
sample_count
notes
```

必须同时报告：

1. 原始系数；
2. 标准化系数；
3. p 值；
4. R²；
5. AIC / BIC；
6. 样本量。

不得只报告显著性。

---

### 5. 输出模型诊断表

输出：

```text
outputs/tables/table_stage12_model_diagnostics.csv
```

字段：

```text
model_id
sample_count
r2
adj_r2
rmse
mae
residual_mean
residual_std
vif_max
spatial_block_used
notes
```

检查：

1. 残差是否明显偏态；
2. VIF 是否过高；
3. FHD 加入后模型是否改善；
4. ForestType 系数是否减小；
5. FVC × FHD 是否方向符合预期。

---

### 6. 绘制交互效应图

输出：

```text
outputs/figures/fig13_fvc_fhd_interaction.png
```

图中展示：

```text
低 FHD：FHD_mean 的 25% 分位数
中 FHD：FHD_mean 的 50% 分位数
高 FHD：FHD_mean 的 75% 分位数
```

横轴：

```text
FVC_mean
```

纵轴：

```text
预测 EQI_mean
```

必须体现：

```text
不同 FHD 水平下，FVC 与 EQI_func 关系是否不同。
```

---

### 7. SEM 路径分析

路径模型：

```text
ForestType → FVC_mean
ForestType → FHD_mean
FVC_mean → EQI_mean
FHD_mean → EQI_mean
ForestType → EQI_mean
```

推荐使用 Python 包：

```text
semopy
```

如果 semopy 未安装，Codex 可以：

1. 在日志中说明缺少 semopy；
2. 使用分步回归近似路径分析；
3. 但必须标记为：

```text
sem_method = regression_path_approximation
```

不得伪造 SEM 结果。

---

### 8. 输出 SEM 路径系数表

输出：

```text
outputs/tables/table_sem_path_coefficients.csv
```

字段：

```text
path
source_variable
target_variable
coefficient
standardized_coefficient
std_error
p_value
direct_effect
indirect_effect
total_effect
method
notes
```

---

### 9. 绘制 SEM 路径图

输出：

```text
outputs/figures/fig14_sem_path_diagram.png
```

图中必须包含：

```text
ForestType
FVC_mean
FHD_mean
EQI_mean
```

并标注路径系数。

图注中必须说明：

```text
SEM 结果表示统计路径关系，不直接证明因果关系。
```

---

### 10. 输出检查表

输出：

```text
outputs/tables/table_stage12_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
输入样本表是否存在
关键字段是否完整
FHD 是否显著解释 EQI
FVC × FHD 是否显著
ForestType 加入后模型是否改善
FHD 加入后 ForestType 系数是否减小
SEM 是否收敛
是否报告效应大小
是否考虑空间样本过密问题
是否未把相关关系写成因果关系
```

---

## 检查标准

必须检查：

1. FHD 是否显著解释 EQI；
2. FVC × FHD 是否显著；
3. ForestType 加入后模型是否改善；
4. FHD 加入后 ForestType 系数是否减小；
5. SEM 是否收敛；
6. 路径方向是否符合生态学解释；
7. 是否报告效应大小；
8. 是否避免将统计相关表述为因果结论。

---

## 禁止事项

* 不允许在空间样本过密的情况下完全忽略空间自相关，至少要分层抽样或空间块稳健标准误；
* 不允许只报告显著性，不报告效应大小；
* 不允许选择性删除不显著模型；
* 不允许把相关关系写成因果结论，SEM 也只能表述为路径关系；
* 不允许读取本地 GeoTIFF；
* 不允许在本阶段生成新的 GEE 栅格 Asset；
* 不允许用 NIRv_mean 替代 EQI_mean 作为主因变量；
* 不允许在缺少 FHD_mean 时继续执行结构调节分析。

# Stage 13：生态稳定性分析

## 目标

评估天然林和人工林生态功能稳定性差异，并检验 FHD 对稳定性的影响。

本阶段输入栅格全部从 Earth Engine Asset 读取，不再读取本地 GeoTIFF。

本阶段输出中：

1. Stability_NIRv 和 CV_NIRv 栅格导出到 Earth Engine Asset；
2. 稳定性统计表和回归表在 Python 端生成并保存到本地；
3. 图件在 Python 端生成并保存到本地；
4. 不下载任何全分辨率 GeoTIFF。

---

## 输入数据

Stage 3 输出的 NIRv 年度影像，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2000
...
users/gyf/forest_csc_alphaearth/stage03_indices/NIRv_2024
```

Stage 1 输出的森林类型图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
```

Stage 10 输出的 FHD 多年平均图，来自 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/FHD_30m_mean_2019_2024
```

Stage 11 输出的分析样本表：

```text
outputs/stage11_forest_comparison/Hainan_forest_analysis_samples.csv
```

环境变量使用 Earth Engine 公共数据：

```text
USGS/SRTMGL1_003
ECMWF/ERA5_LAND/MONTHLY_AGGR
```

---

## 允许创建或修改的文件

```text
gee/stage13_stability_analysis.py
src/stats_utils.py
src/plotting_utils.py
src/io_utils.py
outputs/tables/table_stability_by_forest_type.csv
outputs/tables/table_stability_regression.csv
outputs/tables/table_stage13_stability_asset_manifest.csv
outputs/tables/table_stage13_checks.csv
outputs/figures/fig15_stability_map.png
outputs/figures/fig16_stability_by_forest_type.png
docs/progress_log.md
```

本阶段不再创建本地 GeoTIFF：

```text
outputs/stage12_stability/Stability_NIRv_30m.tif
outputs/stage12_stability/CV_NIRv_30m.tif
```

稳定性栅格统一导出到 Earth Engine Asset：

```text
users/gyf/forest_csc_alphaearth/stage13_stability/Stability_NIRv_30m
users/gyf/forest_csc_alphaearth/stage13_stability/CV_NIRv_30m
```

---

## 具体任务

### 1. 初始化 Python 端 Earth Engine

在 `gee/stage13_stability_analysis.py` 中使用 Python 端 Earth Engine API：

```python
import ee

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()
```

不得使用 JavaScript 端 GEE Code Editor 代码。

---

### 2. 从配置文件读取 Asset ID

从 `config/config.yaml` 读取：

```yaml
gee_assets:
  hainan_roi: projects/your_username/assets/Hainan_ROI
  forest_type_asset: users/gyf/forest_csc_alphaearth/stage01_forest_type/ForestType_30m_clean
  indices_asset_root: users/gyf/forest_csc_alphaearth/stage03_indices
  fhd_asset_root: users/gyf/forest_csc_alphaearth/stage10_fhd_maps
  stability_asset_root: users/gyf/forest_csc_alphaearth/stage13_stability
```

---

### 3. 计算 NIRv 稳定性

在 Earth Engine 端读取 2000—2024 年 NIRv Asset，构建 ImageCollection：

```text
NIRv_2000
...
NIRv_2024
```

对每个像元计算：

```text
NIRv_mean = mean(NIRv_2000–2024)
NIRv_sd = sd(NIRv_2000–2024)
Stability_NIRv = NIRv_mean / NIRv_sd
CV_NIRv = NIRv_sd / NIRv_mean
```

必须掩膜：

```text
NIRv_mean 接近 0 的像元
NIRv_sd = 0 的像元
非森林区
```

建议规则：

```text
NIRv_mean <= 0.001 的像元不计算 CV
NIRv_sd <= 0 的像元不计算 Stability
```

---

### 4. 导出稳定性栅格到 Earth Engine Asset

导出：

```text
users/gyf/forest_csc_alphaearth/stage13_stability/Stability_NIRv_30m
users/gyf/forest_csc_alphaearth/stage13_stability/CV_NIRv_30m
```

Python 端导出示例：

```python
task = ee.batch.Export.image.toAsset(
    image=stability.toFloat(),
    description="Stability_NIRv_30m",
    assetId="users/gyf/forest_csc_alphaearth/stage13_stability/Stability_NIRv_30m",
    region=hainan.geometry(),
    scale=30,
    crs="EPSG:4326",
    maxPixels=1e13
)

task.start()
```

---

### 5. 输出稳定性 Asset 清单

本地输出：

```text
outputs/tables/table_stage13_stability_asset_manifest.csv
```

字段：

```text
asset_name
asset_id
metric
export_description
export_status
scale
crs
notes
```

---

### 6. 天然林和人工林比较

在 Earth Engine 端按森林类型统计：

```text
Stability_NIRv
CV_NIRv
```

Python 端整理为 CSV。

输出：

```text
outputs/tables/table_stability_by_forest_type.csv
```

字段：

```text
forest_type
metric
mean
median
std
q25
q75
valid_pixel_count
valid_area_km2
```

森林类型字段统一为：

```text
all_forest
natural_forest
plantation_forest
rubber_forest
other_plantation
```

---

### 7. 稳定性回归

优先使用 Stage 11 的分析样本表，并从 Earth Engine 端补充抽样得到 Stability_NIRv 和 CV_NIRv。

模型：

```text
Stability_NIRv ~ FHD_mean + FVC_mean + ForestType + DEM + Slope + Precip + Temp
```

也可补充：

```text
CV_NIRv ~ FHD_mean + FVC_mean + ForestType + DEM + Slope + Precip + Temp
```

输出：

```text
outputs/tables/table_stability_regression.csv
```

字段：

```text
dependent_variable
term
coefficient
standardized_coefficient
std_error
p_value
r2
aic
bic
sample_count
notes
```

---

### 8. 输出图件

输出：

```text
outputs/figures/fig15_stability_map.png
outputs/figures/fig16_stability_by_forest_type.png
```

要求：

1. `fig15_stability_map.png` 可使用 Earth Engine 缩略图或低分辨率预览图生成；
2. 不得下载 30 m 全分辨率 Stability / CV GeoTIFF；
3. `fig16_stability_by_forest_type.png` 基于本地统计表或抽样表生成；
4. 图中必须区分天然林和人工林。

---

### 9. 输出检查表

输出：

```text
outputs/tables/table_stage13_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
NIRv 年度 Asset 是否完整
Stability 是否存在异常极大值
CV 是否在合理范围
NIRv_mean 接近 0 的像元是否已掩膜
天然林和人工林稳定性差异是否可解释
FHD 是否与稳定性方向一致
稳定性栅格是否导出到 GEE Asset
本地是否未保存全分辨率 GeoTIFF
```

---

## 检查标准

必须检查：

1. Stability 是否存在异常极大值；
2. CV 是否在合理范围；
3. 天然林和人工林稳定性差异是否可解释；
4. FHD 是否与稳定性方向一致；
5. 稳定性栅格是否输出到 GEE Asset；
6. 本地是否只保存 CSV 表格和图件。

---

## 禁止事项

* 不允许在 NIRv_mean 接近 0 的像元计算 CV；
* 不允许把稳定性作为主生态质量指标替代 EQI_func；
* 不允许只做图不做统计检验；
* 不允许读取本地 GeoTIFF；
* 不允许下载全分辨率 Stability_NIRv 或 CV_NIRv GeoTIFF；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许导出到 Google Drive 作为主方案。


# Stage 14：稳健性检验

## 目标

检验主要结论是否受指标、尺度、森林类型数据和结构指标选择影响。

本阶段遵循全项目统一数据流：

1. 所有已有栅格结果从 Earth Engine Asset 读取；
2. 如需生成新的稳健性栅格，输出到 Earth Engine Asset；
3. 本地只保存稳健性统计表、检查表、必要图件和日志；
4. 不下载全分辨率 GeoTIFF；
5. 不覆盖主结果。

---

## 输入数据

所有主分析结果，包括：

```text
users/gyf/forest_csc_alphaearth/stage01_forest_type/
users/gyf/forest_csc_alphaearth/stage03_indices/
users/gyf/forest_csc_alphaearth/stage04_eqi/
users/gyf/forest_csc_alphaearth/stage05_trend/
users/gyf/forest_csc_alphaearth/stage06_decoupling/
users/gyf/forest_csc_alphaearth/stage10_fhd_maps/
users/gyf/forest_csc_alphaearth/stage13_stability/
```

本地表格：

```text
outputs/tables/table_fvc_thresholds.csv
outputs/tables/table_annual_fvc_nirv_stats.csv
outputs/tables/table_annual_eqi_stats.csv
outputs/tables/table_trend_stats_by_forest_type.csv
outputs/tables/table_decoupling_by_forest_type.csv
outputs/tables/table_fhd_model_comparison.csv
outputs/tables/table_natural_vs_plantation_comparison.csv
outputs/tables/table_same_fvc_group_comparison.csv
outputs/tables/table_regression_results.csv
outputs/tables/table_sem_path_coefficients.csv
outputs/tables/table_stability_by_forest_type.csv
```

---

## 允许创建或修改的文件

```text
gee/stage14_robustness.py
scripts/stage14_robustness_summary.py
outputs/stage14_robustness/
outputs/tables/table_robustness_summary.csv
outputs/tables/table_stage14_asset_manifest.csv
outputs/tables/table_stage14_checks.csv
docs/progress_log.md
```

如生成稳健性栅格，必须输出到：

```text
users/gyf/forest_csc_alphaearth/stage14_robustness/
```

不得覆盖 Stage 3—13 的主结果 Asset。

---

## 具体任务

### 1. FVC 阈值替换

主方案：

```text
5% / 95%
```

稳健性：

```text
2% / 98%
10% / 90%
```

稳健性 FVC 结果如需生成栅格，输出到：

```text
users/gyf/forest_csc_alphaearth/stage14_robustness/fvc_2_98/
users/gyf/forest_csc_alphaearth/stage14_robustness/fvc_10_90/
```

本地输出对应统计表，不下载 GeoTIFF。

---

### 2. 生态质量指标替换

主指标：

```text
EQI_func = FVC 校正后的 NIRv 残差
```

稳健性指标：

```text
NIRv 原始趋势
EVI 残差
kNDVI 残差
MODIS GPP 聚合验证
RSEI 补充验证
```

规则：

1. 若生成新的残差指标，输出到 GEE Asset；
2. 若仅做统计验证，输出 CSV；
3. 不覆盖主 EQI_func；
4. 不把稳健性指标替换为主结论。

---

### 3. 结构指标替换

主指标：

```text
FHD
```

稳健性：

```text
RH98
RH98 - RH25
Cover
CSC
```

只有当 RH98、RH98-RH25、Cover 或 CSC 已可靠外推并通过验证时，才执行结构指标替换。

如果这些结构指标没有可靠 30 m 图，不得伪造或强行填充。

---

### 4. 森林类型数据替换

主森林类型数据：

```text
中国 2020 或 GNPF 2021
```

稳健性：

```text
JRC 2020
Natural Forests 2020
2024 NF/PF forest age product
```

替换后的森林类型图必须：

1. 统一编码；
2. 导出到 GEE Asset；
3. 统计面积；
4. 单独保存在 Stage 14 的稳健性目录；
5. 不覆盖 Stage 1 的主森林类型图。

---

### 5. 空间尺度替换

主尺度：

```text
30 m
```

稳健性：

```text
90 m
300 m
500 m
```

尺度替换在 Earth Engine 端通过聚合实现，结果输出到：

```text
users/gyf/forest_csc_alphaearth/stage14_robustness/scale_90m/
users/gyf/forest_csc_alphaearth/stage14_robustness/scale_300m/
users/gyf/forest_csc_alphaearth/stage14_robustness/scale_500m/
```

不得修改主分析 30 m Asset。

---

### 6. 输出稳健性总表

输出：

```text
outputs/tables/table_robustness_summary.csv
```

字段：

```text
test_name
changed_parameter
input_asset_or_table
output_asset_or_table
main_result_direction
robust_result_direction
consistent_with_main
key_statistic
notes
```

必须判断核心结论是否保持一致：

```text
是否存在 FVC 增加但 EQI 下降区域
量增质减区是否人工林占比较高
同等 FVC 下天然林 EQI 是否高于人工林
FHD 是否显著解释 EQI
FVC × FHD 是否方向稳定
```

---

### 7. 输出稳健性 Asset 清单

输出：

```text
outputs/tables/table_stage14_asset_manifest.csv
```

字段：

```text
test_name
asset_name
asset_id
asset_type
scale
export_status
notes
```

---

### 8. 输出检查表

输出：

```text
outputs/tables/table_stage14_checks.csv
```

字段：

```text
check_item
result
value
notes
```

至少包括：

```text
是否未覆盖主结果
是否所有稳健性结果单独存放
是否记录失败或不一致结果
是否未下载全分辨率 GeoTIFF
是否没有只保留有利于主结论的稳健性
```

---

## 检查标准

必须判断核心结论是否保持一致：

1. 是否存在 FVC 增加但 EQI 下降区域；
2. 量增质减区是否人工林占比较高；
3. 同等 FVC 下天然林 EQI 是否高于人工林；
4. FHD 是否显著解释 EQI；
5. FVC × FHD 是否方向稳定。

---

## 禁止事项

* 不允许只做有利于主结论的稳健性；
* 不允许改参数后覆盖主结果；
* 不允许把稳健性结果和主结果混在同一个文件夹；
* 不允许不记录失败或不一致的稳健性结果；
* 不允许下载全分辨率 GeoTIFF；
* 不允许使用 JavaScript 端 GEE 代码；
* 不允许把未验证的结构指标作为稳健性主结果。

---

# Stage 15：最终论文图表和结果归档

## 目标

整理所有最终图表、表格、方法说明、GEE Asset 清单和结果文件，删除废代码和临时文件，形成可写论文的结果包。

本阶段不重新计算栅格，不下载 GEE 全分辨率 Asset，不生成新的主结果。

本阶段重点是：

1. 汇总本地最终表格；
2. 汇总本地图件；
3. 汇总 GEE Asset ID；
4. 生成最终数据清单；
5. 清理临时文件；
6. 更新 README 和 progress_log。

---

## 输入数据

所有前序阶段结果，包括：

```text
outputs/tables/
outputs/figures/
docs/progress_log.md
users/gyf/forest_csc_alphaearth/ 下所有阶段 Asset
```

---

## 允许创建或修改的文件

```text
scripts/stage15_make_figures_tables.py
outputs/figures/final/
outputs/tables/final/
docs/final_output_manifest.md
docs/final_asset_manifest.md
README.md
docs/progress_log.md
archive/
```

---

## 最终图件

必须整理输出：

```text
Fig. 1 研究区与天然林/人工林分布图
Fig. 2 FVC 与 EQI 年际变化图
Fig. 3 FVC 和 EQI 趋势图
Fig. 4 绿量—生态质量脱钩图
Fig. 5 FHD 30 m 空间分布图
Fig. 6 天然林与人工林指标对比图
Fig. 7 同等 FVC 下天然林与人工林 EQI 差异图
Fig. 8 FVC × FHD 交互效应图
Fig. 9 SEM 路径图
Fig. 10 稳定性分析图
```

保存到：

```text
outputs/figures/final/
```

说明：

* 最终图件使用本地已有 PNG 结果整理；
* 如需地图型图件，可使用 Earth Engine 缩略图或低分辨率预览图；
* 不得下载全分辨率 GEE Asset 作为制图输入。

---

## 最终表格

必须整理输出：

```text
Table 1 数据源表
Table 2 森林类型面积表
Table 3 FVC / NIRv / EQI 年度统计表
Table 4 脱钩区面积与森林类型构成表
Table 5 FHD 模型精度比较表
Table 6 天然林与人工林差异检验表
Table 7 回归模型结果表
Table 8 SEM 路径系数表
Table 9 稳健性检验汇总表
```

保存到：

```text
outputs/tables/final/
```

---

## 最终数据清单

生成：

```text
docs/final_output_manifest.md
```

内容包括：

```text
file_name
path
file_type
generated_stage
is_final_result
usable_for_paper
description
```

---

## 最终 GEE Asset 清单

生成：

```text
docs/final_asset_manifest.md
```

内容包括：

```text
stage
asset_name
asset_id
asset_type
scale
crs
description
is_final_result
used_in_paper
notes
```

必须至少记录：

```text
ForestType_30m_clean
ForestMask_30m
LandsatComposite_2000–2024
NDVI_2000–2024
FVC_2000–2024
NIRv_2000–2024
EQI_func_2000–2024
FVC_SenSlope_30m
EQI_SenSlope_30m
DecouplingType_30m
GEDI_CSC_labels_2019_2024
GEDI_CSC_AlphaEarth_samples
model_final_fhd
FHD_30m_2019–2024
FHD_30m_mean_2019_2024
Stability_NIRv_30m
CV_NIRv_30m
```

---

## 清理规则

必须执行：

1. 删除空文件；
2. 删除未使用的临时脚本；
3. 将旧版本脚本移入 `archive/`；
4. 保留主流程脚本；
5. 确认 README 中记录完整运行顺序；
6. 确认 `outputs/` 中没有大体量全分辨率 GeoTIFF；
7. 确认所有全分辨率栅格结果都以 GEE Asset ID 形式记录。

---

## README 内容

`README.md` 必须包括：

```text
项目简介
数据来源
GEE Asset 根目录
运行环境
阶段执行顺序
每阶段输入输出
如何复现主结果
如何复现图表
如何检查 GEE 导出任务
注意事项
```

必须明确写入：

```text
本项目主流程中，全分辨率栅格结果均存储在 Earth Engine Asset：
users/gyf/forest_csc_alphaearth/
本地仅保存 CSV 表格、模型诊断结果、图件和结果清单。
```

---

## 检查标准

最终结果包必须满足：

1. 所有图表可打开；
2. 所有表格有字段名；
3. 所有最终 GEE Asset ID 已记录；
4. 所有脚本可以按阶段运行；
5. 没有无意义废代码堆在根目录；
6. 每个阶段在 progress_log 中有记录；
7. final_output_manifest 完整；
8. final_asset_manifest 完整；
9. 本地没有保存不必要的大体量全分辨率 GeoTIFF。

---

# Codex 单阶段执行提示词模板

以后每次让 Codex 执行时，不要让它“一次做完整项目”。使用下面模板：

```text
请只执行 AGENTS.md 中的 Stage X，不要执行其他阶段。

要求：
1. 只创建或修改本阶段允许的文件；
2. 不要提前生成后续阶段代码；
3. 所有输出必须写入本阶段指定目录；
4. 全分辨率栅格输出必须导出到 GEE Asset，不要下载为本地 GeoTIFF；
5. 本地只保存 CSV、图件、模型表、日志和必要的轻量文件；
6. 阶段完成后更新 docs/progress_log.md；
7. 如果缺少输入数据或 GEE Asset，立即停止并说明缺少什么，不要编造数据；
8. 不要在项目根目录创建临时文件；
9. 不要保留废弃脚本；
10. 完成后列出本阶段生成的文件、GEE Asset 和检查结果。
```

示例：

```text
请只执行 AGENTS.md 中的 Stage 3：NDVI、FVC 和 NIRv 计算。

只允许创建或修改：
- gee/stage03_export_indices.py
- src/io_utils.py
- outputs/tables/table_fvc_thresholds.csv
- outputs/tables/table_annual_fvc_nirv_stats.csv
- outputs/tables/table_stage03_indices_asset_manifest.csv
- outputs/figures/fig02_annual_fvc_nirv_timeseries.png
- docs/progress_log.md

要求：
1. 输入读取 GEE Asset：
   users/gyf/forest_csc_alphaearth/stage02_landsat/LandsatComposite_2000–2024
2. NDVI、FVC、NIRv 年度栅格输出到 GEE Asset：
   users/gyf/forest_csc_alphaearth/stage03_indices/
3. 本地只保存 CSV 表格和时间序列图；
4. 不要下载年度指数 GeoTIFF；
5. 不要执行趋势分析；
6. 不要生成 EQI_func；
7. 不要生成脱钩图。
```

---

# 最终阶段顺序

严格按以下顺序执行：

```text
Stage 0  项目结构初始化
Stage 1  研究区与森林类型图
Stage 2  Landsat 年度合成
Stage 3  NDVI、FVC、NIRv
Stage 4  EQI_func
Stage 5  FVC 与 EQI 趋势
Stage 6  脱钩区识别
Stage 7  GEDI CSC / FHD 标签
Stage 8  AlphaEarth FHD 模型
Stage 9  多源模型和混合模型备选
Stage 10 FHD / CSC 空间图
Stage 11 天然林与人工林差异分析
Stage 12 回归、交互效应和 SEM
Stage 13 生态稳定性分析
Stage 14 稳健性检验
Stage 15 最终图表与归档
```

任何阶段未通过检查，不得进入下一阶段。

