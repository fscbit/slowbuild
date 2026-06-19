"""
八字命盘推算引擎 — 纯 Python 实现
农历转换 + 天干地支 + 五行 + 排盘 + 解读
"""

import datetime
import math

# ═══════════════════════════
# 天干地支 基础数据
# ═══════════════════════════
TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
SHENG_XIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']
WU_XING_TG = ['木', '木', '火', '火', '土', '土', '金', '金', '水', '水']
WU_XING_DZ = ['水', '土', '木', '木', '土', '火', '火', '土', '金', '金', '土', '水']


# ========== 十神名称 ==========
SHI_SHEN_NAMES = {
    '比肩': {'zh': '比肩', 'en': 'Sibling'},
    '劫财': {'zh': '劫财', 'en': 'Rob Wealth'},
    '食神': {'zh': '食神', 'en': 'Eating God'},
    '伤官': {'zh': '伤官', 'en': 'Hurting Officer'},
    '正财': {'zh': '正财', 'en': 'Direct Wealth'},
    '偏财': {'zh': '偏财', 'en': 'Indirect Wealth'},
    '正官': {'zh': '正官', 'en': 'Direct Officer'},
    '七杀': {'zh': '七杀', 'en': 'Seven Killings'},
    '正印': {'zh': '正印', 'en': 'Direct Resource'},
    '偏印': {'zh': '偏印', 'en': 'Indirect Resource'},
}

# ========== 纳音五行 ==========
NA_YIN = {
    '甲子':'海中金','乙丑':'海中金','丙寅':'炉中火','丁卯':'炉中火',
    '戊辰':'大林木','己巳':'大林木','庚午':'路旁土','辛未':'路旁土',
    '壬申':'剑锋金','癸酉':'剑锋金','甲戌':'山头火','乙亥':'山头火',
    '丙子':'涧下水','丁丑':'涧下水','戊寅':'城头土','己卯':'城头土',
    '庚辰':'白蜡金','辛巳':'白蜡金','壬午':'杨柳木','癸未':'杨柳木',
    '甲申':'泉中水','乙酉':'泉中水','丙戌':'屋上土','丁亥':'屋上土',
    '戊子':'霹雳火','己丑':'霹雳火','庚寅':'松柏木','辛卯':'松柏木',
    '壬辰':'长流水','癸巳':'长流水','甲午':'沙中金','乙未':'沙中金',
    '丙申':'山下火','丁酉':'山下火','戊戌':'平地木','己亥':'平地木',
    '庚子':'壁上土','辛丑':'壁上土','壬寅':'金箔金','癸卯':'金箔金',
    '甲辰':'覆灯火','乙巳':'覆灯火','丙午':'天河水','丁未':'天河水',
    '戊申':'大驿土','己酉':'大驿土','庚戌':'钗钏金','辛亥':'钗钏金',
    '壬子':'桑柘木','癸丑':'桑柘木','甲寅':'大溪水','乙卯':'大溪水',
    '丙辰':'沙中土','丁巳':'沙中土','戊午':'天上火','己未':'天上火',
    '庚申':'石榴木','辛酉':'石榴木','壬戌':'大海水','癸亥':'大海水',
}

NA_YIN_EN = {
    '海中金':'Gold in Sea','炉中火':'Fire in Furnace','大林木':'Forest Wood',
    '路旁土':'Roadside Earth','剑锋金':'Sword Gold','山头火':'Mountain Fire',
    '涧下水':'Stream Water','城头土':'Rampart Earth','白蜡金':'White Wax Gold',
    '杨柳木':'Willow Wood','泉中水':'Spring Water','屋上土':'Roof Earth',
    '霹雳火':'Thunder Fire','松柏木':'Pine Wood','长流水':'Flowing Water',
    '沙中金':'Sand Gold','山下火':'Mountain-base Fire','平地木':'Flat Wood',
    '壁上土':'Wall Earth','金箔金':'Gold Foil','覆灯火':'Lamp Fire',
    '天河水':'Heaven River','大驿土':'Post Earth','钗钏金':'Hairpin Gold',
    '桑柘木':'Mulberry Wood','大溪水':'Big Stream','沙中土':'Sandy Earth',
    '天上火':'Heaven Fire','石榴木':'Pomegranate Wood','大海水':'Sea Water',
}

# ========== 神煞 ==========
def get_shen_sha(pillars, day_zhi):
    """Return auspicious/inauspicious stars for the chart"""
    sha = {'stars': {}, 'explanations_zh': {}, 'explanations_en': {}}
    # Heavenly Noble
    tygr = {'甲':'丑未','戊':'丑未','庚':'丑未','乙':'子申','己':'子申',
            '丙':'亥酉','丁':'亥酉','壬':'卯巳','癸':'卯巳','辛':'午寅'}
    for pname, gz in pillars.items():
        gan = gz[0] if len(gz)>0 else ''
        zhi = gz[1] if len(gz)>1 else ''
        if gan in tygr:
            noble = tygr[gan]
            for z in noble:
                if z == zhi:
                    key = pname + '_tian_yi'
                    sha['stars'][key] = pname + ' pillar: Heavenly Noble'
                    sha['explanations_zh'][key] = '天乙贵人是最大的吉星'
                    sha['explanations_en'][key] = 'Greatest auspicious star; brings fortune'
    # Literary Star
    wenchang = {'甲':'巳','乙':'午','丙':'申','丁':'酉','戊':'申','己':'酉',
                '庚':'亥','辛':'子','壬':'寅','癸':'卯'}
    for pname, gz in pillars.items():
        gan = gz[0] if len(gz)>0 else ''
        zhi = gz[1] if len(gz)>1 else ''
        if gan in wenchang and wenchang[gan] == zhi:
            key = pname + '_wenchang'
            sha['stars'][key] = pname + ' pillar: Literary Star'
            sha['explanations_zh'][key] = '文昌主聪明好学'
            sha['explanations_en'][key] = 'Literary talent, academic success'
    # Peach Blossom (simplified: check if birth month zhi triggers)
    peach_triggers = {'申':'酉','子':'酉','辰':'酉','寅':'卯','午':'卯','戌':'卯',
                      '巳':'午','酉':'午','丑':'午','亥':'子','卯':'子','未':'子'}
    day_zhi_val = pillars.get('day', ['',''])[1] if day_zhi else ''
    if day_zhi_val in peach_triggers:
        peach_zhi = peach_triggers[day_zhi_val]
        # Check if any pillar has the peach blossom zhi
        for pname, gz in pillars.items():
            if gz[1] == peach_zhi:
                key = pname + '_taohua'
                sha['stars'][key] = pname + ' pillar: Peach Blossom'
                sha['explanations_zh'][key] = '桃花主异性缘与魅力'
                sha['explanations_en'][key] = 'Romantic charm and charisma'
    return sha

