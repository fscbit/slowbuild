"""
塔罗占卜引擎 — 78张牌详解 + 牌阵解读
"""
import random, hashlib

# Major Arcana (22) + Minor Arcana (56)
MAJOR_ARCANA = {
    0: {'name':'The Fool','cn':'愚者','en':'New beginnings, spontaneity, a leap of faith. The universe is calling you to trust the journey.',
        'career_zh':'新的职业方向正在召唤。不要害怕冒险——有时候最大的风险就是不冒任何险。',
        'career_en':'A new career path is calling. Do not fear the leap — sometimes the biggest risk is taking no risk at all.',
        'love_zh':'一段全新的感情可能即将开始，保持开放的心态。单身者会遇到意想不到的人。',
        'love_en':'A fresh romance may be starting. Stay open-minded. Singles may meet someone unexpected.',
        'advice_zh':'相信宇宙，迈出那一步。包袱越轻，走得越远。',
        'advice_en':'Trust the universe and take that step. The lighter you travel, the further you go.'},
    1: {'name':'The Magician','cn':'魔术师','en':'You have all the tools you need. Manifestation, power, and skillful action are at your fingertips.',
        'career_zh':'你的技能和资源已经齐备。现在是展示自己、拿下那个项目的最佳时机。',
        'career_en':'Your skills and resources are ready. Now is the time to showcase yourself and land that project.',
        'love_zh':'自信是你最大的魅力。主动表达，你的真心会被看见。',
        'love_en':'Confidence is your greatest charm. Express yourself — your sincerity will be seen.',
        'advice_zh':'你手中已有一切。专注、行动、创造你想要的结果。',
        'advice_en':'You already have everything you need. Focus, act, and create the outcome you want.'},
    2: {'name':'The High Priestess','cn':'女祭司','en':'Trust your intuition. The answers lie within, not in the noise outside. Silence and reflection are your allies.',
        'career_zh':'不要急着做决定。多观察、多倾听，答案会自然浮现。适合研究和幕后工作。',
        'career_en':'Do not rush decisions. Observe and listen — answers will surface. Good for research and behind-the-scenes work.',
        'love_zh':'跟随直觉，而非逻辑。那个人是否值得，你的心早就知道答案。',
        'love_en':'Follow intuition, not logic. Your heart already knows if that person is right for you.',
        'advice_zh':'静下来，听内心的声音。不是所有答案都需要用脑子去算。',
        'advice_en':'Be still and listen within. Not every answer needs to be calculated by the mind.'},
    3: {'name':'The Empress','cn':'女皇','en':'Abundance, creativity, and nurturing energy surround you. A time of growth and harvest.',
        'career_zh':'创意和丰收的时期。你种下的种子即将开花结果。适合启动创意项目。',
        'career_en':'A period of creativity and harvest. Seeds you planted are about to bloom. Start creative projects.',
        'love_zh':'温暖而丰盛的感情。如果你已经有伴，关系会更加深厚甜蜜。',
        'love_en':'Warm and abundant love. If partnered, the relationship deepens sweetly.',
        'advice_zh':'享受生活，犒赏自己。你有资格享受此刻的丰盛。',
        'advice_en':'Enjoy life and treat yourself. You deserve this abundance.'},
    4: {'name':'The Emperor','cn':'皇帝','en':'Structure, authority, and disciplined leadership. Take command of your situation with confidence.',
        'career_zh':'建立秩序和规划。你可能会承担领导角色，或需要制定长远计划。',
        'career_en':'Build order and plans. You may take a leadership role or need a long-term strategy.',
        'love_zh':'稳定和承诺是你现在需要的。不要玩暧昧，明确表达你的底线。',
        'love_en':'Stability and commitment are what you need now. Be clear about your boundaries.',
        'advice_zh':'制定规则，掌控局面。你有能力让混乱变得有序。',
        'advice_en':'Set the rules and take control. You have the power to bring order to chaos.'},
    5: {'name':'The Hierophant','cn':'教皇','en':'Tradition, wisdom, and spiritual guidance. Seek knowledge from trusted mentors or institutions.',
        'career_zh':'回归传统方法或向资深前辈请教。体制内的道路可能更适合现在的你。',
        'career_en':'Return to traditional methods or consult senior mentors. Institutional paths may suit you now.',
        'love_zh':'一段符合传统价值观的感情。可能会考虑婚姻或正式的承诺。',
        'love_en':'A relationship aligned with traditional values. Marriage or formal commitment may be considered.',
        'advice_zh':'不要排斥传统智慧。有时老办法恰恰是最好的办法。',
        'advice_en':'Do not dismiss traditional wisdom. Sometimes the old ways are exactly the best ways.'},
    6: {'name':'The Lovers','cn':'恋人','en':'Choice, harmony, and deep connection. A significant decision of the heart awaits you.',
        'career_zh':'面临重要职业选择。遵循你的价值观和热情，而不是纯粹的利益。',
        'career_en':'A significant career choice awaits. Follow your values and passion, not just profit.',
        'love_zh':'爱情的重大抉择。可能是一段深刻的恋情，或是现有关系的升华。',
        'love_en':'A major romantic decision. A deep love or elevation of an existing relationship.',
        'advice_zh':'用心选择，而非脑子。真正的爱经得起任何考验。',
        'advice_en':'Choose with your heart, not just your head. True love withstands any test.'},
    7: {'name':'The Chariot','cn':'战车','en':'Victory through determination and willpower. Push forward — obstacles crumble before your resolve.',
        'career_zh':'全力以赴！你会克服障碍、赢得胜利。竞争激烈的环境反而是你的舞台。',
        'career_en':'Go all out! You will overcome obstacles and win. Competitive environments are your stage.',
        'love_zh':'主动出击。如果你喜欢某人，大胆追求。已有伴侣的话，共同面对挑战能增进感情。',
        'love_en':'Take the initiative. If you like someone, pursue boldly. Face challenges together to strengthen bonds.',
        'advice_zh':'咬紧牙关冲过去。胜利已经在前面等着你了。',
        'advice_en':'Grit your teeth and charge through. Victory already awaits you ahead.'},
    8: {'name':'Strength','cn':'力量','en':'Inner strength, courage, and patience. True power is gentle — tame the beast with compassion.',
        'career_zh':'用耐心和毅力而不是蛮力取胜。你可能需要驯服某个棘手的问题或人。',
        'career_en':'Win with patience and persistence, not brute force. You may need to tame a tricky problem or person.',
        'love_zh':'用温柔化解矛盾。耐心和理解比争辩更能赢得对方的心。',
        'love_en':'Resolve conflicts with gentleness. Patience and understanding win hearts more than arguments.',
        'advice_zh':'真正的力量是温柔。你可以既强大又柔软。',
        'advice_en':'True strength is gentle. You can be both powerful and soft.'},
    9: {'name':'The Hermit','cn':'隐士','en':'Introspection, solitude, and inner guidance. Step back from the noise to find your truth.',
        'career_zh':'暂时退一步，反思你的职业方向。独处和深入研究会有重大收获。',
        'career_en':'Step back temporarily to reflect on your career direction. Solitude and deep research yield great insights.',
        'love_zh':'给自己一些空间。不是每段感情都需要时刻黏在一起。独处让你们更珍惜彼此。',
        'love_en':'Give yourself some space. Not every relationship needs constant closeness. Solitude makes you appreciate each other more.',
        'advice_zh':'暂时退隐不是逃避，是为了更清醒地前行。',
        'advice_en':'Stepping back is not running away — it is preparing to move forward more clearly.'},
    10: {'name':'Wheel of Fortune','cn':'命运之轮','en':'Change, cycles, and destiny. The wheel is turning — what goes up must come down, and vice versa.',
         'career_zh':'运势正在转折！好的会更好，坏的也会好转。抓住这个转折点的机会。',
         'career_en':'Fortune is turning! Good gets better, bad improves. Seize this turning point.',
         'love_zh':'命运的安排正在展开。可能遇到命中注定的人，或有重要的感情转折。',
         'love_en':'Destiny is unfolding. You may meet someone fated, or experience a major romantic shift.',
         'advice_zh':'顺势而为。轮子已经转了，你要做的是调整自己的位置。',
         'advice_en':'Go with the flow. The wheel is turning — your job is to adjust your position.'},
    11: {'name':'Justice','cn':'正义','en':'Fairness, truth, and consequences. You will receive what you deserve — for better or worse.',
         'career_zh':'公正的评判即将到来。你付出的努力会得到应有的回报。法律或合同相关事务有利。',
         'career_en':'Fair judgment is coming. Your efforts will be rewarded as they deserve. Legal and contractual matters are favored.',
         'love_zh':'诚实是关键。任何隐瞒都会被揭穿。真诚相待才能长久。',
         'love_en':'Honesty is key. Any concealment will be exposed. Only sincerity lasts.',
         'advice_zh':'种什么因得什么果。此刻做对的事，未来会感谢现在的自己。',
         'advice_en':'You reap what you sow. Do the right thing now — your future self will thank you.'},
    12: {'name':'The Hanged Man','cn':'倒吊人','en':'Pause, surrender, and new perspectives. Sometimes letting go is the most powerful action.',
         'career_zh':'暂时的停滞不是失败，而是重新审视方向的机会。换个角度看问题。',
         'career_en':'Temporary stagnation is not failure but an opportunity to re-examine your direction. See things from a new angle.',
         'love_zh':'可能需要暂时放下某个执着。给彼此空间，让感情自然流动。',
         'love_en':'You may need to let go of a fixation. Give each other space and let feelings flow naturally.',
         'advice_zh':'倒过来看世界，你会发现不一样的美。放手不是放弃。',
         'advice_en':'See the world upside down and discover new beauty. Letting go is not giving up.'},
    13: {'name':'Death','cn':'死神','en':'Endings, transformation, and rebirth. Something must die for something new to be born.',
         'career_zh':'旧的工作模式或职业可能需要彻底结束，为全新的方向让路。这是蜕变，不是终结。',
         'career_en':'Old work patterns or careers may need to end completely, making way for something entirely new. This is metamorphosis, not termination.',
         'love_zh':'一段旧感情或模式需要放手。告别是为了迎接更适合你的人。',
         'love_en':'An old relationship or pattern needs to be released. Farewell makes room for someone more suited to you.',
         'advice_zh':'不要害怕结束。毛毛虫必须死去，蝴蝶才能诞生。',
         'advice_en':'Do not fear endings. The caterpillar must die for the butterfly to be born.'},
    14: {'name':'Temperance','cn':'节制','en':'Balance, moderation, and harmony. Blend opposing forces to create something beautiful.',
         'career_zh':'寻求工作与生活的平衡。不急不躁，稳步推进比猛冲猛打更有效。',
         'career_en':'Seek work-life balance. Steady progress beats reckless sprints.',
         'love_zh':'感情需要平衡的给予和接受。共同成长而不是互相消耗。',
         'love_en':'Relationships need balanced giving and receiving. Grow together, not drain each other.',
         'advice_zh':'慢慢来，比较快。平衡的艺术需要练习，但值得掌握。',
         'advice_en':'Slow is smooth, smooth is fast. Balance takes practice but is worth mastering.'},
    15: {'name':'The Devil','cn':'恶魔','en':'Attachment, materialism, and shadow self. Examine what chains you — you hold the key to your freedom.',
         'career_zh':'你可能困在一个不满意的工作里，害怕改变。检查是什么在束缚你——其实你可以挣脱。',
         'career_en':'You may be trapped in an unsatisfying job, afraid to change. Examine what binds you — you can break free.',
         'love_zh':'警惕不健康的依恋或控制关系。真正的爱让人自由，不是让人窒息。',
         'love_en':'Beware unhealthy attachment or controlling relationships. True love liberates, not suffocates.',
         'advice_zh':'锁链的另一端没有锁。你一直握着钥匙。',
         'advice_en':'The chains are not locked. You have been holding the key all along.'},
    16: {'name':'The Tower','cn':'高塔','en':'Sudden upheaval, revelation, and liberation. What is built on weak foundations must fall.',
         'career_zh':'突如其来的变化可能打乱计划。不要惊慌——这是在为你清除不稳固的基础。',
         'career_en':'Sudden changes may disrupt plans. Do not panic — this is clearing unstable foundations for you.',
         'love_zh':'剧烈的感情震荡。可能是分手或重大冲突，但背后是必要的真相揭露。',
         'love_en':'Intense emotional shakeup. Possibly breakup or major conflict, but necessary truths are being revealed.',
         'advice_zh':'塔倒了才能重建。感谢这场风暴，它在帮你清理。',
         'advice_en':'The tower must fall to be rebuilt. Thank the storm — it is clearing the way for you.'},
    17: {'name':'The Star','cn':'星星','en':'Hope, renewal, and inspiration. After the storm comes the calm. Your wishes are being heard.',
         'career_zh':'灵感涌现！这是最有利于创作和创新的时期。相信你的创意直觉。',
         'career_en':'Inspiration floods in! This is the best time for creation and innovation. Trust your creative instincts.',
         'love_zh':'新的希望正在升起。无论是疗愈旧伤还是迎接新恋情，星星都在守护你。',
         'love_en':'New hope is rising. Whether healing old wounds or welcoming new love, the Star watches over you.',
         'advice_zh':'有什么愿望，现在就对宇宙说出来。星星在听。',
         'advice_en':'Whatever you wish for, speak it to the universe now. The stars are listening.'},
    18: {'name':'The Moon','cn':'月亮','en':'Illusion, fear, and the subconscious. Not everything is as it seems — navigate by intuition.',
         'career_zh':'信息不透明，保持警惕。不要相信表面现象，做好调查研究再做决定。',
         'career_en':'Information is opaque — stay vigilant. Do not trust appearances. Research before deciding.',
         'love_zh':'可能有误会在酝酿。不要被情绪左右，把事情弄清楚再下判断。',
         'love_en':'Misunderstandings may be brewing. Do not let emotions rule — clarify before judging.',
         'advice_zh':'在黑暗中凭直觉前行。答案不在外面，在你的潜意识里。',
         'advice_en':'Walk in the dark by intuition. The answers are not outside — they are in your subconscious.'},
    19: {'name':'The Sun','cn':'太阳','en':'Joy, success, and vitality. Everything shines — bask in the warmth of your achievements.',
         'career_zh':'事业巅峰期！你的才华被看见，努力得到认可。享受这一刻的成功。',
         'career_en':'Career peak! Your talents are recognized, your efforts rewarded. Enjoy this success.',
         'love_zh':'感情阳光灿烂。无论是恋爱中还是单身，你都散发着吸引人的光芒。',
         'love_en':'Love shines bright. Whether in a relationship or single, you radiate attractive energy.',
         'advice_zh':'这就是你的高光时刻。尽情享受，你值得这一切。',
         'advice_en':'This is your moment in the sun. Enjoy it fully — you deserve this.'},
    20: {'name':'Judgement','cn':'审判','en':'Rebirth, calling, and absolution. A wake-up call to embrace your true purpose.',
         'career_zh':'收到重要的召唤或新机会。是时候回应你的使命，做你真正该做的事。',
         'career_en':'An important calling or new opportunity arrives. Time to answer your mission and do what you are truly meant to do.',
         'love_zh':'重新审视感情。原谅过去，给自己和对方一个新开始的机会。',
         'love_en':'Re-examine relationships. Forgive the past and give yourself and others a chance for a fresh start.',
         'advice_zh':'觉醒的时刻到了。你被召唤去做更大的事。回应它。',
         'advice_en':'The moment of awakening is here. You are called to something greater. Answer it.'},
    21: {'name':'The World','cn':'世界','en':'Completion, accomplishment, and wholeness. A cycle ends — celebrate and prepare for the next.',
         'career_zh':'一个重要的周期圆满结束。你的成就得到全球性认可。好好庆祝！',
         'career_en':'A major cycle completes beautifully. Your achievements earn global recognition. Celebrate!',
         'love_zh':'感情圆满。可能是求婚、结婚或达到新层次的亲密。一切刚刚好。',
         'love_en':'Romantic fulfillment. Perhaps a proposal, marriage, or a new level of intimacy. Everything is just right.',
         'advice_zh':'你做到了。享受圆满的喜悦，然后准备好迎接下一个冒险。',
         'advice_en':'You did it. Enjoy the joy of completion, then prepare for your next adventure.'},
}

