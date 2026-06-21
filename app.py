"""拾名：可解释的中文姓名文化 Web 应用。"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sqlite3
from datetime import date, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from lunar_python import Solar
from pypinyin import Style, pinyin


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "shiming.db"
HOST = os.getenv("SHIMING_HOST", "127.0.0.1")
PORT = int(os.getenv("SHIMING_PORT", "8000"))
CHAR_API_URL = os.getenv("SHIMING_CHAR_API_URL", "").strip()
CHAR_API_KEY = os.getenv("SHIMING_CHAR_API_KEY", "").strip()
POPULATION_API_URL = os.getenv("SHIMING_POPULATION_API_URL", "").strip()
POPULATION_API_KEY = os.getenv("SHIMING_POPULATION_API_KEY", "").strip()
NAME_CORPUS_PATH = os.getenv("SHIMING_NAME_CORPUS", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
AI_API_URL = os.getenv("SHIMING_AI_API_URL", "https://api.openai.com/v1/responses").strip()
AI_MODEL = os.getenv("SHIMING_AI_MODEL", "gpt-5.5").strip()
AI_TIMEOUT = int(os.getenv("SHIMING_AI_TIMEOUT", "30"))
AI_ENABLED = bool(OPENAI_API_KEY) and os.getenv("SHIMING_AI_ENABLED", "true").lower() in ("1", "true", "yes")
CHINESE_NAME = re.compile(r"^[\u3400-\u9fff·]{2,6}$")
SURNAME = re.compile(r"^[\u3400-\u9fff]{1,2}$")

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ELEMENTS = ("木", "火", "土", "金", "水")
STEM_ELEMENT = {c: ELEMENTS[i // 2] for i, c in enumerate(STEMS)}
BRANCH_ELEMENT = dict(zip(BRANCHES, ("水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水")))
BAGUA = {1: ("乾", "金"), 2: ("兑", "金"), 3: ("离", "火"), 4: ("震", "木"),
         5: ("巽", "木"), 6: ("坎", "水"), 7: ("艮", "土"), 0: ("坤", "土")}

CHAR_INFO = {
    "安": (6, "土", "平安从容"), "宁": (5, "火", "安宁笃定"), "清": (11, "水", "清澈正直"),
    "和": (8, "水", "温润和美"), "景": (12, "木", "前程明朗"), "知": (8, "火", "明理聪慧"),
    "远": (7, "土", "志向高远"), "云": (4, "水", "自在旷达"), "川": (3, "金", "胸怀开阔"),
    "舟": (6, "金", "坚定有向"), "怀": (7, "水", "胸怀宽广"), "瑾": (15, "火", "美德如玉"),
    "嘉": (14, "木", "美好嘉善"), "禾": (5, "水", "丰足质朴"), "若": (8, "木", "温柔从容"),
    "棠": (12, "木", "明艳高雅"), "舒": (12, "金", "舒展自在"), "书": (4, "金", "博学知礼"),
    "辰": (7, "土", "如星璀璨"), "星": (9, "金", "光明闪耀"), "言": (7, "木", "诚信善思"),
    "初": (7, "金", "初心澄澈"), "乐": (5, "火", "乐观开朗"), "月": (4, "木", "澄明温柔"),
    "砚": (9, "土", "勤学沉静"), "屿": (6, "土", "坚定安稳"), "行": (6, "水", "笃实力行"),
    "卓": (8, "火", "卓然出众"), "蹊": (17, "木", "自成芳径"), "南": (9, "火", "温暖明朗"),
    "乔": (6, "木", "高雅挺拔"), "时": (7, "火", "顺时明达"), "雨": (8, "水", "润泽万物"),
    "令": (5, "火", "美善端方"), "仪": (5, "木", "仪态端庄"), "予": (4, "土", "慷慨温厚"),
    "见": (4, "木", "见识通达"), "野": (11, "土", "旷达自由"), "亦": (6, "土", "从容坚定"),
    "以": (5, "土", "持守有度"), "越": (12, "土", "超越进取"), "望": (11, "水", "志有所向"),
    "梓": (11, "木", "生机蓬勃"), "楠": (13, "木", "坚贞贵重"), "桐": (10, "木", "高洁祥瑞"),
    "芊": (6, "木", "草木葱茏"), "芷": (7, "木", "清雅芬芳"), "茗": (9, "木", "清雅有致"),
    "栩": (10, "木", "灵动有神"), "森": (12, "木", "蓬勃丰茂"), "柠": (9, "木", "清新明朗"),
    "榆": (13, "木", "坚韧安定"), "昕": (8, "火", "晨光初现"), "昭": (9, "火", "光明坦荡"),
    "晴": (12, "火", "晴朗开阔"), "晗": (11, "火", "天将明亮"), "晨": (11, "火", "朝气希望"),
    "煜": (13, "火", "光耀灿然"), "烨": (10, "火", "光彩明盛"), "彤": (7, "火", "热情明丽"),
    "夏": (10, "火", "明朗热烈"), "昱": (9, "火", "日光照耀"), "朗": (10, "火", "明朗豁达"),
    "宇": (6, "土", "气宇开阔"), "宥": (9, "土", "宽厚包容"), "依": (8, "土", "温柔可信"),
    "岚": (7, "土", "山岚清逸"), "怡": (8, "土", "和悦安然"), "允": (4, "土", "诚信公允"),
    "岳": (8, "土", "稳重如山"), "坤": (8, "土", "厚德载物"), "垚": (9, "土", "厚重稳健"),
    "锦": (13, "金", "锦绣美好"), "钰": (10, "金", "珍宝坚贞"), "铭": (11, "金", "铭志不忘"),
    "铄": (10, "金", "明亮刚健"), "锐": (12, "金", "敏锐进取"), "诗": (8, "金", "诗意文雅"),
    "悦": (10, "金", "喜悦和畅"), "瑞": (13, "金", "祥瑞美好"), "珩": (10, "金", "美玉端方"),
    "泽": (8, "水", "恩泽润物"), "涵": (11, "水", "涵养宽广"), "沐": (7, "水", "润泽清新"),
    "溪": (13, "水", "清澈灵动"), "澜": (15, "水", "胸怀壮阔"), "泓": (8, "水", "水深而广"),
    "汐": (6, "水", "温柔守时"), "洛": (9, "水", "灵秀从容"), "霖": (16, "水", "甘霖润泽"),
    "凡": (3, "水", "质朴笃实"), "渝": (12, "水", "坚定不改"),
}

# 可用于组合起名的人工校订字库。五行归类属于本产品采用的姓名学规则，
# 笔画使用简体常用字笔画；不把未收录字随机归类。
CHAR_INFO.update({
    "柏": (9, "木", "坚韧常青"), "松": (8, "木", "坚贞长青"), "枫": (8, "木", "明朗洒脱"),
    "楚": (13, "木", "清晰端正"), "萱": (12, "木", "温雅明媚"), "芮": (7, "木", "柔韧新生"),
    "芙": (7, "木", "清雅秀美"), "芸": (7, "木", "勤勉芬芳"), "莉": (10, "木", "清雅芳洁"),
    "蕙": (15, "木", "蕙质兰心"), "竹": (6, "木", "虚心有节"), "筠": (13, "木", "温润有节"),
    "筱": (13, "木", "清秀坚韧"), "朵": (6, "木", "自然明媚"), "杉": (7, "木", "挺拔质朴"),
    "柯": (9, "木", "端正有则"), "柳": (9, "木", "柔韧清新"), "棋": (12, "木", "沉着善思"),
    "启": (7, "木", "启明开拓"), "隽": (10, "木", "才思出众"),
    "明": (8, "火", "光明通达"), "旭": (6, "火", "旭日初升"), "曦": (20, "火", "晨曦光明"),
    "曜": (18, "火", "光耀明盛"), "晟": (10, "火", "光明兴盛"), "炜": (8, "火", "光彩鲜明"),
    "焱": (12, "火", "光华炽盛"), "灿": (7, "火", "灿然明朗"), "炫": (9, "火", "光彩夺目"),
    "熠": (15, "火", "熠熠生辉"), "暖": (13, "火", "温暖和煦"), "映": (9, "火", "光彩映照"),
    "昀": (8, "火", "日光温润"), "易": (8, "火", "平和通达"), "丹": (4, "火", "赤诚明丽"),
    "灵": (7, "火", "灵秀聪敏"), "智": (12, "火", "聪慧明理"), "亭": (9, "火", "端正挺拔"),
    "光": (6, "火", "光明磊落"), "熙": (14, "火", "和乐光明"),
    "维": (11, "土", "持守有度"), "轩": (7, "土", "气度轩昂"), "羽": (6, "土", "轻盈高远"),
    "韵": (13, "土", "气韵雅致"), "恩": (10, "土", "仁厚感恩"), "唯": (11, "土", "专注坚定"),
    "岩": (8, "土", "坚定稳重"), "岑": (7, "土", "沉静秀拔"), "峰": (10, "土", "卓然向上"),
    "峻": (10, "土", "高峻正直"), "嵘": (12, "土", "卓越不凡"), "城": (9, "土", "坚实可靠"),
    "培": (11, "土", "培根厚积"), "均": (7, "土", "平衡公允"), "逸": (11, "土", "从容超逸"),
    "艾": (5, "土", "美好安康"), "玮": (8, "土", "珍奇美好"), "益": (10, "土", "增益向善"),
    "友": (4, "土", "友善真诚"), "圣": (5, "土", "明达高尚"),
    "钧": (9, "金", "公正持衡"), "铠": (11, "金", "坚毅守护"), "铮": (11, "金", "刚正有声"),
    "钦": (9, "金", "敬慎庄重"), "钊": (7, "金", "勉励进取"), "锴": (14, "金", "刚健端正"),
    "锟": (13, "金", "坚韧如玉"), "锶": (14, "金", "沉静坚韧"), "铃": (10, "金", "清越灵动"),
    "钟": (9, "金", "专注凝聚"), "鑫": (24, "金", "兴盛丰足"), "成": (6, "金", "有志竟成"),
    "承": (8, "金", "担当传承"), "诚": (8, "金", "真诚守信"), "思": (9, "金", "善思明辨"),
    "如": (6, "金", "从容如意"), "素": (10, "金", "质朴纯真"), "紫": (12, "金", "典雅庄重"),
    "靖": (13, "金", "安定恭谨"), "静": (14, "金", "沉静从容"), "纯": (7, "金", "纯粹真诚"),
    "正": (5, "金", "正直端方"), "则": (6, "金", "有原则有分寸"),
    "洋": (9, "水", "开阔丰盛"), "浩": (10, "水", "浩然广阔"), "海": (10, "水", "胸怀宽广"),
    "润": (10, "水", "温润泽物"), "淳": (11, "水", "淳厚质朴"), "渊": (11, "水", "渊博深沉"),
    "潇": (14, "水", "潇洒清朗"), "湘": (12, "水", "灵秀悠远"), "洁": (9, "水", "洁净正直"),
    "沁": (7, "水", "清新沁润"), "泉": (9, "水", "源远流长"), "波": (8, "水", "灵动进取"),
    "涛": (10, "水", "气势进取"), "潮": (15, "水", "蓬勃有势"), "霏": (16, "水", "轻盈润泽"),
    "露": (21, "水", "清莹坦荡"), "雪": (11, "水", "澄澈纯洁"), "霞": (17, "水", "绚丽舒展"),
    "文": (4, "水", "文雅有识"), "斐": (12, "水", "文采出众"), "鸿": (11, "水", "志向高远"),
    "鸣": (8, "水", "一鸣有声"), "澄": (15, "水", "澄明通透"),
})

CHAR_DATA_PATH = ROOT / "data" / "naming_characters.json"
CHAR_DATA = json.loads(CHAR_DATA_PATH.read_text(encoding="utf-8")) if CHAR_DATA_PATH.exists() else {
    "base_character_count": len(CHAR_INFO), "eligible_character_count": len(CHAR_INFO),
    "sources": [], "characters": {},
}
BASE_CHAR_INFO = CHAR_DATA.get("characters", {})
CHAR_SOURCES = {char: "项目人工校订姓名字库" for char in CHAR_INFO}
for char, item in BASE_CHAR_INFO.items():
    if item.get("name_eligible") and item.get("element") in ELEMENTS and item.get("meaning"):
        if char not in CHAR_INFO:
            CHAR_INFO[char] = (int(item["strokes"]), item["element"], item["meaning"])
        CHAR_SOURCES.setdefault(char, item.get("source", "离线规范汉字数据"))

NAMING_CHARS = {
    element: [char for char, info in CHAR_INFO.items() if info[1] == element]
    for element in ELEMENTS
}
FEMININE_CHARS = set("丽仪伊俐俪倩依妍妙妤妮姿娅娜娟娴婉婕婷媛嫣姝姣姬娉婧嫒嫦媚嬿彩彤怡悦惠慧晴晶暖燕爱玥玲珊珍珞珠琬琳琴琼瑄瑛瑶璇璐美芊芷若棠月萱芮芙芸莉蕙筱朵丹灵艾铃如静沁霏露雪霞雯霓香馥馨")
MASCULINE_CHARS = set("伟俊健军刚力功勇勋卓国坚坤城培壮宇宏宗宝富尧山岩岳岸峰峻崇嵘帅建弘强彬彪彰征振政斌旭昂昊晟晋朗栋梁森楷正武毅涛瀚炎炜焱煊皓磊禹立翰耀腾舜舟豪超跃轩辉达迈远钊钧铠铮锐锴锟隆雄骁骐骞骥鸿鹏鹤麟钧铠铮钊锴锟成承正浩海潮鸣松柏砚")
STYLE_CHARS = {
    "elegant": set("清舒诗芷若桐茗岚溪洛月宁珩萱芙芸蕙竹筠筱柳韵逸铃如素静沁霏雪澄"),
    "bright": set("昕昭晴晨煜烨彤夏南昱朗景卓泽明旭曦曜晟炜灿炫熠映昀光熙")
              | set("启枫乔森栩棠辰宇轩羽峰玮锦星悦瑞铃铄澜霖霞洋潇鸿鸣潮"),
    "learned": set("知书砚铭景嘉言瑾怀珩茗楚棋隽智维思承诚靖文斐渊淳正则")
}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 仅用于重名风险的分档参考，不表示精确人口比例。
VERY_COMMON_SURNAMES = set("王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万覃武钱戴严莫孔向常汤")
COMMON_GIVEN_CHARS = set("伟芳娜秀英敏静丽强磊军洋勇艳杰娟涛超明华平刚桂丹萍鑫浩宇轩涵梓睿欣怡子雨晨嘉一可思琪俊泽昊博文佳诗梦安宁辰诺玥熙宸")
VERY_COMMON_FULL_NAMES = {"张伟", "王伟", "王芳", "李伟", "李娜", "张敏", "刘伟", "王静", "刘洋", "陈伟", "杨洋", "赵静", "李静", "王丽", "张丽"}


def load_name_corpus() -> dict:
    if not NAME_CORPUS_PATH:
        return {}
    path = Path(NAME_CORPUS_PATH).expanduser().resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data.get("bigrams", {}), dict) or not data.get("source"):
            raise ValueError
        return data
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("姓名语料文件必须是包含 source、bigrams 和可选 ambiguous_terms 的合法 JSON") from exc


NAME_CORPUS = load_name_corpus()

COMMON_SURNAME_STROKES = {"赵": 9, "钱": 10, "孙": 6, "李": 7, "周": 8, "吴": 7, "郑": 8, "王": 4,
                          "冯": 5, "陈": 7, "褚": 13, "卫": 3, "蒋": 12, "沈": 7, "韩": 12, "杨": 7,
                          "朱": 6, "秦": 10, "许": 6, "何": 7, "吕": 6, "张": 7, "孔": 4, "曹": 11,
                          "严": 7, "华": 6, "金": 8, "魏": 17, "陶": 10, "姜": 9, "谢": 12, "邹": 7,
                          "喻": 12, "柏": 9, "水": 4, "窦": 13, "章": 11, "云": 4, "苏": 7, "潘": 15,
                          "葛": 12, "范": 8, "彭": 12, "郎": 8, "鲁": 12, "韦": 4, "昌": 8, "马": 3,
                          "苗": 8, "凤": 4, "花": 7, "方": 4, "俞": 9, "任": 6, "袁": 10, "柳": 9,
                          "鲍": 13, "史": 5, "唐": 10, "费": 9, "廉": 13, "岑": 7, "薛": 16, "雷": 13,
                          "贺": 9, "倪": 10, "汤": 6, "滕": 15, "殷": 10, "罗": 8, "毕": 6, "郝": 9,
                          "邬": 6, "安": 6, "常": 11, "乐": 5, "于": 3, "傅": 12, "皮": 5, "卞": 4,
                          "齐": 6, "康": 11, "伍": 6, "余": 7, "元": 4, "卜": 2, "顾": 10, "孟": 8,
                          "平": 5, "黄": 11, "和": 8, "穆": 16, "萧": 11, "尹": 4, "林": 8}
COMMON_SURNAME_STROKES.update({
    "丁": 2, "万": 3, "付": 5, "侯": 9, "刘": 6, "卢": 5, "叶": 5, "向": 6, "夏": 10,
    "姚": 9, "宋": 7, "崔": 11, "廖": 14, "徐": 10, "戴": 17, "曾": 12, "杜": 7,
    "梁": 11, "武": 8, "段": 9, "毛": 4, "江": 6, "汪": 7, "熊": 14, "田": 5,
    "白": 5, "石": 5, "程": 12, "肖": 7, "胡": 9, "莫": 10, "董": 12, "蔡": 14,
    "覃": 12, "谭": 14, "贾": 10, "邓": 4, "邱": 7, "邵": 7, "郭": 10, "钟": 9,
    "闫": 6, "陆": 7, "高": 10, "黎": 15, "龙": 5, "龚": 11,
})

HEXAGRAMS = [
    ("乾为天", "自强不息", "当下宜主动谋划、稳步行动。目标虽远，守正并坚持，局面便会逐渐打开。"),
    ("地山谦", "谦谦君子", "保持克制与谦逊比急于证明自己更重要。适合先完善准备，再等待合适时机。"),
    ("风水涣", "涣然冰释", "阻滞正在松动，沟通是关键。把复杂问题拆开处理，先求共识，再谈推进。"),
    ("水火既济", "守成有度", "事情已有较好基础，越接近完成越需谨慎。留心细节，避免因松懈产生反复。"),
    ("雷风恒", "持之以恒", "短期变化并非重点，稳定节奏更有价值。选择长期正确的方向，持续积累。"),
    ("火地晋", "明出地上", "当前有向上生长之势。宜展示真实能力，同时照顾协作关系，不可冒进。"),
    ("山水蒙", "启蒙求知", "信息尚不充分，贸然决定容易反复。主动求教、补全事实，会比猜测更有效。"),
    ("泽山咸", "感而遂通", "真诚互动能促成转机。先听懂对方的关切，再表达自己的立场。"),
]


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    try:
        db.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature TEXT NOT NULL, input_text TEXT NOT NULL,
            result_json TEXT NOT NULL, created_at TEXT NOT NULL)""")
        db.commit()
    finally:
        db.close()


