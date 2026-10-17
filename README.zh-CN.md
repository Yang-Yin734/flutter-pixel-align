# flutter-pixel-align（Flutter UI 像素级对齐与视觉回归验收）

一个可复用的 Agent **Skill**：把"让 UI 看起来一样"从主观感觉变成可测量的工程流程。它适用于需要让当前 Flutter 界面与**参考标准**（竞品 App、Figma / 设计稿导出图、或上一次通过的 `golden` 截图）在像素层面对齐，并产出带测量值的差异报告、且能在每次改动后回归验证的场景。

> 本 Skill 的核心规则：**无测量，不宣布对齐。** 任何"已对齐 / 已通过"的结论都必须附带可复核的测量值或 diff 图，绝不说"看起来差不多"。

## 它能做什么

- 定义**参考基线**与可量化对齐清单（每一项对应一个可测量指标）。
- 指导**同条件下截图采集**（相同设备、分辨率、像素密度、字体缩放、亮 / 暗模式），优先用 golden 测试保证可复现。
- 提取**可测量指标**：间距 / 边距、颜色（CIELAB ΔE）、字号 / 字重 / 行高、组件几何（包围盒、圆角、阴影）、整体像素差。
- 产出**结构化验收报告**（逐项 PASS / WARN / FAIL，含测量值与证据）。
- 驱动**修复与回归**：改动后重跑，确认 FAIL 归零且原 PASS 项不退化，再把通过的截图固化为新 golden。

## 何时使用

- "和 XX 应用对齐" / "像素级一致" / "视觉要和参考应用一样"
- "对比设计稿 / 截图，给我差异证据"
- "验收 UI" / "视觉回归" / "发版前视觉冻结"
- 在 Flutter 项目改动布局 / 主题后，确认没有视觉退化

## 仓库结构

```
flutter-pixel-align/
├── SKILL.md                      # Skill 定义：触发条件 + 工作流 + 硬性规则
├── references/
│   ├── metrics.md               # 可测量指标定义与判定阈值
│   ├── measurement-method.md    # 截图采集、golden 测试、取色与像素 diff 命令
│   └── report-template.md       # 逐条验收报告模板
├── scripts/
│   └── pixel_diff.py            # 量化像素 diff（MSE / 最大差 / 差异占比 / diff 图 / 取色）
├── README.md
└── README.zh-CN.md
```

## 安装

把 skill 文件夹复制到 Agent 的 skills 目录即可。以 WorkBuddy / Claude 类加载器为例：

```bash
# 项目级
cp -r flutter-pixel-align <项目>/.workbuddy/skills/

# 用户级（全局）
cp -r flutter-pixel-align ~/.workbuddy/skills/
```

Agent 会自动加载，并在你提出像素级对齐需求时触发。

## 使用

1. **设定基线。** 告诉 Agent 参考来源与对齐范围（单页面、某个组件，还是整套视觉规范），并**事先约定偏差阈值**（如间距 ±1px、ΔE ≤ 5）。
2. **同条件截图。** 用 golden 测试渲染固定 fixture，或在相同条件下真机 / 模拟器截图。把 `reference.png` 与 `current.png` 放在同一目录。
3. **跑 diff 脚本**（推荐，但不是必须）：

   ```bash
   pip install pillow
   python scripts/pixel_diff.py reference.png current.png \
       --threshold 16 --grid 4 --out diff.png
   ```

   输出：MSE、最大单像素差、差异像素占比、按 grid 分区占比，以及高亮 `diff.png`。当差异像素占比超过 `--fail-ratio` 时退出码为 `1`——可作为 CI / PR 视觉回归门禁。

   若只需抽取某一坐标的颜色并对比 ΔE：

   ```bash
   python scripts/pixel_diff.py reference.png current.png --color-at 40,40
   ```

   会输出该坐标在两图中的 hex 颜色，以及 CIE76 ΔE（判定 PASS ≤2 / WARN ≤5 / FAIL >5）。
4. **填写报告。** 用 `references/report-template.md` 记录测量值与基于数字的结论。
5. **修复与回归。** 改动后重跑第 2–4 步，直到 FAIL 归零且原 PASS 项未退化，再用 `flutter test --update-goldens` 固化新的 golden。

## 指标阈值（默认）

| 指标 | 单位 | 默认判定 |
|---|---|---|
| 间距 / 边距 | px | ≤1 PASS；≤2 WARN；>2 FAIL |
| 颜色（ΔE, CIELAB） | ΔE | ≤2 PASS；≤5 WARN；>5 FAIL |
| 字号 | px | ≤0.5 PASS；≤1 WARN；>1 FAIL |
| 包围盒 (x,y,w,h) | px | ≤1 PASS；≤2 WARN；>2 FAIL |
| 圆角半径 | px | ≤1 PASS；否则 WARN/FAIL |
| 阴影偏移/模糊 | px,% | ≤1px / ≤5% PASS |
| 总体像素差 | % | <0.1% PASS；<1% WARN；≥1% FAIL |

阈值可按项目调整，但必须在测量前与用户约定并写入报告。

## 许可证

MIT —— 见 [LICENSE](LICENSE)。
