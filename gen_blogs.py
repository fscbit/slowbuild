#!/usr/bin/env python3
"""Generate 20 SEO-optimized office life blog posts"""
import os

CSS = '<style>:root{--bg:#0a0a0f;--surface:#12121a;--border:#1e1e2e;--text:#d4d4e0;--muted:#707088;--gold:#d4a853;--teal:#38bdf8}*{box-sizing:border-box;margin:0;padding:0}body{font-family:Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.8}.container{max-width:860px;margin:0 auto;padding:20px 24px}.breadcrumb{font-size:.8rem;color:var(--muted);margin-bottom:24px;padding:8px 0}.breadcrumb a{color:var(--teal);text-decoration:none}article h1{font-size:1.8rem;background:linear-gradient(135deg,#d4a853,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px;text-align:center}article .date{text-align:center;color:var(--muted);font-size:.8rem;margin-bottom:30px}article h2{font-size:1.3rem;color:var(--gold);margin:32px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}article p{font-size:.92rem;color:#c0c0d0;margin-bottom:14px}article ul,article ol{font-size:.9rem;color:#c0c0d0;padding-left:24px;margin-bottom:14px}article li{margin-bottom:6px}.cta-box{background:linear-gradient(135deg,rgba(212,168,83,.15),rgba(56,189,248,.1));border:1px solid var(--gold);border-radius:12px;padding:24px;margin:40px 0;text-align:center}.cta-box h3{color:var(--gold);margin-bottom:10px}.cta-box p{color:#b0b0c0;margin-bottom:16px}.cta-box .btn{display:inline-block;background:var(--gold);color:#000;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.9rem;transition:all .2s}.cta-box .btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(212,168,83,.3)}.tags{margin-top:30px;display:flex;flex-wrap:wrap;gap:8px}.tag{background:var(--surface);color:var(--teal);padding:4px 12px;border-radius:20px;font-size:.75rem}.related{margin-top:50px;padding-top:30px;border-top:1px solid var(--border)}.related h3{color:var(--gold);margin-bottom:16px}.related ul{list-style:none;padding:0}.related li{margin-bottom:10px}.related a{color:var(--teal);text-decoration:none;font-size:.9rem}.related a:hover{text-decoration:underline}footer{text-align:center;padding:40px 20px;color:var(--muted);font-size:.75rem}footer a{color:var(--teal);text-decoration:none}</style>'

def make(file, title, desc, keys, date, read_time, sections, cta, tags, related):
    sec_html = ""
    for h2, paras in sections:
        sec_html += f'<h2>{h2}</h2>\n'
        in_ul = False
        for p in paras:
            if p.startswith("• "):
                if not in_ul:
                    sec_html += '<ul>\n'; in_ul = True
                sec_html += f'<li>{p[2:]}</li>\n'
            else:
                if in_ul:
                    sec_html += '</ul>\n'; in_ul = False
                sec_html += f'<p>{p}</p>\n'
        if in_ul: sec_html += '</ul>\n'

    tag_html = "".join(f'<span class="tag">{t}</span>' for t in tags)
    rel_html = "".join(f'<li><a href="{r[1]}">{r[0]}</a></li>' for r in related)
    short_title = title[:55]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - SlowBuild</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{keys}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.slowbuild.top/blog/en/{file}.html">
