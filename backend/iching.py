"""
周易六爻引擎 — 64卦详解 + 变爻解读
"""
import random

HEXAGRAMS = {
    '111111': {'name':'乾为天','en':'Qian / The Creative','trigram':'☰☰',
        'desc_zh':'元亨利贞。伟大的创造力正在流动。现在是采取大胆行动的最佳时机。天空是你的极限。',
        'desc_en':'The Creative. Supreme success. Creative power flows freely. The time for bold action is now.',
        'career_zh':'领导力和创新力极强。适合开启新项目、创业或争取晋升。',
        'career_en':'Leadership and innovation at their peak. Start new projects or seek promotion.',
        'love_zh':'阳刚之气充沛。主动表达爱意，你的真诚和力量会打动对方。',
        'love_en':'Yang energy abundant. Express love boldly — your sincerity and strength will move them.'},
    '000000': {'name':'坤为地','en':'Kun / The Receptive','trigram':'☷☷',
        'desc_zh':'元亨，利牝马之贞。以柔克刚的智慧。现在不是冲锋的时候，而是包容和等待。',
        'desc_en':'The Receptive. Supreme success through yielding. Not a time to charge ahead but to embrace and wait.',
        'career_zh':'适合辅助他人、做好后勤和执行工作。稳扎稳打会有意外收获。',
        'career_en':'Support others, handle logistics and execution. Steady work brings unexpected rewards.',
        'love_zh':'温柔而坚定。用包容去化解矛盾，你的耐心会赢得最终胜利。',
        'love_en':'Gentle yet firm. Resolve conflicts with acceptance — your patience wins in the end.'},
    '010001': {'name':'水雷屯','en':'Zhun / Difficulty at Beginning','trigram':'☵☳',
        'desc_zh':'万事开头难。新事物诞生时的阵痛。需要耐心和坚持，不要轻易放弃。',
        'desc_en':'Difficulty at the beginning. Birth pains of something new. Patience and persistence needed.',
        'career_zh':'创业初期或新项目的困难期。坚持住，乌云会散开。',
        'career_en':'Early stage struggles. Hold on — the clouds will part.',
        'love_zh':'新的感情可能遇到波折。给对方和自己一些时间，不要急着下结论。',
        'love_en':'New romance may face bumps. Give it time — do not rush to conclusions.'},
    '100010': {'name':'山水蒙','en':'Meng / Youthful Folly','trigram':'☶☵',
        'desc_zh':'蒙昧初开，需要学习。虚心求教是最好的策略。不要假装自己什么都懂。',
        'desc_en':'Youthful inexperience. Best strategy: seek guidance humbly. Do not pretend to know everything.',
        'career_zh':'学习的黄金期。报课程、找导师、提升技能。基础打好了路才走得远。',
        'career_en':'Golden period for learning. Take courses, find mentors, build skills. Solid foundation enables long journeys.',
        'love_zh':'你或对方可能还不太成熟。不要急着承诺，先了解自己和对方真正需要什么。',
        'love_en':'You or the other may still be maturing. Do not rush commitment — first learn what you both truly need.'},
    '010111': {'name':'水天需','en':'Xu / Waiting','trigram':'☵☰',
        'desc_zh':'耐心等待，时机未到。就像种子在土壤下等待春雨。该来的自然回来。',
        'desc_en':'Wait patiently — the time is not yet ripe. Like a seed waiting for spring rain. What is meant to come will come.',
        'career_zh':'暂时不要有大动作。积蓄力量、做好准备，机会很快就会来。',
        'career_en':'No big moves for now. Gather strength and prepare — opportunity is coming soon.',
        'love_zh':'感情急不得。你在等待的那个人或那个时机，正在来的路上。',
        'love_en':'Love cannot be rushed. The person or moment you are waiting for is on its way.'},
    '111010': {'name':'天水讼','en':'Song / Conflict','trigram':'☰☵',
        'desc_zh':'争讼和冲突。退一步海阔天空。寻求和解比争个输赢更明智。',
        'desc_en':'Conflict and disputes. Step back — the sea and sky open wide. Seeking peace is wiser than winning.',
        'career_zh':'职场可能有纷争或官司风险。避免站队，保持中立。',
        'career_en':'Workplace disputes or legal risks possible. Avoid taking sides, stay neutral.',
        'love_zh':'争吵解决不了问题。冷静下来再谈，你会发现大部分矛盾都是误会。',
        'love_en':'Arguments solve nothing. Cool down before talking — most conflicts are misunderstandings.'},
    '000010': {'name':'地水师','en':'Shi / The Army','trigram':'☷☵',
        'desc_zh':'团队行动，需要纪律和组织。单打独斗不如协同作战。',
        'desc_en':'Collective action needs discipline and organization. Working alone is less effective than coordinated effort.',
        'career_zh':'适合带领团队或加入一个有组织的力量。群策群力才能成事。',
        'career_en':'Lead a team or join an organized force. Collective wisdom achieves what individuals cannot.',
        'love_zh':'感情需要共同面对外部挑战。你们是战友，不是对手。',
        'love_en':'Face external challenges together. You are allies, not opponents.'},
}

def get_reading(lines, level='free'):
    """Generate hexagram reading from 6 lines (0=broken, 1=solid)"""
    key = ''.join(str(l) for l in lines)
    hex = HEXAGRAMS.get(key)
    if not hex:
        # Try reversed
        key_rev = ''.join(str(l) for l in reversed(lines))
        hex = HEXAGRAMS.get(key_rev)
    if not hex:
        hex = HEXAGRAMS['111111']  # Default to Qian

    result = {
        'hex_key': key,
        'name': hex['name'],
        'name_en': hex['en'],
        'trigram': hex['trigram'],
        'desc_zh': hex['desc_zh'],
        'desc_en': hex['desc_en'],
        'lines_display': ''.join('⚊ ' if l == '1' else '⚋ ' for l in reversed(lines)),
    }

    if level in ('basic', 'full'):
        result['career_zh'] = hex.get('career_zh', '')
        result['career_en'] = hex.get('career_en', '')
        result['love_zh'] = hex.get('love_zh', '')
        result['love_en'] = hex.get('love_en', '')

    if level == 'full':
        result['advice_zh'] = hex.get('advice_zh', hex.get('desc_zh', ''))
        result['advice_en'] = hex.get('advice_en', hex.get('desc_en', ''))

    return result


if __name__ == '__main__':
    import json
    r = get_reading([1,1,1,1,1,1], 'full')
    print(json.dumps(r, ensure_ascii=False, indent=2))