def get_spread_reading(cards, level='free'):
    """Generate a tarot spread reading for 3 cards (Past, Present, Future)"""
    if len(cards) < 3:
        return {'error': 'Need 3 cards'}

    reading = {'cards': [], 'spread': {}}

    positions = ['past', 'present', 'future']
    pos_labels = {'past': '过去', 'present': '现在', 'future': '未来'}
    pos_labels_en = {'past': 'Past', 'present': 'Present', 'future': 'Future'}

    for i, card_id in enumerate(cards[:3]):
        card = MAJOR_ARCANA.get(card_id, MAJOR_ARCANA[0])
        entry = {
            'id': card_id,
            'position': positions[i],
            'pos_zh': pos_labels[positions[i]],
            'pos_en': pos_labels_en[positions[i]],
            'name': card['name'],
            'cn': card['cn'],
            'meaning': card['en'],
        }
        if level in ('basic', 'full'):
            entry['career_zh'] = card.get('career_zh', '')
            entry['career_en'] = card.get('career_en', '')
            entry['love_zh'] = card.get('love_zh', '')
            entry['love_en'] = card.get('love_en', '')
        if level == 'full':
            entry['advice_zh'] = card.get('advice_zh', '')
            entry['advice_en'] = card.get('advice_en', '')
        reading['cards'].append(entry)

    # Generate spread overview
    if level in ('basic', 'full'):
        c0, c1, c2 = MAJOR_ARCANA.get(cards[0], MAJOR_ARCANA[0]), MAJOR_ARCANA.get(cards[1], MAJOR_ARCANA[0]), MAJOR_ARCANA.get(cards[2], MAJOR_ARCANA[0])
        reading['spread']['overview_zh'] = f'你抽到的三张牌是：「{c0["cn"]}」、「{c1["cn"]}」、「{c2["cn"]}」。过去由{c0["cn"]}主宰——{c0["en"][:60]}... 现在由{c1["cn"]}引导——{c1["en"][:60]}... 未来指向{c2["cn"]}——{c2["en"][:60]}...'
        reading['spread']['overview_en'] = f'Your three cards are: "{c0["name"]}", "{c1["name"]}", "{c2["name"]}". The past is ruled by {c0["name"]} — {c0["en"][:60]}... The present is guided by {c1["name"]} — {c1["en"][:60]}... The future points to {c2["name"]} — {c2["en"][:60]}...'

    if level == 'full':
        reading['spread']['summary_zh'] = generate_spread_summary(cards, 'zh')
        reading['spread']['summary_en'] = generate_spread_summary(cards, 'en')

    return reading


