"""
风水堪舆引擎 — Kua Number / 八宅风水 / 五鬼财运 / 流年飞星
"""
import datetime

# 五行生克
WUXING = ['金','木','水','火','土']
WUXING_EN = ['Metal','Wood','Water','Fire','Earth']
WU_CYCLE = {0:{2:'生',3:'克',4:'生',1:'克'},1:{3:'生',4:'克',0:'克',2:'生'},2:{4:'生',0:'克',1:'生',3:'克'},3:{1:'生',2:'克',0:'克',4:'生'},4:{0:'生',1:'克',3:'生',2:'克'}}
WU_EMOJI = {'金':'🪙','木':'🌿','水':'💧','火':'🔥','土':'🏔️'}

# 八卦方位
GUA_DIRECTIONS = {
    1: {'name':'坎','en':'Kan','trigram':'☵','element':'水','element_en':'Water'},
    2: {'name':'坤','en':'Kun','trigram':'☷','element':'土','element_en':'Earth'},
    3: {'name':'震','en':'Zhen','trigram':'☳','element':'木','element_en':'Wood'},
    4: {'name':'巽','en':'Xun','trigram':'☴','element':'木','element_en':'Wood'},
    6: {'name':'乾','en':'Qian','trigram':'☰','element':'金','element_en':'Metal'},
    7: {'name':'兑','en':'Dui','trigram':'☱','element':'金','element_en':'Metal'},
    8: {'name':'艮','en':'Gen','trigram':'☶','element':'土','element_en':'Earth'},
    9: {'name':'离','en':'Li','trigram':'☲','element':'火','element_en':'Fire'},
}

# 八宅吉凶方位 (以卦位为中心)
# 顺序: 祸害、绝命、五鬼、六煞、生气、天医、延年、伏位
BAGUA_MAP = {
    1: {1:'V', 2:'A', 3:'B', 4:'C', 6:'D', 7:'E', 8:'F', 9:'G'},  # 坎
    2: {1:'G', 2:'V', 3:'E', 4:'F', 6:'A', 7:'B', 8:'C', 9:'D'},  # 坤
    3: {1:'F', 2:'G', 3:'V', 4:'A', 6:'C', 7:'D', 8:'E', 9:'B'},  # 震
    4: {1:'E', 2:'F', 3:'G', 4:'V', 6:'D', 7:'C', 8:'B', 9:'A'},  # 巽
    6: {1:'C', 2:'D', 3:'E', 4:'F', 6:'V', 7:'G', 8:'A', 9:'B'},  # 乾
    7: {1:'D', 2:'C', 3:'F', 4:'E', 6:'G', 7:'V', 8:'B', 9:'A'},  # 兑
    8: {1:'B', 2:'A', 3:'D', 4:'C', 6:'E', 7:'F', 8:'V', 9:'G'},  # 艮
    9: {1:'A', 2:'B', 3:'C', 4:'D', 6:'F', 7:'E', 8:'G', 9:'V'},  # 离
}
# V=伏位 A=生气 B=延年 C=天医 D=祸害 E=绝命 F=五鬼 G=六煞
STAR_NAMES = {
    'V': {'zh':'伏位','en':'Fu Wei / Stable Base'},
    'A': {'zh':'生气','en':'Sheng Qi / Prosperity'},
    'B': {'zh':'延年','en':'Yan Nian / Longevity'},
    'C': {'zh':'天医','en':'Tian Yi / Health'},
    'D': {'zh':'祸害','en':'Huo Hai / Calamity'},
    'E': {'zh':'绝命','en':'Jue Ming / Severed Fate'},
    'F': {'zh':'五鬼','en':'Wu Gui / Five Ghosts'},
    'G': {'zh':'六煞','en':'Liu Sha / Six Killings'},
}
DIR_NAMES = {1:'北',2:'西南',3:'东',4:'东南',6:'西北',7:'西',8:'东北',9:'南'}
DIR_EN = {1:'North',2:'Southwest',3:'East',4:'Southeast',6:'Northwest',7:'West',8:'Northeast',9:'South'}
DIR_EMOJI = {1:'🧭',2:'↙️',3:'➡️',4:'↘️',6:'↖️',7:'⬅️',8:'↗️',9:'⬆️'}

GOOD_STARS = ['A','B','C']
BAD_STARS = ['D','E','F','G']

