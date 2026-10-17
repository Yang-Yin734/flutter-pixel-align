# 可测量指标定义与判定阈值

对齐清单中的每一项都必须对应下列某类可测量指标。阈值可随项目调整，但**必须在 Step 1 与用户约定并写入报告**。

| 指标 | 定义 | 单位 | 默认判定阈值 |
|---|---|---|---|
| 间距 / 边距 (Spacing) | 两元素边缘之间的像素距离 | px | ≤1px PASS；≤2px WARN；>2px FAIL |
| 颜色 (Color) | 取色 hex → 转 CIELAB 计算 ΔE | ΔE | ≤2 不可辨 PASS；2<ΔE≤5 肉眼接近 WARN；>5 FAIL |
| 字号 (Font size) | 文本实际渲染高度 | px | ≤0.5px PASS；≤1px WARN；>1px FAIL |
| 字重 (Font weight) | 字体字重枚举匹配 | enum | 完全匹配 PASS；否则 FAIL |
| 行高 (Line height) | 文本行盒高度 / 字号 | ratio | 偏差 ≤2% PASS；否则 FAIL |
| 组件几何 - 包围盒 | 元素 (x, y, w, h) | px | 各分量 ≤1px PASS；≤2px WARN；>2px FAIL |
| 组件几何 - 圆角 | 圆角半径 | px | ≤1px PASS；否则 WARN/FAIL |
| 阴影 (Shadow) | offset / blur / alpha | px,% | 偏差 ≤1px / ≤5% PASS；否则 FAIL |
| 对齐基线 | 元素左/右/中线与参考对齐 | px | ≤1px PASS；≤2px WARN；>2px FAIL |
| 总体像素差 | 整图逐像素差异汇总 | % | 差异像素占比 <0.1% PASS；<1% WARN；≥1% FAIL |

## 说明

- **ΔE** 使用 CIELAB 色差公式（推荐 CIE76 或 CIEDE2000）。ΔE≤2 通常被认为人眼不可分辨。
- **差异像素占比** = 单像素通道最大差值超过阈值（默认 16/255）的像素数 / 总像素数。
- 阈值应随"对齐严格度"调整：像素级复刻用上表；品牌规范对齐可放宽。
- 所有数值必须来自截图测量或设计 token，不得估算。
