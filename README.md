# 拾名（Good Name, Good Life）

面向中文姓名场景的本地 Web 应用，提供姓名评分、八字五行智能起名和重名风险预测。

> 命理、姓名学五行及卦象不属于可被科学验证的预测方法。本项目用于传统文化参考，不应替代医疗、法律、教育或人生决策建议。

## 功能

- 姓名评分：统一计算音韵、字形、寓意、五行和姓名卦象。
- 智能起名：根据姓氏、出生日期、十二时辰、性别和气质偏好动态组合名字。
- 五行分析：通过节气万年历排四柱，展示五行计数、缺失项和补益规则。
- 优先用字：可指定一个优先汉字，在不破坏五行与质量要求的前提下尽量采用。
- 双向比较：评分结果可一键进入起名；候选名可一键带参数返回评分。
- 候选管理：收藏候选、并排对比、导出 JSON 和打印报告。
- 规则版本：可切换“缺失补足/月令平衡”和“综合均衡/五行侧重”。
- 隐私控制：查询历史默认不保存，用户可主动开启本地历史记录。
- AI 姓名顾问：可选的语义、气质、谐音歧义和文化意象分析，不改变确定性评分。
- AI 功能使用独立 Tab；评分页和候选名可携带参数一键进入。
- 重名风险：根据姓氏常见度、名字结构和高频用字输出透明风险等级，不伪造人口数量。

## 快速启动

要求 Python 3.10 或更高版本。

```powershell
cd D:\cbx\IdeaProjects\good-name-life
python -m pip install -r requirements.txt
python app.py
```

访问 http://127.0.0.1:8000 。Windows 也可以直接双击 `start.bat`。

指定其他端口：

```powershell
$env:SHIMING_PORT=8080
python app.py
```

## 项目结构

```text
good-name-life/
├── app.py               # HTTP 服务、排盘、评分、起名及风险模型
├── app.js               # 页面交互、API 请求及跨页面参数传递
├── index.html           # 单页应用结构
├── styles.css           # 响应式视觉样式
├── requirements.txt     # Python 依赖
├── start.bat            # Windows 一键启动脚本
├── PRODUCT_DESIGN.md    # 产品设计与规则说明
├── README.md
└── .gitignore
```

查询历史默认关闭；用户主动开启后才会生成 `shiming.db`，该文件已被 Git 忽略。候选收藏保存在浏览器 `localStorage`。

## 外部数据配置

未配置授权外部数据时，程序保持现有内置字库和透明风险模型，不伪造在线结果。

```powershell
$env:SHIMING_CHAR_API_URL="https://provider.example/character"
$env:SHIMING_CHAR_API_KEY="your-api-key"
$env:SHIMING_POPULATION_API_URL="https://provider.example/population"
$env:SHIMING_POPULATION_API_KEY="your-api-key"
$env:SHIMING_NAME_CORPUS="D:\data\authorized-name-corpus.json"
$env:OPENAI_API_KEY="your-openai-api-key"
$env:SHIMING_AI_MODEL="gpt-5.5"
python app.py
```

汉字 API 请求为 `{ "char": "珩" }`，响应必须提供 `strokes`、`element`、`meaning`、`source`。人口 API 请求为 `{ "name": "张伟" }`，响应必须提供 `total`、`source`，可选 `male` 和 `female`。

授权姓名语料格式：

```json
{
  "source": "数据集名称与授权说明",
  "bigrams": { "安宁": 120, "知远": 85 },
  "ambiguous_terms": ["不雅谐音词"]
}
```

## 评分规则

所有页面共用唯一的确定性评分函数，同一姓名和生辰参数不会因重新生成而改变分数。气质风格只影响候选排序，不参与评分。

| 指标 | 权重 | 依据 |
| --- | ---: | --- |
| 音韵 | 18% | `pypinyin` 声调组合变化 |
| 字形 | 14% | 收录字的笔画差与结构均衡 |
| 寓意 | 18% | 内置释义字库覆盖情况 |
| 五行 | 35% | 名字用字对八字缺失或少量元素的覆盖 |
| 卦象 | 15% | 姓氏与名字笔画所得上下卦及其五行匹配 |

八字由 `lunar-python 1.4.8` 按公历、北京时间和节气排盘。当前产品规则为：八个干支本气中计数为 0 的元素视为缺失；没有缺失时，取计数最少项作为起名参考。这是明确的产品规则，不等同于所有传统命理流派的“喜用神”判断。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 服务健康状态 |
| POST | `/api/score` | 姓名评分 |
| POST | `/api/names` | 智能起名 |
| POST | `/api/population` | 重名风险预测 |
| GET | `/api/ai/status` | AI 姓名顾问配置状态 |
| POST | `/api/ai/analyze` | AI 姓名语义体检 |

姓名评分请求示例：

```json
{
  "name": "曹芷晴",
  "birth": "2023-01-25",
  "birth_time": "17:00",
  "gender": "女"
}
```

智能起名请求示例：

```json
{
  "surname": "曹",
  "birth": "2023-01-25",
  "birth_time": "17:00",
  "gender": "girl",
  "style": "elegant",
  "fixed_char": "安"
}
```

## 数据边界

- 姓名字库未收录的汉字会明确报错，不使用随机笔画或五行兜底。
- 字的五行归类并无国家统一标准；项目采用内置姓名学规则并公开计算依据。
- 出生时间采用十二时辰和北京时间，未计算出生地真太阳时。
- 重名风险属于启发式评估，不是公安人口查询，不返回估算人数。
- 若接入在线字典或人口数据，必须使用合法授权 API，并在结果中标明数据来源。

更完整的需求、用户流程和后续规划见 [PRODUCT_DESIGN.md](PRODUCT_DESIGN.md)。

AI 语义分析、约束式起名和对话顾问的完整方案见 [AI_FEATURE_DESIGN.md](AI_FEATURE_DESIGN.md)。
AI 语义体检已接入 OpenAI Responses API；未配置 `OPENAI_API_KEY` 时保持禁用且不生成模拟分析。约束式 AI 起名和多轮对话仍按设计分阶段实现。