STAR_ADVICE = {
    'V': {'zh':'安放神位、主人房、客厅最佳方位','en':'Best for altar, master bedroom, living room.'},
    'A': {'zh':'大门、房门朝向最佳，利财运事业','en':'Best direction for main door and bedroom. Boosts wealth.'},
    'B': {'zh':'放床位、办公桌吉利，利健康和长寿','en':'Good for bed and desk placement. Enhances health and longevity.'},
    'C': {'zh':'\u653e\u5e8a\u4f4d\u3001\u6551\u62a4\u4eba\u4f4d\uff0c\u5229\u5065\u5eb7\u6062\u590d','en':'Good for bed and nursing. Aids health recovery.'},
    'D': {'zh':'宜放厕所、杂物间，忌做主人房','en':'Best for bathroom and storage. Avoid as master bedroom.'},
    'E': {'zh':'最凶之方，宜空置或放高大重物镇之','en':'Most dangerous direction. Keep empty or place heavy items here.'},
    'F': {'zh':'宜放厕所、厨房灶位，忌安床','en':'Good for bathroom and kitchen stove. Avoid bedroom placement.'},
    'G': {'zh':'宜做厕所或储物，忌做卧室大门','en':'Good for bathroom or storage. Avoid as bedroom or main entrance.'},
}


def get_kua(year, gender):
    """计算命卦 (Kua Number)"""
    if year < 1900 or year > 2100:
        return 0
    # 男性: (100 - 年份后两位) % 9, 女性: (年份后两位 - 4) % 9
    last2 = year % 100
    if gender == 'male':
        kua = (100 - last2) % 9
    else:
        kua = (last2 - 4) % 9
    if kua == 0:
        kua = 9
    if kua == 5:
        kua = 2 if gender == 'male' else 8  # 坤命(男) 艮命(女)
    return kua


def get_directions(kua):
    """获取八宅方位吉凶"""
    gua = GUA_DIRECTIONS[kua]
    bagua = BAGUA_MAP[kua]
    good_dirs = []
    bad_dirs = []
    for gk, star in bagua.items():
        dname = DIR_NAMES.get(gk, '')
        entry = {
            'direction': dname,
            'direction_en': DIR_EN.get(gk, ''),
            'direction_emoji': DIR_EMOJI.get(gk, ''),
            'star': STAR_NAMES.get(star, {}).get('zh', ''),
            'star_en': STAR_NAMES.get(star, {}).get('en', ''),
            'advice': STAR_ADVICE.get(star, {}).get('zh', ''),
            'advice_en': STAR_ADVICE.get(star, {}).get('en', ''),
            'is_good': star in GOOD_STARS,
        }
        if star in GOOD_STARS:
            good_dirs.append(entry)
        else:
            bad_dirs.append(entry)
    return {
        'gua': gua,
        'east_west': '东四命' if kua in [1,3,4,9] else '西四命',
        'east_west_en': 'East Group' if kua in [1,3,4,9] else 'West Group',
        'good_directions': good_dirs,
        'bad_directions': bad_dirs,
    }


def get_annual_flying_star(year):
    """流年飞星 (九宫飞星)"""
    # Simplified: 年紫白飞星
    # 计算年星: (9 - (year - 1) % 9, 1-indexed)
    base = 10 - ((year - 1) % 9 + 1)
    stars = {
        1: {'zh':'一白贪狼星','en':'1 White - Greedy Wolf','nature_zh':'吉·桃花·人缘','nature_en':'Auspicious - Romance & Social'},
        2: {'zh':'二黑巨门星','en':'2 Black - Giant Gate','nature_zh':'凶·病符·是非','nature_en':'Inauspicious - Illness & Quarrels'},
        3: {'zh':'三碧禄存星','en':'3 Green - Lu Cun','nature_zh':'凶·口舌·官司','nature_en':'Inauspicious - Arguments & Lawsuits'},
        4: {'zh':'四绿文昌星','en':'4 Green - Literary Star','nature_zh':'吉·学业·考运','nature_en':'Auspicious - Studies & Exams'},
        5: {'zh':'五黄廉贞星','en':'5 Yellow - Integrity','nature_zh':'大凶·灾祸·疾病','nature_en':'Very Inauspicious - Disasters & Illness'},
        6: {'zh':'六白武曲星','en':'6 White - Military Star','nature_zh':'吉·偏财·权贵','nature_en':'Auspicious - Wealth & Authority'},
        7: {'zh':'七赤破军星','en':'7 Red - Broken Army','nature_zh':'凶·盗贼·破损','nature_en':'Inauspicious - Theft & Damage'},
        8: {'zh':'八白左辅星','en':'8 White - Left Assistant','nature_zh':'大吉·正财·置业','nature_en':'Very Auspicious - Wealth & Property'},
        9: {'zh':'九紫右弼星','en':'9 Purple - Right Assistant','nature_zh':'吉·喜事·姻缘','nature_en':'Auspicious - Joy & Marriage'},
    }
    # Map stars to 9 palaces (central=5, then clockwise from north)
    # 方位顺序: 中→北→西南→东→东南→西北→西→东北→南
    palace_order = [5, 1, 2, 3, 4, 6, 7, 8, 9]  # 九宫本位
    dir_labels = ['中','北','西南','东','东南','西北','西','东北','南']
    dir_labels_en = ['Center','North','Southwest','East','Southeast','Northwest','West','Northeast','South']
    dir_emoji = ['🏠','🧭','↙️','➡️','↘️','↖️','⬅️','↗️','⬆️']
    
    result = []
    for i, palace in enumerate(palace_order):
        star_num = (base + palace - 1) % 9 + 1
        s = stars[star_num]
        result.append({
            'direction': dir_labels[i],
            'direction_en': dir_labels_en[i],
            'direction_emoji': dir_emoji[i],
            'star': s['zh'],
            'star_en': s['en'],
            'nature_zh': s['nature_zh'],
            'nature_en': s['nature_en'],
            'number': star_num,
        })
    return result


