# Lakebook → Obsidian（语雀知识库转 Markdown）

将语雀导出的 `.lakebook` 知识库转为 Obsidian 可用的 Markdown：保留目录层级，图片下载到本地。

## 使用方法

1. **把语雀导出的 `.lakebook` 文件放入项目里的 `yuque` 文件夹**
2. **首次使用**：创建虚拟环境并安装依赖
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. **执行批量转换**（会转换 `yuque` 下所有 `.lakebook`，输出到 `out/`）
   ```bash
   .venv/bin/python scripts/batch_convert.py
   ```

转换完成后，在 `out/` 下按知识库名称生成子目录，每个知识库的文档和图片（在对应 `assets/` 中）都在其中，可直接用 Obsidian 打开 `out/` 作为仓库。

## 可选：单文件转换

指定单个 `.lakebook` 和输出目录：

```bash
PYTHONPATH=src .venv/bin/python -m yuque_export --lakebook yuque/某知识库.lakebook --output out/某知识库
```
安装后也可使用：`lakebook2obsidian --lakebook ... --output ...`

常用参数：`--no-images` 不下载图片；`--no-frontmatter` 不写 YAML；`--unique-suffix` 文件名加 8 位后缀。

## License

MIT
