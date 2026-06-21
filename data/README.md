# 汉字数据说明

`naming_characters.json` 是应用运行时直接读取的离线生产数据，包含8105个规范汉字。其他机器克隆仓库后无需下载原始数据，也无需联网。

## 数据分层

- 基础层：8105字，用于笔画、拼音、部首、释义和五行查询。
- 姓名精选层：其中889字满足公开数据含五行、含释义且进入项目编辑精选清单。
- 项目人工校订层：`app.py` 中少量已复核姓名字优先覆盖公开数据，因此运行时推荐池共903字。

没有公开五行属性的字仍保留在基础层，但不会被猜测归类，也不会参与评分或自动起名。

## 来源与许可证

1. [ben-hua/general_standard_chinese](https://github.com/ben-hua/general_standard_chinese)，Apache-2.0。提供《通用规范汉字表》衍生的拼音、部首、笔画和五行字段，项目构建时使用 `backup/word_05_31.csv`。
2. [pwxcoo/chinese-xinhua](https://github.com/pwxcoo/chinese-xinhua)，MIT。提供中文释义，项目构建时使用 `data/word.json`。

每条数据均保留 `source` 字段。五行归类不是国家统一标准，产品只透明采用数据源提供的分类。
原始许可证文本保存在本目录的 `licenses/` 中，并随项目分发。

## 重建

原始约27MB新华字典和CSV只在重建时使用，不提交仓库：

```powershell
python scripts/build_character_data.py `
  .cache/general_standard_chinese.csv `
  .cache/xinhua_word.json `
  data/naming_characters.json
```

构建脚本会校验基础层数量在8000–8200之间、精选层不少于500字，并检查五行分布。
