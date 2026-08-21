#!/usr/bin/env python3
"""Generate the Jesse Rich Ministries podcast RSS feed (Spotify/Apple compatible)."""
import os, subprocess
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).parent
AUDIO = BASE / "audio"
PUB = "https://bmob222.github.io/jrm-podcast"
OWNER_EMAIL = "customerservice@enemiesbynature.com"   # Spotify verification email

CHANNEL_DESC = (
    "No-compromise, faith-building teaching from Pastor Jesse Rich to help you live the victorious, "
    "abundant life Jesus promised. Each episode takes you straight to the Word of God on faith, divine "
    "healing, biblical prosperity, and total victory over fear, doubt, and discouragement. Whether you're "
    "facing a mountain or believing for a breakthrough, Pastor Jesse will stir your faith to take God at His "
    "Word — and expect Him to move.\n\n"
    "Worship with us in person: Sundays 9:30 AM & Tuesdays 7:00 PM at the Residence Inn, 942 Main Street, "
    "Downtown Hartford, CT. For more messages and to partner with this ministry, visit JesseRichMinistries.com. "
    "Jesse Rich Ministries is a 501(c)(3) nonprofit."
)

CTA = ("\n\nWorship with us — Sundays 9:30 AM & Tuesdays 7:00 PM in Hartford, CT. "
       "More at JesseRichMinistries.com.")

