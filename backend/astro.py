"""
西方占星引擎 — 太阳/月亮/上升星座 + 行星 + 每日运势
"""
import datetime, hashlib, json

# 星座范围
ZODIAC = [
    ('摩羯座','Capricorn',(12,22),(1,19)),
    ('水瓶座','Aquarius',(1,20),(2,18)),
    ('双子座','Gemini',(5,21),(6,21)),
    ('巨蟹座','Cancer',(6,22),(7,22)),
    ('狮子座','Leo',(7,23),(8,22)),
    ('处女座','Virgo',(8,23),(9,22)),
    ('天秤座','Libra',(9,23),(10,23)),
    ('天蝎座','Scorpio',(10,24),(11,22)),
    ('射手座','Sagittarius',(11,23),(12,21)),
    ('双鱼座','Pisces',(2,19),(3,20)),
    ('白羊座','Aries',(3,21),(4,19)),
    ('金牛座','Taurus',(4,20),(5,20)),
]

def get_sun_sign(month, day):
    """太阳星座"""
    zodiac_list = [
        ('摩羯座','Capricorn',12,22,1,19),
        ('水瓶座','Aquarius',1,20,2,18),
        ('双鱼座','Pisces',2,19,3,20),
        ('白羊座','Aries',3,21,4,19),
        ('金牛座','Taurus',4,20,5,20),
        ('双子座','Gemini',5,21,6,21),
        ('巨蟹座','Cancer',6,22,7,22),
        ('狮子座','Leo',7,23,8,22),
        ('处女座','Virgo',8,23,9,22),
        ('天秤座','Libra',9,23,10,23),
        ('天蝎座','Scorpio',10,24,11,22),
        ('射手座','Sagittarius',11,23,12,21),
    ]
    for cn, en, m1, d1, m2, d2 in zodiac_list:
        if m1 == 12:
            if (month == 12 and day >= d1) or (month == 1 and day <= d2):
                return {'cn': cn, 'en': en, 'element': '土' if cn == '摩羯座' else '', 'emoji': '♑' if en == 'Capricorn' else '♑'}
        elif (month == m1 and day >= d1) or (month == m2 and day <= d2):
            emojis = {'Aries':'♈','Taurus':'♉','Gemini':'♊','Cancer':'♋','Leo':'♌','Virgo':'♍','Libra':'♎','Scorpio':'♏','Sagittarius':'♐','Capricorn':'♑','Aquarius':'♒','Pisces':'♓'}
            elements = {'Aries':'Fire','Taurus':'Earth','Gemini':'Air','Cancer':'Water','Leo':'Fire','Virgo':'Earth','Libra':'Air','Scorpio':'Water','Sagittarius':'Fire','Capricorn':'Earth','Aquarius':'Air','Pisces':'Water'}
            return {'cn': cn, 'en': en, 'element': elements.get(en,''), 'emoji': emojis.get(en,'')}
    return {'cn': '未知','en': 'Unknown','element': '','emoji':'?'}

def get_moon_sign(day_of_year, year):
    """月亮星座（简化计算，基于日期估算）"""
    moon_cycle = day_of_year % 28
    signs_order = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座','天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']
    signs_en = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    idx = (moon_cycle * 12) // 28
    return {'cn': signs_order[idx], 'en': signs_en[idx]}

