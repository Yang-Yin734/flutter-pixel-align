# 测量方法、工具链与命令

## 1. 确定性截图（首选：Golden Test）

用固定 fixture 渲染，保证每次结果可复现、可回归。

```yaml
# pubspec.yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  golden_toolkit: ^0.15.0
```

```dart
// test/golden/home_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:golden_toolkit/golden_toolkit.dart';
import 'package:your_app/main.dart';

void main() {
  testGoldens('home screen', (tester) async {
    await loadAppFonts();           // 使用确定字体，避免系统字体差异
    final builder = DeviceBuilder()
      ..addScenario(name: 'home', widget: HomePage(fakeData()));
    await tester.pumpDeviceBuilder(builder);
    await screenMatchesGolden(tester, 'home');
  });
}
```

- 生成基线：`flutter test --update-goldens`
- 回归对比：`flutter test`（失败即表示出现像素级差异）
- 把 `*.png` 基线与当前失败图放入同一目录供 `pixel_diff.py` 量化。

## 2. 真实设备 / 模拟器截图（需严格同条件）

- 固定同一机型/分辨率/像素密度、相同系统字体缩放、相同暗亮模式。
- 用固定 seed 或 mock 数据消除随机内容（头像、时间、网络图）。
- `flutter screenshot -o reference_home.png`（需连接设备/模拟器）。

## 3. 取色与颜色差异

- 截图在图像工具或 DevTools 中取色得到 hex。
- 用 `pixel_diff.py` 的 `--color-at x,y` 模式提取指定坐标颜色，再算 ΔE；或在代码中读取 `Theme`/`Color` 的 `value`、`toRadixString` 与设计 token 核对。

## 4. 间距 / 几何测量

- DevTools "Layout Inspector" 读取元素包围盒与边距。
- 或截图叠加参考线后用标尺读数。
- 组件几何统一以"包围盒 (x, y, w, h) + 圆角 + 阴影参数"记录。

## 5. 像素级 diff（脚本）

```bash
pip install pillow
python scripts/pixel_diff.py reference.png current.png \
  --threshold 16 --grid 4 --out diff.png
```

输出：MSE、最大单像素差、差异像素占比、按 grid 分区的差异占比，并生成高亮 diff 图 `diff.png`（差异区标红，其余压暗）。

## 6. 设计 token 提取

- 从 `theme.dart` / 常量文件读取 spacing 阶梯、主色/中性色、TextStyle 阶梯。
- 将"目标设计 token"与"参考图实测值"并列比对，定位是 token 偏差还是组件实现偏差。