# ========== 空亡 ==========
def get_xun_kong(day_gz):
    """Calculate Xun Kong (Emptiness) based on day pillar"""
    all_gz = []
    for i in range(60):
        all_gz.append(TIAN_GAN[i%10] + DI_ZHI[i%12])
    idx = all_gz.index(day_gz) if day_gz in all_gz else 0
    xun_start = (idx // 10) * 10
    used = set()
    for i in range(xun_start, xun_start+10):
        used.add(DI_ZHI[i%12])
    return [z for z in DI_ZHI if z not in used]

# ========== 十神 ==========
def get_shi_shen(day_gan, target_gan):
    """Calculate Ten God relationship of target_gan relative to day_gan"""
    gan_list = TIAN_GAN
    wuxing_list = WU_XING_TG
    day_idx = gan_list.index(day_gan) if day_gan in gan_list else 0
    target_idx = gan_list.index(target_gan) if target_gan in gan_list else 0
    day_wx = wuxing_list[day_idx]
    target_wx = wuxing_list[target_idx]
    same_polarity = (day_idx % 2) == (target_idx % 2)
    wx_order = ['木','火','土','金','水']
    day_wx_i = wx_order.index(day_wx)
    target_wx_i = wx_order.index(target_wx)
    if target_wx == day_wx:
        return '比肩' if same_polarity else '劫财'
    elif target_wx == wx_order[(day_wx_i + 1) % 5]:
        return '食神' if same_polarity else '伤官'
    elif target_wx == wx_order[(day_wx_i + 2) % 5]:
        return '偏财' if same_polarity else '正财'
    elif wx_order[(target_wx_i + 2) % 5] == day_wx:
        return '七杀' if same_polarity else '正官'
    else:
        return '偏印' if same_polarity else '正印'

def _shi_shen_en(cn_name):
    return SHI_SHEN_NAMES.get(cn_name, {}).get('en', cn_name)

# ========== 大运 ==========
def calculate_dayun(year, month, day, hour, gender, lang='zh'):
    """Calculate Luck Pillars (Decade Luck)"""
    date_obj = datetime.date(year, month, day)
    year_gz = get_year_gz(year)
    lunar_year, lunar_month, lunar_day, is_leap = solar_to_lunar(date_obj)
    month_gz = get_month_gz(year_gz, month, day, is_leap)
    day_gz = get_day_gz(date_obj)

    year_gan_idx = TIAN_GAN.index(year_gz[0])
    is_yang = (year_gan_idx % 2 == 0)
    forward = (is_yang and gender == 'male') or (not is_yang and gender == 'female')

    days_to_jieqi = abs(day - JIE_QI.get(month, 5))
    start_age = max(1, round(days_to_jieqi / 3.0))
    if not forward:
        prev_month = month - 1 if month > 1 else 12
        prev_jq = JIE_QI.get(prev_month, 5)
        days_from = (30 - prev_jq) + day
        start_age = max(1, round(days_from / 3.0))

    month_zhi_idx = DI_ZHI.index(month_gz[1])
    month_gan_idx = TIAN_GAN.index(month_gz[0])

    results = []
    for i in range(10):
        age = start_age + i * 10
        if forward:
            ng = (month_gan_idx + 1 + i) % 10
            nz = (month_zhi_idx + 1 + i) % 12
        else:
            ng = (month_gan_idx - 1 - i) % 10
            nz = (month_zhi_idx - 1 - i) % 12
        gz = TIAN_GAN[ng] + DI_ZHI[nz]
        nayin = NA_YIN.get(gz, '')
        nayin_en = NA_YIN_EN.get(nayin, '')
        results.append({
            'start_age': age, 'end_age': age + 9, 'ganzhi': gz,
            'nayin': nayin_en if lang.startswith('en') else nayin,
            'nayin_cn': nayin,
        })
    return results

# ========== 流年 ==========
def calculate_liunian(day_gz, current_year, count=5, lang='zh'):
    """Calculate Yearly Luck for upcoming years"""
    year_gz_2020 = get_year_gz(2020)
    all_gz = []
    for i in range(60):
        all_gz.append(TIAN_GAN[i%10] + DI_ZHI[i%12])
    gz_2020_idx = all_gz.index(year_gz_2020) if year_gz_2020 in all_gz else 0

    day_zhi = day_gz[1] if len(day_gz)>1 else ''
    liuhe = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯',
             '辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}
    chong = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅',
             '卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}

    results = []
    for i in range(count):
        yr = current_year + i
        gz_idx = (gz_2020_idx + (yr - 2020)) % 60
        gz = all_gz[gz_idx]
        ss = get_shi_shen(day_gz[0], gz[0])
        yr_zhi = gz[1] if len(gz)>1 else ''
        relations = []
        if liuhe.get(day_zhi) == yr_zhi:
            relations.append('Union' if lang.startswith('en') else '六合')
        if chong.get(day_zhi) == yr_zhi:
            relations.append('Clash' if lang.startswith('en') else '相冲')
        results.append({
            'year': yr, 'ganzhi': gz,
            'shi_shen': _shi_shen_en(ss) if lang.startswith('en') else ss,
            'nayin': NA_YIN.get(gz, ''),
            'zhi_relations': relations,
        })
    return results

# ========== 五行详细 ==========
def detailed_wuxing_balance(pillars):
    """Detailed five-element analysis with per-pillar breakdown"""
    wuxing_detail = {'金':0,'木':0,'水':0,'火':0,'土':0}
    pillar_wx = {}
    for pname, gz in pillars.items():
        gan = gz[0]
        zhi = gz[1] if len(gz)>1 else ''
        gan_wx = WU_XING_TG[TIAN_GAN.index(gan)]
        zhi_wx = WU_XING_DZ[DI_ZHI.index(zhi)] if zhi else ''
        wuxing_detail[gan_wx] += 2
        if zhi_wx:
            wuxing_detail[zhi_wx] += 1
        pillar_wx[pname] = {'gan':gan,'gan_wx':gan_wx,'zhi':zhi,'zhi_wx':zhi_wx}
    total = sum(wuxing_detail.values()) or 1
    wuxing_pct = {k: round(v/total*100, 1) for k,v in wuxing_detail.items()}
    missing = [k for k,v in wuxing_detail.items() if v < 1]
    weak = [k for k,v in wuxing_pct.items() if 0 < v < 12]
    dominant = max(wuxing_detail, key=wuxing_detail.get)
    return {
        'detail': wuxing_detail, 'percent': wuxing_pct,
        'missing': missing, 'weak': weak, 'dominant': dominant,
        'pillar_wx': pillar_wx,
    }

# ========== 日主强弱 ==========
def day_master_strength(day_master, pillars, wuxing_balance):
    """Determine if Day Master is strong, weak, or balanced"""
    wx = day_master['wuxing']
    wx_cycle_gen = {'木':'水','火':'木','土':'火','金':'土','水':'金'}
    support_wx = wx_cycle_gen.get(wx, '')
    self_count = wuxing_balance['detail'].get(wx, 0)
    support_count = wuxing_balance['detail'].get(support_wx, 0)
    score = self_count + support_count
    if score >= 6:
        return '身强'
    elif score <= 3:
        return '身弱'
    else:
        return '中和'

# ========== 日主详解 ==========
DAY_MASTER_FULL = {
    '甲': {
        'summary_zh': '甲木参天，栋梁之材。性格直率果敢，有领导力和开创精神。',
        'summary_en': 'Jia Wood: towering and upright, a born leader with pioneering spirit.',
        'career_zh': '从政、管理、教育、建筑、林业、法律。宜做大方向引领者。',
        'career_en': 'Politics, management, education, construction, forestry, law.',
        'love_zh': '感情中主动强势，喜欢温柔体贴的伴侣，需注意适当退让。',
        'love_en': 'Assertive in love; prefers gentle partners; learn to compromise.',
        'health_zh': '注意肝胆、筋骨。多运动疏解压力，避免暴怒伤肝。',
        'health_en': 'Watch liver, tendons. Exercise to relieve stress; avoid anger.',
    },
    '乙': {
        'summary_zh': '乙木柔韧，花草之姿。心思细腻，善于变通，有艺术天赋。',
        'summary_en': 'Yi Wood: flexible and delicate, artistic and adaptable.',
        'career_zh': '艺术设计、文学写作、公关传媒、园林园艺、心理咨询。',
        'career_en': 'Arts, design, writing, PR, media, horticulture, counseling.',
        'love_zh': '重视情感沟通，渴望浪漫，需要坚定有担当的伴侣。',
        'love_en': 'Values emotional connection; longs for romance; needs a decisive partner.',
        'health_zh': '注意肝胆、眼睛。保持充足睡眠，少熬夜。',
        'health_en': 'Watch liver, eyes. Maintain good sleep; avoid late nights.',
    },
    '丙': {
        'summary_zh': '丙火炎上，烈日之光。热情开朗，慷慨大方，感染力强。',
        'summary_en': 'Bing Fire: blazing sun. Warm, generous, highly charismatic.',
        'career_zh': '传媒演艺、销售市场、互联网、能源行业、教育演讲。',
        'career_en': 'Media, entertainment, sales, tech, energy, public speaking.',
        'love_zh': '爱情中热情似火，主动大方。热烈过后需学会细水长流。',
        'love_en': 'Passionate and bold in love; learn to sustain warmth over time.',
        'health_zh': '注意心脏、血压。夏天防暑降温，情绪不宜大起大落。',
        'health_en': 'Watch heart, blood pressure. Stay cool; avoid emotional extremes.',
    },
    '丁': {
        'summary_zh': '丁火柔中，灯烛之光。内心明亮，心思缜密，有独特见解。',
        'summary_en': 'Ding Fire: gentle candle flame. Insightful, meticulous, unique perspective.',
        'career_zh': '学术研究、技术开发、医疗护理、编辑校对、数据分析。',
        'career_en': 'Research, tech development, healthcare, editing, data analysis.',
        'love_zh': '追求灵魂伴侣，感情极为认真。但过于理想化，易受伤。',
        'love_en': 'Seeks soulmate; takes love seriously but too idealistic. Learn to accept imperfection.',
        'health_zh': '注意心脏、神经系统。多做冥想、瑜伽等静心活动。',
        'health_en': 'Watch heart, nervous system. Try meditation, yoga.',
    },
    '戊': {
        'summary_zh': '戊土厚重，城墙之固。稳重可靠，诚信务实，责任心强。',
        'summary_en': 'Wu Earth: fortress walls. Steady, reliable, trustworthy, responsible.',
        'career_zh': '金融地产、工程建设、仓储物流、行政管理、农业。',
        'career_en': 'Finance, real estate, engineering, logistics, administration, agriculture.',
        'love_zh': '感情中责任感极强，可靠伴侣。但缺乏浪漫，需学会表达。',
        'love_en': 'Extremely responsible partner; but lacks romance. Learn to express affection.',
        'health_zh': '注意脾胃、消化系统。饮食规律，忌暴饮暴食。',
        'health_en': 'Watch spleen, stomach, digestion. Eat regularly; avoid overeating.',
    },
    '己': {
        'summary_zh': '己土卑湿，田园之壤。温和包容，有耐心，善于培育他人。',
        'summary_en': 'Ji Earth: fertile garden soil. Gentle, patient, nurturing.',
        'career_zh': '教育培训、护理保育、营养健康、社会工作、服务行业。',
        'career_en': 'Education, nursing, nutrition, social work, service industries.',
        'love_zh': '温柔体贴，理想居家伴侣。但容易依赖，需培养独立性。',
        'love_en': 'Tender and caring partner; but tends to depend. Cultivate independence.',
        'health_zh': '注意脾胃、肌肉。适当运动，避免久坐。',
        'health_en': 'Watch spleen, stomach, muscles. Exercise moderately.',
    },
    '庚': {
        'summary_zh': '庚金带煞，刀剑之刚。意志坚定，杀伐果断，执行力极强。',
        'summary_en': 'Geng Metal: forged steel. Strong-willed, decisive, execution-oriented.',
        'career_zh': '军警法律、机械制造、工程技术、竞技体育、外科医生。',
        'career_en': 'Military, law, mechanics, engineering, sports, surgery.',
        'love_zh': '行动胜于言语，言出必行。但不擅甜言蜜语，需对方理解。',
        'love_en': 'Actions over words — a partner who delivers. Needs understanding of your love language.',
        'health_zh': '注意肺、大肠、皮肤。戒烟限酒，多呼吸新鲜空气。',
        'health_en': 'Watch lungs, large intestine, skin. Avoid smoking; get fresh air.',
    },
    '辛': {
        'summary_zh': '辛金温润，珠宝之精。精致优雅，品味不俗，追求完美。',
        'summary_en': 'Xin Metal: fine jewelry. Refined, elegant, perfectionist.',
        'career_zh': '珠宝首饰、美容美妆、音乐艺术、奢侈品、精密制造。',
        'career_en': 'Jewelry, beauty, music, luxury goods, precision manufacturing.',
        'love_zh': '追求浪漫和完美，宁缺毋滥。一旦认定，会用心经营。',
        'love_en': 'Pursues romantic perfection; would rather wait than settle. Devoted once committed.',
        'health_zh': '注意肺、呼吸道、牙齿。注意口腔卫生和空气质量。',
        'health_en': 'Watch lungs, respiratory system, teeth. Maintain oral hygiene.',
    },
    '壬': {
        'summary_zh': '壬水通河，江海之广。心胸开阔，聪慧机敏，适应力强。',
        'summary_en': 'Ren Water: great river. Broad-minded, intelligent, highly adaptable.',
        'career_zh': '国际贸易、外交谈判、旅游物流、水利航运、策划咨询。',
        'career_en': 'Trade, diplomacy, tourism, logistics, water resources, consulting.',
        'love_zh': '自由奔放不喜约束，感情中空间大于陪伴。需成熟包容的伴侣。',
        'love_en': 'Free-spirited; needs space more than company. Needs mature, tolerant partner.',
        'health_zh': '注意肾、膀胱、耳朵。多喝水，避免憋尿，注意保暖。',
        'health_en': 'Watch kidneys, bladder, ears. Stay hydrated; keep warm.',
    },
    '癸': {
        'summary_zh': '癸水至阴，雨露之润。智慧深厚，洞察力强，内心世界丰富。',
        'summary_en': 'Gui Water: morning dew. Deep wisdom, strong perception, rich inner world.',
        'career_zh': '学术研究、战略策划、心理咨询、刑侦调查、玄学命理。',
        'career_en': 'Academia, strategy, psychology, investigation, metaphysics.',
        'love_zh': '情感神秘深沉，不轻易敞开内心。一旦认定，便是此生深情。',
        'love_en': 'Mysteriously deep; doesn\'t open easily. Once committed, it\'s for life.',
        'health_zh': '注意肾、泌尿系统。保持心情愉快，避免长期压抑。',
        'health_en': 'Watch kidneys, urinary system. Stay cheerful; avoid long-term emotional suppression.',
    },
}
# 节气日期 (近似，用于月柱划分)
JIE_QI = {
    1: 5, 2: 4, 3: 6, 4: 5, 5: 6, 6: 6,
    7: 7, 8: 8, 9: 8, 10: 8, 11: 7, 12: 7
}

# 农历数据 1900-2050
# 每个条目: (year_encoded, ...)
# year_encoded: bit0-3=闰月月份(0=无), bit4-15=每月大小月(1=大30天,0=小29天), bit16-19=闰月大小
LUNAR_DATA = [
    0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,
    0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,
    0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,
    0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,
    0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,
    0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,
    0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,
    0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,
    0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,
    0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x055c0,0x0ab60,0x096d5,0x092e0,
    0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,
    0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,
    0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,
    0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,
    0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,
    0x14b63
]

# ═══════════════════════════
# 农历转换 (公历 → 农历)
# ═══════════════════════════

def get_lunar_month_days(year, m):
    """获取农历年 year 的第 m 个月的天数"""
    return 30 if LUNAR_DATA[year - 1900] & (0x10000 >> m) else 29

def get_lunar_year_days(year):
    """获取农历年 year 的总天数"""
    days = 0
    for m in range(1, 13):
        days += get_lunar_month_days(year, m)
    leap_month = LUNAR_DATA[year - 1900] & 0xf
    if leap_month:
        days += 30 if LUNAR_DATA[year - 1900] & 0x10000 else 29
    return days

def get_lunar_leap_month(year):
    """获取农历年 year 的闰月月份，0 表示没有"""
    return LUNAR_DATA[year - 1900] & 0xf

def solar_to_lunar(date_obj):
    """公历日期 → 农历日期
    返回: (lunar_year, lunar_month, lunar_day, is_leap)
    """
    year, month, day = date_obj.year, date_obj.month, date_obj.day
    
    # 计算该日期距离 1900-01-31 的天数 (1900年正月初一)
    base_date = datetime.date(1900, 1, 31)
    offset = (date_obj - base_date).days
    
    # 遍历农历年找到对应的农历日期
    lunar_year = 1900
    while offset >= get_lunar_year_days(lunar_year):
        offset -= get_lunar_year_days(lunar_year)
        lunar_year += 1
    
    # 在找到的农历年内定位月份和日子
    leap_month = get_lunar_leap_month(lunar_year)
    is_leap = False
    
    for m in range(1, 13):
        # 检查是否是闰月
        if leap_month > 0 and m == leap_month + 1:
            month_days = 30 if LUNAR_DATA[lunar_year - 1900] & 0x10000 else 29
            if offset < month_days:
                return (lunar_year, leap_month, offset + 1, True)
            offset -= month_days
            is_leap = False
        
        month_days = get_lunar_month_days(lunar_year, m)
        if offset < month_days:
            return (lunar_year, m, offset + 1, is_leap)
        offset -= month_days
    
    # should never reach here
    return (lunar_year, 12, offset + 1, False)


# ═══════════════════════════
# 八字排盘
# ═══════════════════════════

def get_year_gz(year):
    """年柱天干地支"""
    base = 1984  # 甲子年
    offset = (year - base) % 60
    return TIAN_GAN[offset % 10] + DI_ZHI[offset % 12]

def get_month_gz(year_gz, month, day, is_leap):
    """月柱天干地支 (以节气为界)"""
    # 年干索引
    year_gan_idx = TIAN_GAN.index(year_gz[0])
    
    # 根据节气确定月支
    # 立春=寅月, 惊蛰=卯月, ...
    jie_qi_day = JIE_QI.get(month, 5)
    
    if month == 2 and day >= 4:
        month_idx = 1  # 寅月
    elif month == 3 and day >= 6:
        month_idx = 2
    elif month == 4 and day >= 5:
        month_idx = 3
    elif month == 5 and day >= 6:
        month_idx = 4
    elif month == 6 and day >= 6:
        month_idx = 5
    elif month == 7 and day >= 7:
        month_idx = 6
    elif month == 8 and day >= 8:
        month_idx = 7
    elif month == 9 and day >= 8:
        month_idx = 8
    elif month == 10 and day >= 8:
        month_idx = 9
    elif month == 11 and day >= 7:
        month_idx = 10
    elif month == 12 and day >= 7:
        month_idx = 11
    else:
        month_idx = (month + 9) % 12 if month >= 3 else month - 1
    
    # 月天干 = (年天干索引 * 2 + 月支索引) % 10
    month_gan_idx = (year_gan_idx * 2 + month_idx) % 10
    return TIAN_GAN[month_gan_idx] + DI_ZHI[month_idx]

def get_day_gz(date_obj):
    """日柱天干地支 (标准算法)"""
    base_date = datetime.date(1900, 1, 1)
    diff_days = (date_obj - base_date).days
    # 1900-01-01 是甲戌日 (甲戌 = 天干0 + 地支10)
    gan_idx = (diff_days + 0) % 10
    zhi_idx = (diff_days + 10) % 12
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_hour_gz(day_gz, hour):
    """时柱天干地支"""
    day_gan_idx = TIAN_GAN.index(day_gz[0])
    # 时辰: 23-1子时, 1-3丑时, ...
    zhi_idx = ((hour + 1) // 2) % 12
    # 时天干 = (日天干索引 * 2 + 时支索引) % 10
    gan_idx = (day_gan_idx * 2 + zhi_idx) % 10
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_hour_name(hour):
    """获取时辰名称"""
    names = ['子时 (23:00-01:00)', '丑时 (01:00-03:00)', '寅时 (03:00-05:00)',
             '卯时 (05:00-07:00)', '辰时 (07:00-09:00)', '巳时 (09:00-11:00)',
             '午时 (11:00-13:00)', '未时 (13:00-15:00)', '申时 (15:00-17:00)',
             '酉时 (17:00-19:00)', '戌时 (19:00-21:00)', '亥时 (21:00-23:00)']
    idx = ((hour + 1) // 2) % 12
    return names[idx]


# ═══════════════════════════
# 五行分析
# ═══════════════════════════

def analyze_wuxing(pillars):
    """分析八字五行"""
    wuxing = {'金': 0, '木': 0, '水': 0, '火': 0, '土': 0}
    
    for pillar_name, gz in pillars.items():
        if not gz or len(gz) < 2:
            continue
        gan = gz[0]
        zhi = gz[1]
        
        # 天干五行
        gan_idx = TIAN_GAN.index(gan)
        wuxing[WU_XING_TG[gan_idx]] += 1
        
        # 地支五行
        zhi_idx = DI_ZHI.index(zhi)
        wuxing[WU_XING_DZ[zhi_idx]] += 1
    
    # 缺失的五行
    missing = [w for w, count in wuxing.items() if count == 0]
    
    # 找出最强的五行
    dominant = max(wuxing, key=wuxing.get)
    
    return {'count': wuxing, 'missing': missing, 'dominant': dominant}


def get_day_master(pillars):
    """日主（日柱天干）"""
    day_gz = pillars.get('day', '')
    if len(day_gz) >= 1:
        gan = day_gz[0]
        wx = WU_XING_TG[TIAN_GAN.index(gan)]
        return {'gan': gan, 'wuxing': wx}
    return {'gan': '?', 'wuxing': '?'}


# ═══════════════════════════
# 解读生成
# ═══════════════════════════

SELF_INTERPRETATIONS = {
    '甲': {'nature': '参天大树，正直坚毅，有领导力但自尊心强',
           'career': '适合管理、教育、林业、建筑行业',
           'love': '对伴侣忠诚但固执己见，需要互补型伴侣'},
    '乙': {'nature': '花草藤蔓，柔韧细腻，善交际但易优柔寡断',
           'career': '适合艺术、设计、咨询、服务业',
           'love': '重视情感交流，适合有主见的伴侣带动'},
    '丙': {'nature': '太阳之火，热情开朗，慷慨大方但有时鲁莽',
           'career': '适合传媒、演艺、销售、互联网行业',
           'love': '爱情热烈主动，注意给对方空间'},
    '丁': {'nature': '灯烛之火，内向细腻，心思缜密但易敏感',
           'career': '适合研究、写作、技术、医疗行业',
           'love': '渴望灵魂伴侣，感情投入但容易受伤'},
    '戊': {'nature': '城墙之土，稳重踏实，诚信可靠但保守固执',
           'career': '适合金融、地产、行政、工程行业',
           'love': '责任感强但缺乏浪漫，需有耐心的伴侣'},
    '己': {'nature': '田园之土，温和包容，有耐心但魄力不足',
           'career': '适合教育、护理、农业、后勤行业',
           'love': '温柔体贴但有依赖倾向，需能扛事的伴侣'},
    '庚': {'nature': '刀剑之金，果断刚毅，执行力强但缺乏柔情',
           'career': '适合军警、法律、机械、竞技行业',
           'love': '行动胜于言语，追求效率十足但不懂甜言蜜语'},
    '辛': {'nature': '珠宝之金，精致优雅，品味高但有时候过于挑剔',
           'career': '适合珠宝、美容、音乐、奢侈品行业',
           'love': '追求浪漫完美的爱情，宁缺毋滥'},
    '壬': {'nature': '江河之水，心胸宽广，聪明灵活但缺乏定力',
           'career': '适合贸易、外交、旅游、物流行业',
           'love': '自由奔放不喜束缚，需成熟包容的伴侣'},
    '癸': {'nature': '雨露之水，智慧深沉，洞察力强但容易忧郁',
           'career': '适合学术、策划、心理咨询、侦探行业',
           'love': '情感深沉神秘，需要一个懂自己的人'},
}

# English interpretations
SELF_INTERPRETATIONS_EN = {
    '甲': {'nature': 'A towering tree — upright and persistent, a natural leader with strong self-esteem',
           'career': 'Management, education, forestry, construction',
           'love': 'Loyal to partners but stubborn; needs a complementary match'},
    '乙': {'nature': 'Flowers and vines — flexible and delicate, sociable but sometimes indecisive',
           'career': 'Arts, design, consulting, service industries',
           'love': 'Values emotional connection, thrives with a decisive partner'},
    '丙': {'nature': 'The blazing sun — passionate and generous, outgoing but sometimes impulsive',
           'career': 'Media, entertainment, sales, tech industry',
           'love': 'Bold and active in love; needs to give partner space'},
    '丁': {'nature': 'A candle flame — introspective and meticulous, thoughtful but easily hurt',
           'career': 'Research, writing, technology, healthcare',
           'love': 'Seeks a soulmate; emotionally invested but vulnerable'},
    '戊': {'nature': 'A fortress of earth — steady and reliable, trustworthy but conservative',
           'career': 'Finance, real estate, administration, engineering',
           'love': 'Strong sense of duty but lacks romance; needs a patient partner'},
    '己': {'nature': 'Garden soil — gentle and tolerant, patient but lacking boldness',
           'career': 'Education, nursing, agriculture, logistics',
           'love': 'Tender and caring but dependent; needs a capable partner'},
    '庚': {'nature': 'Forged steel — decisive and strong-willed, execution-oriented but lacks tenderness',
           'career': 'Military, law, mechanics, competitive sports',
           'love': 'Actions speak louder than words; pragmatic but not sweet-talking'},
    '辛': {'nature': 'Fine jewelry — refined and elegant, has great taste but can be picky',
           'career': 'Jewelry, beauty, music, luxury goods',
           'love': 'Pursues perfect romantic love; would rather wait than settle'},
    '壬': {'nature': 'A great river — broad-minded and intelligent, flexible but lacks persistence',
           'career': 'Trade, diplomacy, tourism, logistics',
           'love': 'Free-spirited and dislikes constraints; needs a mature, tolerant partner'},
    '癸': {'nature': 'Morning dew — deep and wise, perceptive but prone to melancholy',
           'career': 'Academia, strategy, psychology, investigation',
           'love': 'Emotionally deep and mysterious; needs someone who truly understands'},
}

def generate_interpretation(bazi_result, level='basic', lang='zh'):
    """根据八字结果生成详细解读。lang='en' 返回英文"""
    pillars = bazi_result['pillars']
    day_master = bazi_result['day_master']
    wuxing_info = bazi_result['wuxing']
    gan = day_master['gan']
    wx = day_master['wuxing']
    is_en = lang.startswith('en') if lang else False
    interp_db = SELF_INTERPRETATIONS_EN if is_en else SELF_INTERPRETATIONS
    dm_full = DAY_MASTER_FULL.get(gan, {})
    
    self_info = interp_db.get(gan, {'nature': 'Insufficient data' if is_en else '目前数据不足', 'career': 'No suggestion' if is_en else '暂无建议', 'love': 'No suggestion' if is_en else '暂无建议'})
    
    if is_en:
        wx_en = {'木': 'Wood', '火': 'Fire', '土': 'Earth', '金': 'Metal', '水': 'Water'}
        nature_first = self_info['nature'].split(',')[0].split(' — ')[0] if ' — ' in self_info['nature'] else self_info['nature'].split(',')[0]
        summary = f"You are a {wx_en.get(wx, '')} {gan} person, like a {nature_first}."
    else:
        summary = f"您是{gan}木命人，如同{self_info['nature'].split('，')[0]}。"
    
    result = {
        'summary': dm_full.get('summary_en' if is_en else 'summary_zh', summary),
        'nature': self_info['nature'],
        'wuxing_balance': '',
        'career': '',
        'love': '',
        'health': '',
        'lucky_elements': [],
        'day_master_strength': '',
        'ten_gods_analysis': '',
    }
    
    # 五行详细
    dominant = wuxing_info.get('dominant', '')
    missing = wuxing_info.get('missing', [])
    pct = wuxing_info.get('percent', {})
    if is_en:
        wx_en_full = {'金':'Metal','木':'Wood','水':'Water','火':'Fire','土':'Earth'}
        dominant_en = wx_en_full.get(dominant, dominant)
        if missing:
            missing_en = [wx_en_full.get(m,m) for m in missing]
            result['wuxing_balance'] = f"Missing {' & '.join(missing_en)}. Dominant: {dominant_en} ({pct.get(dominant,0)}%). Balance through colors, accessories and habits."
        else:
            result['wuxing_balance'] = f"All five elements present. Dominant: {dominant_en} ({pct.get(dominant,0)}%). Naturally balanced."
    else:
        if missing:
            result['wuxing_balance'] = f"五行缺{'、'.join(missing)}。{dominant}最旺（占{pct.get(dominant,0)}%）。建议通过颜色、饰品或日常习惯来补充缺失元素。"
        else:
            result['wuxing_balance'] = f"五行齐全，先天命格较为平衡。{dominant}最旺（占{pct.get(dominant,0)}%），这是你的核心特质。"
    
    # 日主强弱
    strength = bazi_result.get('day_master_strength', '')
    if is_en:
        strength_map = {'身强':'Strong','身弱':'Weak','中和':'Balanced'}
        result['day_master_strength'] = strength_map.get(strength, strength)
    else:
        result['day_master_strength'] = strength
    
    # 十神
    ten_gods = bazi_result.get('ten_gods', {})
    if ten_gods:
        pillar_names = {'year': 'Year' if is_en else '年柱', 'month': 'Month' if is_en else '月柱', 'day': 'Day' if is_en else '日柱', 'hour': 'Hour' if is_en else '时柱'}
        tg_lines = []
        for pname, gods in ten_gods.items():
            pn = pillar_names.get(pname, pname)
            g = _shi_shen_en(gods.get('gan','')) if is_en else gods.get('gan','')
            z = _shi_shen_en(gods.get('zhi','')) if is_en else gods.get('zhi','')
            tg_lines.append(f"{pn}: {g}/{z}")
        result['ten_gods_analysis'] = ' | '.join(tg_lines)
    
    # 神煞
    shen_sha = bazi_result.get('shen_sha', {})
    if shen_sha and shen_sha.get('stars'):
        result['shen_sha'] = {
            'stars': list(shen_sha['stars'].values()),
            'explanations': list((shen_sha['explanations_en'] if is_en else shen_sha['explanations_zh']).values())
        }
    
    # 解读层级
    if level in ('basic', 'full'):
        result['career'] = dm_full.get('career_en' if is_en else 'career_zh', self_info['career'])
        result['love'] = dm_full.get('love_en' if is_en else 'love_zh', self_info['love'])
        result['health'] = dm_full.get('health_en' if is_en else 'health_zh', '')
    
    if level == 'full':
        wx_cycle = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
        wx_support = wx_cycle.get(wx, '')
        if wx_support:
            wx_support_en = {'木':'Wood','火':'Fire','土':'Earth','金':'Metal','水':'Water'}.get(wx_support, wx_support)
            if is_en:
                result['lucky_elements'] = [wx_support_en]
                result['lucky_tip'] = f"Favor {wx_support_en}-related colors, numbers, and environments"
            else:
                result['lucky_elements'] = [wx_support]
                result['lucky_tip'] = f"适合多接触与「{wx_support}」相关的颜色、数字、环境"
        
        # 大运总结
        dayun = bazi_result.get('dayun', [])
        if dayun:
            mid = dayun[len(dayun)//2] if len(dayun)>3 else dayun[0]
            if is_en:
                result['current_luck'] = f"Current decade ({mid['start_age']}-{mid['end_age']}): {mid['ganzhi']} ({mid.get('nayin','')})"
            else:
                result['current_luck'] = f"当前大运（{mid['start_age']}-{mid['end_age']}岁）：{mid['ganzhi']}（{mid.get('nayin_cn','')}）"
        
        # 流年
        liunian = bazi_result.get('liunian', [])
        if liunian:
            if is_en:
                result['yearly_luck'] = []
                for ln in liunian:
                    rel = ', '.join(ln.get('zhi_relations',[])) or 'neutral'
                    result['yearly_luck'].append(f"{ln['year']} ({ln['ganzhi']}): {ln['shi_shen']}, {rel}")
            else:
                result['yearly_luck'] = []
                for ln in liunian:
                    rel = '、'.join(ln.get('zhi_relations',[])) or '平和'
                    result['yearly_luck'].append(f"{ln['year']}年（{ln['ganzhi']}）：十神{ln['shi_shen']}，地支{rel}")
    
    return result


# ═══════════════════════════
# 主函数
# ═══════════════════════════

def calculate_bazi(year, month, day, hour=12, minute=0, level='basic', lang='zh', gender='male'):
    """
    计算八字命盘（完整版）
    year, month, day: 公历日期
    hour: 小时 (0-23)
    minute: 分钟 (0-59, 精确排盘)
    level: 'free' / 'basic' / 'full'
    lang: 'zh' / 'en'
    gender: 'male' / 'female' (大运顺逆排)
    """
    try:
        date_obj = datetime.date(year, month, day)
    except ValueError:
        return {'error': '日期不合法' if lang.startswith('zh') else 'Invalid date'}
    
    # 农历转换
    lunar_year, lunar_month, lunar_day, is_leap = solar_to_lunar(date_obj)
    
    # 四柱推算
    year_gz = get_year_gz(lunar_year)
    month_gz = get_month_gz(year_gz, month, day, is_leap)
    day_gz = get_day_gz(date_obj)
    hour_gz = get_hour_gz(day_gz, hour)
    
    pillars = {
        'year': year_gz,
        'month': month_gz,
        'day': day_gz,
        'hour': hour_gz
    }
    
    # 纳音
    nayin = {k: NA_YIN.get(v, '') for k, v in pillars.items()}
    
    # 生肖
    zhi_idx = DI_ZHI.index(year_gz[1])
    shengxiao = SHENG_XIAO[zhi_idx]
    
    # 时辰名称
    hour_name = get_hour_name(hour)
    
    # 五行详细分析
    wuxing = detailed_wuxing_balance(pillars)
    
    # 空亡
    xun_kong = get_xun_kong(day_gz)
    
    # 日主
    day_master = get_day_master(pillars)
    
    # 日主强弱
    dm_strength = day_master_strength(day_master, pillars, wuxing)
    
    # 十神
    ten_gods = {}
    day_gan = day_gz[0]
    for pname, gz in pillars.items():
        gan = gz[0]
        zhi = gz[1] if len(gz) > 1 else ''
        ten_gods[pname] = {
            'gan': get_shi_shen(day_gan, gan),
            'zhi': get_shi_shen(day_gan, zhi) if zhi else '',
        }
    
    # 神煞
    shen_sha = get_shen_sha(pillars, day_gz[1] if len(day_gz) > 1 else '')
    
    # 农历日期字符串
    lunar_month_str = f"{'闰' if is_leap else ''}{lunar_month}月"
    lunar_day_str = f"{lunar_day}日"
    
    result = {
        'solar': f"{year}年{month}月{day}日",
        'lunar': f"{lunar_year}年{lunar_month_str}{lunar_day_str}",
        'hour': hour_name,
        'shengxiao': shengxiao,
        'pillars': pillars,
        'nayin': nayin,
        'day_master': day_master,
        'wuxing': wuxing,
        'xun_kong': xun_kong,
        'day_master_strength': dm_strength,
        'ten_gods': ten_gods,
        'shen_sha': shen_sha,
    }
    
    # 大运 (free: 3个, basic: 6个, full: 10个)
    dayun = calculate_dayun(year, month, day, hour, gender, lang)
    result['dayun'] = dayun[:3] if level == 'free' else (dayun[:6] if level == 'basic' else dayun)
    
    # 流年 (free: 1个, basic/full: 5个)
    current_year = datetime.date.today().year
    liunian = calculate_liunian(day_gz, current_year, 5, lang)
    result['liunian'] = liunian[:1] if level == 'free' else liunian
    
    # 生成解读
    interp = generate_interpretation(result, level, lang)
    result['interpretation'] = interp
    
    return result

# ═══════════════════════════
# 命令行测试
# ═══════════════════════════

if __name__ == '__main__':
    import json
    # 测试: 1990-05-20 08:00
    result = calculate_bazi(1990, 5, 20, 8, 0, 'full', 'zh', 'male')
    print(json.dumps(result, ensure_ascii=False, indent=2))
