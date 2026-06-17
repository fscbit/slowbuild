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

def generate_interpretation(bazi_result, level='basic'):
    """根据八字结果生成解读"""
    pillars = bazi_result['pillars']
    day_master = bazi_result['day_master']
    wuxing_info = bazi_result['wuxing']
    gan = day_master['gan']
    wx = day_master['wuxing']
    
    self_info = SELF_INTERPRETATIONS.get(gan, {'nature': '目前数据不足', 'career': '暂无建议', 'love': '暂无建议'})
    
    result = {
        'summary': f"您是{gan}木命人，如同{self_info['nature'].split('，')[0]}。",
        'nature': self_info['nature'],
        'wuxing_balance': "五行",
        'career': '',
        'love': '',
        'lucky_elements': [],
    }
    
    if level == 'basic':
        result['career'] = self_info['career']
        result['love'] = self_info['love']
    
    if level == 'full':
        # 详细解读
        missing = wuxing_info['missing']
        dominant = wuxing_info['dominant']
        
        if len(missing) > 1:
            result['wuxing_balance'] = f"五行缺{'、'.join(missing)}，建议通过颜色、饰品或名字来补充。{dominant}过旺，注意平衡。"
        elif len(missing) == 1:
            result['wuxing_balance'] = f"五行缺{missing[0]}，建议在日常生活中多接触与{missing[0]}相关的元素。"
        else:
            result['wuxing_balance'] = f"五行齐全，先天命格比较平衡。{dominant}较旺，这是你的核心特质。"
        
        result['career'] = self_info['career']
        result['love'] = self_info['love']
        
        # 吉祥元素
        wx_cycle = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
        wx_support = wx_cycle.get(wx, '')
        if wx_support:
            result['lucky_elements'] = [wx_support]
    
    return result


# ═══════════════════════════
# 主函数
# ═══════════════════════════

def calculate_bazi(year, month, day, hour=12, level='basic'):
    """
    计算八字命盘
    year, month, day: 公历日期
    hour: 小时 (0-23)
    level: 'free' / 'basic' / 'full'
    """
    try:
        date_obj = datetime.date(year, month, day)
    except ValueError:
        return {'error': '日期不合法'}
    
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
    
    # 生肖
    zhi_idx = DI_ZHI.index(year_gz[1])
    shengxiao = SHENG_XIAO[zhi_idx]
    
    # 时辰名称
    hour_name = get_hour_name(hour)
    
    # 五行分析
    wuxing = analyze_wuxing(pillars)
    
    # 日主
    day_master = get_day_master(pillars)
    
    # 农历日期字符串
    lunar_month_str = f"{'闰' if is_leap else ''}{lunar_month}月"
    lunar_day_str = f"{lunar_day}日"
    
    result = {
        'solar': f"{year}年{month}月{day}日",
        'lunar': f"{lunar_year}年{lunar_month_str}{lunar_day_str}",
        'hour': hour_name,
        'shengxiao': shengxiao,
        'pillars': pillars,
        'day_master': day_master,
        'wuxing': wuxing,
    }
    
    # 生成解读
    interp = generate_interpretation(result, level)
    result['interpretation'] = interp
    
    return result


# ═══════════════════════════
# 命令行测试
# ═══════════════════════════

if __name__ == '__main__':
    import json
    # 测试: 1990-05-20 08:00
    result = calculate_bazi(1990, 5, 20, 8, 'full')
    print(json.dumps(result, ensure_ascii=False, indent=2))