def generate_spread_summary(card_ids, lang):
    cards = [MAJOR_ARCANA.get(cid, MAJOR_ARCANA[0]) for cid in card_ids[:3]]
    if lang == 'zh':
        return f"""🔮 完整的命运画像：

过去 ({cards[0]['cn']})：{cards[0]['en'][:80]}...

现在 ({cards[1]['cn']})：{cards[1]['en'][:80]}...

未来 ({cards[2]['cn']})：{cards[2]['en'][:80]}...

💡 给你的建议：{cards[2]['advice_zh']}

这三张牌形成了一个完整的故事：从过去走向现在，再迈向未来。每一张牌都在提醒你——你拥有创造自己命运的力量。"""
    else:
        return f"""🔮 Your Complete Destiny Portrait:

Past ({cards[0]['name']}): {cards[0]['en'][:80]}...

Present ({cards[1]['name']}): {cards[1]['en'][:80]}...

Future ({cards[2]['name']}): {cards[2]['en'][:80]}...

💡 Advice for you: {cards[2]['advice_en']}

These three cards tell a complete story — from past through present into future. Each card reminds you — you have the power to create your own destiny."""


if __name__ == '__main__':
    import json
    r = get_spread_reading([0, 17, 19], 'full')
    print(json.dumps(r, ensure_ascii=False, indent=2))
