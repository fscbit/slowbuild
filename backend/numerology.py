"""
生命灵数引擎 — Life Path + Expression + Soul Urge numbers
"""
import datetime

def reduce_num(num):
    """Pythagorean reduction (keep 11,22,33 master numbers)"""
    s = str(num)
    total = sum(int(c) for c in s)
    if total in (11, 22, 33):
        return total
    if total < 10:
        return total
    return reduce_num(total)

def get_life_path(year, month, day):
    """Life Path Number"""
    return reduce_num(reduce_num(year) + reduce_num(month) + reduce_num(day))

def get_expression(name):
    """Expression/Destiny Number from name (Pythagorean numerology)"""
    mapping = {
        'a':1,'b':2,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,
        'j':1,'k':2,'l':3,'m':4,'n':5,'o':6,'p':7,'q':8,'r':9,
        's':1,'t':2,'u':3,'v':4,'w':5,'x':6,'y':7,'z':8,
    }
    total = 0
    for ch in name.lower():
        if ch in mapping:
            total += mapping[ch]
    return reduce_num(total)

def get_soul_urge(name):
    """Soul Urge / Heart's Desire Number (vowels only)"""
    vowels = set('aeiou')
    total = 0
    for ch in name.lower():
        if ch in vowels:
            # Simple a=1,b=2 mapping for vowels
            total += ord(ch) - ord('a') + 1
    return reduce_num(total) if total > 0 else 1

LIFE_PATH_READINGS = {
    1: {'zh': '天生的领导者，独立自主，创造力强。需要学会合作而非单打独斗。适合创业、管理、自由职业。',
        'en': 'The Leader — independent, creative, ambitious. Learn to collaborate. Suited for entrepreneurship and leadership.'},
    2: {'zh': '和平的缔造者，善于合作，敏感细腻。是天生的外交家和调解人。适合外交、咨询、服务行业。',
        'en': 'The Peacemaker — cooperative, sensitive, diplomatic. Natural mediator. Ideal for diplomacy and counseling.'},
    3: {'zh': '天生的表达者，乐观开朗，有艺术天赋。需要用创造性的方式表达自己。适合演艺、写作、设计。',
        'en': 'The Communicator — optimistic, expressive, artistic. Needs creative outlets. Suited for arts and media.'},
    4: {'zh': '稳步的建设者，踏实可靠，组织能力强。是团队中最稳固的基石。适合工程、会计、管理。',
        'en': 'The Builder — steady, reliable, organized. The solid foundation of any team. Suited for engineering and management.'},
    5: {'zh': '自由的探险者，热爱变化，适应力强。最大的恐惧是被束缚。适合旅行、销售、媒体行业。',
        'en': 'The Adventurer — freedom-loving, adaptable, curious. Fears being tied down. Suited for travel and media.'},
    6: {'zh': '无私的奉献者，有责任感，关爱他人。把家庭和社群放在第一位。适合教育、医疗、公益。',
        'en': 'The Nurturer — responsible, caring, devoted. Puts family and community first. Suited for education and healthcare.'},
    7: {'zh': '深度的思考者，哲学家气质，善于分析。需要独处时间来充电。适合学术、研究、技术。',
        'en': 'The Thinker — philosophical, analytical, introspective. Needs solitude to recharge. Suited for academia and tech.'},
    8: {'zh': '力量的追求者，有野心，商业头脑强。物质和精神需要找到平衡。适合金融、法律、管理。',
        'en': 'The Powerhouse — ambitious, business-minded. Must balance material and spiritual. Suited for finance and law.'},
    9: {'zh': '博爱的理想主义者，有人道精神。放手和给予是你的功课。适合慈善、艺术、精神领域。',
        'en': 'The Humanitarian — idealistic, compassionate. Learning to let go and give. Suited for charity and arts.'},
    11: {'zh': '灵性导师，高度直觉，双重天赋。需要将灵感落地。这是大师数字，潜力巨大。',
         'en': 'Spiritual Messenger — highly intuitive, double gifts. Must ground inspiration. Master number with great potential.'},
    22: {'zh': '大师建造者，能将梦想变为现实。具有改变世界的力量。最高的大师数字之一。',
         'en': 'Master Builder — turns dreams into reality. Power to change the world. Highest master number.'},
    33: {'zh': '宇宙导师，伟大的爱与牺牲精神。你的使命是照亮他人。最稀有的大师数字。',
         'en': 'Cosmic Teacher — great love and sacrifice. Mission is to enlighten others. Rarest master number.'},
}

