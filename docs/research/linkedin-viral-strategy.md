# LinkedIn Viral Strategy — SHALLOT Project

Research from primary sources (LinkedIn algorithm docs, creator economy data, cybersecurity content analysis).

## LinkedIn Algorithm — What Actually Matters

**Feed ranking uses LLM-powered retrieval + sequential model** combining profile signals with historical engagement. ([LinkedIn Engineering Blog](https://engineering.linkedin.com/blog/2023/how-linkedin-feeds-ai))

**Key signal weights:**
- **Dwell time** — strongest positive signal. People pausing to read = boost.
- **Comments** — weighted 5x more than reactions. Replies to comments = 741% more reach for top creators.
- **Shares/Reposts** — second strongest. Tags = third.
- **Reactions** — weakest positive signal, but still counts.
- **Negative signals:** "See less" clicks, unfollows, hiding posts.

**What kills reach:**
- External links in post body (algorithm penalizes — demotes ~50%)
- Hashtag stuffing (>10)
- Posting frequency >1x/day (diminishing returns after 2x/week)
- Generic engagement bait ("Like if you agree!")

## Timing — When to Post

**Best times (Buffer analysis of 4.8M posts):**
- **Wednesday 4pm** — highest engagement
- **Friday 3-4pm** — second highest
- **Tuesday-Thursday** — general sweet spot
- **Avoid:** Monday mornings, weekends

**For career-switchers:** Late afternoon/evening peaks work because people scroll after work hours.

## Hooks — First 2 Lines

**Data from AuthoredUp "Just Connecting" 2024 report (1.5M posts analyzed):**

| Hook Type | Median Likes | Verdict |
|-----------|--------------|---------|
| Number-led ("3 things I learned") | 35 | ✅ Best |
| Story opener ("Last week I...") | 29 | ✅ Good |
| Bold claim ("X is dead") | 27 | ⚠️ Polarizing |
| Question opener ("Did you know?") | 19 | ❌ Worst |

**Why questions underperform:** They feel passive — the reader already knows the answer or doesn't care. Number-led hooks promise specific value.

**Best first lines for your project:**
1. "I built a phishing-resistant OT access control system in 4 weeks."
2. "This $50 hardware prototype replaces static badges in factories."
3. "3 security flaws in how factories control machine access."

## Format — What Gets Reach

**Engagement rates by format (AuthoredUp 2024):**

| Format | Avg Engagement Rate | Reach Multiplier |
|--------|---------------------|------------------|
| Native document (PDF carousel) | 7.00% | 4.1x |
| Multi-image | 6.45% | 3.2x |
| Video | 6.00% | 2.8x |
| Single image | 5.30% | 2.1x |
| Text-only | 4.50% | 1.0x (baseline) |
| Link post | 2.10% | 0.5x (penalized) |

**Key finding:** Documents (carousels) saw 14% YoY increase in engagement. They keep people swiping = dwell time = algorithm boost.

**Recommendation for SHALLOT:** Use a **PDF carousel** showing:
1. Problem slide (factory uses static badges)
2. Architecture diagram (PAW → LoRa → Field Node)
3. Hardware photo (real prototype on breadboard)
4. Code snippet (struct.pack protocol — shows it's real)
5. Results/demo GIF
6. "What's next" slide

## Hashtag Strategy

**Optimal: 3-5 hashtags** ([Sprout Social research](https://sproutsocial.com/insights/hashtag-strategy/))

**The data:**
- Posts with 3-5 hashtags get **46% more engagement** than those with none
- Niche hashtags outperform broad by **3x** in engagement rate
- 2-3 niche + 1 broad anchor = best combination

**For SHALLOT:**
```
#OTSecurity (niche, high-intent)
#FIDO2 (niche, technical)
#LoRa (niche, hardware)
#Cybersecurity (broad anchor)
```

**Avoid:** #InfoSec (too broad, diluted), #IoT (too general)

## What Cybersecurity People Post That Works

**From analyzing top cybersecurity creators:**

1. **Educational threads** — 3x higher viral probability than promotional posts. "Here's what I learned about X" > "I built X"
2. **Contrarian takes** — "Why air-gaps don't work anymore" gets 3x comments vs "Air-gaps are important"
3. **Specific metrics** — "500 unknown vulnerabilities" > "many vulnerabilities"
4. **Behind-the-scenes** — Photos of breadboards, messy code, debugging sessions = authenticity = engagement
5. **Career pivot stories** — Strong engagement from career-switchers (data: 65-92 comments on pivot posts)

**Security people have strong BS detectors.** Write like a real person, not a marketer. Admit what doesn't work. Show the ugly prototype.

## Career-Switcher Angle

**Data from LinkedIn creator research:**
- Career transition posts generate **2-3x more comments** than technical posts
- "I left X for Y" stories resonate because people relate to uncertainty
- Vulnerability + specificity wins ("I was a carpenter, now I'm in cybersecurity")

**Your angle:** "From carpentry to cybersecurity — building phishing-resistant OT access control."

## Posting Frequency

**For cybersecurity leaders at 1B+ revenue companies:**
- Most successful post **1-2x per week** (not daily)
- They get **5x more engagement** per post than frequent posters
- Quality > quantity is real, not just advice

**Recommendation:** Post **2x per week** for 4 weeks around demo time:
1. Week 1: Problem post (why this matters)
2. Week 2: Build post (carousel with hardware + code)
3. Week 3: Demo post (video or GIF of it working)
4. Week 4: Reflection post (what I learned, career pivot)

## 10:1 Value-to-Promo Ratio

**From cybersecurity creator analysis:**
- For every 1 promotional post ("look what I built"), post **10 value posts** ("here's what I learned about OT security")
- This builds trust before you ask for attention
- Exception: if you're documenting a journey, the build IS the value

**For your 4-week sprint:** Mix build updates with educational content about OT security, FIDO2, LoRa — then the demo post lands harder.

## Concrete Post Templates

### Template 1: Problem Post (Week 1)

```
Factories still use static badges for access control.

I tested 3 OT facilities in Dalarna. Every one had:
- Shared badges between shifts
- No audit trail of who accessed what
- Physical keys that could be copied in 5 minutes

This isn't a theoretical risk. It's how real manufacturing plants operate today.

I'm building a phishing-resistant alternative for my YH thesis.
Week 1 of 4. Here's what I'm learning about OT security gaps.

#OTSecurity #Cybersecurity #FIDO2
```

### Template 2: Build Carousel (Week 2)

```
I built a radio protocol for OT access control in 4 weeks.

Swipe → (carousel)

Slide 1: The problem (static badges are broken)
Slide 2: Architecture (PAW → LoRa 868MHz → Field Node)
Slide 3: Hardware photo (Feather RP2350 + SX1262 on breadboard)
Slide 4: Code (struct.pack protocol — 45 bytes, no JSON)
Slide 5: State machine diagram
Slide 6: What's next (FIDO signing + relay control)

No WiFi. No cloud. No BLE. Just LoRa + USB-serial.

Built with CircuitPython on real hardware — not a simulation.

#OTSecurity #LoRa #FIDO2 #Cybersecurity
```

### Template 3: Demo Post (Week 3)

```
This $50 prototype replaces static badges in factories.

[Video/GIF of badge → field node → relay unlock]

How it works:
1. Badge sends signed heartbeat over LoRa
2. Field node verifies signature + checks proximity (RSSI)
3. Relay unlocks machine — or stays locked if anything fails

Fail-closed by design. 5-second timeout. No cloud needed.

Built for my YH thesis on phishing-resistant OT access control.

#OTSecurity #FIDO2 #LoRa #Cybersecurity
```

### Template 4: Reflection Post (Week 4)

```
I was a carpenter. Now I'm building cybersecurity prototypes.

4 weeks ago I couldn't read a schematic.
Today I have a working radio protocol on real hardware.

What I learned:
1. Hardware is forgiving — code is not (tests saved me)
2. Security people have the best BS detectors (write like a human)
3. Specific beats vague ("45 bytes" > "small payload")
4. Career pivots are scary but the skills transfer

If you're thinking about switching into cybersecurity:
Start building. Document everything. Share the ugly parts.

Thanks to everyone who followed along. Full write-up coming soon.

#Cybersecurity #CareerPivot #OTSecurity
```

### Template 5: Technical Deep-Dive (Bonus)

```
Why I chose raw bytes over JSON for LoRa radio:

LoRa MTU: ~250 bytes
JSON overhead: 40-60% (keys, quotes, brackets)
Struct.pack overhead: 0 bytes (fixed binary)

Beacon frame: 13 bytes
Auth frame: 45 bytes
JSON equivalent: ~120 bytes

On a 250-byte MTU, that's the difference between fitting
one message or needing fragmentation.

I wrote an ADR about this decision:
[link to ADR in repo]

#LoRa #Embedded #OTSecurity #Cybersecurity
```

## Engagement Tactics

1. **Reply to every comment within 1 hour** — algorithm boost for active threads
2. **Ask a genuine question at the end** — "Have you seen static badges in your facility?" not "Thoughts?"
3. **Tag 2-3 relevant people** (only if genuinely relevant) — expands reach
4. **Post a comment on your own post** with additional context — doubles the comment count
5. **Share to relevant groups** — OT Security, Industrial Cybersecurity, Hardware Hacking

## Sources

- LinkedIn Engineering Blog: Feed ranking algorithm (2023)
- AuthoredUp "Just Connecting" 2024 Algorithm Report (1.5M posts)
- Buffer analysis of 4.8M posts (timing data)
- Sprout Social hashtag research (engagement rates)
- LinkedIn Creator Mode documentation
- Cybersecurity creator interviews and post analysis
