# 抖音下载失败排查与修复方案

> 文档版本：1.0  
> 更新日期：2026-05-22  
> 关联代码：`backend/services/douyin_service.py`、`backend/services/video_service.py`

---

## 1. 问题现象

用户使用本站解析抖音链接时，后端返回类似错误：

```text
解析失败：ERROR: [Douyin] 7611772889654477541: Fresh cookies (not necessarily logged in) are needed; ...
WARNING: [Douyin] ... Failed to parse JSON: Expecting value in '': line 1 column 1 (char 0)
```

常见误解是「Cookie 过期或未登录」。实际上在多数公开视频场景下，**仅补充 Cookie 无法根治**。

---

## 2. 根因分析

### 2.1 yt-dlp 抖音提取器的数据路径

本项目 V1 对全平台统一使用 [yt-dlp](https://github.com/yt-dlp/yt-dlp)。抖音由 `tiktok.py` 中的 `Douyin` 提取器处理，核心步骤为：

1. 请求 `https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=...`
2. 解析返回 JSON，从中读取 `play_addr` 等字段

### 2.2 抖音 Web API 的签名机制

根据社区逆向与 [yt-dlp Issue #9667](https://github.com/yt-dlp/yt-dlp/issues/9667) 的讨论，上述接口在浏览器中实际会附带多组查询参数，例如：

| 参数 | 说明 |
|------|------|
| `verifyFp` / `fp` | 设备指纹相关 |
| `msToken` | 会话令牌 |
| `a_bogus` | **每次请求动态生成** 的签名字段 |

若在请求中省略任一参数，或复用旧的 `a_bogus`，服务端常返回**空响应体**。yt-dlp 对空 body 做 `json.loads` 失败，进而抛出 `Failed to parse JSON`，并在缺少有效 `s_v_web_id` 等条件下统一提示 `Fresh cookies needed`。

因此：

- 报错文案指向 Cookie，但**本质是 API 通道缺少完整 Web 签名**；
- 该问题在 yt-dlp 侧长期存在（2024–2026 年仍有大量复现报告），属于 **site-bug / extractor 与站点风控不匹配**，而非本项目单独配置错误。

### 2.3 原项目内的缓解尝试为何不够

修复前，`video_service.py` 曾实现自动 Cookie：

- 向 `ttwid.bytedance.com` 注册获取 `ttwid`
- 本地生成 `s_v_web_id`
- 访问 `www.douyin.com` 首页写入 `__ac_nonce` 等
- 将 Netscape 格式 Cookie 文件传给 yt-dlp

该方案只改善了「访客身份」这一环，**仍走 aweme detail API**，无法生成 per-request 的 `a_bogus`，故仍会出现相同报错。

---

## 3. 方案选型

| 方案 | 思路 | 优点 | 缺点 | 是否采用 |
|------|------|------|------|----------|
| A. API 签名 | 集成 F2 / a_bogus 等逆向算法，继续调 aweme API | 与浏览器行为一致，可扩展批量能力 | 算法频繁变更，维护成本高 | 未采用（可作后续 fallback） |
| B. 浏览器 Cookie + yt-dlp | 用户手动过验证码后导出 cookies.txt | 零自研 | 不适合「只贴链接」产品；社区反馈仍常失败 | 未采用 |
| C. SSR 页面解析 | 请求服务端渲染页，解析内嵌 `RENDER_DATA` | 不依赖 `a_bogus`；适合单条公开视频 | 依赖页面结构；私密视频可能失败 | **已采用** |

方案 C 与社区 [yt-dlp PR #16367](https://github.com/yt-dlp/yt-dlp/pull/16367)（`jingxuan?modal_id=` + `RENDER_DATA`）思路一致。对本产品「粘贴链接 → 解析 → 选清晰度 → 下载」的场景足够。

---

## 4. 最终实现架构

### 4.1 平台分流

对前端 **API 契约不变**（`POST /api/parse`、`GET /api/download`）。后端在 `video_service.py` 中按域名分流：

```text
用户 URL
    → _normalize_url()          # 短链跳转、modal_id 统一为 /video/{id}
    → _is_douyin() ?
         ├─ 是 → douyin_service.parse_douyin / download_douyin
         └─ 否 → yt-dlp extract_info / download
```

### 4.2 数据流（抖音专用）

```text
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  aweme_id   │────▶│ jingxuan?modal_id=   │────▶│  RENDER_DATA    │
│  (视频 ID)  │     │ (SSR 精选页)          │     │  app.videoDetail │
└─────────────┘     └──────────────────────┘     └────────┬────────┘
                                                            │
                    ┌───────────────────────────────────────┘
                    ▼
         标题 / 作者 / 封面 / bitRateList[].playAddr[].src
                    │
                    ▼
         requests 流式下载 CDN（如 *.douyinvod.com）
```

### 4.3 关键实现细节

#### URL 规范化

支持形态：

- `https://www.douyin.com/video/{id}`
- `https://www.douyin.com/jingxuan?modal_id={id}`（及带 `modal_id` 的其它页）
- `https://v.douyin.com/...` 短链（`resolve_douyin_url` 跟随重定向）
- `https://www.douyin.com/note/{id}`

#### 为何使用 `jingxuan?modal_id=` 而非 `/video/{id}`

| 请求 | 典型响应 | 是否含 RENDER_DATA |
|------|----------|-------------------|
| `/video/{aweme_id}` | 体积小（~6KB） | 否，多为 CSR 空壳 |
| `/jingxuan?modal_id={aweme_id}` | 体积大（~1MB+） | 是，含完整 `videoDetail` |

#### RENDER_DATA 解析

页面内嵌：

```html
<script id="RENDER_DATA" type="application/json">…URL 编码的 JSON…</script>
```

处理步骤：正则提取 → `urllib.parse.unquote` → `json.loads` → 读取 `payload["app"]["videoDetail"]`。

#### 多清晰度与直链结构

Douyin Web 的 `bitRateList` 中，`playAddr` 为列表，每项含 `src`（CDN URL），与 TikTok 常见的 `url_list` 字段不同。解析时跳过 `format == "dash"` 的分片，优先 progressive mp4。

下载阶段根据用户选择的 `format_id`（如 `best`、`1080`、`720`）选取对应 `src`，使用 `requests` 流式写入临时目录，再由 FastAPI `StreamingResponse` 返回。

#### 轻量 Cookie 的作用

`douyin_service._fetch_douyin_cookies()` 仍会获取 `ttwid`、`s_v_web_id` 并访问首页，目的仅为 **正常打开 SSR 页面**，而非供 yt-dlp 调用 aweme API。

---

## 5. 代码变更清单

| 文件 | 变更 |
|------|------|
| `backend/services/douyin_service.py` | **新增**：抖音 SSR 解析、格式列表构建、直链下载 |
| `backend/services/video_service.py` | 抖音走 `douyin_service`；移除无效的「仅 Cookie + yt-dlp」抖音路径；修复 yt-dlp 下载分支缩进错误 |
| `backend/requirements.txt` | 增加 `requests` |

### 5.1 顺带修复：yt-dlp 下载分支缩进

`download_video` 中 yt-dlp 分支曾在 `raise ValueError("下载失败")` 之后放置 `prepare_filename` 等逻辑，导致成功下载后也无法定位文件。已修正缩进，影响 B 站等非抖音平台。

---

## 6. 验证记录

测试视频 ID：`7611772889654477541`（用户报错同款）

| 步骤 | 结果 |
|------|------|
| `parse_douyin` / `POST /api/parse` | 成功返回标题、作者、4K/1080P/720P 等格式 |
| CDN 直链 HEAD | HTTP 200，`video/mp4` |
| 完整大文件下载（后台 480P 测试） | 因体积过大测试进程被中断，逻辑为流式写入，需在业务环境按清晰度实测 |

---

## 7. 使用与部署

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

无需用户手动导出 Cookie 即可解析**多数公开视频**。若解析失败，可排查：

1. 视频是否为私密 / 仅好友可见  
2. 服务器是否在海外（抖音可能限流）  
3. 抖音是否改版导致 `RENDER_DATA` 结构变化  

---

## 8. 已知限制与后续演进

### 8.1 当前限制

- 强依赖 `jingxuan` SSR 页面结构  
- 未登录态下，部分仅登录可见内容无法获取  
- 4K 文件体积大，下载耗时长，建议前端默认推荐 720P  

### 8.2 可选后续

1. **用户上传 `cookies.txt`**：支持登录态视频  
2. **API 签名 fallback**：SSR 失败时尝试 F2 / a_bogus 方案（方案 A）  
3. **跟进 yt-dlp 上游**：若官方合并 Douyin 修复，可评估回退或双通道  

---

## 9. 参考资料

- [yt-dlp #9667 - Douyin always errors saying fresh cookies are needed](https://github.com/yt-dlp/yt-dlp/issues/9667)
- [yt-dlp #8139 - Douyin can't download and how to fix?](https://github.com/yt-dlp/yt-dlp/issues/8139)
- [yt-dlp PR #16367 - Fix extraction for modal_id and RENDER_DATA](https://github.com/yt-dlp/yt-dlp/pull/16367)
- [Johnserf-Seed/f2](https://github.com/Johnserf-Seed/f2)（API 签名参考实现）
- [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)（a_bogus 参考实现）

---

## 10. 一句话结论

**抖音报错的根因是 yt-dlp 使用的 aweme API 需要动态签名（尤其 `a_bogus`），不是单纯缺 Cookie。**  
本项目通过 **绕过该 API、解析 SSR 页面 `RENDER_DATA` 获取 CDN 直链** 实现稳定解析与下载，其它平台继续使用 yt-dlp。
