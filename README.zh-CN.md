# better-image-gen

**Claude Code AI 生图技能** — 由 [apiyi](https://api.apiyi.com/register/?aff_code=ijv5) 驱动，使用 OpenAI 兼容的 `gpt-image-2-all` 图片接口。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://claude.ai/code)
[![apiyi](https://img.shields.io/badge/Powered_by-apiyi-orange)](https://api.apiyi.com/register/?aff_code=ijv5)

[English](README.md) · [中文](#)

---

## 能做什么

在 Claude Code 里直接说，不需要任何命令或每次配置：

```
生成一张东京夜晚街头的电影感女性肖像
帮我做一个 App logo，深色主题，极简风格
并行生成 8 张产品图
做一个 Runcat 风格的菜单栏机器人跑步帧动画
做一张 Mac 动态壁纸，深海珊瑚礁，白天/夜晚切换
```

技能按图片类型选择 GPT 工作流、后处理输出，并保存到 `~/Pictures/better-image-gen/`。

---

## 模型

一个模型，一个 API Key。

| 模型 ID | 适合场景 | 尺寸 |
|---------|---------|------|
| `gpt-image-2-all` | 写实照片、人像、产品图、壁纸、sprite sheet | 30 个预设 |

**GPT 16:9 尺寸预设：**

| 档位 | 尺寸 |
|------|------|
| 1K | 1280×720 |
| 2K | 2048×1152 |
| 4K | 3840×2160 |

完整 30 个预设见 `references/apiyi.md`。

---

## 使用场景

| 请求类型 | 模型 | 输出 |
|---------|-------------|------|
| 人像 / 插图 | GPT | `.webp` q78，≤ 300 KB |
| Logo / favicon | GPT | `.png`（pngquant），≤ 100 KB |
| Mac 静态壁纸（4K） | GPT | `wallpaper.png`（无损 PNG） |
| Mac 动态壁纸 | GPT | `wallpaper-apr.heic`（2 帧，亮/暗模式切换） |
| Sprite loop 帧动画 | GPT | 序列帧 PNG + `preview.gif` |
| 高质感内容（T3+） | GPT，必要时软化 prompt | `.webp` q78 |
| 批量生成（N 张） | 每张独立 GPT 请求 | N × `.webp`，并行生成 |

---

## Mac 动态壁纸

生成含 `apple_desktop:apr` 元数据的 2 帧 HEIC。系统外观切换到深色模式时，macOS 自动切换壁纸帧。

```
做一张动态壁纸，深夜星空下的山脉
```

**依赖：** `pip3 install pillow-heif`（内置 libheif，无需 Homebrew）

**输出路径：** `~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic`

> **macOS Sonoma 说明：** 时间型（h24）HEIC 动态壁纸在 Sonoma 上已失效——苹果将该格式迁移到私有 `.madesktop` 体系。亮/暗模式切换（apr）完全可用。

---

## Sprite Loop 帧动画

用于 Runcat 类菜单栏动画、状态 mascot、loading loop、小型 App 动画。技能会先生成 sprite sheet，再切成编号 PNG 序列帧，写入 `manifest.json`，并打开 `preview.gif` 预览。

**输出路径：** `~/Pictures/better-image-gen/sprite-loop/{name}/`

---

## 输出规范

| 资产类型 | 格式 | 路径 |
|---------|------|------|
| 封面 / 插图 | 有损 WebP q78 | `~/Pictures/better-image-gen/{name}.webp` |
| Mac 静态壁纸 | 无损 PNG | `~/Pictures/better-image-gen/wallpaper.png` |
| Mac 动态壁纸 | 2 帧 HEIC | `~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic` |
| Sprite loop 帧动画 | PNG 序列帧 + preview GIF | `~/Pictures/better-image-gen/sprite-loop/{name}/` |
| Logo | PNG（pngquant） | 项目本地 |
| 元数据 | JSON | 与图片同目录 |

中间 PNG 写入 `/tmp/`，打包完成后自动清理。

---

## 安装配置

**1. 获取 API Key**

在 [apiyi.com](https://api.apiyi.com/register/?aff_code=ijv5) 注册，新用户有免费额度。

**2. 配置 Key**
```bash
export APIYI_API_KEY="your-key-here"
# 加到 ~/.zshrc 永久生效
```

**3. 安装技能**
```bash
git clone https://github.com/zisheng-ai/apiyi-image-gen ~/.claude/skills/apiyi-image-gen
```

**4. 动态壁纸专用依赖**
```bash
pip3 install pillow-heif
```

---

## 文件结构

```
SKILL.md                      ← 技能入口与触发规则
references/
  apiyi.md                    ← API 鉴权、模型规格、尺寸表、错误码
  generation.md               ← API Key 检查、模型别名、gen_image_apiyi、metadata helper
  post-process.md             ← WebP 转换、尺寸调整、PNG 压缩
  portrait.md                 ← 人像、封面、banner、通用单图
  high-allure.md              ← 高质感 romance / editorial 图片
  logo-icon.md                ← 透明 Logo、图标、favicon、抠图素材
  static-wallpaper.md         ← 静态壁纸 PNG 流程
  dynamic-wallpaper.md        ← Mac 动态壁纸：生成 + HEIC 打包
  sprite-loop.md              ← Runcat 类序列帧动画资产
```

---

## License

MIT — 见 [LICENSE](LICENSE)。