def get_rising_sign(hour, day_of_year):
    """上升星座（简化估算，每2小时切换）"""
    signs_order = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座','天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']
    signs_en = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    idx = (hour // 2 + day_of_year) % 12
    return {'cn': signs_order[idx], 'en': signs_en[idx]}

SIGN_TRAITS = {
    'Aries': {'nature_zh':'勇敢直接，行动力强，天生的领袖','nature_en':'Brave and direct. A natural leader with unstoppable drive.',
              'career_zh':'适合军警、运动、创业、销售等竞争激烈的行业','career_en':'Military, sports, startups, sales — competitive fields.',
              'love_zh':'热情似火，爱情中主动追求。适合同样有活力的伴侣。','love_en':'Passionate pursuer. Thrives with an equally energetic partner.',
              'lucky_zh':'红色、火星能量、勇敢行动的日子','lucky_en':'Red, Mars energy, days for bold action.'},
    'Taurus': {'nature_zh':'稳重可靠，享受生活，固执但值得信赖','nature_en':'Steady and reliable. Enjoys finer things. Stubborn but loyal.',
               'career_zh':'适合金融、美食、农业、艺术、设计行业','career_en':'Finance, cuisine, agriculture, arts, design.',
               'love_zh':'重视安全感和忠诚，慢热但深情。需要能给你安定的伴侣。','love_en':'Values security and loyalty. Slow to warm but deeply devoted.',
               'lucky_zh':'绿色、金星能量、星期五','lucky_en':'Green, Venus energy, Fridays.'},
    'Gemini': {'nature_zh':'聪明灵活，好奇心强，善于沟通','nature_en':'Witty and versatile. Endlessly curious and communicative.',
               'career_zh':'适合传媒、写作、教育、销售、IT行业','career_en':'Media, writing, education, sales, tech.',
               'love_zh':'喜欢交流和精神共鸣，需要一个能跟上你话题切换的伴侣。','love_en':'Craves mental connection. Needs a partner who keeps up with your topics.',
               'lucky_zh':'黄色、水星能量、星期三','lucky_en':'Yellow, Mercury energy, Wednesdays.'},
    'Cancer': {'nature_zh':'情感丰富，顾家护短，直觉敏锐','nature_en':'Deeply emotional, protective of home, highly intuitive.',
               'career_zh':'适合医疗、教育、房地产、餐饮、咨询行业','career_en':'Healthcare, education, real estate, food, counseling.',
               'love_zh':'极度重视家庭和情感安全感，是最会照顾人的伴侣。','love_en':'Prioritizes family and emotional security. The most nurturing partner.',
               'lucky_zh':'银色、月亮能量、星期一','lucky_en':'Silver, Moon energy, Mondays.'},
    'Leo': {'nature_zh':'自信大度，有领导力，热爱表现','nature_en':'Confident and generous. Natural performer with magnetic charisma.',
            'career_zh':'适合演艺、管理、教育、奢侈品、公关行业','career_en':'Entertainment, management, education, luxury, PR.',
            'love_zh':'耀眼夺目，渴望被仰慕。需要一个欣赏你光芒的伴侣。','love_en':'Shines bright and craves admiration. Needs a partner who celebrates you.',
            'lucky_zh':'金色、太阳能量、星期日','lucky_en':'Gold, Sun energy, Sundays.'},
    'Virgo': {'nature_zh':'细心缜密，追求完美，服务精神','nature_en':'Meticulous and analytical. Perfectionist with a service mindset.',
              'career_zh':'适合医疗、科研、编辑、会计、IT行业','career_en':'Healthcare, research, editing, accounting, tech.',
              'love_zh':'用行动表达爱意。不擅甜言蜜语，但会默默为你做好一切。','love_en':'Shows love through actions. Not flowery with words but does everything for you.',
              'lucky_zh':'棕色、水星能量、细节关注','lucky_en':'Brown, Mercury energy, attention to detail.'},
    'Libra': {'nature_zh':'优雅和谐，追求平衡，有艺术品味','nature_en':'Graceful and diplomatic. Seeks balance and has refined taste.',
              'career_zh':'适合法律、设计、传媒、外交、美妆行业','career_en':'Law, design, media, diplomacy, beauty.',
              'love_zh':'追求浪漫的完美关系。讨厌冲突，喜欢平等的伴侣。','love_en':'Seeks romantic perfection. Hates conflict; likes equal partnership.',
              'lucky_zh':'粉色、金星能量、美丽的事物','lucky_en':'Pink, Venus energy, beautiful things.'},
    'Scorpio': {'nature_zh':'深沉神秘，意志力强，洞察人心','nature_en':'Deep and mysterious. Powerful will and penetrating insight.',
                'career_zh':'适合心理、刑侦、科研、金融、玄学行业','career_en':'Psychology, investigation, research, finance, metaphysics.',
                'love_zh':'爱得深也恨得深。需要灵魂层面的连接，不容背叛。','love_en':'Loves and hates deeply. Needs soul-level connection. Betrayal is unforgivable.',
                'lucky_zh':'黑色、冥王星能量、深沉的地方','lucky_en':'Black, Pluto energy, deep places.'},
    'Sagittarius': {'nature_zh':'乐观自由，热爱冒险，哲学思辨','nature_en':'Optimistic and free. Loves adventure and philosophical inquiry.',
                    'career_zh':'适合旅游、教育、出版、外贸、体育行业','career_en':'Travel, education, publishing, trade, sports.',
                    'love_zh':'热爱自由不喜束缚。需要一个陪你一起探索世界的伴侣。','love_en':'Loves freedom and hates constraints. Needs an adventure buddy partner.',
                    'lucky_zh':'紫色、木星能量、远行','lucky_en':'Purple, Jupiter energy, long journeys.'},
    'Capricorn': {'nature_zh':'脚踏实地，野心勃勃，坚韧不拔','nature_en':'Grounded and ambitious. Unwavering determination.',
                  'career_zh':'适合金融、工程、管理、建筑、政府行业','career_en':'Finance, engineering, management, construction, government.',
                  'love_zh':'慢热但持久。重视责任和承诺，是最可靠的伴侣。','love_en':'Slow to warm but lasting. Values duty and commitment. Most reliable partner.',
                  'lucky_zh':'深蓝、土星能量、时间沉淀','lucky_en':'Dark blue, Saturn energy, time-tested things.'},
    'Aquarius': {'nature_zh':'独立创新，人道主义，思想前卫','nature_en':'Independent and innovative. Humanitarian with progressive ideas.',
                 'career_zh':'适合科技、科研、公益、发明、占星行业','career_en':'Tech, research, charity, invention, astrology.',
                 'love_zh':'重视精神契合和自由。需要一个理解你独立性的伴侣。','love_en':'Values intellectual connection and freedom. Needs a partner who respects your independence.',
                 'lucky_zh':'电蓝色、天王星能量、新技术','lucky_en':'Electric blue, Uranus energy, new technology.'},
    'Pisces': {'nature_zh':'浪漫梦幻，有同理心，艺术天赋','nature_en':'Romantic and dreamy. Deeply empathetic with artistic gifts.',
               'career_zh':'适合艺术、音乐、心理咨询、医疗、慈善行业','career_en':'Arts, music, counseling, healthcare, charity.',
               'love_zh':'付出型恋人，把伴侣理想化。注意不要失去自我。','love_en':'Generous lover who idealizes partners. Be careful not to lose yourself.',
               'lucky_zh':'海蓝色、海王星能量、水边','lucky_en':'Sea blue, Neptune energy, near water.'},
}

def build_full_chart(year, month, day, hour, level='free'):
    """构建完整星盘"""
    try:
        dobj = datetime.date(year, month, day)
    except:
        return {'error': 'Invalid date'}
    day_of_year = dobj.timetuple().tm_yday
    sun = get_sun_sign(month, day)
    moon = get_moon_sign(day_of_year, year)
    rising = get_rising_sign(hour, day_of_year)

    result = {
        'sun': sun,
        'moon': moon,
        'rising': rising,
        'day_of_year': day_of_year,
    }

    traits = SIGN_TRAITS.get(sun['en'], {})
    result['traits'] = {k: traits.get(k, '') for k in ['nature_zh','nature_en','career_zh','career_en','love_zh','love_en','lucky_zh','lucky_en']}

    if level in ('basic', 'full'):
        # Detailed report
        result['report_zh'] = f"太阳{sun['cn']}、月亮{moon['cn']}、上升{rising['cn']}——{traits.get('nature_zh','')}"
        result['report_en'] = f"Sun {sun['en']}, Moon {moon['en']}, Rising {rising['en']} — {traits.get('nature_en','')}"

    if level == 'full':
        result['career_detail_zh'] = traits.get('career_zh','')
        result['career_detail_en'] = traits.get('career_en','')
        result['love_detail_zh'] = traits.get('love_zh','')
        result['love_detail_en'] = traits.get('love_en','')
        result['lucky_detail_zh'] = traits.get('lucky_zh','')
        result['lucky_detail_en'] = traits.get('lucky_en','')

    return result


def get_daily_horoscope(sun_en, date_str):
    """每日运势（基于日期+星座哈希的伪随机）"""
    seed_str = sun_en + date_str
    seed = sum(ord(c) for c in seed_str)
    horoscopes_zh = [
        '今天适合果断行动。相信直觉，推进那个你一直拖延的事情。',
        '放慢脚步的一天。静下心来，你会发现身边的美好细节。',
        '沟通运势极佳。主动联系你想联系的人，会有意外惊喜。',
        '直觉力超强。注意你的梦境和第六感，它们会给你重要指引。',
        '今天你是焦点。大方分享想法，大家都在认真听你说。',
        '细节运势强。适合整理计划、收拾空间、清算旧账。',
        '平衡是关键。如果最近太忙，今天就给自己放个小假。',
        '深层变化在酝酿。放下不再属于你的，拥抱新的可能。',
        '冒险精神在召唤！走出舒适圈，新奇体验在等你。',
        '努力终有回报。保持专注和自律，成果就在不远处。',
        '你独特的视角正是大家需要的。大胆分享那个不一样的想法。',
        '创意能量爆棚。投入到艺术、音乐或任何自我表达中去。',
        '今天遇见的人可能是贵人。保持开放心态，主动打招呼。',
        '财运不错。可能会收到一笔意外之喜或有新的收入机会。',
    ]
    horoscopes_en = [
        'Bold action is favored today. Trust your instincts and move on that thing you\'ve been postponing.',
        'A day for slowing down. Quiet your mind and notice the small beauties around you.',
        'Communication flows easily. Reach out to someone — a pleasant surprise awaits.',
        'Intuition is heightened. Pay attention to dreams and gut feelings today.',
        'The spotlight is on you. Share your ideas confidently — people are listening.',
        'Detail-oriented energy. Perfect for organizing, decluttering, and tying loose ends.',
        'Balance is everything. If you've been overworking, take a break today.',
        'Deep transformation is brewing. Release what no longer serves you.',
        'Adventure calls! Step outside your comfort zone — new experiences await.',
        'Hard work pays off. Stay disciplined and focused — results are near.',
        'Your unique perspective is needed. Share that unconventional idea boldly.',
        'Creative energy surges. Dive into art, music, or any form of self-expression.',
        'Someone you meet today could be pivotal. Stay open and say hello first.',
        'Financial luck is strong. Unexpected income or new earning opportunities may appear.',
    ]
    idx = seed % len(horoscopes_zh)
    return {
        'date': date_str,
        'horoscope_zh': horoscopes_zh[idx],
        'horoscope_en': horoscopes_en[idx],
        'lucky_number': (seed % 9) + 1,
        'lucky_color_zh': ['红','黄','蓝','绿','紫','粉','白','黑','金'][idx % 9],
        'lucky_color_en': ['Red','Yellow','Blue','Green','Purple','Pink','White','Black','Gold'][idx % 9],
    }


if __name__ == '__main__':
    import json
    chart = build_full_chart(1990, 5, 20, 8, 'full')
    print(json.dumps(chart, ensure_ascii=False, indent=2))
    daily = get_daily_horoscope('Taurus', '2026-06-19')
    print(json.dumps(daily, ensure_ascii=False, indent=2))
