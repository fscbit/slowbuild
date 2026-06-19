"""
姓名学引擎 — 笔画五行分析 + 三才五格
"""
import hashlib

# Complete stroke dictionary (extended)
STROKES = {
    '一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
    '口':3,'土':3,'大':3,'女':3,'子':3,'小':3,'山':3,'川':3,'工':3,'己':3,'巾':3,'干':3,'弓':3,'才':3,
    '丑':4,'不':4,'中':4,'丹':4,'之':4,'云':4,'井':4,'仁':4,'公':4,'化':4,'天':4,'太':4,'孔':4,'少':4,
    '心':4,'戈':4,'手':4,'支':4,'文':4,'斗':4,'方':4,'日':4,'月':4,'木':4,'止':4,'比':4,'毛':4,'氏':4,'水':4,'火':4,'父':4,'牛':4,'王':4,
    '世':5,'丘':5,'主':5,'以':5,'兄':5,'冬':5,'出':5,'加':5,'可':5,'右':5,'外':5,'巨':5,'巧':5,'市':5,'平':5,'弘':5,'本':5,'正':5,'母':5,'民':5,'永':5,'生':5,'用':5,'由':5,'甲':5,'申':5,'白':5,'目':5,'石':5,'立':5,
    '丞':6,'交':6,'仰':6,'任':6,'光':6,'先':6,'全':6,'共':6,'列':6,'刑':6,'印':6,'吉':6,'同':6,'名':6,'回':6,'因':6,'地':6,'多':6,'好':6,'如':6,'宇':6,'守':6,'安':6,'年':6,'州':6,'江':6,'池':6,'百':6,'竹':6,'米':6,'臣':6,'自':6,'至':6,'行':6,'西':6,
    '亨':7,'伯':7,'余':7,'兵':7,'冷':7,'利':7,'君':7,'吟':7,'呈':7,'吾':7,'坊':7,'均':7,'坐':7,'壮':7,'妙':7,'孝':7,'宏':7,'局':7,'序':7,'廷':7,'弟':7,'志':7,'成':7,'材':7,'李':7,'杜':7,'束':7,'步':7,'每':7,'男':7,'秀':7,'良':7,'见':7,'角':7,'言':7,'谷':7,'豆':7,'赤':7,'走':7,'足':7,'身':7,'车':7,'辛':7,'辰':7,'邦':7,'里':7,'防':7,
    '并':8,'亚':8,'京':8,'佳':8,'依':8,'卓':8,'周':8,'和':8,'固':8,'坤':8,'坦':8,'奇':8,'妹':8,'始':8,'孟':8,'季':8,'宗':8,'官':8,'定':8,'宛':8,'宜':8,'尚':8,'居':8,'岳':8,'幸':8,'府':8,'政':8,'昌':8,'明':8,'易':8,'昂':8,'东':8,'林':8,'松':8,'欣':8,'武':8,'河':8,'炎':8,'牧':8,'直':8,'秉':8,'花':8,'芳':8,'虎':8,'金':8,'长':8,'雨':8,'青':8,'非':8,
    '信':9,'冠':9,'勇':9,'厚':9,'品':9,'哉':9,'姿':9,'宣':9,'客':9,'帝':9,'帅':9,'度':9,'建':9,'彦':9,'待':9,'思':9,'恒':9,'恢':9,'星':9,'春':9,'昭':9,'柏':9,'柳':9,'泉':9,'洋':9,'洪':9,'洲':9,'炫':9,'炯':9,'珊':9,'玲':9,'皇':9,'科':9,'秋':9,'纪':9,'红':9,'美':9,'羿':9,'胡':9,'范':9,'英':9,'衍':9,'虹':9,'军':9,'革':9,'音':9,'风':9,'飞':9,
    '刚':10,'修':10,'展':10,'峻':10,'峰':10,'庭':10,'恩':10,'振':10,'效':10,'晋':10,'书':10,'朗':10,'桂':10,'桃':10,'桐':10,'桑':10,'桓':10,'格':10,'殊':10,'殷':10,'流':10,'海':10,'烈':10,'特':10,'真':10,'秦':10,'纹':10,'纯':10,'素':10,'育':10,'航':10,'虔':10,'袁':10,'记':10,'训':10,'财':10,'起':10,'轩':10,'钊':10,'哲':10,'城':10,'夏':10,'孙':10,'家':10,'容':10,'师':10,'悟':10,'拳':10,'敏':10,'斌':10,'旅':10,'时':10,'晖':10,'效':10,'航':10,'芬':10,'若':10,'茂':10,'虔':10,'袁':10,
    '泰':11,'浩':11,'海':11,'浪':11,'涌':11,'涛':11,'涵':11,'淑':11,'清':11,'淳':11,'深':11,'淋':11,'渠':11,'焕':11,'理':11,'甜':11,'祥':11,'章':11,'笙':11,'绍':11,'统':11,'翌':11,'翎':11,'聆':11,'聪':11,'胜':11,'舒':11,'菁':11,'菊':11,'虚':11,'彪':11,'诚':11,'许':11,'翊':11,'望':11,'梁':11,'梓':11,'烽':11,'聆':11,'硕':11,'紫':11,'绅':11,'维':11,'绵':11,'绪':11,'习':11,'翌':11,'耕':11,'舜':11,'芊':11,'裕':11,'通':11,'连':11,'郭':11,'钧':11,'陈':11,'雪':11,'健':11,'伟':11,
    '崎':12,'凯':12,'博':12,'善':12,'喜':12,'尧':12,'婷':12,'媚':12,'富':12,'寒':12,'尊':12,'强':12,'复':12,'惠':12,'扬':12,'敦':12,'斐':12,'景':12,'智':12,'曾':12,'朝':12,'栋':12,'森':12,'植':12,'钦':12,'款':12,'游':12,'湛':12,'湖':12,'温':12,'然':12,'琳':12,'琢':12,'琼':12,'琴':12,'登':12,'发':12,'皓':12,'盛':12,'砚':12,'禄':12,'程':12,'策':12,'翔':12,'舜':12,'萍':12,'超':12,'迪':12,'雄':12,'雅':12,'集':12,'顺':12,
    '廉':13,'微':13,'意':13,'慈':13,'新':13,'暄':13,'晖':13,'暖':13,'杨':13,'枫':13,'楷':13,'愉':13,'滔':13,'溪':13,'溢':13,'溶':13,'源':13,'焕':13,'煌':13,'煜':13,'照':13,'瑞':13,'睛':13,'睦':13,'祺':13,'禄':13,'经':13,'群':13,'义':13,'圣':13,'肃':13,'与':13,'萱':13,'裘':13,'诗':13,'诚':13,'焕':13,'煜':13,
    '碧':14,'福':14,'祯':14,'种':14,'端':14,'维':14,'综':14,'绮':14,'绸':14,'翠':14,'翡':14,'肇':14,'闻':14,'聪':14,'聚':14,'豪':14,'诚':14,'宾':14,'齐':14,
    '仪':15,'亿':15,'俭':15,'儒':15,'剑':15,'厉':15,'增':15,'宽':15,'广':15,'德':15,'慧':15,'慕':15,'庆':15,'摩':15,'辉':15,'娴':15,'娇':15,'乐':15,'毅':15,'洁':15,'澄':15,'潜':15,'润':15,'澎':15,'辉':15,'颖':15,'纬':15,'缘':15,'谊':15,'豫':15,'贤':15,'质':15,'辉':15,'伦':15,
    '凝':16,'学':16,'宇':16,'宪':16,'寰':16,'导':16,'龙':16,'整':16,'晓':16,'树':16,'桦':16,'桥':16,'机':16,'历':16,'燕':16,'默':16,'龙':16,
    '孺':17,'岭':17,'岳':17,'应':17,'恳':17,'矫':17,'禅':17,'聪':17,'声':17,'举':17,'励':17,'优':17,'临':17,'阳':17,'隆':17,'蔓':17,'谦':17,'霜':17,'霞':17,'韩':17,'鸿':17,'鹤':17,
}