def save_history(feature: str, input_text: str, result: dict, enabled: bool = False) -> None:
    if not enabled:
        return
    init_db()
    db = sqlite3.connect(DB_PATH)
    try:
        db.execute("INSERT INTO history(feature,input_text,result_json,created_at) VALUES(?,?,?,?)",
                   (feature, input_text, json.dumps(result, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")))
        db.commit()
    finally:
        db.close()


def stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def require_text(data: dict, key: str, pattern: re.Pattern, label: str) -> str:
    value = str(data.get(key, "")).strip()
    if not pattern.fullmatch(value):
        raise ValueError(f"{label}格式不正确")
    return value


def parse_birth(value: object) -> date:
    try:
        birth = date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("出生日期格式不正确") from exc
    if birth > date.today() or birth.year < 1900:
        raise ValueError("出生日期超出有效范围")
    return birth


def parse_birth_time(value: object) -> tuple[int, int]:
    try:
        parts = str(value).split(":")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        return hour, minute
    except (ValueError, IndexError) as exc:
        raise ValueError("请选择准确的出生时辰") from exc


def calculate_bazi(birth: date, birth_time: tuple[int, int]) -> dict:
    """通过 lunar-python 的节气万年历排四柱，按八个干支本气统计五行。"""
    hour, minute = birth_time
    solar = Solar.fromYmdHms(birth.year, birth.month, birth.day, hour, minute, 0)
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()
    eight_char.setSect(2)
    pillars = [eight_char.getYear(), eight_char.getMonth(), eight_char.getDay(), eight_char.getTime()]
    counts = {element: 0 for element in ELEMENTS}
    for pillar in pillars:
        counts[STEM_ELEMENT[pillar[0]]] += 1
        counts[BRANCH_ELEMENT[pillar[1]]] += 1
    seasonal = BRANCH_ELEMENT[pillars[1][1]]
    missing = [element for element in ELEMENTS if counts[element] == 0]
    if missing:
        favorable = missing
        required_elements = missing[:2]
        rule = "缺失五行直接补足"
    else:
        minimum = min(counts.values())
        favorable = [element for element in ELEMENTS if counts[element] == minimum][:2]
        required_elements = []
        rule = "五行齐全，取数量最少项"
    return {"pillars": pillars, "counts": counts, "day_master": STEM_ELEMENT[pillars[2][0]],
            "seasonal": seasonal, "missing": missing, "favorable": favorable, "rule": rule,
            "required_elements": required_elements,
            "lunar_date": lunar.toString(), "calendar_source": "lunar-python 1.4.8"}


def _external_char_profile(char: str) -> tuple[int, str, str, str] | None:
    if not CHAR_API_URL:
        return None
    payload = json.dumps({"char": char}, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if CHAR_API_KEY:
        headers["Authorization"] = f"Bearer {CHAR_API_KEY}"
        headers["X-API-Key"] = CHAR_API_KEY
    try:
        with urlopen(Request(CHAR_API_URL, data=payload, headers=headers, method="POST"), timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
        item = body.get("data", body)
        strokes, element = int(item["strokes"]), str(item["element"])
        meaning, source = str(item["meaning"]), str(item["source"])
        if not (1 <= strokes <= 64 and element in ELEMENTS and meaning and source):
            raise ValueError
        return strokes, element, meaning, source
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"在线字典未能返回“{char}”的有效笔画、五行、释义和来源") from exc


def char_profile(char: str) -> tuple[int, str, str, str]:
    if char in CHAR_INFO:
        return (*CHAR_INFO[char], CHAR_SOURCES.get(char, "内置姓名字库"))
    if char in BASE_CHAR_INFO:
        item = BASE_CHAR_INFO[char]
        if item.get("element") not in ELEMENTS:
            raise ValueError(f"基础字库已收录“{char}”，但公开数据未提供五行，无法在不猜测的前提下评分")
        return (int(item["strokes"]), item["element"], item.get("meaning") or "规范汉字",
                item.get("source", "离线规范汉字数据"))
    if char in COMMON_SURNAME_STROKES:
        strokes = COMMON_SURNAME_STROKES[char]
        last = strokes % 10
        element = "木" if last in (1, 2) else "火" if last in (3, 4) else "土" if last in (5, 6) else "金" if last in (7, 8) else "水"
        return strokes, element, "按姓名学笔画数理归类", "内置常见姓氏表"
    external = _external_char_profile(char)
    if external:
        return external
    raise ValueError(f"姓名字库暂未收录“{char}”，无法在不猜测的前提下判定五行")


COMPOUND_SURNAMES = ("欧阳", "司马", "上官", "诸葛", "东方", "皇甫", "尉迟", "公孙", "慕容", "司徒")


def split_full_name(name: str) -> tuple[str, str]:
    surname = name[:2] if name[:2] in COMPOUND_SURNAMES else name[0]
    return surname, name[len(surname):]


def name_trigram(name: str) -> dict:
    surname, given = split_full_name(name)
    surname_strokes = sum(char_profile(char)[0] for char in surname)
    given_strokes = sum(char_profile(char)[0] for char in given)
    upper, upper_element = BAGUA[surname_strokes % 8]
    lower, lower_element = BAGUA[given_strokes % 8]
    return {"name": f"{upper}上{lower}下", "upper": upper, "lower": lower,
            "elements": [upper_element, lower_element]}


def normalize_gender(value: str) -> str:
    return "boy" if value in ("男", "男孩", "boy") else "girl" if value in ("女", "女孩", "girl") else "neutral"


def evaluate_name(name: str, birth: date, birth_time: tuple[int, int], gender: str,
                  bazi: dict | None = None) -> dict:
    """唯一姓名评分入口；所有指标确定性计算，禁止随机数和风格加分。"""
    _, given = split_full_name(name)
    if not given:
        raise ValueError("请输入包含名字的完整姓名")
    profiles = [char_profile(char) for char in name]
    given_profiles = [char_profile(char) for char in given]
    bazi = bazi or calculate_bazi(birth, birth_time)
    trigram = name_trigram(name)

    tone_values = []
    for item in pinyin(name, style=Style.TONE3, neutral_tone_with_five=True):
        match = re.search(r"([1-5])$", item[0])
        tone_values.append(int(match.group(1)) if match else 5)
    adjacent = max(1, len(tone_values) - 1)
    different_tones = sum(a != b for a, b in zip(tone_values, tone_values[1:]))
    pronunciation = round(78 + 14 * different_tones / adjacent + (4 if len(set(tone_values)) >= min(3, len(tone_values)) else 0))
    pronunciation = min(96, pronunciation)

    strokes = [profile[0] for profile in profiles]
    spread = max(strokes) - min(strokes)
    adjacent_gap = sum(abs(a - b) for a, b in zip(strokes, strokes[1:])) / max(1, len(strokes) - 1)
    shape = round(max(72, 96 - spread * .8 - adjacent_gap * .7))

    known_meanings = sum(char in CHAR_INFO for char in given)
    meaning = round(78 + 14 * known_meanings / len(given))

    name_elements = [profile[1] for profile in profiles]
    given_elements = [profile[1] for profile in given_profiles]
    if bazi["required_elements"]:
        covered = len(set(bazi["required_elements"]) & set(given_elements))
        element_score = round(62 + 36 * covered / len(bazi["required_elements"]))
    else:
        matches = sum(element in bazi["favorable"] for element in given_elements)
        element_score = min(96, round(78 + 18 * matches / len(given_elements)))

    trigram_matches = sum(element in bazi["favorable"] for element in trigram["elements"])
    trigram_score = min(96, 78 + trigram_matches * 9)
    w = (.18, .14, .18, .35, .15)
    total = round(pronunciation * w[0] + shape * w[1] + meaning * w[2] + element_score * w[3] + trigram_score * w[4])
    return {"score": total, "metrics": {"音韵": pronunciation, "字形": shape, "寓意": meaning,
                                           "五行": element_score, "卦象": trigram_score},
            "bazi": bazi, "trigram": trigram, "name_elements": name_elements,
            "given_elements": given_elements, "tones": tone_values, "strokes": strokes,
            "character_sources": {char: profile[3] for char, profile in zip(name, profiles)},
            "gender": normalize_gender(gender), "weights": w}


def score_name(data: dict) -> dict:
    name = require_text(data, "name", CHINESE_NAME, "姓名")
    birth = parse_birth(data.get("birth"))
    birth_time = parse_birth_time(data.get("birth_time"))
    gender = normalize_gender(str(data.get("gender", "不限定")))
    assessment = evaluate_name(name, birth, birth_time, gender)
    bazi, trigram = assessment["bazi"], assessment["trigram"]
    total, name_elements = assessment["score"], assessment["name_elements"]
    meanings = [CHAR_INFO[c][2] for c in name if c in CHAR_INFO]
    result = {
        "name": name, "score": total,
        "grade": "上佳之名" if total >= 92 else "温润佳名" if total >= 85 else "平稳之名",
        "metrics": assessment["metrics"],
        "bazi": bazi, "name_elements": name_elements, "trigram": trigram,
        "calculation": {"tones": assessment["tones"], "strokes": assessment["strokes"],
                        "weights": assessment["weights"], "character_sources": assessment["character_sources"]},
        "summary": "、".join(meanings) if meanings else "读音流畅，结构协调，具有良好的日常辨识度",
        "advice": f"四柱五行计数为{'、'.join(f'{key}{value}' for key, value in bazi['counts'].items())}；按“{bazi['rule']}”规则，本次补“{'、'.join(bazi['favorable'])}”。姓名用字为“{'、'.join(name_elements)}”，主卦为{trigram['name']}。",
    }
    save_history("score", name, result, bool(data.get("_store_history")))
    return result


def duplicate_risk_profile(name: str) -> dict:
    """本地透明规则评估组合稀有度；生成阶段调用时不会触发外部人口接口。"""
    surname, given = split_full_name(name)
    signals = []
    score = 8
    if surname in VERY_COMMON_SURNAMES:
        score += 24
        signals.append(f"姓氏“{surname}”属于常见姓氏，重名基础概率较高")
    else:
        score += 8
        signals.append(f"姓氏“{surname}”不在内置常见姓氏档，重名风险相对较低")
    popular = [char for char in given if char in COMMON_GIVEN_CHARS]
    if popular:
        score += len(popular) * 18
        signals.append(f"名字中有{len(popular)}个常见起名字：{'、'.join(popular)}")
    else:
        signals.append("名字用字未命中内置高频起名字表")
    if len(given) == 1:
        score += 20
        signals.append("单字名组合空间较小，通常更容易重名")
    elif len(given) >= 2:
        score += 4
        signals.append("双字名或多字名组合空间较大")
    if len(set(given)) < len(given):
        score += 8
        signals.append("名字包含叠字，常见组合风险增加")
    if name in VERY_COMMON_FULL_NAMES:
        score += 25
        signals.append("完整姓名命中内置常见姓名表")
    score = min(100, score)
    if score >= 80:
        level, label = "very_high", "很高"
    elif score >= 60:
        level, label = "high", "较高"
    elif score >= 40:
        level, label = "medium", "中等"
    elif score >= 25:
        level, label = "low", "较低"
    else:
        level, label = "very_low", "很低"
    confidence = "中" if name in VERY_COMMON_FULL_NAMES or popular else "低"
    return {"mode": "risk", "name": name, "score": score, "level": level, "label": label,
            "confidence": confidence, "signals": signals,
            "method": "姓氏分档 + 高频用字 + 名字长度 + 叠字 + 常见完整姓名",
            "disclaimer": "这是组合稀有度风险评估，不是公安人口查询，不提供虚构的同名人数。"}


def generate_names(data: dict) -> dict:
    surname = require_text(data, "surname", SURNAME, "姓氏")
    birth = parse_birth(data.get("birth"))
    birth_time = parse_birth_time(data.get("birth_time"))
    gender = str(data.get("gender", "neutral"))
    style = str(data.get("style", "elegant"))
    fixed_char = str(data.get("fixed_char", "")).strip()
    if gender not in ("boy", "girl", "neutral") or style not in STYLE_CHARS:
        raise ValueError("性别或风格选项不正确")
    if fixed_char:
        if len(fixed_char) != 1 or not re.fullmatch(r"[\u3400-\u9fff]", fixed_char):
            raise ValueError("指定用字必须是一个中文汉字")
        char_profile(fixed_char)
    bazi = calculate_bazi(birth, birth_time)
    favorable = bazi["favorable"]
    supporting = [source for source, target in GENERATES.items() if target in favorable]
    allowed_elements = set(favorable + supporting)
    chars = [char for element in allowed_elements for char in NAMING_CHARS[element]]
    if gender == "boy":
        chars = [char for char in chars if char not in FEMININE_CHARS]
    elif gender == "girl":
        chars = [char for char in chars if char not in MASCULINE_CHARS]
    if fixed_char and fixed_char not in chars:
        chars.append(fixed_char)
    nonce = str(data.get("nonce", ""))
    bazi_signature = ":".join(bazi["pillars"])
    rng = random.Random(stable_seed(f"{surname}:{bazi_signature}:{birth_time}:{gender}:{style}:{nonce}"))
    raw_candidates = []
    for first in chars:
        for second in chars:
            if first == second or first in surname or second in surname:
                continue
            elements = [char_profile(first)[1], char_profile(second)[1]]
            required = set(bazi["required_elements"])
            if required and not required.issubset(set(elements)):
                continue
            if not required and not any(element in favorable for element in elements):
                continue
            style_matches = sum(char in STYLE_CHARS[style] for char in (first, second))
            # 气质是推荐筛选条件，不进入通用姓名评分。不同气质必须命中对应字池。
            if style_matches == 0:
                continue
            fixed_match = 1 if fixed_char and fixed_char in (first, second) else 0
            if fixed_char and not fixed_match:
                continue
            corpus_rank = int(NAME_CORPUS.get("bigrams", {}).get(first + second, 0))
            full_name = surname + first + second
            # 完整四柱参与确定性择名；相邻日期的日柱不同，会得到不同的优先序。
            birth_affinity = stable_seed(f"{bazi_signature}:{full_name}") % 1000 / 1000
            raw_candidates.append((first, second, elements, style_matches, fixed_match, corpus_rank, birth_affinity))

    # 先按气质、语料自然度和完整八字确定性择优，再精评一个较大的候选池。
    rng.shuffle(raw_candidates)
    raw_candidates.sort(key=lambda item: (item[4], item[3], min(item[5], 100), item[6]), reverse=True)
    candidates = []
    for first, second, elements, style_matches, fixed_match, corpus_rank, birth_affinity in raw_candidates[:500]:
            full_name = surname + first + second
            assessment = evaluate_name(full_name, birth, birth_time, gender, bazi=bazi)
            meaning = f"{char_profile(first)[2]}，{char_profile(second)[2]}"
            warnings = [term for term in NAME_CORPUS.get("ambiguous_terms", []) if term and term in full_name]
            risk = duplicate_risk_profile(full_name)
            quality = (assessment["score"] - risk["score"] * .16 + style_matches * 2
                       + min(corpus_rank, 100) * .015 + birth_affinity * 3 - len(warnings) * 10)
            candidates.append({"name": full_name, "score": assessment["score"], "meaning": meaning,
                               "elements": elements, "trigram": assessment["trigram"]["name"],
                               "corpus_frequency": corpus_rank, "ambiguity_warnings": warnings,
                               "duplicate_risk": {"score": risk["score"], "level": risk["level"], "label": risk["label"]},
                               "style_matches": style_matches, "_quality": quality})

    # 逐个选择并惩罚已经出现过的字，避免十个名字围绕两三个高分字来回组合。
    results, remaining, usage = [], candidates[:], {}
    while remaining and len(results) < 10:
        eligible = [item for item in remaining if all(
            char == fixed_char or usage.get(char, 0) < 2
            for char in split_full_name(item["name"])[1]
        )]
        pool = eligible or remaining
        best = max(pool, key=lambda item: item["_quality"]
                   - sum(usage.get(char, 0) * 10 for char in split_full_name(item["name"])[1]
                         if char != fixed_char))
        results.append(best)
        remaining.remove(best)
        for char in split_full_name(best["name"])[1]:
            usage[char] = usage.get(char, 0) + 1
    results.sort(key=lambda item: (item["score"], -item["duplicate_risk"]["score"]), reverse=True)
    for item in results:
        item.pop("_quality", None)
    missing_text = "、".join(bazi["missing"]) if bazi["missing"] else "无"
    favorable_text = "、".join(favorable)
    support_text = "、".join(supporting) if supporting else "无"
    if bazi["required_elements"]:
        analysis = (f"八个干支本气的五行计数中，{missing_text}为0，按当前采用的“缺什么补什么”规则判定缺{missing_text}。"
                    f"候选名强制包含{favorable_text}属性字，同时可参考相生的{support_text}属性字。")
    else:
        analysis = (f"当前采用“{bazi['rule']}”；本次推荐方向为{favorable_text}。"
                    f"优先选用{favorable_text}属性字，并参考相生的{support_text}属性字保持组合平衡。")
    if fixed_char:
        analysis += f" 已将“{fixed_char}”设为优先用字；在不破坏补五行和质量要求的前提下尽量采用。"
    strategy = {"analysis": analysis, "required": bazi["required_elements"],
                "recommended": favorable, "supporting": supporting, "fixed_char": fixed_char,
                "style": style, "character_pool_size": len(chars),
                "base_character_count": int(CHAR_DATA.get("base_character_count", len(BASE_CHAR_INFO))),
                "eligible_character_count": len(CHAR_INFO),
                "valid_combinations": len(raw_candidates), "evaluated_candidates": len(candidates),
                "diversity_note": "气质命中字池后，按完整四柱择优，并限制推荐列表中的重复用字",
                "corpus_source": NAME_CORPUS.get("source", "未配置授权姓名语料")}
    result = {"surname": surname, "bazi": bazi, "strategy": strategy, "names": results}
    save_history("naming", surname, result, bool(data.get("_store_history")))
    return result


def cast_hexagram(data: dict) -> dict:
    question = str(data.get("question", "")).strip()
    if not question or len(question) > 80:
        raise ValueError("请输入不超过80字的问题")
    rng = random.SystemRandom()
    lines = [rng.choice([0, 1]) for _ in range(6)]
    index = sum(bit << i for i, bit in enumerate(lines)) % len(HEXAGRAMS)
    name, title, interpretation = HEXAGRAMS[index]
    result = {"question": question, "lines": lines, "name": name, "title": title, "interpretation": interpretation}
    save_history("divination", question, result)
    return result


def population(data: dict) -> dict:
    name = require_text(data, "name", CHINESE_NAME, "姓名")
    if POPULATION_API_URL:
        payload = json.dumps({"name": name}, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if POPULATION_API_KEY:
            headers["Authorization"] = f"Bearer {POPULATION_API_KEY}"
            headers["X-API-Key"] = POPULATION_API_KEY
        try:
            with urlopen(Request(POPULATION_API_URL, data=payload, headers=headers, method="POST"), timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
            item = body.get("data", body)
            result = {"mode": "official", "name": name, "total": int(item["total"]),
                      "male": int(item.get("male", 0)), "female": int(item.get("female", 0)),
                      "source": str(item["source"]), "queried_at": datetime.now().isoformat(timespec="seconds")}
            save_history("population", name, result, bool(data.get("_store_history")))
            return result
        except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("授权人口 API 未返回有效的总人数和数据来源") from exc
    result = duplicate_risk_profile(name)
    save_history("duplicate_risk", name, result, bool(data.get("_store_history")))
    return result


AI_ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "semantic_analysis": {"type": "string"},
        "style_tags": {"type": "array", "items": {"type": "string"}},
        "era_impression": {"type": "string"},
        "pronunciation_review": {"type": "string"},
        "cultural_imagery": {"type": "string"},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "risk_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["type", "description", "confidence"],
            },
        },
        "source_notes": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "semantic_analysis", "style_tags", "era_impression",
                 "pronunciation_review", "cultural_imagery", "risk_level", "risk_items",
                 "source_notes", "warnings"],
}


AI_SYSTEM_PROMPT = """你是中文姓名语言顾问，不是命理计算器。四柱、五行、笔画、卦象和分数是只读事实，不得修改或重新计算。
分析姓名的整体语义、语言气质、时代感、普通话读音、常见谐音歧义和文化意象。
不得声称姓名决定命运、财富、健康、婚姻或人生结果。不得编造古籍出处；无法核实出处时必须称为“意象联想”。
风险判断应克制，给出置信度；没有明显风险时返回空 risk_items。所有输出使用简体中文并符合给定 JSON Schema。"""


def ai_status() -> dict:
    return {"enabled": AI_ENABLED, "provider": "OpenAI Responses API" if AI_ENABLED else "未配置",
            "model": AI_MODEL if AI_ENABLED else "", "sends_raw_birth": False,
            "message": "AI 姓名顾问可用" if AI_ENABLED else "请配置 OPENAI_API_KEY 后启用 AI 姓名顾问"}


def _extract_response_text(body: dict) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    for output in body.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "refusal":
                raise ValueError(f"AI 拒绝分析：{content.get('refusal', '请求不适用')}")
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("AI 服务未返回可解析的结构化文本")


def _validate_ai_analysis(result: dict) -> None:
    required_strings = ("summary", "semantic_analysis", "era_impression", "pronunciation_review", "cultural_imagery")
    if not isinstance(result, dict) or any(not isinstance(result.get(key), str) for key in required_strings):
        raise ValueError("AI 分析结果字段不完整")
    if result.get("risk_level") not in ("low", "medium", "high"):
        raise ValueError("AI 风险等级不正确")
    for key in ("style_tags", "risk_items", "source_notes", "warnings"):
        if not isinstance(result.get(key), list):
            raise ValueError("AI 分析结果列表字段不正确")


def analyze_name_with_ai(data: dict) -> dict:
    if not data.get("_ai_consent"):
        raise ValueError("使用 AI 姓名顾问前需要明确授权")
    if not AI_ENABLED:
        raise ValueError("AI 姓名顾问未配置：请设置 OPENAI_API_KEY")
    deterministic = score_name({**data, "_store_history": False})
    facts = {
        "name": deterministic["name"],
        "pillars": deterministic["bazi"]["pillars"],
        "element_counts": deterministic["bazi"]["counts"],
        "rule": deterministic["bazi"]["rule"],
        "score": deterministic["score"],
        "metrics": deterministic["metrics"],
        "name_elements": deterministic["name_elements"],
        "trigram": deterministic["trigram"]["name"],
        "tones": deterministic["calculation"]["tones"],
        "strokes": deterministic["calculation"]["strokes"],
    }
    request_body = {
        "model": AI_MODEL,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": AI_SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": "请基于以下只读事实进行姓名语义体检：\n" + json.dumps(facts, ensure_ascii=False)}]},
        ],
        "text": {"format": {"type": "json_schema", "name": "name_semantic_analysis",
                            "strict": True, "schema": AI_ANALYSIS_SCHEMA}},
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    try:
        with urlopen(Request(AI_API_URL, data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
                             headers=headers, method="POST"), timeout=AI_TIMEOUT) as response:
            body = json.loads(response.read().decode("utf-8"))
        analysis = json.loads(_extract_response_text(body))
        _validate_ai_analysis(analysis)
    except HTTPError as exc:
        raise ValueError(f"AI 服务请求失败（HTTP {exc.code}）") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError("AI 服务连接超时或不可用") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("AI 服务返回的结构化结果无法解析") from exc
    result = {"name": deterministic["name"], "analysis": analysis,
              "meta": {"provider": "OpenAI Responses API", "model": AI_MODEL,
                       "raw_birth_sent": False, "deterministic_score": deterministic["score"]},
              "disclaimer": "AI 仅提供语言与文化语境辅助分析，不改变八字、五行和姓名评分。"}
    save_history("ai_analysis", deterministic["name"], result, bool(data.get("_store_history")))
    return result


ROUTES = {
    "/api/score": score_name,
    "/api/names": generate_names,
    "/api/population": population,
    "/api/ai/analyze": analyze_name_with_ai,
}


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"ok": True, "service": "拾名", "time": datetime.now().isoformat(timespec="seconds")})
            return
        if path == "/api/ai/status":
            self.send_json({"ok": True, "data": ai_status()})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        handler = ROUTES.get(path)
        if handler is None:
            self.send_json({"ok": False, "error": "接口不存在"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("请求内容为空或过大")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            data["_store_history"] = self.headers.get("X-Store-History", "false").lower() == "true"
            data["_ai_consent"] = self.headers.get("X-AI-Consent", "false").lower() == "true"
            self.send_json({"ok": True, "data": handler(data)})
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            print(f"API error: {exc}")
            self.send_json({"ok": False, "error": "服务器处理失败，请稍后重试"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print("\n拾名已启动")
    print(f"访问地址：http://{HOST}:{PORT}")
    print("停止服务：按 Ctrl+C\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
