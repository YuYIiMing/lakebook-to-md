# Lakebook → Obsidian（语雀知识库转 Markdown）

将语雀导出的 `.lakebook` 知识库转为 Obsidian 可用的 Markdown：保留目录层级，图片下载到本地。

## 使用方法（从零开始）

按顺序执行下面几步即可。

**第一步：克隆项目到本地**

```bash
git clone https://github.com/YuYIiMing/lakebook-to-md.git
cd lakebook-to-md
```

**第二步：把要转换的语雀文件放进 `yuque` 文件夹**

- 在语雀里导出知识库，得到 `.lakebook` 文件
- 把这些文件放进刚克隆下来的项目里的 `yuque` 文件夹（没有就新建一个）

**第三步：安装依赖（只需做一次）**

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**第四步：执行转换**

```bash
.venv/bin/python scripts/batch_convert.py
```
完成后，所有转换好的 Markdown 和图片会在 **`out/`** 文件夹里，按知识库分好了目录。 移动到Obsidian仓库即可使用。


## 可选：单文件转换

指定单个 `.lakebook` 和输出目录：

```bash
PYTHONPATH=src .venv/bin/python -m yuque_export --lakebook yuque/某知识库.lakebook --output out/某知识库
```
安装后也可使用：`lakebook2obsidian --lakebook ... --output ...`

常用参数：`--no-images` 不下载图片；`--no-frontmatter` 不写 YAML；`--unique-suffix` 文件名加 8 位后缀。

## License

MIT