WUXING_MAP = {1:'木',2:'木',3:'火',4:'火',5:'土',6:'土',7:'金',8:'金',9:'水',10:'水'}
GOOD_BAD = {
    1:{'zh':'大吉','en':'Great Fortune','dz':'独立权威，万事开头。','de':'Independent authority. Beginning of all things.'},
    3:{'zh':'大吉','en':'Great Fortune','dz':'天地人和，万事顺遂。','de':'Heaven and Earth in harmony.'},
    5:{'zh':'大吉','en':'Great Fortune','dz':'五行俱全，福禄长寿。','de':'Five elements complete. Blessings and longevity.'},
    6:{'zh':'大吉','en':'Great Fortune','dz':'天德地祥，福泽深厚。','de':'Heavenly virtue, earthly grace.'},
    7:{'zh':'大吉','en':'Great Fortune','dz':'精悍严谨，天赋之力。','de':'Rigorous talent, natural gifts.'},
    8:{'zh':'大吉','en':'Great Fortune','dz':'坚毅果断，勤勉发展。','de':'Perseverance leads to success.'},
    11:{'zh':'大吉','en':'Great Fortune','dz':'万象更新，富贵繁荣。','de':'All things renewed. Prosperity flows.'},
    13:{'zh':'大吉','en':'Great Fortune','dz':'智略超群，博学多能。','de':'Exceptional wisdom, multi-talented.'},
    15:{'zh':'大吉','en':'Great Fortune','dz':'福寿圆满，万事如意。','de':'Complete blessing. Everything prospers.'},
    16:{'zh':'大吉','en':'Great Fortune','dz':'贵人得助，万事顺利。','de':'Noble helpers. All endeavors smooth.'},
    17:{'zh':'大吉','en':'Great Fortune','dz':'刚柔兼备，功成名就。','de':'Breakthrough to fame and achievement.'},
    18:{'zh':'大吉','en':'Great Fortune','dz':'内外有助，名利双收。','de':'Inner and outer support. Name and wealth.'},
    21:{'zh':'大吉','en':'Great Fortune','dz':'明月中天，领袖之数。','de':'Bright moon in the sky. Leader number.'},
    23:{'zh':'大吉','en':'Great Fortune','dz':'旭日东升，权势旺盛。','de':'Rising sun. Power flourishes.'},
    24:{'zh':'大吉','en':'Great Fortune','dz':'白手成家，财源广进。','de':'Self-made fortune. Wealth flows in.'},
    25:{'zh':'大吉','en':'Great Fortune','dz':'资性英敏，奇才之数。','de':'Brilliant and decisive. Exceptional talent.'},
    29:{'zh':'大吉','en':'Great Fortune','dz':'智谋优秀，成就大业。','de':'Shrewd and resourceful. Great achievements.'},
    31:{'zh':'大吉','en':'Great Fortune','dz':'智勇得志，统领众人。','de':'Wisdom and courage rewarded. Leadership.'},
    32:{'zh':'大吉','en':'Great Fortune','dz':'如龙得水，贵人得助。','de':'Dragon in water. Noble assistance.'},
    33:{'zh':'大吉','en':'Great Fortune','dz':'鸾凤相会，名闻天下。','de':'Phoenix meets. World-renowned.'},
    35:{'zh':'大吉','en':'Great Fortune','dz':'温和平静，优雅发展。','de':'Gentle and elegant growth.'},
    37:{'zh':'大吉','en':'Great Fortune','dz':'忠肝义胆，德望并臻。','de':'Loyal and righteous. Virtue ascends.'},
}

