# Waline 评论区嵌入规范（供追加到报告生成类 cronjob prompt 末尾）

## 规范段落（可直接粘贴到 prompt 末尾）

---

**评论区组件（必须执行，与上述导航栏/面包屑规范并存，不冲突）：**

1. 在生成的报告 HTML 中，于 `</body>` 结束标签**之前**插入 Waline 评论区。
2. 嵌入代码（根目录报告使用以下原样代码；若报告位于子目录（如 `gold-etf/`、`world-cup-2026/`、`gpt6-astra/`），则把两处资源路径的 `assets/` 前缀改为 `../assets/`）：

```html
<!-- Waline 评论区 -->
<link rel="stylesheet" href="assets/waline/waline.css" />
<div id="waline-comments" style="max-width: 960px; margin: 48px auto 0; padding: 0 24px;"></div>
<script src="assets/waline/waline.umd.js"></script>
<script>
  Waline.init({
    el: '#waline-comments',
    serverURL: 'https://comment.hosamzj.cn',
    path: location.pathname.replace(/\.html$/, ''),
    dark: 'body',
    lang: 'zh-CN',
    pageview: true
  });
</script>
```

3. **幂等要求**：写入前先检查文件内容，若已包含 `waline-comments` 字符串则跳过插入，不得重复嵌入。
4. 评论区插入位置在面包屑、正文和页脚之后、`</body>` 之前，不得破坏既有 navbar、breadcrumb、设计 token（`--accent: #c96442`）等规范。
5. 对于由脚本生成 HTML 的任务（prompt 本身不直接产出 HTML 的情况），必须将上述代码块同步写入生成脚本的 HTML 模板中（同样在 `</body>` 前），而不是只改输出文件。
