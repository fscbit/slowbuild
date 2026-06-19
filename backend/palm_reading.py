"""
手相解读引擎 — 4条主要掌纹详解
"""
import hashlib

PALM_DATA = {
    'life': {
        'name_zh': '生命线','name_en': 'Life Line',
        'variants': {
            0: {'zh':'生命线长而深，弧度大——体质强健，精力充沛，生命力极其旺盛。天生好体质，不易生病。',
                'en':'Long, deep life line with wide arc — robust constitution and abundant vitality. Naturally strong health.'},
            1: {'zh':'生命线清晰但较短——身体素质不错但需注意保养。年轻时冲劲大，中年后需要更注意休息。',
                'en':'Clear but shorter life line — decent health but needs maintenance. High energy in youth, need more rest after mid-life.'},
            2: {'zh':'生命线有岛纹或断开——在某一年龄段可能经历重大生活变化。注意规律作息。',
                'en':'Island or break in life line — significant life change at certain age. Maintain regular routines.'},
        }
    },
    'head': {
        'name_zh': '智慧线','name_en': 'Wisdom Line',
        'variants': {
            0: {'zh':'智慧线长而深刻，笔直延伸——思维敏捷，逻辑清晰，善于分析和长远规划。天生的战略家。',
                'en':'Long, deep, straight head line — sharp mind, clear logic, excellent at analysis and long-term planning. Natural strategist.'},
            1: {'zh':'智慧线较短但粗——实践派，行动先于思考。虽不擅长理论但动手能力极强。',
                'en':'Shorter but thick head line — practical doer, acts before thinking. Not theoretical but extremely hands-on.'},
            2: {'zh':'智慧线有多个分叉——多方面才能，兴趣广泛但可能犹豫不决。你适合多元化的职业道路。',
                'en':'Multiple forks in head line — multi-talented with wide interests but may be indecisive. Suited for diverse career paths.'},
        }
    },
    'heart': {
        'name_zh': '感情线','name_en': 'Heart Line',
        'variants': {
            0: {'zh':'感情线长而深，延伸到食指下方——感情丰富深刻，重视亲情友情爱情。一旦投入就会全力以赴。',
                'en':'Long, deep heart line reaching under index finger — emotionally rich and deep. Once committed, you go all in.'},
            1: {'zh':'感情线较短，止于中指下方——表达感情的方式内敛稳重。不轻易袒露心声，但一旦认定就非常长情。',
                'en':'Shorter heart line ending under middle finger — reserved in expressing feelings. Slow to open up but deeply loyal.'},
            2: {'zh':'感情线呈链状或有岛纹——感情经历丰富，可能有几段重要的情感关系。每一段都让你成长。',
                'en':'Chained or islanded heart line — rich emotional history with several significant relationships. Each one helped you grow.'},
        }
    },
    'fate': {
        'name_zh': '命运线','name_en': 'Fate Line',
        'variants': {
            0: {'zh':'命运线长而清晰，从手腕直贯中指——目标明确，事业有成，人生轨迹清晰有力。注定成就一番事业。',
                'en':'Long, clear fate line from wrist to middle finger — clear goals, career success, defined life path. Destined for achievement.'},
            1: {'zh':'命运线较模糊或断断续续——人生自由度高，不拘泥于固定轨道。你更适合多元化的生活方式。',
                'en':'Faint or intermittent fate line — high life freedom, not bound to fixed tracks. Better suited for diverse lifestyles.'},
            2: {'zh':'命运线在中年后加深——大器晚成型。年轻时各种尝试，中年以后事业起飞，后来居上。',
                'en':'Fate line deepens after mid-life — late bloomer. Various trials in youth, career takes off mid-life, catching up strong.'},
        }
    }
}

def get_palm_reading(line_types, hand='right', gender='male', level='free'):
    """Generate palm reading for one or more lines"""
    readings = []
    for lt in line_types:
        if lt not in PALM_DATA:
            continue
        data = PALM_DATA[lt]
        # Deterministic pseudo-random based on hand+gender+line
        seed_val = sum(ord(c) for c in hand + gender + lt) % 3
        variant = data['variants'].get(seed_val, data['variants'][0])
        readings.append({
            'line': lt,
            'name_zh': data['name_zh'],
            'name_en': data['name_en'],
            'reading_zh': variant['zh'],
            'reading_en': variant['en'],
        })
    return {'readings': readings}


if __name__ == '__main__':
    import json
    r = get_palm_reading(['life','head','heart','fate'], 'right', 'male', 'full')
    print(json.dumps(r, ensure_ascii=False, indent=2))