def get_stroke(ch):
    if ch in STROKES:
        return STROKES[ch]
    code = ord(ch)
    if 0x4E00 <= code <= 0x9FFF:
        return 10  # Default CJK
    return 1

def count_strokes(name):
    return sum(get_stroke(c) for c in name)

def get_wuxing(num):
    return WUXING_MAP.get((num - 1) % 10 + 1, '?')

def analyze_name(family, given, level='free'):
    if not family or not given:
        return {'error': 'Need surname and given name'}

    f_count = count_strokes(family)
    g_count = count_strokes(given)
    total = f_count + g_count

    # 三才五格
    ten = (f_count + 1) % 10 or 10  # 天格
    person = g_count % 10 or 10     # 人格
    earth = g_count % 10 or 10      # 地格
    outer = (total - f_count) % 10 or 10  # 外格

    gb = GOOD_BAD.get(total, {})
    if not gb:
        gb = {'zh':'中平','en':'Moderate','dz':'吉凶参半','de':'Mixed fortune'}

    result = {
        'name': family + given,
        'family_count': f_count,
        'given_count': g_count,
        'total': total,
        'judgment_zh': gb['zh'],
        'judgment_en': gb['en'],
        'desc_zh': gb['dz'],
        'desc_en': gb['de'],
        'grids': {
            'ten': ten, 'ten_el': get_wuxing(ten),
            'person': person, 'person_el': get_wuxing(person),
            'earth': earth, 'earth_el': get_wuxing(earth),
            'outer': outer, 'outer_el': get_wuxing(outer),
        }
    }

    if level in ('basic', 'full'):
        # Name meaning per character
        result['name_analysis_zh'] = f'天格{ten}（{get_wuxing(ten)}）：祖上福荫，早年起运。人格{person}（{get_wuxing(person)}）：你的核心，决定一生运势。地格{earth}（{get_wuxing(earth)}）：中年运势，家庭事业。外格{outer}（{get_wuxing(outer)}）：对外关系，社交运。总格{total}：一生总体运势——{gb["zh"]}。'
        result['name_analysis_en'] = f'Heaven Grid {ten} ({get_wuxing(ten)}): Ancestral blessing, early luck. Man Grid {person} ({get_wuxing(person)}): Your core, determines life path. Earth Grid {earth} ({get_wuxing(earth)}): Mid-life, family & career. Outer Grid {outer} ({get_wuxing(outer)}): External relations, social luck. Total {total}: Overall life fortune — {gb["en"]}.'

    if level == 'full':
        result['advice_zh'] = generate_name_advice(total, ten, person, earth, 'zh')
        result['advice_en'] = generate_name_advice(total, ten, person, earth, 'en')

    return result


def generate_name_advice(total, ten, person, earth, lang):
    el_total = get_wuxing(total)
    el_person = get_wuxing(person)
    if lang == 'zh':
        return f'你的姓名总格为{total}（五行属{el_total}），人格{person}属{el_person}。姓名数理分析提示：名字不仅仅是代号，它承载着长辈的期望和自身的能量场。保持对自己名字的珍视和自信，好运会随之而来。'
    return f'Your name total is {total} (element: {el_total}), Man Grid {person} (element: {el_person}). Name numerology suggests: a name is more than a label — it carries the expectations of your elders and your own energy field. Cherish your name and be confident in it, and good fortune will follow.'


if __name__ == '__main__':
    import json
    r = analyze_name('方', '世聪', 'full')
    print(json.dumps(r, ensure_ascii=False, indent=2))
