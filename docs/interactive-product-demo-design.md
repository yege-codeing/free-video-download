# SaveAny 交互式产品演示 — 前端设计方案

> 版本：V1.0  
> 创建日期：2026-06-13  
> 状态：已落地  
> 设计来源：[UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) skill 智能推荐

---

## 一、设计目标

将 SaveAny 从「工具页直接操作」升级为 **Interactive Product Demo（交互式产品演示）** 落地页：

- 用户无需注册，在页面内直接体验完整流程
- 通过浏览器 Mockup + 三步引导降低学习成本
- 悬停/点击揭示功能亮点，强化产品价值感知
- 保持原有珊瑚红品牌色，不破坏既有视觉识别

---

## 二、UI UX Pro Max 推荐摘要

通过 `search.py --design-system` 为 SaveAny 生成的核心推荐：

| 维度 | skill 推荐 | 本项目决策 |
|------|-----------|-----------|
| 页面模式 | Product Demo + Features | ✅ 已采用 |
| UI 风格 | Interactive Product Demo | ✅ 已采用 |
| 配色 | Cinema dark + play red | 保留珊瑚红 `#FF6B6B` + 琥珀金 `#FFD93D` |
| 字体 | Plus Jakarta Sans / Inter | 保留 Inter（skill 备选） |
| 反模式 | 避免杂乱、缺乏存在感 | Mockup 框 + 阴影强化边界 |

### 推荐页面结构

```
Hero（演示入口 + Live Demo CTA）
  ↓
三步引导（粘贴链接 → 解析视频 → 下载/总结）
  ↓
浏览器 Mockup 框（DemoFrame）
  ├── 模式切换 Tab
  ├── URL 输入 + 解析
  └── 视频卡片 / AI 总结面板
  ↓
功能亮点（悬停/点击揭示）
  ↓
即将上线
```

---

## 三、配色系统

沿用项目原有暗色 + 珊瑚红渐变品牌色（skill 允许保留高辨识度配色）：

| 角色 | 变量 | 色值 |
|------|------|------|
| 页面背景 | `--color-bg-primary` | `#0B0B0F` |
| 次级背景 | `--color-bg-secondary` | `#16161D` |
| 卡片背景 | `--color-bg-tertiary` | `#1E1E28` |
| 主强调色 | `--color-accent` | `#FF6B6B` |
| 渐变终点 | `--color-accent-gold` | `#FFD93D` |
| 主文字 | `--color-text-primary` | `#F0F0F0` |
| 次要文字 | `--color-text-secondary` | `#9CA3AF` |

辅助 RGB 通道（用于半透明效果）：

```css
--accent-rgb: 255, 107, 107;
--accent-light-rgb: 255, 217, 61;
```

---

## 四、新增组件

| 组件 | 文件 | 职责 |
|------|------|------|
| DemoFrame | `DemoFrame.vue` | 浏览器窗口 Mockup（地址栏 + Live Demo 徽章） |
| DemoWalkthrough | `DemoWalkthrough.vue` | 三步引导，随用户操作自动推进 |
| FeatureHighlights | `FeatureHighlights.vue` | 6 张功能卡片，悬停/点击揭示详情 |
| VideoCardSkeleton | `VideoCardSkeleton.vue` | 解析等待骨架屏 |

### 改造组件

| 组件 | 主要变化 |
|------|---------|
| `App.vue` | 重组布局，接入演示框与步骤联动逻辑 |
| `HeroSection.vue` | 演示徽章 +「立即体验 Live Demo」按钮 |
| `NavBar.vue` | 浮动导航 + 浏览器圆点 + Live Demo 徽章 |
| `ModeTabs.vue` | emoji → SVG 图标，tablist 语义 |
| `ComingSoon.vue` | 悬停/点击揭示卡片 |
| `SummaryIntro.vue` | 精简为演示框内占位引导 |
| `UrlInput.vue` | 暴露 `focus()` 供步骤引导调用 |

---

## 五、交互逻辑

### 步骤自动推进（`demoStep` computed）

| 步骤 | 条件 |
|------|------|
| 0 粘贴链接 | 无 URL、未解析 |
| 1 解析视频 | 有 URL 或正在解析 |
| 2 下载/总结 | 有解析结果或正在下载/总结 |

### 用户操作

- 点击 Hero「立即体验 Live Demo」→ 平滑滚动到 Mockup 框
- 点击步骤 1「粘贴链接」→ 滚动并聚焦 URL 输入框
- 功能卡片：桌面悬停揭示 / 移动端点击切换（`feature-reveal-open`）

---

## 六、无障碍（WCAG AA）

按 skill UX 规范补强的高优先级项：

| 项 | 实现 |
|----|------|
| 触屏点击揭示 | 卡片改为 `<button>` + `toggle()` + `aria-expanded` |
| 键盘焦点 | `.focus-ring`（`focus-visible` 触发，鼠标点击不显示） |
| 图标按钮标签 | 清空按钮 `aria-label="清空输入"`，输入框 `aria-label="视频链接"` |
| 减少动画偏好 | `@media (prefers-reduced-motion: reduce)` 全局降级 |
| 无 emoji 图标 | ModeTabs / FeatureHighlights / ComingSoon 全部 SVG |

---

## 七、样式工具类（`style.css`）

| 类名 | 用途 |
|------|------|
| `.demo-frame` | 浏览器 Mockup 外框 |
| `.demo-chrome` / `.demo-chrome-badge` | 顶栏与 Live Demo 徽章 |
| `.demo-step` / `.demo-step-active` / `.demo-step-done` | 三步引导状态 |
| `.feature-reveal` / `.feature-reveal-open` | 悬停/点击揭示卡片 |
| `.btn-demo-cta` | Hero 演示入口按钮 |
| `.skeleton-shimmer` | 解析等待骨架动画 |
| `.focus-ring` | 键盘焦点环 |

---

## 八、如何用 UI UX Pro Max 迭代设计

在本机运行（需 Python 3）：

```powershell
$SCRIPT = "C:\Users\Administrator\.cursor\skills\ui-ux-pro-max\scripts\search.py"

# 1. 生成完整设计系统推荐
python $SCRIPT "video downloader AI summary interactive demo" --design-system -p "SaveAny" -f markdown

# 2. 配色方案对比
python $SCRIPT "video streaming downloader" --domain color -n 8

# 3. UX 规范自查
python $SCRIPT "accessibility focus loading skeleton" --domain ux

# 4. Vue 栈实现规范
python $SCRIPT "component state transition" --stack vue

# 5. 持久化到项目（可选）
cd f:\vibecoding\free-video-download
python $SCRIPT "video downloader tool" --design-system --persist -p "SaveAny"
```

持久化后会在项目根目录生成 `design-system/MASTER.md`，可作为后续迭代的基准。

---

## 九、交付前 Checklist（来自 skill）

- [x] 无 emoji 作为 UI 图标（使用 SVG）
- [x] 可点击元素有 `cursor-pointer`
- [x] 悬停/点击过渡 150–300ms
- [x] 键盘 `focus-visible` 焦点环
- [x] `prefers-reduced-motion` 支持
- [x] 响应式断点 375 / 768 / 1024 / 1440
- [ ] 浅色模式对比度（当前为暗色主题，未启用）

---

## 十、相关文档

- [需求文档](requirements.md)
- [系统方案设计](design.md)
- [AI 总结功能设计](ai-summary-design.md)
- [运维文档](operations.md)