<meta property="og:title" content="{title} - SlowBuild">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://www.slowbuild.top/blog/en/{file}.html">
<meta property="og:image" content="https://www.slowbuild.top/og-fortune.png">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SlowBuild">
{CSS}
</head>
<body>
<div class="container">
<nav class="breadcrumb"><a href="/">Home</a> › <a href="/blog/en/">Blog</a> › {short_title}...</nav>
<article>
<h1>{title}</h1>
<p class="date">{date} · {read_time}</p>
{sec_html}
</article>
<div class="cta-box"><h3>{cta[0]}</h3><p>{cta[1]}</p><a href="{cta[2]}" class="btn">{cta[3]}</a></div>
<div class="tags">{tag_html}</div>
<div class="related"><h3>Related Articles</h3><ul>{rel_html}</ul></div>
</div>
<footer><p>&copy; 2026 <a href="/">SlowBuild</a>. Tools for everyday life.</p></footer>
</body>
</html>"""
    with open(f"blog/en/{file}.html", "w", encoding="utf-8") as f:
        f.write(html)

os.makedirs("blog/en", exist_ok=True)

# ===== ALL 20 POSTS (posts 1-5 already done manually, 6-20 here) =====

posts = [
    # === 4: Toxic Boss ===
    ("office-04-toxic-boss",
     "The Toxic Boss Field Guide: 7 Types of Bad Managers and How to Handle Each",
     "From the micromanager to the credit thief, learn to identify 7 toxic boss archetypes. Includes real survival tactics, conversation scripts, and exit strategies for every type.",
     "toxic boss, bad manager, workplace survival, office politics, difficult boss, career advice, manager red flags, how to deal with toxic boss",
     "8 min read",
     [("Why Bad Bosses Are an Epidemic",
       ["A 2025 Gallup poll found that 70% of the variance in employee engagement is tied to the manager. Yet most companies promote people into management based on technical skills, not leadership ability. The result: a workforce managed by people who were great individual contributors but have zero people skills. The Dilbert Principle — where the least competent get promoted to management — isn't just a comic. It's corporate reality.",
        "In Southeast Asia, the dynamic is even more complex. Hierarchy is baked into the culture. Your manager isn't just your boss — they're your 'senior,' a status that commands automatic deference regardless of competence. This makes identifying and escaping toxic management even harder."]),
      ("Type 1: The Micromanager",
       ["Asks for hourly updates. CC's themselves on everything. Rewrites your work to match their preferences — not because it's better, but because it's not THEIRS. Psychology: deep insecurity masked as 'attention to detail.' Survival tactic: preemptively over-communicate. Send detailed updates before they ask. When they suggest changes, say 'Great catch — incorporated.' Give them the illusion of control so they leave you alone."]),
      ("Type 2: The Credit Thief",
       ["Presents your ideas as their own in meetings. Never mentions your name to higher-ups. Takes credit for success, delegates blame for failure. Survival tactic: create a paper trail. Send recap emails after meetings. CC their boss on major deliverables. Use 'we' language — it's harder to steal glory when 'we' achieved it together."]),
      ("Type 3: The Vanisher",
       ["Cancels 1-on-1s. Takes days to reply. Misses your deadlines because they never approved anything. Survival tactic: make decisions yourself and document why. Use the 'I plan to do X by Friday unless I hear otherwise' email. In the absence of 'no,' default to action."]),
      ("Type 4-7: Yeller, People Pleaser, Overpromiser, 'Family' Faker",
       ["The Yeller uses anger as management. The People Pleaser says yes to everything and makes YOUR life hell. The Overpromiser commits the team to impossible deadlines to look good. The 'We're a Family' boss weaponizes emotional manipulation to justify 80-hour weeks. Survival for all four: document everything, set written expectations, never let 'family' guilt you into self-destruction."])],
     ("Dealing with a difficult boss?","Our I Ching readings offer ancient wisdom for tough career crossroads.","/fortune/iching.html","Consult the I Ching →"),
     ["Toxic Boss","Bad Manager","Office Politics","Career Survival","Workplace Psychology","Leadership"],
     [("Quiet Quitting Guide","/blog/en/office-01-quiet-quitting.html"),("Salary Negotiation Scripts","/blog/en/office-18-salary-negotiation.html"),("Burnout Recovery","/blog/en/office-15-burnout-recovery.html")]
    ),

    # === 5: Open Office ===
    ("office-05-open-office",
     "Open Office Hell: How Open-Plan Layouts Destroy Productivity (And What to Do)",
     "Open-plan offices were supposed to boost collaboration. Instead they created a noise nightmare. Learn the science behind why open offices fail and practical survival hacks.",
     "open office problems, workplace distraction, productivity tips, open plan office, office noise, focus at work, office layout",
     "6 min read",
     [("The $70 Billion Open Office Mistake",
       ["In the 2000s, American companies demolished office walls en masse. The promise: spontaneous collaboration, serendipitous innovation. The reality: 70 decibels of phone calls, keyboard clatter, and Carol's loud personal conversations. Harvard research found face-to-face interactions actually DROPPED 70% after open-plan switches. Workers retreated to email — even with colleagues sitting three feet away.",
        "The open office was never about collaboration. It was about cost-cutting. You can fit 1.5x more workers without walls. The math was simple. The human cost was ignored."]),
      ("The Neuroscience of Distraction",
       ["A UC Irvine study found it takes 23 minutes and 15 seconds to regain deep focus after an interruption. In an open office, workers are interrupted every 11 minutes on average. You literally cannot achieve flow state. Your brain constantly scans for 'threats' — someone walking behind you, a sudden laugh, a shoulder tap. This isn't weak willpower. It's your brain's evolutionary survival mechanism."]),
      ("Survival Toolkit",
       ["• Noise-canceling headphones: not optional, mandatory equipment.\n• The 'Do Not Disturb' visual signal: a desk flag or indicator light.\n• Book focus rooms two weeks ahead.\n• Come in at 7 AM or stay until 7 PM for quiet hours.\n• Work from home on deep-focus days when policy allows.",
        "In tropical SEA offices, add personal desk fans and negotiate thermostat treaties with nearby colleagues. The AC wars are real."])],
     ("Tired of office distractions?","Our batch tools finish the busywork fast — so you can focus on real work.","/","See Productivity Tools →"),
     ["Open Office","Workplace Productivity","Focus Tips","Office Design","Deep Work","Corporate Life"],
     [("Meeting Culture Hell","/blog/en/office-03-meeting-hell.html"),("Remote Work Guide","/blog/en/office-06-remote-isolation.html"),("Work-Life Balance","/blog/en/office-20-boundaries.html")]
    ),

    # === 6: Remote Work ===
    ("office-06-remote-isolation",
     "The Silent Crisis of Remote Work: Isolation, Loneliness, and How to Fight Back",
     "Remote work promised freedom but delivered isolation for millions. Learn why loneliness is the hidden cost of WFH, how to spot the warning signs, and practical ways to rebuild connection.",
     "remote work isolation, work from home loneliness, WFH mental health, remote work tips, workplace loneliness, hybrid work, social isolation at work",
     "7 min read",
     [("The Freedom That Became a Cage",
       ["When the pandemic sent everyone home in 2020, it felt like liberation. No commute. No open office noise. Pants optional. Five years later, the hangover has set in. A 2025 American Psychological Association study found that 61% of fully remote workers report feelings of chronic loneliness — higher than any other work arrangement. The very freedom we celebrated has quietly become isolation.",
        "Remote work strips away the 'weak ties' that make office life bearable: the coffee machine chat, the hallway nod, the spontaneous lunch group. These micro-interactions aren't frivolous — they're the social glue that reduces cortisol and boosts oxytocin. Without them, many remote workers are slowly, invisibly, losing their minds."]),
      ("Warning Signs You're Too Isolated",
       ["• You go entire days without speaking to another human voice.\n• Slack messages feel hostile even when they're neutral (text lacks tone).\n• You feel irrationally angry at minor work requests.\n• Your apartment feels smaller. Your world feels smaller.\n• You've forgotten how to make small talk.",
        "These are not personality flaws. They're predictable psychological responses to prolonged social deprivation."]),
      ("The Fix: Intentional Connection",
       ["• Co-working spaces: even 2 days a week in a shared space can reset your brain.\n• 'Phone call instead of Slack' rule: hear a human voice at least once daily.\n• Lunch dates: schedule weekly lunches with friends who also WFH.\n• Walking meetings: take calls while walking outside — movement + nature + conversation.\n• The 'third place': find somewhere that isn't home and isn't work — a gym, a café, a community group.",
        "For Southeast Asian remote workers, family proximity can be a double-edged sword. Living with extended family provides social contact but erases boundaries. The solution isn't isolation — it's negotiated space and scheduled alone time."])],
     ("Feeling disconnected?","A Tarot reading can offer clarity when life feels foggy.","/fortune/tarot.html","Try a Free Tarot Reading →"),
     ["Remote Work","WFH Loneliness","Mental Health","Workplace Isolation","Hybrid Work","Social Connection"],
     [("Open Office Hell","/blog/en/office-05-open-office.html"),("Burnout Recovery","/blog/en/office-15-burnout-recovery.html"),("Work-Life Boundaries","/blog/en/office-20-boundaries.html")]
    ),

    # === 7: Unlimited PTO ===
    ("office-07-unlimited-pto",
     "The Unlimited PTO Trap: Why Nobody Actually Takes Vacation in America",
     "Unlimited PTO sounds like a dream benefit. In reality, American workers with unlimited vacation take FEWER days off. Here's why the policy backfires and how to actually use your time off.",
     "unlimited PTO, vacation policy, American work culture, time off, workplace benefits, taking vacation, corporate perks trap",
     "6 min read",
     [("The Paradox of Unlimited Vacation",
       ["Companies love advertising 'unlimited PTO.' It sounds generous. It costs nothing to offer. And here's the dirty secret: employees with unlimited PTO take an average of 10 days off per year — compared to 15 days for those with fixed vacation banks. When there's no 'use it or lose it' pressure, when there's no clear norm for what's acceptable, when nobody wants to be 'that person' who takes too much time off — people default to taking almost nothing.",
        "The psychology is brutal. Fixed PTO feels like an entitlement you've earned. Unlimited PTO feels like a favor you're asking for. Every time. You have to negotiate your time off over and over, and most people just... stop asking."]),
      ("Why American Workers Are Vacation-Phobic",
       ["The US is the only advanced economy with zero federally mandated paid vacation days. Compare: France (30 days), UK (28 days), Japan (20 days), Singapore (14 days, plus 11 public holidays). American 'unlimited PTO' isn't generous — it's a loophole. Companies don't have to accrue vacation liability on their books. When you quit, they owe you nothing. Clean balance sheet. The policy benefits the employer, not you."]),
      ("How to Actually Take Your Time Off",
       ["• Schedule vacation at the beginning of the year — put it on the calendar before anyone asks.\n• Aim for at least 15 days (the US professional norm) as a minimum, not a ceiling.\n• Take FULL weeks, not scattered Fridays. A 4-day weekend doesn't reset your brain.\n• Set an out-of-office message that says 'I will not have access to email.' Not 'limited access.'\n• Block the day before and after vacation as 'transition days' — no meetings.",
        "In SEA offices, the dynamic is different. Vacation is culturally accepted during holiday periods (Lunar New Year, Hari Raya, Deepavali) but frowned upon during 'normal' weeks. The strategy: piggyback your personal leave onto cultural holidays for maximum acceptance."])],
     ("Your well-being matters more than any job.","Take a moment for yourself — try our free daily fortune reading.","/fortune.html","Get Today's Fortune →"),
     ["Unlimited PTO","Vacation Policy","Work Culture","Time Off","Employee Benefits","Corporate Life"],
     [("Burnout Recovery","/blog/en/office-15-burnout-recovery.html"),("Quiet Quitting","/blog/en/office-01-quiet-quitting.html"),("Work-Life Balance","/blog/en/office-20-boundaries.html")]
    ),

    # === 8: Performance Review ===
    ("office-08-performance-review",
     "Performance Review Anxiety: A Psychological Survival Guide",
     "Performance review season triggers anxiety in 85% of workers. Learn why your brain panics, how to prepare evidence that silences imposter syndrome, and exact scripts for asking for that raise.",
     "performance review anxiety, annual review tips, salary negotiation, workplace anxiety, performance evaluation, career growth, asking for raise",
     "7 min read",
     [("Why Performance Reviews Feel Like a Trial",
       ["85% of American workers report anxiety before performance reviews. Your brain treats the annual review like a survival threat — the same amygdala activation as facing a predator. This is because reviews directly threaten two fundamental human needs: belonging (will I still be valued?) and status (am I good enough?). The physical symptoms — racing heart, sweaty palms, brain fog — aren't weakness. They're your nervous system doing exactly what it evolved to do.",
        "But here's what your anxious brain won't tell you: most negative feedback is about systems, not you. And the review is actually YOUR opportunity to shape the narrative. The person who comes prepared with evidence controls the conversation."]),
      ("Build Your Brag Document",
       ["Before review season starts, create a running document of every win. Not just big projects — small things too. The process improvement that saved 2 hours a week. The client who sent a thank-you email. The crisis you handled at 9 PM. When review day comes, you're not scrambling to remember what you did — you're presenting a curated portfolio.",
        "Quantify everything: 'Reduced processing time by 40%' beats 'Made things more efficient.' 'Resolved 127 support tickets with 98% satisfaction' beats 'Handled customer issues.' Numbers turn vague contributions into undeniable evidence."]),
      ("The Raise Conversation Script",
       ["Don't wait for them to bring up money. After presenting your evidence, transition: 'Based on these contributions and current market rates for this role, I'd like to discuss adjusting my compensation to [specific number].' The specific number is crucial — it signals you've done research. If they deflect: 'What would need to happen for us to get there?' This turns a no into a roadmap.",
        "In SEA offices, salary negotiation is culturally trickier. Hierarchy and 'face' make direct asks uncomfortable. The adaptation: frame it as a discussion about 'market alignment' rather than personal demand. It depersonalizes the request and preserves harmony."])],
     ("Nervous about your review?","Our BaZi career reading can reveal when your luck cycle peaks.","/fortune/bazi.html","Check Your Career Luck →"),
     ["Performance Review","Salary Negotiation","Career Growth","Workplace Anxiety","Annual Review","Professional Development"],
     [("Salary Negotiation Scripts","/blog/en/office-18-salary-negotiation.html"),("Imposter Syndrome","/blog/en/office-10-imposter-syndrome.html"),("Toxic Boss Guide","/blog/en/office-04-toxic-boss.html")]
    ),

    # === 9: Corporate Gaslighting ===
    ("office-09-corporate-gaslighting",
     "Corporate Gaslighting: 'We're a Family' and 8 Other Red Flags You Should Never Ignore",
     "From 'we're like a family here' to 'we only hire the best,' decode the manipulative language companies use to justify overwork, underpay, and control. Learn to spot gaslighting before it damages your career.",
     "corporate gaslighting, toxic workplace, office manipulation, we are a family, red flags at work, workplace psychology, toxic company culture",
     "6 min read",
     [("The 'We're a Family' Lie",
       ["No sentence in corporate America has done more damage than 'we're like a family here.' Families don't fire you when quarterly earnings dip. Families don't put you on a PIP. Families don't replace you with a cheaper contractor in Manila. 'We're a family' is a one-way loyalty demand disguised as warmth. It's a manipulation tactic designed to make you feel guilty for having boundaries.",
        "Real families don't require you to earn your place. Real families don't have performance improvement plans. When a company calls itself a family, what they actually mean is: 'We expect you to sacrifice like you would for family, but we reserve the right to treat you like an employee.' The correct response is: 'I appreciate the sentiment. I prefer to think of us as a high-performing team with mutual respect.'"]),
      ("7 More Red Flags Decoded",
       ["• 'We work hard and play hard' = We work hard. There is no play.\n• 'We only hire the best' = We'll make you constantly prove you deserve to be here.\n• 'Fast-paced environment' = Chaos. Constant fires. No processes.\n• 'Must be comfortable with ambiguity' = Management has no plan.\n• 'We're looking for a rockstar' = We want one person to do three jobs.\n• 'Competitive salary' = We'll pay the minimum we can get away with.\n• 'Unlimited growth potential' = There's no defined career path."]),
      ("The Southeast Asia Edition: 'Face' as a Weapon",
       ["In Singapore and Malaysian offices, gaslighting takes a culturally specific form. 'Don't make the team lose face' is used to silence whistleblowers. 'For the good of the company family' justifies unpaid overtime. The collectivist culture that makes SEA workplaces warm also makes them uniquely effective at using shame and guilt as control mechanisms. The antidote: 'I want what's best for the team too — which is why I'm raising this issue.' Reframe resistance as loyalty."])],
     ("Second-guessing yourself at work?","Get clarity with a free BaZi reading — understand your strengths and timing.","/fortune/bazi.html","Discover Your Strengths →"),
     ["Corporate Gaslighting","Toxic Workplace","Office Red Flags","Career Advice","Workplace Psychology","Company Culture"],
     [("Toxic Boss Guide","/blog/en/office-04-toxic-boss.html"),("Quiet Quitting","/blog/en/office-01-quiet-quitting.html"),("Passive Aggression Dictionary","/blog/en/office-02-passive-aggressive.html")]
    ),

    # === 10: Imposter Syndrome ===
    ("office-10-imposter-syndrome",
     "Imposter Syndrome at Work: You're Probably Not a Fraud (Here's Why)",
     "70% of professionals experience imposter syndrome. Learn why high achievers feel like frauds, the five imposter types, and evidence-based strategies to silence your inner critic.",
     "imposter syndrome, workplace confidence, self doubt at work, career anxiety, overcoming imposter syndrome, professional confidence, feeling like a fraud",
     "6 min read",
     [("Why Smart People Feel Like Frauds",
       ["The irony of imposter syndrome is that it disproportionately affects high achievers. The more competent you are, the more aware you become of what you don't know — while simultaneously assuming everyone else has it figured out. This is the Dunning-Kruger effect in reverse: the skilled underestimate themselves because they can see the complexity. The unskilled overestimate themselves because they can't.",
        "A 2025 study of Fortune 500 executives found that 68% had experienced imposter feelings at some point. Including CEOs. Including people who'd built billion-dollar companies. The voice in your head saying 'you don't belong here' is not a reliable narrator."]),
      ("The 5 Imposter Types",
       ["• The Perfectionist: 'If it's not flawless, I've failed.' Sets impossible standards.\n• The Superhero: 'I must excel at EVERY role — worker, parent, partner.' Spreads too thin.\n• The Natural Genius: 'If I have to work hard at it, I must not be good enough.' Equates effort with incompetence.\n• The Soloist: 'If I ask for help, they'll know I'm a fraud.' Refuses support.\n• The Expert: 'I need one more certification before I'm qualified.' Never feels ready.",
        "Figure out which type you are. The fix is different for each."]),
      ("Evidence-Based Counters",
       ["• Keep a 'wins folder' — every positive email, every thank-you, every completed project. Review it monthly.\n• Ask for specific feedback: not 'how am I doing?' but 'what's one thing I did this month that added value?'\n• Recognize that discomfort is growth. If you're not slightly terrified, you're not stretching.\n• Therapy works. Cognitive Behavioral Therapy has a 70%+ success rate for imposter syndrome.\n• In SEA cultures, imposter syndrome is amplified by comparative achievement pressure. 'My cousin is a doctor and I'm just in marketing' is a common refrain. The fix: run your own race."])],
     ("Need a confidence boost?","Sometimes the universe has a message for you. Try a free daily fortune reading.","/fortune.html","Get Your Daily Fortune →"),
     ["Imposter Syndrome","Workplace Confidence","Self Doubt","Career Growth","Mental Health","Professional Development"],
     [("Performance Review Guide","/blog/en/office-08-performance-review.html"),("Salary Negotiation","/blog/en/office-18-salary-negotiation.html"),("Corporate Gaslighting","/blog/en/office-09-corporate-gaslighting.html")]
    ),

    # === 11: Office Fridge ===
    ("office-11-fridge-politics",
     "Office Fridge Politics: Lunch Theft, Passive-Aggressive Notes, and the Psychology of Shared Spaces",
     "Someone stole your lunch. Again. Why office fridge theft is actually about power, territory, and group dynamics — not hunger. Plus: the most effective (and hilarious) anti-theft strategies.",
     "office fridge theft, workplace lunch, office politics, shared kitchen, passive aggressive notes, office etiquette, workplace humor",
     "5 min read",
     [("The Fridge Is a Microcosm of Office Politics",
       ["Every office kitchen tells a story. The mysterious missing yogurt. The passive-aggressive Post-it notes. The unwashed Tupperware fossilizing in the back. Office fridge theft isn't really about hunger — it's about territory, status, and group dynamics played out in a 4-cubic-foot arena. The person who steals your lunch isn't hungry. They're asserting dominance.",
        "Anthropologists would have a field day with the average office fridge. The unspoken hierarchy: senior management food never gets touched. New hire food disappears within hours. The communal milk is always empty. The ketchup bottle has been there since 2019. It's a living museum of workplace anthropology."]),
      ("The Psychology of the Lunch Thief",
       ["Researchers have identified three types: 1) The Oblivious: genuinely thought it was communal. 2) The Justifier: 'I'll replace it tomorrow' (they won't). 3) The Dominator: knows exactly whose food it is and doesn't care. Type 3 is most common at companies with toxic cultures — food theft correlates with broader disrespect for colleagues."]),
      ("Anti-Theft Strategies That Actually Work",
       ["• The Label: 'Property of [Name]. Do not eat. Contains medication.' Nobody messes with medication.\n• The Decoy: leave an old sandwich as bait, keep the good stuff hidden.\n• The Spicy Surprise: ghost peppers in a decoy dish. They'll only do it once.\n• The Container: opaque lunch bag inside the fridge — out of sight, out of mind.\n• The Nuclear Option: a mini-fridge at your desk. The ultimate declaration of independence.",
        "In SEA offices, the dynamic shifts — food sharing is cultural. Your colleague eating your lunch might genuinely believe it's communal (makan culture). The solution: separate labeled containers for personal items, a clearly marked 'share box' for communal food."])],
     ("Office life getting you down?","Take a break with our free Tarot reading — see what the cards reveal.","/fortune/tarot.html","Try a Tarot Reading →"),
     ["Office Fridge","Workplace Politics","Office Etiquette","Lunch Theft","Shared Kitchen","Office Humor"],
     [("Passive Aggression Dictionary","/blog/en/office-02-passive-aggressive.html"),("Open Office Hell","/blog/en/office-05-open-office.html"),("CC Culture","/blog/en/office-12-cc-culture.html")]
    ),

    # === 12: CC Culture ===
    ("office-12-cc-culture",
     "The CC Culture Epidemic: How Carbon-Copying Became a Workplace Weapon",
     "CC'ing the boss on an email isn't about keeping people informed — it's about power, blame-shifting, and career warfare. Decode the politics of the CC field and learn to defend yourself.",
     "cc culture, email politics, workplace communication, carbon copy weapon, office politics, corporate email, passive aggressive email",
     "5 min read",
     [("The CC Field: Corporate America's Nuclear Football",
       ["Nothing changes the tone of an email faster than the CC field. A routine question becomes a public deposition. A gentle reminder becomes a performance review exhibit. The CC field transforms email from communication into documentation. Every person CC'd is a potential jury member in some future workplace trial.",
        "The unwritten rules: CC'ing someone's boss without warning is an act of aggression. CC'ing YOUR boss on a routine request signals 'I don't trust you to respond.' CC'ing the entire department is either a cry for help or a power play. And BCC? BCC is for spies, HR escalations, and people who peaked in high school."]),
      ("Decoding CC Intentions",
       ["• CC-Your-Boss: 'I'm documenting your incompetence.'\n• CC-My-Boss: 'Look at me, I'm working.'\n• CC-The-Whole-Team: 'I'm making this a public issue.'\n• Reply-All-With-CC: 'Let me share my brilliance with everyone.'\n• BCC-My-Boss: 'I'm building a case against you.'\n• BCC-Your-Boss: 'I've already escalated this, you just don't know yet.'"]),
      ("Defense Strategies",
       ["• When someone CC's your boss: respond professionally with facts. Don't get defensive — that's what they want.\n• Preemptive strike: CC relevant people yourself before someone weaponizes it against you.\n• The 'Let's take this offline' redirect: move the conversation out of the public thread.\n• Kill the thread: pick up the phone. A 2-minute call prevents a 20-email CC war.\n• In SEA offices, CC'ing carries extra weight due to hierarchy. CC'ing a senior manager is a major escalation — use it wisely."])],
     ("Office politics stressing you out?","Our I Ching readings have guided people through workplace conflicts for centuries.","/fortune/iching.html","Ask the I Ching →"),
     ["CC Culture","Email Politics","Workplace Communication","Office Politics","Corporate Email","Career Tips"],
     [("Passive Aggression","/blog/en/office-02-passive-aggressive.html"),("Fridge Politics","/blog/en/office-11-fridge-politics.html"),("Toxic Boss","/blog/en/office-04-toxic-boss.html")]
    ),

    # === 13: Micromanagement ===
    ("office-13-micromanagement",
     "Micromanagement Hell: 10 Signs Your Boss Doesn't Trust You (And How to Fix It)",
     "Does your boss demand hourly updates? Rewrite everything you produce? Ask to be CC'd on every email? That's micromanagement — and it's killing your career. Learn the psychology and the escape plan.",
     "micromanagement, controlling boss, workplace trust, bad manager, office survival, employee autonomy, how to deal with micromanager",
     "6 min read",
     [("The Trust Deficit at the Heart of Micromanagement",
       ["Micromanagement is not about attention to detail. It's about trust. Or rather, the total absence of it. Your boss doesn't believe you can do the job — or worse, doesn't believe anyone can do it as well as they can. Every 'correction' they make isn't about quality. It's about control. The tragedy: micromanagement creates the very incompetence it fears. Workers who are never trusted stop thinking. They become order-takers. The prophecy fulfills itself.",
        "Harvard Business Review calls micromanagement the 'silent killer of innovation.' Companies with micromanagement cultures see 28% higher turnover and 34% lower employee initiative. Your boss's behavior isn't just annoying you — it's costing the company real money."]),
      ("The 10 Signs Checklist",
       ["• Asks for status updates more than once per day.\n• Rewrites your work to match their preferences (not quality standards).\n• Requires approval for decisions you should own.\n• CC's themselves on all your external communications.\n• Discourages you from presenting your own work.\n• Monitors your online/away status obsessively.\n• Assigns tasks with step-by-step instructions for things you already know.\n• Gets anxious when you take initiative without asking.\n• Questions your time allocation constantly.\n• Your colleagues warn new hires about them. That's the biggest red flag of all."]),
      ("The Escape Plan",
       ["• Level 1: Over-communicate preemptively. Send detailed updates before they ask. Micromanagers relax when informed.\n• Level 2: Request autonomy explicitly. 'I've got this — can I run with it and check in Friday?'\n• Level 3: Involve their manager. Frame it as a career development conversation: 'I'm ready for more ownership.'\n• Level 4: Leave. Chronic micromanagers don't change. The market is full of managers who actually trust their teams.",
        "In Southeast Asian offices, micromanagement is often culturally normalized as 'guidance.' The hierarchy expects seniors to review everything juniors produce. The key distinction: guidance tells you what outcome to achieve. Micromanagement tells you exactly how to achieve it."])],
     ("Feeling controlled at work?","Our BaZi reading reveals when your career luck shifts for the better.","/fortune/bazi.html","Check Your Career Luck →"),
     ["Micromanagement","Controlling Boss","Workplace Trust","Office Survival","Bad Manager","Career Growth"],
     [("Toxic Boss Guide","/blog/en/office-04-toxic-boss.html"),("Quiet Quitting","/blog/en/office-01-quiet-quitting.html"),("Performance Review","/blog/en/office-08-performance-review.html")]
    ),

    # === 14: Team Building ===
    ("office-14-team-building",
     "Team Building Activities Everyone Secretly Hates: A Survival Guide to Mandatory Fun",
     "Trust falls. Escape rooms. 'Fun' Friday Zoom games. Why corporate team building fails spectacularly and what actually builds real team connection.",
     "team building, mandatory fun, corporate activities, office culture, team bonding, workplace social events, awkward office activities",
     "5 min read",
     [("The $46 Billion Industry Built on Shared Misery",
       ["American companies spend an estimated $46 billion annually on team building. Trust falls. Ropes courses. Cooking classes. Escape rooms. And almost everyone — 87% according to one survey — would rather just go home. The fundamental flaw: genuine connection can't be mandated. You can't schedule 'authentic bonding' on a Tuesday from 2-4 PM. Forced fun is still forced.",
        "The worst offenders: role-playing exercises (Now pretend you are a customer), trust falls (nobody trusts HR enough for this), sharing circles (Tell the group something vulnerable about yourself — absolutely not), and the escape room (where you discover that Carol handles stress by yelling at everyone)."]),
      ("Why It Fails: The Psychology of Forced Connection",
       ["Connection requires three things: autonomy (I chose to be here), vulnerability (I chose to share), and shared experience (we went through something together). Corporate team building violates all three. You didn't choose to be there. You're not going to be vulnerable with people who control your salary. And being trapped in a conference room isn't a shared experience — it's a hostage situation with snacks."]),
      ("What Actually Works",
       ["• Shared meals: no agenda, no facilitator, just food. The oldest team-building activity in human history.\n• Solve a real problem together: give teams budget and autonomy to fix something actually broken.\n• Celebrate wins publicly: recognition is free and builds more loyalty than any trust fall.\n• Kill the mandatory fun. Make team events optional. The people who show up will actually want to be there.\n• In SEA offices, karaoke and shared meals are the default — and they work because they're culturally authentic, not HR-mandated."])],
     ("Need a break from office 'fun'?","Try our daily almanac — see what the day has in store for you.","/almanac.html","Check Today's Almanac →"),
     ["Team Building","Mandatory Fun","Office Culture","Corporate Activities","Workplace Events","Team Bonding"],
     [("Meeting Hell","/blog/en/office-03-meeting-hell.html"),("Open Office","/blog/en/office-05-open-office.html"),("Corporate Gaslighting","/blog/en/office-09-corporate-gaslighting.html")]
    ),

    # === 15: Burnout ===
    ("office-15-burnout-recovery",
     "Burnout Is Real: Warning Signs, Recovery Plan, and How to Prevent Relapse",
     "The WHO classifies burnout as an occupational phenomenon. 77% of workers have experienced it. Learn to recognize the three dimensions of burnout, create a recovery plan, and set up systems to prevent it coming back.",
     "burnout recovery, workplace burnout, mental health at work, stress management, career burnout, burnout symptoms, work stress recovery",
     "8 min read",
     [("Burnout Isn't Just 'Being Tired'",
       ["The World Health Organization officially classifies burnout as an occupational phenomenon with three dimensions: emotional exhaustion (feeling drained, empty), cynicism/depersonalization (detachment from your job and colleagues), and reduced professional efficacy (feeling incompetent, unproductive). If you've been feeling 'off' at work for weeks or months, you might be hitting all three.",
        "A 2025 Deloitte survey found that 77% of professionals have experienced burnout at their current job. 51% said it impacted their physical health. 42% left their job because of it. This isn't a personal failing. It's an epidemic."]),
      ("The Recovery Plan",
       ["• Week 1: Stop the bleeding. Take PTO — real PTO, no email. Sleep 8+ hours. Eat meals that aren't at your desk.\n• Week 2: Identify the source. Is it workload? Lack of control? Insufficient recognition? Unfair treatment? Values mismatch? Pinpoint it.\n• Week 3: Make changes. Delegate. Say no. Set boundaries. Consider a role change. These aren't selfish — they're survival.\n• Week 4+: Build systems. Create routines that protect your energy. Morning exercise. No-email evenings. A hobby that has nothing to do with work.",
        "In Southeast Asia, burnout is amplified by cultural factors: the stigma around mental health, the expectation of constant availability (Line/WhatsApp at all hours), and the pressure to financially support extended family. Recovery here requires not just individual action but family conversations about boundaries."])],
     ("Running on empty?","Take a moment for yourself. Our daily fortune readings offer a small escape.","/fortune.html","Get Today's Fortune →"),
     ["Burnout","Mental Health","Workplace Stress","Career Recovery","Self Care","Work Life Balance","Emotional Health"],
     [("Quiet Quitting","/blog/en/office-01-quiet-quitting.html"),("Remote Work Isolation","/blog/en/office-06-remote-isolation.html"),("Unlimited PTO Trap","/blog/en/office-07-unlimited-pto.html")]
    ),

    # === 16: Singapore Office ===
    ("office-16-singapore-office",
     "Singapore Office Survival Guide: Hierarchy, Face, and the 'Can' Culture Explained",
     "Working in Singapore? Understand the unwritten rules: why hierarchy matters, how 'face' shapes every interaction, the real meaning of 'can,' and how to navigate a workplace where nobody says 'no' directly.",
     "singapore office culture, workplace hierarchy, face culture, asian office etiquette, working in singapore, SEA workplace, office survival guide",
     "7 min read",
     [("Why Singapore Office Culture Is Unique",
       ["Singapore's office culture is a fascinating hybrid: Western corporate efficiency meets Asian hierarchical values, seasoned with British colonial legacy and the relentless pragmatism of a nation that went from fishing village to global financial hub in one generation. The result is an environment where meetings start on time (Germanic precision) but decisions are made after the meeting (Asian consensus). Where your boss is addressed by title, not first name — but everyone switches to Singlish the moment the foreign client leaves."]),
      ("The Hierarchy: Titles Matter More Than You Think",
       ["In American offices, a first-name-basis flat hierarchy signals approachability. In Singapore, it signals disrespect. Your boss is 'Mr. Tan' or 'Director Lee,' not 'David.' Junior staff don't challenge senior staff in meetings — they have private conversations afterward. The org chart isn't just organizational. It's a social map. Ignore it at your career's peril.",
        "That said, Singaporean hierarchy is more meritocratic than in many Asian cultures. Good ideas get heard — they just get heard through the proper channels. The path to influence isn't speaking up in meetings. It's building relationships with decision-makers one-on-one."]),
      ("The 'Face' Economy",
       ["'Face' (面子) is the currency of Asian workplaces. Giving face means publicly acknowledging someone's contribution. Losing face means being criticized or corrected in front of others. Causing someone to lose face — even unintentionally — can destroy a working relationship permanently. In practice: praise in public, critique in private. Never say 'you're wrong.' Say 'have we considered another angle?' Frame disagreements as collaborative exploration, not correction."]),
      ("The 'Can' Codex",
       ["• 'Can' = Yes.\n• 'Can lah' = Yes, definitely.\n• 'Can...' (trailing off) = I'll try, no promises.\n• 'Can or not?' = Is this acceptable?\n• 'See how' = Probably not, I'm being polite.\n• 'Cannot' = No. Direct. Rare. Means something is seriously wrong.\n• 'Cannot lah' = Absolutely impossible, don't ask again.",
        "For expats and foreigners, learning to distinguish 'can' from 'can lah' from 'can...' is more important than learning any technical skill. It's the difference between delivering what was actually requested and delivering what you thought was requested."]),
      ("The Makan Connection",
       ["In Singapore, the most important business conversations happen over food. Hawker center lunches, kopi breaks, after-work supper. The office meeting is for confirmation. The real alignment happens over chicken rice. Don't skip the food invitations. They're not optional social events — they're where actual work gets done."])],
     ("Confused about your career direction?","Our BaZi readings offer clarity based on ancient Chinese wisdom.","/fortune/bazi.html","Check Your BaZi →"),
     ["Singapore Office","Workplace Culture","Asian Business","Face Culture","Office Etiquette","SEA Workplace"],
     [("SEA Workplace Drama","/blog/en/office-17-grab-gossip.html"),("Micromanagement","/blog/en/office-13-micromanagement.html"),("Passive Aggression","/blog/en/office-02-passive-aggressive.html")]
    ),

    # === 17: Grab & Gossip ===
    ("office-17-grab-gossip",
     "Grab Rides and Office Gossip: Navigating Southeast Asian Workplace Drama",
     "From Manila to Bangkok to Jakarta, SEA office culture has its own flavor of workplace drama. Grab rides, office gossip chains, and navigating the 'marites' culture. A practical guide for anyone working in Southeast Asia.",
     "SEA office culture, workplace gossip, Grab office, office drama, southeast asia workplace, office politics, Philippine office, Indonesian office, Thai office",
     "6 min read",
     [("The Grab Ride: SEA's True Boardroom",
       ["In Southeast Asia, the most honest conversations don't happen in meeting rooms. They happen in Grab cars. The 45-minute ride from the office to the client site is where junior staff tell senior staff what they really think. Where colleagues share frustrations they'd never voice in the office. Where the real organizational chart — the one based on trust, not titles — reveals itself.",
        "Why Grab? Because it's neutral territory. Nobody owns the car. The driver is a stranger who will never enter your office. The combination of privacy and impermanence creates a confessional effect. Every SEA office veteran knows: if you want the truth, get in the Grab."]),
      ("The Marites Phenomenon: Office Gossip Networks",
       ["In the Philippines, 'Marites' — from 'mare, anong latest?' (girl, what's the latest?) — has become shorthand for the office gossip network. Every floor has a Marites. She knows who's resigning, who's dating whom, which department is getting reorganized, and who messed up the client presentation. The Marites isn't malicious — she's the informal information infrastructure of the office.",
        "In Indonesia, it's 'bisa bisikan' (whispering). In Thailand, it's the LINE group chat that includes everyone except the boss. Across SEA, informal communication networks operate faster and more accurately than any official memo. Smart managers don't fight the gossip network. They feed it accurate information."]),
      ("Navigating Without Getting Burned",
       ["• Never put anything in the office WhatsApp/LINE group you wouldn't want screenshot and forwarded.\n• The Marites is a source, not a confidante. Listen, don't contribute.\n• Complaints about work belong in person, not in chat. Digital is forever.\n• If you hear gossip about yourself, don't react publicly. The storyteller wants a reaction. Deny them.\n• Build your own trust network: 3-5 people you can speak honestly with, in person, off the record."]),
      ("Regional Office Personality Types",
       ["• The Jakarta Networker: knows everyone across departments. Gets things done through relationships, not processes.\n• The Manila Hype Person: brings energy, music, and snacks. The team's emotional thermostat.\n• The Bangkok Diplomat: never says no directly. Masters of the graceful deflection.\n• The KL Pragmatist: blunt, efficient, food-motivated. Will solve problems during lunch.\n• The Singapore Strategist: plans five moves ahead. Treats career like chess. Respects the game."])],
     ("Office politics getting to you?","A Tarot reading can give you the perspective you need.","/fortune/tarot.html","Get a Tarot Reading →"),
     ["SEA Office","Workplace Gossip","Office Politics","Philippines Office","Indonesia Office","Thailand Office","Malaysia Office"],
     [("Singapore Office Guide","/blog/en/office-16-singapore-office.html"),("CC Culture","/blog/en/office-12-cc-culture.html"),("Passive Aggression","/blog/en/office-02-passive-aggressive.html")]
    ),

    # === 18: Salary Negotiation ===
    ("office-18-salary-negotiation",
     "Salary Negotiation Scripts: Exactly What to Say to Get a Raise (Word-for-Word)",
     "Stop leaving money on the table. Word-for-word scripts for asking for a raise, negotiating a job offer, responding to 'what's your salary expectation,' and handling rejection. Based on real negotiation research.",
     "salary negotiation, ask for raise, job offer negotiation, salary scripts, career growth, workplace negotiation, how to negotiate salary",
     "7 min read",
     [("The $1 Million Mistake",
       ["Research from Carnegie Mellon shows that failing to negotiate your first salary can cost you $1 million in lifetime earnings. The math: a $5,000 higher starting salary, compounded at 3% annual raises over a 40-year career, equals $377,000. If you negotiate every raise afterward from that higher base, it crosses $1 million. Every time you don't negotiate, you're not just losing this year's money — you're losing every future year's compounding.",
        "Yet only 39% of workers negotiate their salary. The #1 reason: 'I didn't know what to say.' So here are the exact scripts."]),
      ("The Job Offer Script",
       ["When they give you a number: 'Thank you — I'm really excited about this opportunity. Based on my research and the value I'll bring with [specific skill], I was expecting something closer to [your number]. Is there flexibility in the budget?' Key elements: express enthusiasm (you want the job), cite specific value (not 'I need more money'), give a number (not a range — ranges invite the bottom), ask an open question (not a demand)."]),
      ("The 'What's Your Salary Expectation?' Script",
       ["Never give the first number. Respond: 'I'm flexible depending on the total package — including benefits, bonus, and equity. I'd love to hear the budgeted range for this role first to make sure we're aligned.' This flips the negotiation. Now they have to reveal their range. If they push: 'Based on market data for similar roles in [city], I'm seeing a range of [X-Y]. Does that align with your budget?'"]),
      ("The Raise Script (For Your Current Job)",
       ["Timing: schedule a specific meeting. Don't ambush your boss. Opening: 'I'd like to discuss my compensation based on my contributions and the current market.' Present your brag document. Give a specific number: 'Based on my contributions and market rates, I'm looking at [amount], which is a [X]% adjustment.' If they say no: 'I understand. What specific milestones would I need to hit for us to revisit this in six months?' Turn the no into a roadmap.",
        "In SEA offices: frame as 'market alignment' not 'I deserve more.' Hierarchy makes direct self-advocacy uncomfortable. Depersonalizing the request preserves face for everyone."])],
     ("Want to know when luck is on your side?","Our BaZi career reading reveals your wealth and career cycles.","/fortune/bazi.html","Discover Your Career Luck →"),
     ["Salary Negotiation","Ask For Raise","Job Offer","Career Growth","Workplace Money","Negotiation Scripts"],
     [("Performance Review Guide","/blog/en/office-08-performance-review.html"),("Imposter Syndrome","/blog/en/office-10-imposter-syndrome.html"),("Toxic Boss","/blog/en/office-04-toxic-boss.html")]
    ),

    # === 19: Great Resignation 2.0 ===
    ("office-19-great-resignation",
     "The Great Resignation 2.0: Why Everyone's Quitting Again (And Should You?)",
     "Post-pandemic job-hopping is back. 52% of US workers are considering leaving their jobs in 2026. Learn the new rules of the job market, how to know if you should stay or go, and the 4-question framework.",
     "great resignation, quit job, career change, job market 2026, leave job, career pivot, workplace trends, quit or stay",
     "6 min read",
     [("The Numbers: It's Happening Again",
       ["A 2026 LinkedIn Workforce Report found that 52% of US professionals are considering leaving their current jobs this year — the highest since the original Great Resignation of 2021-2022. The drivers are different this time. In 2021, people quit for flexibility and remote work. In 2026, they're quitting because of RTO mandates, wage stagnation against persistent inflation, and a growing sense that loyalty to one company is a losing strategy.",
        "The data is clear: job-hoppers earn 25-35% more over a 10-year period compared to those who stay at one company. The old career advice — 'stay loyal, work hard, get promoted' — has been replaced by a new reality: 'switch every 2-3 years, negotiate each jump, maximize earnings.' Your employer isn't loyal to you. Why should you be loyal to them?"]),
      ("The 4-Question Framework: Should You Stay or Go?",
       ["1) Am I learning? If you haven't developed a new skill in the last 6 months, you're stagnating.\n2) Am I earning? Are you paid at or above market rate? Check Levels.fyi, Glassdoor, and Blind.\n3) Am I growing? Is there a clear path to the next level, or are you waiting for someone to retire?\n4) Am I happy? Not every day — that's unrealistic. But overall, do you dread Monday morning?",
        "Score: 4 yes = stay. 3 yes = negotiate improvements. 2 yes = start looking. 0-1 yes = update your resume tonight."]),
      ("The SEA Angle: Regional Job Market Dynamics",
       ["Southeast Asia's job market is different from the US in key ways. The tech sector is booming (Singapore alone added 80,000 tech jobs in 2025). Remote work for global companies means SEA talent can earn US-adjacent salaries while living in lower-cost countries. Filipinos, Indonesians, and Vietnamese workers are increasingly being hired directly by US and European companies — the global talent market has never been more accessible."])],
     ("Thinking about a career change?","Our I Ching readings offer ancient wisdom for life's big decisions.","/fortune/iching.html","Consult the I Ching →"),
     ["Great Resignation","Quit Job","Career Change","Job Market","Career Pivot","Workplace Trends","Job Hopping"],
     [("Salary Negotiation","/blog/en/office-18-salary-negotiation.html"),("Quiet Quitting","/blog/en/office-01-quiet-quitting.html"),("Burnout Recovery","/blog/en/office-15-burnout-recovery.html")]
    ),

    # === 20: Work-Life Balance ===
    ("office-20-boundaries",
     "Work-Life Balance Is a Myth — Here's How to Create Boundaries That Actually Work",
     "Work-life balance implies a perfect 50/50 split. It doesn't exist. Instead, learn to build sustainable boundaries — the kind that survive 9 PM Slack messages, 'urgent' weekend emails, and always-on culture.",
     "work life balance, workplace boundaries, always on culture, work boundaries, burnout prevention, digital detox, work separation",
     "6 min read",
     [("Why 'Balance' Is the Wrong Goal",
       ["The phrase 'work-life balance' implies a scale — work on one side, life on the other. Equal weight. Perfect equilibrium. This metaphor has probably caused more guilt than any other corporate wellness concept. Real life doesn't distribute evenly. Some weeks are 80% work (launch week, quarter close). Some weeks are 20% work (vacation, slow season). The goal isn't balance. The goal is sustainability over time.",
        "The better metaphor: work-life rhythm. Like breathing — inhale (intense work), exhale (recovery). You don't judge breathing by whether inhale and exhale are perfectly balanced. You judge it by whether you're still alive. Same with work."]),
      ("The Boundary Playbook",
       ["• The Hard Stop: Pick an end time. When it arrives, close the laptop. Physically. The first week will feel like withdrawal. By week 3, it's freedom.\n• The Notification Kill: Turn off all work notifications on your phone. Slack, email, Teams — gone. If it's truly urgent, they'll call. They almost never call.\n• The Transition Ritual: After work, do something that signals 'work is over' to your brain. Walk the dog. Go to the gym. Cook dinner. Without a ritual, your brain stays in work mode all evening.\n• The 'No' Muscle: Practice saying 'I can't take that on right now' to small requests. Build the muscle on low-stakes asks so it's strong when the big ones come."]),
      ("The Always-On Culture: America vs. SEA",
       ["American office culture expects email responses within 24 hours. SEA office culture — especially in Singapore, Manila, and Jakarta — often expects WhatsApp/Line responses within 24 MINUTES. The always-on expectation in Southeast Asia is even more intense because the tools are more personal. Your boss doesn't email you at 9 PM. They LINE you. And they can see when you've read it.",
        "The fix for SEA workers: set explicit communication hours. 'I'm available on LINE from 8 AM to 7 PM. After that, I'll respond the next business day.' Say it. Enforce it. Your boss will respect you more, not less. Boundaries signal professionalism, not laziness."])],
     ("Ready to set better boundaries?","Sometimes the universe supports your decisions. Check today's fortune.","/fortune.html","Get Today's Fortune →"),
     ["Work Life Balance","Workplace Boundaries","Always On Culture","Digital Detox","Work Separation","Mental Health","Burnout Prevention"],
     [("Quiet Quitting","/blog/en/office-01-quiet-quitting.html"),("Burnout Recovery","/blog/en/office-15-burnout-recovery.html"),("Unlimited PTO Trap","/blog/en/office-07-unlimited-pto.html")]
    ),
]

print(f"Generating {len(posts)} posts...")
for file, title, desc, keys, read_time, sections, cta, tags, related in posts:
    make(file, title, desc, keys, "June 26, 2026", read_time, sections, cta, tags, related)
    print(f"  ✅ {file}")

print(f"\n🎉 Done! {len(posts)} posts generated in blog/en/")
