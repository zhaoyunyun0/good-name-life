"""从有许可证的公开数据构建可审计的生产起名字库。

输入文件不提交仓库：
1. general_standard_chinese.csv: ben-hua/general_standard_chinese, Apache-2.0
2. xinhua_word.json: pwxcoo/chinese-xinhua, MIT
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


# 编辑精选层：只允许常见、含义适合姓名且日常可读写的规范汉字进入推荐池。
# 笔画、拼音、部首、五行和释义不在此手写，全部来自下面两个公开数据源。
NAMING_ALLOWLIST = """
一乙丁乃之乐乔予云亦京亭亮仁令仪伊伟传伦伯佳俊俐俪倩健儒元先光克全兴军冠冬凡凯刚利力功勇勋勤华卓博卫厚友发可叶吉同君启和哲善嘉国圣坚坤城培基堂壮夏天奇奕如妍妙妤妮姿娅娜娟娴婉婕婷媛嫣子存孝孟季宁宇守安宏宗宜宝实宣宥家宸容宾富寅尊小少尚尧展山岑岚岩岳岸峰峻崇嵘川州帅希常平年广庄庆康建弘强彬彪彤彦彩彬彰影征德心忆志忠念怀思怡恒恩恺悦惠意慕慧成承振捷政敏敬文斌新方旭时昌明易星昕昭晗晟晨景晴晶智暄暖曦曜有朋朗望朝木未本朴杉杏材村杜杨杭杰松林果枝枫柏柯柳栋栎树栩桂桃桐桦梁梅梓梦梧梨棠森植楚楠榆榕槿樊欣正武毅民永江沅沐沛河治泉泊泓法波泰泽洋洛津洲洵流济浏浩海涛润涵淇淑淳清渊渝渠湘湛源溪溢滢滨漪漫潇澄澜瀚灿炎炜炫烁烟烨焕焱煊熙熠燕爱爽牧献玉王玥玮环玲珂珊珍珏珞珠珩琛琦琪琬琳琴琼瑜瑞瑄瑛瑜瑾璇璐甘生甫田甲申白百皓盛睿知礼祎祥祺禹秀秋科秦程稷稼穆立章童端竹笑笛策筠筱简米粟精素紫红纯绍维绮绵缘美羽翔翰耀聪胜舒航良艺艾芃芝芙芮芯芳芷芸苏苑若英茂茗茜荟荣莉莎莹菁菡萱葳蓉蓓蕊蕙薇虹融行衡裕西言誉诗诚语诺谊谨豪贝贤贞贵超越跃路轩辉辰达迈远连迪逸道邦郁金鑫钊钧钰铃铄铭铠铮锐锦锴长阳隆雄雅雨雪雯霁霄霆震霞霖霏露青靖静韦韵顺颖颜风飞香馥馨驰骏高鸿鹏鹤麟麦齐龙龚
世业东中丰丹丽义书乾亚亨享介仕仙以仰仲任伍伏会伟佐佑佩依侠信俞倚倡倬偲允充兆兰关其典冉冰凌凝凤初前剑励劲升南卿原参双向含听呈周品唐唯商喜园均坦垚垣垒埔堃奎奥好姝姣姬娉婧嫒嫦媚嬿孜学宛宵寰寻寿尔尚屹岐峥峦崧崴嵩帆帝庄序庭庚庸延廷开弈弦弥彧徐循微徽忻怿恬恭恪悠惜惟愉慈慎慷懿戈扬拓持挚敦斯旻昀昂昆昊昶晏晋晓晖晞晤普晰暻曈朔朦权来枢枥栖栗校格桓桥梵棣椿楷榛樾橙檀欢歆殷毓沂沄沅沫泱泳洁洪洺浚浦浴涣涌淞淡添淼渤温滕滟潞潮濡瀛灵炅炜炯焜然煦熹燊燚玎玟玢玺珉珑珲琚琨琰琮琲琸瑀瑗瑶璋璟璞畴皎真石研砚硕磊祉祯祺祚祜禛禺禾秉秩稚穗穹竞笑笙笠笺箫篪籽粲绅经绘继绚绣绪绫绮翊翎翌翕翡翼耘联肖育胤腾致臻舜舟良芊芃芄芩芪芫苇苒苓苡茉茵荃荔荞荻莘莞菀菘菱菲萌萧葆葵蒨蔚蔓蕴薏薰藜藤衍裕观觅觉言訸誉许谦谷豫贺赋赫赟起轶轲轻 辰 辅 辰 迎适逊逍遥邈邵郡酉醒釆钏钦钫钺铂铉铎铖铧锟锶镕闻闵阁阅阔阮际陶陌隽雁霓霜音韶项颂颐颢飒骁骐骞骥魁鲲鸣鸥鹰黎默黛鼎
"""


ELEMENTS = {"木", "火", "土", "金", "水"}


def compact_explanation(char: str, text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(rf"^{re.escape(char)}[^ ]*\s*", "", text)
    text = text.replace('"', "”")
    if not text:
        return ""
    return text[:88].rstrip("，。；; ")


def main(source_csv: Path, xinhua_json: Path, output: Path) -> None:
    with source_csv.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if len(row.get("word", "")) == 1]
        standard = {row["word"]: row for row in rows}
    xinhua_rows = json.loads(xinhua_json.read_text(encoding="utf-8"))
    xinhua = {row["word"]: row for row in xinhua_rows if len(row.get("word", "")) == 1}

    allowed = dict.fromkeys(re.findall(r"[\u3400-\u9fff]", NAMING_ALLOWLIST))
    characters = {}
    for char, base in standard.items():
        definition = xinhua.get(char, {})
        element = base.get("wuxing") if base.get("wuxing") in ELEMENTS else None
        meaning = compact_explanation(char, definition.get("explanation", ""))
        characters[char] = {
            "strokes": int(base["stroke_count"]), "element": element,
            "meaning": meaning or None, "pinyin": base.get("pinyin", ""),
            "radical": base.get("radical", ""), "name_eligible": False,
            "source": "通用规范汉字数据" + (" + 中华新华字典数据" if meaning else ""),
        }

    missing = []
    for char in allowed:
        base, definition = standard.get(char), xinhua.get(char)
        if not base or not definition or base.get("wuxing") not in ELEMENTS:
            missing.append(char)
            continue
        characters[char]["name_eligible"] = True

    eligible = {char: item for char, item in characters.items() if item["name_eligible"]}
    by_element = {element: sum(item["element"] == element for item in eligible.values()) for element in ELEMENTS}
    if not 8000 <= len(characters) <= 8200:
        raise RuntimeError(f"基础字库数量异常：{len(characters)}")
    if len(eligible) < 500 or min(by_element.values()) < 60:
        raise RuntimeError(f"精选字库不足：总数={len(eligible)}，五行={by_element}，缺少={''.join(missing)}")
    payload = {
        "schema_version": 1,
        "sources": [
            {"name": "general_standard_chinese", "license": "Apache-2.0",
             "url": "https://github.com/ben-hua/general_standard_chinese"},
            {"name": "chinese-xinhua", "license": "MIT",
             "url": "https://github.com/pwxcoo/chinese-xinhua"},
        ],
        "base_character_count": len(characters),
        "eligible_character_count": len(eligible),
        "selection": "编辑精选常见正向姓名用字；属性取公开数据，项目人工校订字优先覆盖",
        "characters": characters,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated base={len(characters)}, eligible={len(eligible)}: {by_element}; skipped={len(missing)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: build_character_data.py SOURCE_CSV XINHUA_JSON OUTPUT_JSON")
    main(*(Path(value) for value in sys.argv[1:]))