def get_home_advice(door_direction, kua, level='free'):
    """居家风水建议"""
    directions = get_directions(kua)
    
    # 大门方位吉凶
    door_gua = None
    for gk, entry in GUA_DIRECTIONS.items():
        if DIR_NAMES.get(gk) == door_direction:
            door_gua = gk
            break
    
    # 简化分析
    result = {
        'kua': kua,
        'gua': directions['gua'],
        'east_west': directions['east_west'],
        'east_west_en': directions['east_west_en'],
        'good_directions': directions['good_directions'],
        'bad_directions': directions['bad_directions'],
        'door_direction': door_direction,
    }
    
    if door_gua:
        star_code = BAGUA_MAP[kua].get(door_gua, '?')
        door_star = {
            'good': star_code in GOOD_STARS,
            'star_zh': STAR_NAMES.get(star_code, {}).get('zh', ''),
            'star_en': STAR_NAMES.get(star_code, {}).get('en', ''),
        }
        result['door_analysis'] = door_star
    
    if level in ('basic', 'full'):
        result['annual_stars'] = get_annual_flying_star(datetime.date.today().year)
    
    if level == 'full':
        # 详细建议
        result['advice_zh'] = generate_full_advice(result, 'zh')
        result['advice_en'] = generate_full_advice(result, 'en')
    
    return result


def generate_full_advice(data, lang):
    """生成完整风水建议"""
    kua = data['kua']
    ew = data['east_west']
    dname = data['door_direction']
    da = data.get('door_analysis', {})
    
    if lang == 'zh':
        lines = []
        lines.append(f"📐 你的命卦是{data['gua']['trigram']} {data['gua']['name']}卦，属{ew}。")
        
        good = ', '.join(f"{d['direction']}({d['star']})" for d in data['good_directions'])
        bad = ', '.join(f"{d['direction']}({d['star']})" for d in data['bad_directions'])
        lines.append(f"🍀 吉方：{good}")
        lines.append(f"⚠️ 凶方：{bad}")
        
        if da:
            s = da.get('star_zh', '')
            if da.get('good'):
                lines.append(f"✅ 大门朝{dname}为{s}，吉利。适合迎纳旺气。")
            else:
                lines.append(f"❌ 大门朝{dname}为{s}，犯凶星。建议调换朝向或在门口放化煞物品。")
        
        lines.append(f"\n💡 实用建议：")
        lines.append(f"· 主人房宜在{data['good_directions'][0]['direction']}方（{data['good_directions'][0]['star']}位）")
        lines.append(f"· 厨房宜在{data['bad_directions'][0]['direction']}方（压凶星）")
        lines.append(f"· 厕所宜在{data['bad_directions'][3]['direction']}方（{data['bad_directions'][3]['star']}位）")
        lines.append(f"· 财位在{data['good_directions'][1]['direction']}方，可放水晶或招财物品")
        return '\n'.join(lines)
    else:
        lines = []
        lines.append(f"📐 Your Kua is {data['gua']['en']} (Trigram: {data['gua']['trigram']}), belongs to {data['east_west_en']}.")
        
        good = ', '.join(f"{d['direction_en']}({d['star_en']})" for d in data['good_directions'])
        bad = ', '.join(f"{d['direction_en']}({d['star_en']})" for d in data['bad_directions'])
        lines.append(f"🍀 Auspicious: {good}")
        lines.append(f"⚠️ Inauspicious: {bad}")
        
        if da:
            s = da.get('star_en', '')
            if da.get('good'):
                lines.append(f"✅ Door facing {data['door_direction']} is {s} — auspicious!")
            else:
                lines.append(f"❌ Door facing {data['door_direction']} is {s} — inauspicious. Consider adjusting or adding remedies.")
        
        lines.append(f"\n💡 Practical tips:")
        lines.append(f"· Master bedroom: best in {data['good_directions'][0]['direction_en']} ({data['good_directions'][0]['star_en']})")
        lines.append(f"· Kitchen: best in {data['bad_directions'][0]['direction_en']} (suppress negative star)")
        lines.append(f"· Bathroom: best in {data['bad_directions'][3]['direction_en']} ({data['bad_directions'][3]['star_en']})")
        lines.append(f"· Wealth corner: {data['good_directions'][1]['direction_en']} — place crystals or wealth objects here")
        return '\n'.join(lines)


if __name__ == '__main__':
    import json
    r = get_home_advice('南', get_kua(1990, 'male'), 'full')
    print(json.dumps(r, ensure_ascii=False, indent=2))
