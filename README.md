# 拾名（Good Name, Good Life）

可直接运行的中文姓名文化 Web 程序，包含四柱八字与五行姓名评分、支持指定用字的智能起名和重名风险预测。

## 立即启动

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

Windows 可以直接双击 `start.bat`，它会启动服务并打开浏览器。

```powershell
cd D:\cbx\IdeaProjects\good-name-life
python app.py
```

浏览器访问：http://127.0.0.1:8000

按 `Ctrl+C` 停止。端口被占用时可以这样启动：

```powershell
$env:SHIMING_PORT=8080
python app.py
```

## 数据说明

- 页面与 JSON API 由 Python 提供。
- 查询记录保存在自动创建的 `shiming.db` 中。
- 重名功能仅输出透明规则计算的风险分值，不生成或估算公安同名人数。
- 八字通过 `lunar-python 1.4.8` 按公历、北京时间和节气排盘，不再使用近似节气边界。
- 补五行规则严格执行“八字八个干支本气计数为 0 即缺失，名字必须含缺失属性字”；五行齐全时取数量最少项。
- 命理及姓名学五行并非可被科学验证的预测方法，结果属于传统文化参考。
- 出生时辰采用十二时辰；候选名从五行用字库动态组合，每次生成会在高匹配候选中变化。
- 智能起名可额外指定一个优先汉字；留空时按原逻辑生成，指定后在满足补五行和质量要求的前提下尽量采用。
- 若取得合法 API 授权，可替换 `app.py` 中的 `population()` 数据源。

## API

- `GET /api/health`
- `POST /api/score`
- `POST /api/names`
- `POST /api/divination`
- `POST /api/population`