PERSONAL_YEARS = {
    1: {'zh': '新开始的一年。播种期，适合开启新项目、新关系。',
        'en': 'Year of New Beginnings. Plant seeds — start new projects and relationships.'},
    2: {'zh': '合作与耐心的一年。适合建立联盟、等待时机成熟。',
        'en': 'Year of Cooperation. Build alliances and wait for the right timing.'},
    3: {'zh': '创造与表达的一年。适合社交、创作、享受生活。',
        'en': 'Year of Creativity. Socialize, create, and enjoy life.'},
    4: {'zh': '建设与扎根的一年。努力工作、打好基础。',
        'en': 'Year of Building. Work hard and lay solid foundations.'},
    5: {'zh': '变化与自由的一年。拥抱改变、冒险尝试。',
        'en': 'Year of Change. Embrace transformation and take risks.'},
    6: {'zh': '责任与家庭的一年。关注家人、感情和承诺。',
        'en': 'Year of Responsibility. Focus on family, love, and commitments.'},
    7: {'zh': '内省与学习的一年。静心思考、深造研究。',
        'en': 'Year of Introspection. Reflect deeply and pursue knowledge.'},
    8: {'zh': '收获与权力的年份。事业上升、财务状况改善。',
        'en': 'Year of Harvest. Career advancement and financial improvement.'},
    9: {'zh': '完成与释放的一年。清理旧物、结束不必要的关系。',
        'en': 'Year of Completion. Clear out the old, release what no longer serves.'},
}

def build_numerology_report(year, month, day, name='', level='free'):
    """构建完整的灵数报告"""
    try:
        datetime.date(year, month, day)
    except:
        return {'error': 'Invalid date'}

    lp = get_life_path(year, month, day)
    result = {
        'life_path': lp,
        'life_path_reading_zh': LIFE_PATH_READINGS.get(lp, {}).get('zh', '独特的生命之路'),
        'life_path_reading_en': LIFE_PATH_READINGS.get(lp, {}).get('en', 'A unique life path.'),
    }

    # Personal year
    current_year = datetime.date.today().year
    py_num = reduce_num(reduce_num(month) + reduce_num(day) + reduce_num(current_year))
    result['personal_year'] = py_num
    result['personal_year_zh'] = PERSONAL_YEARS.get(py_num, {}).get('zh', '')
    result['personal_year_en'] = PERSONAL_YEARS.get(py_num, {}).get('en', '')

    if level in ('basic', 'full') and name:
        expr = get_expression(name)
        soul = get_soul_urge(name)
        result['expression'] = expr
        result['soul_urge'] = soul
        result['expression_reading_zh'] = LIFE_PATH_READINGS.get(expr, {}).get('zh', '')
        result['expression_reading_en'] = LIFE_PATH_READINGS.get(expr, {}).get('en', '')
        result['soul_urge_reading_zh'] = LIFE_PATH_READINGS.get(soul, {}).get('zh', '')
        result['soul_urge_reading_en'] = LIFE_PATH_READINGS.get(soul, {}).get('en', '')

    if level == 'full':
        # Challenge numbers, maturity number, etc
        result['maturity'] = reduce_num(lp + get_expression(name) if name else lp + 1)
        result['maturity_reading_zh'] = LIFE_PATH_READINGS.get(result['maturity'], {}).get('zh', '')
        result['maturity_reading_en'] = LIFE_PATH_READINGS.get(result['maturity'], {}).get('en', '')

    return result


if __name__ == '__main__':
    import json
    r = build_numerology_report(1990, 5, 20, 'John', 'full')
    print(json.dumps(r, ensure_ascii=False, indent=2))