# newest first; pubDate RFC-822
EPISODES = [
    {"file": "ep24_2026-08-20_camp-meeting-thu-pm.mp3", "ep": 24,
     "title": "Camp Meeting Day 5 Evening: Covenant Prosperity — Isaac Sowed in the Year of Famine",
     "pub": "Thu, 20 Aug 2026 19:00:00 -0400",
     "desc": ("Closing night of camp meeting. A teaching on covenant prosperity: when we bring the "
              "tithe we worship God and acknowledge that everything we have is His — and everything "
              "He has is ours, a covenant sealed in the blood of Jesus. From the patriarchs: Abraham "
              "very rich in cattle, silver and gold; Isaac exceedingly rich because he sowed in the "
              "year of famine and received a hundredfold the same year. The believer's covenant does "
              "not depend on natural circumstances — famine, inflation or recession — because in "
              "Christ we are on a whole other system than the world's."),
     },
    {"file": "ep23_2026-08-20_camp-meeting-thu-am.mp3", "ep": 23,
     "title": "Camp Meeting Day 5 Morning: Give Earnest Heed — The Grace of Giving",
     "pub": "Thu, 20 Aug 2026 10:30:00 -0400",
     "desc": ("Morning session on Hebrews 2:1 and 2 Corinthians 8: give earnest heed to the things "
              "you have heard, lest at any time you let them slip — even great ministers have let "
              "the Word slip away. Then into the grace of giving: the churches of Macedonia, whose "
              "deep poverty abounded unto the riches of their liberality, and Jesus, who though He "
              "was rich became poor for our sakes, that we through His poverty might be rich. "
              "Worshiping the Lord with the tithe says: everything I have is Yours — and everything "
              "You have is mine."),
     },
    {"file": "ep22_2026-08-19_camp-meeting-wed-pm.mp3", "ep": 22,
     "title": "Camp Meeting Day 4 Evening: The Power of the Tithe — Worship the Lord with Your Increase",
     "pub": "Wed, 19 Aug 2026 19:00:00 -0400",
     "desc": ("An evening teaching on the tithe: the first ten percent of all your increase, holy "
              "unto the Lord — not just a donation, but worship that goes out before the Father. "
              "We don't only sing, praise and lift our hands; we worship God with the tithe and the "
              "offerings. There is power in the freedom of tithing — it is not bondage, it is "
              "freedom — and the covenant believer who understands that power finds it easy to "
              "honor God with the firstfruits."),
     },
    {"file": "ep21_2026-08-19_camp-meeting-wed-am.mp3", "ep": 21,
     "title": "Camp Meeting Day 4 Morning: Sow in the Famine — Show Your Faith by Your Actions",
     "pub": "Wed, 19 Aug 2026 10:30:00 -0400",
     "desc": ("If you have a need, sow a seed. A morning teaching on giving in hard times: when "
              "the bank account is low is not the time to back off but the time to show your faith "
              "by your words and your actions — because Jesus is looking for faith, and it is "
              "through faith and patience that we inherit the promises. From Elijah and the widow "
              "of Zarephath — a single mother at the bottom of the barrel whose last meal became a "
              "supply through the famine — and the Macedonian churches whose deep poverty did not "
              "keep them from giving."),
     },
    {"file": "ep20_2026-08-18_camp-meeting-tue-pm.mp3", "ep": 20,
     "title": "Camp Meeting Day 3 Evening: This Is Real — Tongues, Interpretation, and Believing for Miracles",
     "pub": "Tue, 18 Aug 2026 19:00:00 -0400",
     "desc": ("An evening service opening with a remarkable testimony: a message in tongues and "
              "its interpretation checked by an AI company worker — the tongue was an African "
              "dialect and the interpretation was word for word. 'This is real.' The service moves "
              "into the grace of God that always works, expectation for miracles all week, and "
              "God showing His people who they are in Christ — because when the presence of God "
              "and faith get together, miracles start happening."),
     },
    {"file": "ep19_2026-08-18_camp-meeting-tue-am.mp3", "ep": 19,
     "title": "Camp Meeting Day 3 Morning: There Has to Be More — Breaking the Poverty Mindset",
     "pub": "Tue, 18 Aug 2026 10:30:00 -0400",
     "desc": ("A morning teaching confronting religious tradition that says poverty is godliness — "
              "'you keep them humble, Lord, we'll keep them poor.' A congregation rarely rises "
              "above the economic level of its pastor, which is exactly why the devil wants the "
              "shepherd kept poor. From a testimony of growing up hearing only salvation preached "
              "every Sunday — 'I love being saved, but there has to be more' — into what the Word "
              "actually teaches about God's will for His children to prosper and be in health."),
     },
    {"file": "ep18_2026-08-17_camp-meeting-mon-pm.mp3", "ep": 18,
     "title": "Camp Meeting Day 2 Evening: A Good Father — Healing and Financial Miracles",
     "pub": "Mon, 17 Aug 2026 19:00:00 -0400",
     "desc": ("Our good, good Father wants His children healthy and prosperous — 'I wish above all "
              "things that thou mayest prosper and be in health' (3 John 2). If we being evil know "
              "how to give good gifts to our children, how much more our Father in heaven. An "
              "evening of believing for miracles, with testimonies of healings in meetings across "
              "Europe, Armenia, Portugal, Spain, London, Greece and Ireland this year, and a look "
              "at Jesus' financial miracles — feeding the five thousand and more — showing both "
              "sides of God's miracle provision: healing and prosperity."),
     },
    {"file": "ep17_2026-08-17_camp-meeting-mon-am.mp3", "ep": 17,
     "title": "Camp Meeting Day 2 Morning: Run Doubt Off — Believe You Receive When You Pray",
     "pub": "Mon, 17 Aug 2026 10:30:00 -0400",
     "desc": ("This is where people usually crash and burn on believing God: they let doubt in. A "
              "morning teaching on Mark 11:24 — believe you receive when you pray — and what to do "
              "when the devil brings thoughts that you don't have it yet: tell doubt to go in "
              "Jesus' name. Make your mind up before you release your faith that you're in for the "
              "long haul, standing on nothing but God's Word. Pastor Jesse also shares his own "
              "story of being born again in a Pentecostal church having never once heard the "
              "gospel, an altar call, or hands laid on the sick in the church he grew up in."),
     },
    {"file": "ep16_2026-08-16_camp-meeting-day1.mp3", "ep": 16,
     "title": "Camp Meeting Night 1: Speak to the Mountain — Take Full Responsibility for Your Life",
     "pub": "Sun, 16 Aug 2026 19:00:00 -0400",
     "desc": ("Opening night of camp meeting. From Mark 11:23 and the Gospels, Pastor Jesse Rich "
              "teaches that everything talks to you — sickness, lack, the storm — and the believer "
              "answers back the way Jesus did: speaking to the mountain in Jesus' name. Jesus "
              "answered the fig tree, spoke to the storm, and said whosoever shall SAY unto this "
              "mountain, Be thou removed, and shall not doubt in his heart, shall have whatsoever "
              "he saith. A teaching on using your God-given authority instead of excuses: you can "
              "have an excuse, but you will not have a testimony. Includes a testimony of a "
              "little girl instantly healed when her mother commanded it in the name of Jesus, "
              "why God wants the Word in you so it comes out when your mind is not thinking, and "
              "a closing invitation to receive Jesus Christ as Lord."),
     },
    {"file": "ep15_2026-08-11_evening-live.mp3", "ep": 15,
     "title": "Speak to Your Mountain — Faith as a Grain of Mustard Seed",
     "pub": "Tue, 11 Aug 2026 19:00:00 -0400",
     "desc": ("From Matthew 15, 17 and 21: Pastor Jesse Rich teaches that faith is released "
              "with words. Not what goes into the mouth defiles a man, but what comes out — "
              "and what comes out of the mouth proceeds from the heart. When the disciples "
              "could not cure the lunatic son, Jesus pointed to their unbelief: if ye have "
              "faith as a grain of mustard seed, ye shall SAY unto this mountain, Remove "
              "hence to yonder place, and it shall remove, and nothing shall be impossible "
              "unto you. A Tuesday evening teaching on speaking to the mountain instead of "
              "talking about it, keeping your words in agreement with God's Word, and "
              "putting your faith to work with your mouth."),
     },
    {"file": "ep14_2026-08-09_sunday-service.mp3", "ep": 14,
     "title": "It Wasn't God That Did This — Loosed from a Spirit of Infirmity",
     "pub": "Sun, 09 Aug 2026 12:00:00 -0400",
     "desc": ("Pastor Jesse Rich teaches from Matthew 17 and Luke 13 on where sickness and "
              "oppression really come from — and Who sets people free. The woman bowed over "
              "eighteen years was a daughter of Abraham 'whom Satan hath bound' — it wasn't God "
              "that made her that way; Jesus called her, laid hands on her, and she was made "
              "straight and glorified God. From Luke 10:19 he teaches the believer's authority "
              "over all the power of the enemy: casting down the devil's thoughts and "
              "suggestions in Jesus' name, staying built up by praying in the Spirit and a "
              "lifestyle of praise, and guarding your family through prayer. Includes his "
              "personal 9/11 testimony — 'don't go downtown, go uptown' — of how the inward "
              "witness of the Holy Spirit kept him out of the towers, teaching from Acts 5 and "
              "Acts 16 on dealing with demonic influence, the ministry of laying on of hands, "
              "and a closing prayer to receive Jesus Christ as Lord."),
     },
    {"file": "ep13_2026-08-02_sunday-message.mp3", "ep": 13,
     "title": "Attend to His Word — Health to All Your Flesh",
     "pub": "Sun, 02 Aug 2026 12:00:00 -0400",
     "desc": ("Pastor Jesse Rich teaches from Proverbs 4:20-22 on attending to God's Word — putting "
              "the Word first, inclining your ear to it, and reading the scriptures out loud so your "
              "own ears hear them, because they are life to those that find them and health to all "
              "their flesh. From Matthew 12:34 he shows why: out of the abundance of the heart the "
              "mouth speaks, so what you have put inside your spirit is what comes out of your mouth "
              "when trouble hits and there is no time to think. He points to Jesus in the wilderness "
              "answering Satan with 'it is written,' and teaches that the Word you know is the sword "
              "of the Spirit and your line of defense — if you don't know the Word you can't quote "
              "it, and if you can't quote it you can't defend yourself. He closes on using your mouth "
              "to call those things which be not as though they were, and on God's will for His "
              "children to prosper and be in health."),
     },
    {"file": "ep12_live0020.mp3", "ep": 12,
     "title": "Take Full Responsibility — Stand on Chapter and Verse",
     "pub": "Sun, 26 Jul 2026 12:00:00 -0400",
     "desc": ("Pastor Jesse Rich opens in Ephesians 4:11-15 and 1 Corinthians 12:28 on the ministry "
              "gifts God set in the church and the ministry of helps, teaching that it is God's will "
              "that every one of His children be taught who they are in Christ Jesus so they are no "
              "longer tossed to and fro. He teaches the law of seed and harvest — you cannot buy a "
              "miracle, you plant a seed — and Jesus' promise in Luke 6:38 that what you give comes "
              "back good measure, pressed down, shaken together and running over. He then teaches "
              "healing purchased at the whipping post: Jesus was beaten before He was ever crucified, "
              "He was wounded for our transgressions, and by His stripes you were healed (Isaiah 53:5), "
              "and how partaking of the Lord's body in communion is receiving that healing. The message "
              "closes where it began — take full responsibility for your life, get a Bible, get the "
              "Word inside of you, and speak God's Word over your life.")},
    {"file": "ep11_live0003.mp3", "ep": 11,
     "title": "If You Have Faith, You Shall Say — Calling Things That Be Not",
     "pub": "Sat, 25 Jul 2026 12:00:00 -0400",
     "desc": ("Four times in the Gospels — Matthew 17:20, Matthew 21:21, Mark 11:23 and Luke 17:6 — "
              "Jesus said the same thing: if you have faith, you shall SAY. Pastor Jesse Rich teaches "
              "how to speak to your mountain instead of talking about it, and how Abraham (Romans 4:17) "
              "called those things that be not as though they were until what was dead came alive. "
              "Hear the testimony of the man who spoke to the mulberry tree in his driveway, the "
              "Shunammite woman who wouldn't talk death, and the attorney who refused to accept a "
              "negative report — and kept his job. If you want things different in your life, call "
              "them different: call yourself healthy, call your finances blessed, and put your name in "
              "the scripture. Includes a prayer to receive Jesus Christ as Lord.")},
    {"file": "ep10_live0002.mp3", "ep": 10,
     "title": "Your Youth Renewed Like the Eagle's — The Power of Your Words",
     "pub": "Sat, 25 Jul 2026 11:00:00 -0400",
     "desc": ("Bless the Lord, O my soul, and forget not all His benefits (Psalm 103) — He forgives, "
              "He heals, He redeems, and He renews your youth like the eagle's. Pastor Jesse Rich takes "
              "you from James 3 (the bit, the rudder, and the tongue) to Caleb at 85 still saying "
              "'give me this mountain,' to show that your body — and your whole life — goes the way of "
              "your mouth. Learn to stop speaking against your body and start speaking life over it: "
              "'Let the weak say I am strong,' 'I go from strength to strength,' 'I shall not die but "
              "live and declare the works of the Lord' (Psalm 118:17). Never be embarrassed about your "
              "covenant — stand confident in the Word of God, keep thanking God every day, and make "
              "your mouth work for you. Includes a prayer to receive Jesus Christ as Lord.")},
    {"file": "ep9_live0001.mp3", "ep": 9,
     "title": "By His Stripes You Were Healed — Receiving Divine Healing by Faith",
     "pub": "Sat, 25 Jul 2026 10:00:00 -0400",
     "desc": ("Isaiah prophesied it (Isaiah 53:4-5), Matthew confirmed it (Matthew 8:17), and Peter put "
              "it in the past tense: by whose stripes you WERE healed (1 Peter 2:24). Pastor Jesse Rich "
              "shares how he kept confessing that verse as a brand-new believer until healing became a "
              "reality, and teaches how to receive divine healing by faith — not by being good enough. "
              "From 3 John 2 ('I wish above all things that thou mayest prosper and be in health'), "
              "Mark 11:23 (speak to the mountain), Matthew 18:19 (the point of contact), and James "
              "5:14-15 (the prayer of faith), learn to take authority over sickness and pain the moment "
              "it shows up, keep the switch of faith on, and refuse doubt — because Jesus loves you so "
              "much He doesn't want you hurt. Includes a prayer to receive Jesus Christ as Lord.")},
    {"file": "ep8_a_prayer_project.mp3", "ep": 8,
     "title": "A Prayer Project — Pray for Your Leaders, Pray Over Your Food",
     "pub": "Tue, 21 Jul 2026 12:00:00 -0400",
     "desc": ("From 1 Timothy 2 and 4, Pastor Jesse Rich lays out a practical prayer project every "
              "believer can start today: pray first for your president and those in authority over you, "
              "and watch what you say about them; then pray over everything you eat and drink, believing "
              "it sanctified to nourish your body — the very thing that turned around a lifetime of "
              "sickness for him after he was born again. Learn why the devil is defeated but not dead, "
              "how to take authority over sickness, fear, anxiety and 'brain fog' the moment it shows up "
              "instead of wondering what's going on; how Jesus spoke to the storm and expects you to "
              "speak to your mountain; why praying in tongues (Jude 20) builds up your faith and is the "
              "red flag when your faith runs low; and why faith works by love — so guard the decision "
              "you make the moment you get offended. Includes prayers to receive Jesus Christ and for "
              "healing.")},
    {"file": "ep7_praying_in_tongues.mp3", "ep": 7,
     "title": "Praying in Tongues — Power for Your Breakthrough",
     "pub": "Tue, 14 Jul 2026 12:00:00 -0400",
     "desc": ("'You shall receive power' (Acts 1:8). Pastor Jesse Rich teaches that the baptism of the Holy "
              "Spirit and praying in tongues is the gift God wants every believer to have — and the power "
              "is activated when you pray in the Spirit. From Jude 20, Isaiah 28, Romans 8:26-28 and 1 "
              "Corinthians 14, learn why praying in tongues builds up your faith, gives you direction, and "
              "prays the perfect will of God when you don't know what to pray; how your problems are simply "
              "signals showing where you're lacking in your prayer life; and the unforgettable testimony of "
              "Norvel Hayes — eleven businesses broke, down to his last $85, who kept praying in tongues "
              "until God broke it all loose and made him a multi-millionaire. Includes prayers to receive "
              "Jesus and to be filled with the Holy Spirit.")},
    {"file": "ep6_guard_your_mouth.mp3", "ep": 6,
     "title": "Guard Your Mouth — Walking in Love Brings Divine Health",
     "pub": "Sun, 12 Jul 2026 12:00:00 -0400",
     "desc": ("Divine health isn't only about what you eat or how often you hit the gym — Pastor Jesse "
              "Rich teaches that it hinges on your mouth. From Jude 20-21 and 1 Peter 3, learn why "
              "walking in love and refraining your tongue from evil is the key to living long and living "
              "well: how the enemy uses gossip, judgment, and offense to hinder your prayers and open the "
              "door to sickness; why you must take authority over the devil in your home, on your job, and "
              "even over the weather; and how quick repentance — 'Lord, forgive me' — keeps you protected. "
              "Includes a prayer to receive Jesus and a prayer for healing.")},
    {"file": "ep5_lifestyle_of_worship.mp3", "ep": 5,
     "title": "Develop a Lifestyle of Worship",
     "pub": "Sun, 05 Jul 2026 12:00:00 -0400",
     "desc": ("What you do in secret, God rewards openly (Matthew 6). Pastor Jesse Rich teaches how to "
              "develop a daily lifestyle of worship — bowing your knees and lifting your hands to God in "
              "the privacy of your own home, morning and night (Psalm 89, Psalm 92). Learn why gratitude "
              "and worship — not protests — are how the church wins its battles, how to eliminate "
              "complaining, and why a life of private worship brings God's open reward. Includes communion "
              "and a prayer of salvation.")},
    {"file": "ep4_worship_miracle.mp3", "ep": 4,
     "title": "Worship Brings the Miracle — The Canaanite Woman's Faith",
     "pub": "Sun, 28 Jun 2026 12:00:00 -0400",
     "desc": ("The Canaanite woman had no covenant — she wasn't Jewish, and Jesus hadn't yet paid the "
              "salvation price — yet she received her miracle simply by worshiping the Lord (Matthew 15). "
              "Pastor Jesse Rich teaches that worship is the key that moves the hand of God: ten lepers "
              "were healed but only the one who returned to worship was made whole, embarrassment is fear "
              "from the enemy that boldness defeats, and how to recognize Satan's voice and guard your walk. "
              "A faith-building message on worshiping your way into everything Jesus has already provided.")},
    {"file": "ep2_take_control.mp3", "ep": 3,
     "title": "Living the Abundant Life",
     "pub": "Thu, 25 Jun 2026 12:00:00 -0400",
     "desc": ("God didn't just save you — He gave you abundant life to enjoy right now. So why do so many "
              "believers never walk in it? Pastor Jesse Rich shows you what the enemy uses to rob your "
              "abundant life and how to take hold of everything Jesus already paid for.")},
    {"file": "ep1_promised_land.mp3", "ep": 2,
     "title": "Faith Over the Giants — The 12 Spies (Numbers 13)",
     "pub": "Mon, 23 Jun 2026 20:00:00 -0400",
     "desc": ("Pastor Jesse Rich teaches from Numbers 13 — the twelve spies sent to scout the Promised Land. "
              "Ten saw the giants and shrank back in fear; two saw the same land flowing with blessing and "
              "believed God. Which report are you living by? A faith-building message on refusing to let the "
              "giants steal the prosperous life God has already promised you.")},
    {"file": "ep3_message.mp3", "ep": 3,
     "title": "Watch Your Words — The Power of Your Mouth",
     "pub": "Wed, 18 Jun 2026 19:00:00 -0400",
     "desc": ("It all starts with the mouth. Pastor Jesse Rich teaches on the power of your words — how loose "
              "talk gets us into trouble and weakens our authority over the enemy, and why watching what you "
              "say is a key to walking in victory.")},
    {"file": "ep02_2025-10-12_sunday-message.mp3", "ep": 2,
     "title": "A Better Covenant, Better Promises",
     "pub": "Sun, 12 Oct 2025 12:00:00 -0400",
     "desc": ("Pastor Jesse Rich teaches on the better covenant we have in Christ — established on better "
              "promises (Hebrews 8). Divine healing, divine health, and divine protection (Psalm 91) are "
              "covenant benefits that already belong to you. Anchored in Hebrews 8 and Isaiah 61.")},
    {"file": "ep01_2025-09-07_sunday-message.mp3", "ep": 1,
     "title": "His Word Is Health to Your Flesh",
     "pub": "Sun, 07 Sep 2025 12:00:00 -0400",
     "desc": ("Pastor Jesse Rich opens Proverbs 4 — God's Word is life and health to all your flesh. Learn "
              "why putting Scripture first changes everything, and the truth about where sickness really "
              "comes from (hint: not from God).")},

    # ---- Conquering Fear — bonus shorts (Daily Word) ----
    {"file": "short_01_fear_oxygen.mp3", "type": "bonus", "title": "Fear Needs Oxygen",
     "pub": "Mon, 16 Jun 2026 08:00:00 -0400",
     "desc": "Like a fire-eater's torch, fear needs oxygen to survive. Pastor Jesse Rich on starving your fear instead of feeding it. (Conquering Fear series)"},
    {"file": "short_02_kill_fear.mp3", "type": "bonus", "title": "How to Kill Fear: Decisive Action",
     "pub": "Tue, 17 Jun 2026 08:00:00 -0400",
     "desc": "The only way to get rid of fear is to face it head-on with immediate, decisive action. A short, punchy word from Pastor Jesse Rich. (Conquering Fear series)"},
    {"file": "short_03_out_of_boat.mp3", "type": "bonus", "title": "Get Out of the Boat",
     "pub": "Wed, 18 Jun 2026 08:00:00 -0400",
     "desc": "Peter did what no one else dared — he stepped out of the boat and walked on water. Pastor Jesse Rich on leaving your comfort zone. (Conquering Fear series)"},
    {"file": "short_04_make_a_list.mp3", "type": "bonus", "title": "Make a Fear List",
     "pub": "Thu, 19 Jun 2026 08:00:00 -0400",
     "desc": "Fear will lock you up. Pastor Jesse Rich gives a practical first step: write down everything you don't do because you're afraid. (Conquering Fear series)"},
    {"file": "short_05_wrong_not_blessed.mp3", "type": "bonus", "title": "It's Wrong Not to Be Blessed",
     "pub": "Fri, 20 Jun 2026 08:00:00 -0400",
     "desc": "Success, health, joy, peace — God gave them to you. Pastor Jesse Rich on claiming the gifts that already belong to you. (Conquering Fear series)"},
    {"file": "short_06_wasting_life.mp3", "type": "bonus", "title": "Don't Waste Your Life in the Comfort Zone",
     "pub": "Sat, 21 Jun 2026 08:00:00 -0400",
     "desc": "You're wasting the abundant life God gave you by staying where you're comfortable. A short challenge from Pastor Jesse Rich. (Conquering Fear series)"},
    {"file": "short_07_selfish.mp3", "type": "bonus", "title": "It's Selfish Not to Step Out",
     "pub": "Sun, 22 Jun 2026 08:00:00 -0400",
     "desc": "When you hold back in fear, the world misses what God put in you. Pastor Jesse Rich on why stepping out is unselfish. (Conquering Fear series)"},
]


def dur_hhmmss(f):
    s = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],
                             capture_output=True, text=True).stdout.strip() or 0)
    s = int(s); return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


items = []
for e in EPISODES:
    fp = AUDIO / e["file"]
    size = fp.stat().st_size
    etype = e.get("type", "full")
    epnum = f"\n      <itunes:episode>{e['ep']}</itunes:episode>" if etype == "full" and e.get("ep") else ""
    items.append(f"""    <item>
      <title>{escape(e['title'])}</title>
      <itunes:title>{escape(e['title'])}</itunes:title>
      <description>{escape(e['desc'] + CTA)}</description>
      <itunes:summary>{escape(e['desc'] + CTA)}</itunes:summary>
      <itunes:author>Pastor Jesse Rich</itunes:author>
      <enclosure url="{PUB}/audio/{e['file']}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">jrm-{e['file']}</guid>
      <pubDate>{e['pub']}</pubDate>
      <itunes:duration>{dur_hhmmss(fp)}</itunes:duration>{epnum}
      <itunes:episodeType>{etype}</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Jesse Rich Ministries</title>
    <link>https://JesseRichMinistries.com</link>
    <language>en-us</language>
    <copyright>© Jesse Rich Ministries</copyright>
    <description>{escape(CHANNEL_DESC)}</description>
    <itunes:summary>{escape(CHANNEL_DESC)}</itunes:summary>
    <itunes:author>Pastor Jesse Rich</itunes:author>
    <itunes:type>episodic</itunes:type>
    <itunes:owner>
      <itunes:name>Jesse Rich Ministries</itunes:name>
      <itunes:email>{OWNER_EMAIL}</itunes:email>
    </itunes:owner>
    <itunes:image href="{PUB}/art/jrm_cover_v2_cross.png"/>
    <itunes:category text="Religion &amp; Spirituality">
      <itunes:category text="Christianity"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
(BASE / "feed.xml").write_text(feed)
print("wrote feed.xml with", len(EPISODES), "episodes")
print("feed URL:", PUB + "/feed.xml")
