#!/usr/bin/env python3
"""Generate the Jesse Rich Ministries podcast RSS feed (Spotify / Apple / Podcast Index compatible).

v2 — Nov 6 2026 redesign (track T5):
  * Topic-first titles: <title> '{Topic} ({Scripture}) | Pastor Jesse Rich', <itunes:title> '{Topic} ({Scripture})';
    the service type + date moved into the first line of the description.
  * GUIDs NEVER change: guid = 'jrm-' + file name for every episode, whatever the title or host. Retired GUIDs
    (retired_episodes.json, e.g. the duplicate ep36) can never come back.
  * Chapters as plain '(00:00) Label' lines (>= 3, first at 00:00, >= 30 s apart) — Spotify and Apple read these —
    plus content:encoded show notes with YouTube / giving / site links.
  * Podcasting 2.0: podcast:guid, podcast:locked, podcast:funding, podcast:person, podcast:transcript (WebVTT made
    from the whisper transcript, small files under transcripts/ on Pages); atom:link rel=self; lastBuildDate; <image>.
  * Unique itunes:episode numbers (two legacy collisions resolved, see EP_NUMBER_OVERRIDE); pubDate offsets computed
    with zoneinfo America/New_York (EST after Nov 1) and weekday names re-derived (two legacy dates had wrong days).

HOSTING — never commit a new MP3 into audio/: the GitHub Pages site has a hard 1 GB cap (it is at ~950 MB).
  * New episodes: MP3 in audio_release/ (gitignored) + asset on the GitHub Release 'audio', entry in
    episodes_auto.json with "host": "release" (sermon_watch.py does all of this).
  * Legacy Pages MP3s (audio/) move to the Release with migrate_audio_to_release.sh; it writes
    audio_release_manifest.json and every file listed there is served from the Release (same GUID).

    python3 build_feed.py            # write feed.xml (atomically) after validating it; exit 1 on any problem
    python3 build_feed.py --check    # build + validate only, feed.xml untouched

Python 3.9+ (stdlib only).
"""
import email.utils
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    TZ = None

BASE = Path(__file__).resolve().parent
AUDIO = BASE / "audio"
AUDIO_REL = BASE / "audio_release"
TRANSCRIPTS = BASE / "transcripts"
MANIFEST = BASE / "audio_release_manifest.json"
RETIRED = BASE / "retired_episodes.json"
PUB = "https://bmob222.github.io/jrm-podcast"
FEED_URL = PUB + "/feed.xml"
REL_URL = "https://github.com/bmob222/jrm-podcast/releases/download/audio"
OWNER_EMAIL = "customerservice@enemiesbynature.com"   # Spotify verification email
COVER_URL = PUB + "/art/jrm_cover_v2_cross.png"
SITE = "https://jesserichministries.com"
GIVING_URL = "https://jesserichministries.com/donation.htm"
YT_FULL_SERMONS = "https://www.youtube.com/playlist?list=PLOaiQv0ktN3A"
PODCAST_GUID = "ec50d07f-0504-5f21-9af5-e7bc6d12564e"   # UUIDv5(podcast ns, 'bmob222.github.io/jrm-podcast/feed.xml')
LOCKED = "yes"   # set to "no" only while deliberately moving the show to another host
HOST_NAME = "Pastor Jesse Rich"

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

CTA = ("Worship with us — Sundays 9:30 AM & Tuesdays 7:00 PM in Hartford, CT. "
       "More at JesseRichMinistries.com.")

# newest first; pubDate RFC-822 (wall-clock Eastern time; the offset is recomputed below)
EPISODES = [
    {"file": "ep29_2026-09-06_sunday-service.mp3", "ep": 29,
     "title": "Sunday Service 9/6/26: Get the Word in You — It Is Written",
     "pub": "Sun, 06 Sep 2026 12:00:00 -0400",
     "desc": ("Sunday service from downtown Hartford. Faith comes by hearing, and hearing by the Word of "
              "God, so get the New Testament inside you and find out what Jesus purchased for you. Jesus "
              "defeated the devil in the wilderness by quoting scripture: It is written. Pastor Jesse "
              "Rich teaches on the sword of the Spirit, Matthew 12 and the empty house, and the man of "
              "the Gadarenes set free in Mark 5. Don't live by your feelings, be careful who you walk "
              "with, and keep the Word ready in your mouth for the moment you need it. Closes with a call "
              "to receive Jesus Christ as Lord from Romans 10.")},
    {"file": "ep28_2026-09-22_tuesday-service.mp3", "ep": 28,
     "title": "Tuesday Service 9/22/26: Bind the Strong Man — Speak to Your Mountain",
     "pub": "Tue, 22 Sep 2026 20:00:00 -0400",
     "desc": ("Tuesday night service. Pastor Jesse Rich walks through the scriptures to use every day "
              "against the enemy: Matthew 11:12, 12:29, 16:19, 17:20, 18:18 and 21:21. Jesus did not cope "
              "with the storm in Mark 4. He spoke to it, and He gave us His name to do the same. When pain "
              "or any problem comes, take authority right away and keep saying it. You can't live off your "
              "church's faith; develop your own. David spoke his covenant to Goliath while the ten spies "
              "talked about giants. Pastor Jesse shares how he used these scriptures to get a job and keep "
              "it, and closes with a call to receive Jesus Christ as Lord from Romans 10:9-10.")},
    {"file": "ep27_2026-09-20_sunday-service.mp3", "ep": 27,
     "title": "Sunday Service 9/20/26: Finding God's Perfect Will — Led by the Inward Witness",
     "pub": "Sun, 20 Sep 2026 12:00:00 -0400",
     "desc": ("Sunday service from downtown Hartford. Pastor Jesse Rich teaches from Romans 12:1-2, "
              "1 John 5:9-10 and 1 Corinthians 2:14 on the difference between God's acceptable will and "
              "His perfect will, and how to be led by the inward witness of the Holy Spirit. Your flesh, "
              "your mind and the devil will work together against your spirit, so pray before major "
              "decisions and never make a decision when you're angry, hurt or offended. Full of stories: "
              "the website God never told him to start, the car he was told not to buy, getting cussed "
              "out over a 35-cent tithe, and the homeowner who told a young carpet layer he belonged in "
              "the ministry. Closes with prayer to step out and obey God, and a call to receive Jesus "
              "Christ as Lord from Romans 10:9-10."),
     },
    {"file": "ep26_2026-09-13_sunday-service.mp3", "ep": 26,
     "title": "Sunday Service 9/13/26: The Baptism in the Holy Spirit — Why Every Believer Should Pray in Tongues",
     "pub": "Sun, 13 Sep 2026 12:00:00 -0400",
     "desc": ("Sunday service from downtown Hartford. Pastor Jesse Rich teaches on the baptism in the Holy "
              "Spirit from Luke 24:49, Acts 1, 2, 10 and 19, and 1 Corinthians 14: God wants every believer "
              "to receive this gift as soon as they are saved and to pray in tongues daily. Praying in the "
              "Spirit builds you up, magnifies God, gives you confidence, and opens the door to the "
              "supernatural, and the Holy Spirit will give you direction in situations you don't know how "
              "to handle. Then Romans 12:1-2: the Spirit and the Word always agree, so first do what the "
              "Word says, then follow the inner witness. Closes with a call to receive Jesus Christ as Lord "
              "from Romans 10:9-10."),
     },
    {"file": "ep25_2026-08-30_sunday-service.mp3", "ep": 25,
     "title": "Sunday Service 8/30/26: Authority Over the Devil — Mark 5 and Faith as a Mustard Seed",
     "pub": "Sun, 30 Aug 2026 12:00:00 -0400",
     "desc": ("Sunday service from downtown Hartford. Pastor Jesse Rich opens in Mark 5 with the man "
              "of the Gadarenes — bound with chains no man could hold, living among the tombs — set "
              "free and in his right mind the moment Jesus spoke: come out of the man. Then to "
              "Matthew 17, where the disciples could not cast the devil out of a father's son and "
              "Jesus told them plainly why: because of your unbelief. If you have faith as a grain of "
              "mustard seed, nothing shall be impossible unto you. A teaching on the believer's "
              "authority in the name of Jesus over every unclean spirit, and on walking in faith "
              "instead of unbelief."),
     },
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


# ---- v2 metadata for the hand-written episodes above (titles above are kept only as a fallback) ----
# file -> (service label or None = derive from weekday, topic, main scripture or "", show the date?)
LEGACY_META = {
    "ep29_2026-09-06_sunday-service.mp3": ("Sunday Service", "Get the Word in You: It Is Written", "Romans 10:17", True),
    "ep28_2026-09-22_tuesday-service.mp3": ("Tuesday Service", "Bind the Strong Man: Speak to Your Mountain", "Matthew 12:29", True),
    "ep27_2026-09-20_sunday-service.mp3": ("Sunday Service", "Finding God's Perfect Will: Led by the Inward Witness", "Romans 12:2", True),
    "ep26_2026-09-13_sunday-service.mp3": ("Sunday Service", "Baptism in the Holy Spirit: Why Every Believer Should Pray in Tongues", "Luke 24:49", True),
    "ep25_2026-08-30_sunday-service.mp3": ("Sunday Service", "Authority Over the Devil: Faith as a Grain of Mustard Seed", "Matthew 17:20", True),
    "ep24_2026-08-20_camp-meeting-thu-pm.mp3": ("Camp Meeting Day 5 Evening", "Covenant Prosperity: Isaac Sowed in the Year of Famine", "Genesis 26:12", True),
    "ep23_2026-08-20_camp-meeting-thu-am.mp3": ("Camp Meeting Day 5 Morning", "Give Earnest Heed: The Grace of Giving", "Hebrews 2:1", True),
    "ep22_2026-08-19_camp-meeting-wed-pm.mp3": ("Camp Meeting Day 4 Evening", "The Power of the Tithe: Worship the Lord With Your Increase", "", True),
    "ep21_2026-08-19_camp-meeting-wed-am.mp3": ("Camp Meeting Day 4 Morning", "Sow in the Famine: Show Your Faith by Your Actions", "1 Kings 17", True),
    "ep20_2026-08-18_camp-meeting-tue-pm.mp3": ("Camp Meeting Day 3 Evening", "This Is Real: Tongues, Interpretation and Believing for Miracles", "", True),
    "ep19_2026-08-18_camp-meeting-tue-am.mp3": ("Camp Meeting Day 3 Morning", "There Has to Be More: Breaking the Poverty Mindset", "3 John 2", True),
    "ep18_2026-08-17_camp-meeting-mon-pm.mp3": ("Camp Meeting Day 2 Evening", "A Good Father: Healing and Financial Miracles", "3 John 2", True),
    "ep17_2026-08-17_camp-meeting-mon-am.mp3": ("Camp Meeting Day 2 Morning", "Run Doubt Off: Believe You Receive When You Pray", "Mark 11:24", True),
    "ep16_2026-08-16_camp-meeting-day1.mp3": ("Camp Meeting Night 1", "Speak to the Mountain: Take Full Responsibility for Your Life", "Mark 11:23", True),
    "ep15_2026-08-11_evening-live.mp3": ("Tuesday Service", "Speak to Your Mountain: Faith as a Grain of Mustard Seed", "Matthew 17:20", True),
    "ep14_2026-08-09_sunday-service.mp3": ("Sunday Service", "It Wasn't God That Did This: Loosed From a Spirit of Infirmity", "Luke 13:16", True),
    "ep13_2026-08-02_sunday-message.mp3": ("Sunday Message", "Attend to His Word: Health to All Your Flesh", "Proverbs 4:20-22", True),
    "ep12_live0020.mp3": ("Sunday Service", "Take Full Responsibility: Stand on Chapter and Verse", "Isaiah 53:5", True),
    "ep11_live0003.mp3": ("Message", "If You Have Faith, You Shall Say: Calling Things That Be Not", "Mark 11:23", False),
    "ep10_live0002.mp3": ("Message", "Your Youth Renewed Like the Eagle's: The Power of Your Words", "Psalm 103:5", False),
    "ep9_live0001.mp3": ("Message", "By His Stripes You Were Healed: Receiving Divine Healing by Faith", "1 Peter 2:24", False),
    "ep8_a_prayer_project.mp3": ("Tuesday Service", "A Prayer Project: Pray for Your Leaders, Pray Over Your Food", "1 Timothy 2:1-2", True),
    "ep7_praying_in_tongues.mp3": ("Tuesday Service", "Praying in Tongues: Power for Your Breakthrough", "Jude 20", True),
    "ep6_guard_your_mouth.mp3": ("Sunday Service", "Guard Your Mouth: Walking in Love Brings Divine Health", "1 Peter 3:10", True),
    "ep5_lifestyle_of_worship.mp3": ("Sunday Service", "Develop a Lifestyle of Worship", "Matthew 6:6", True),
    "ep4_worship_miracle.mp3": ("Sunday Service", "Worship Brings the Miracle: The Canaanite Woman's Faith", "Matthew 15:25", True),
    "ep2_take_control.mp3": ("Message", "Living the Abundant Life", "John 10:10", False),
    "ep1_promised_land.mp3": ("Message", "Faith Over the Giants: The 12 Spies", "Numbers 13", False),
    "ep3_message.mp3": ("Message", "Watch Your Words: The Power of Your Mouth", "", False),
    "ep02_2025-10-12_sunday-message.mp3": ("Sunday Message", "A Better Covenant, Better Promises", "Hebrews 8:6", True),
    "ep01_2025-09-07_sunday-message.mp3": ("Sunday Message", "His Word Is Health to Your Flesh", "Proverbs 4:22", True),
}

# itunes:episode collisions in the legacy list (2 and 3 were each used twice). The earlier-published item of each
# pair keeps its number; the later one carries none (numbers are optional for an 'episodic' show) — every other
# number stays as listeners already know it.
EP_NUMBER_OVERRIDE = {"ep1_promised_land.mp3": None, "ep2_take_control.mp3": None}

# Chapters / transcript for legacy episodes that have a word-timed whisper transcript (same timeline as the MP3).
LEGACY_EXTRAS = {
    "ep28_2026-09-22_tuesday-service.mp3": {
        "chapters": [{"t": 0, "label": "Scriptures on Binding and Loosing"}, {"t": 146, "label": "Jesus Calms the Storm"},
                     {"t": 331, "label": "Claim Your Inheritance"}, {"t": 540, "label": "Fight With Your Mouth"},
                     {"t": 772, "label": "Speak to the Mountain"}, {"t": 1169, "label": "Confess Jesus as Lord"},
                     {"t": 1354, "label": "Prosperity Belongs to You"}, {"t": 1852, "label": "Talk to It, Not About It"},
                     {"t": 2027, "label": "Salvation Prayer"}],
        "transcript": "transcripts/ep28_2026-09-22_tuesday-service.vtt",
        "yt_video": "yp6IHv9YYBw",
    },
}

_auto = BASE / "episodes_auto.json"
AUTO_EPISODES = json.loads(_auto.read_text()) if _auto.exists() else []


# ------------------------------------------------------------------ helpers
def load_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return default


def dur_seconds(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def hhmmss(s):
    s = int(round(s))
    return "%02d:%02d:%02d" % (s // 3600, (s % 3600) // 60, s % 60)


def ts(t):
    t = int(t)
    return "%d:%02d:%02d" % (t // 3600, t % 3600 // 60, t % 60) if t >= 3600 else "%02d:%02d" % (t // 60, t % 60)


def eastern(pub):
    """Parse an RFC-822 pubDate and return an aware datetime in America/New_York.
    Strings written with a fixed -0400/-0500 are treated as Eastern WALL-CLOCK time (the old builder hard-coded
    -0400 even after DST ended); anything else is converted properly."""
    d = email.utils.parsedate_to_datetime(pub)
    if TZ is None:
        return d
    off = d.utcoffset()
    if off in (timedelta(hours=-4), timedelta(hours=-5)):
        return d.replace(tzinfo=None).replace(tzinfo=TZ)
    return d.astimezone(TZ)


def rfc822(d):
    return d.strftime("%a, %d %b %Y %H:%M:%S %z")


def chapters_ok(ch):
    try:
        ts_ = [float(c["t"]) for c in ch]
    except Exception:
        return False
    return (len(ch) >= 3 and ts_[0] == 0 and all(b - a >= 30 for a, b in zip(ts_, ts_[1:]))
            and all(str(c.get("label", "")).strip() for c in ch))


def clean_label(s):
    s = re.sub(r"[^\w\s'’:,.!?&()/-]", "", str(s))   # Spotify: plain text, no emojis / HTML
    return re.sub(r"\s+", " ", s).strip()[:80]


def titles_for(e):
    """(itunes:title, title). Topic-first; the scripture is appended unless the topic already names a verse."""
    topic = (e.get("topic") or "").strip()
    if not topic:
        t = e["title"].strip()
        return t, (t if HOST_NAME in t else t + " | " + HOST_NAME)
    scr = (e.get("scripture") or (e.get("scriptures") or [""])[0] or "").strip()
    if scr and (scr.lower() in topic.lower() or re.search(r"\d+:\d+", topic)):
        scr = ""
    it = topic + (" (%s)" % scr if scr else "")
    return it, it + " | " + HOST_NAME


def service_line(e, d):
    if e.get("type") == "bonus":
        return ""
    svc = e.get("service") or ""
    if not svc or svc == "Message":
        svc = {6: "Sunday Service", 1: "Tuesday Service"}.get(d.weekday(), "Message")
    parts = [svc]
    if e.get("show_date", True):
        parts.append("%s %d, %d" % (d.strftime("%B"), d.day, d.year))
    if svc in ("Sunday Service", "Tuesday Service", "Sunday Message"):
        parts.append("Hartford, CT")
    return " · ".join(parts)


def yt_link(e):
    return "https://youtu.be/%s" % e["yt_video"] if e.get("yt_video") else ""


def build_item(e, n_by_file, manifest, retired):
    f = e["file"]
    guid = "jrm-" + f
    if guid in retired:
        raise SystemExit("ERROR: %s is a retired GUID (%s) — never reuse it" % (guid, retired[guid].get("reason")))
    local = AUDIO_REL / f if (AUDIO_REL / f).exists() else AUDIO / f
    if not local.exists():
        raise SystemExit("ERROR: audio file for %s not found in audio_release/ or audio/" % f)
    on_release = e.get("host") == "release" or f in manifest
    url = "%s/%s" % (REL_URL, f) if on_release else "%s/audio/%s" % (PUB, f)
    size = local.stat().st_size
    seconds = float(e.get("duration_s") or 0) or dur_seconds(local)
    d = eastern(e["pub"])
    it_title, title = titles_for(e)
    etype = e.get("type", "full")
    epn = n_by_file.get(f)
    svc = service_line(e, d)
    desc = e["desc"].strip()
    chapters = e.get("chapters") or []
    chapters = chapters if chapters_ok(chapters) else []
    ch_lines = ["(%s) %s" % (ts(c["t"]), clean_label(c["label"])) for c in chapters]
    yt = yt_link(e)
    watch = yt or YT_FULL_SERMONS
    # plain-text description (Spotify/Apple chapters come from these lines)
    plain = []
    if svc:
        plain += [svc, ""]
    plain.append(desc)
    if ch_lines:
        plain += ["", "Chapters:"] + ch_lines
    if etype == "full":
        plain += ["", ("Watch this message on YouTube: %s" % yt) if yt else
                  ("Full sermons on YouTube: %s" % YT_FULL_SERMONS)]
    plain += ["Support this ministry: %s" % GIVING_URL, "", CTA]
    plain_s = "\n".join(plain)
    # HTML show notes
    h = []
    if svc:
        h.append("<p><strong>%s</strong></p>" % escape(svc))
    h.append("<p>%s</p>" % escape(desc))
    scr = e.get("scriptures") or ([e["scripture"]] if e.get("scripture") else [])
    if scr:
        h.append("<p>Scriptures: %s</p>" % escape(", ".join(scr[:6])))
    if ch_lines:
        h.append("<p>Chapters:</p>")
        h += ["<p>%s</p>" % escape(x) for x in ch_lines]
    if etype == "full":
        h.append('<p>%s <a href=%s>%s</a></p>' % ("Watch this message on YouTube:" if yt else "Full sermons on YouTube:",
                                                quoteattr(watch), escape(watch)))
    h.append('<p>Support this ministry: <a href=%s>%s</a></p>' % (quoteattr(GIVING_URL), escape(GIVING_URL)))
    h.append('<p>Worship with us — Sundays 9:30 AM &amp; Tuesdays 7:00 PM in Hartford, CT. More at '
             '<a href=%s>JesseRichMinistries.com</a>.</p>' % quoteattr(SITE))
    html = "".join(h).replace("]]>", "]]&gt;")
    lines = ["    <item>",
             "      <title>%s</title>" % escape(title),
             "      <itunes:title>%s</itunes:title>" % escape(it_title),
             "      <link>%s</link>" % escape(yt or SITE),
             "      <description>%s</description>" % escape(plain_s),
             "      <content:encoded><![CDATA[%s]]></content:encoded>" % html,
             "      <itunes:summary>%s</itunes:summary>" % escape(plain_s),
             "      <itunes:author>%s</itunes:author>" % HOST_NAME,
             '      <enclosure url=%s length="%d" type="audio/mpeg"/>' % (quoteattr(url), size),
             '      <guid isPermaLink="false">%s</guid>' % escape(guid),
             "      <pubDate>%s</pubDate>" % rfc822(d),
             "      <itunes:duration>%s</itunes:duration>" % hhmmss(seconds)]
    if epn:
        lines.append("      <itunes:episode>%d</itunes:episode>" % epn)
    lines += ["      <itunes:episodeType>%s</itunes:episodeType>" % etype,
              "      <itunes:explicit>false</itunes:explicit>"]
    tr = e.get("transcript")
    if tr and (BASE / tr).exists():
        lines.append('      <podcast:transcript url=%s type="text/vtt" language="en"/>'
                     % quoteattr("%s/%s" % (PUB, tr)))
    lines.append("    </item>")
    return "\n".join(lines), {"guid": guid, "url": url, "size": size, "ep": epn, "title": title,
                              "chapters": len(ch_lines), "transcript": bool(tr and (BASE / tr).exists())}


def episodes():
    eps = []
    for e in AUTO_EPISODES:
        eps.append(dict(e))
    for e in EPISODES:
        e = dict(e)
        meta = LEGACY_META.get(e["file"])
        if meta:
            svc, topic, scr, show_date = meta
            e.setdefault("service", svc)
            e.setdefault("topic", topic)
            e.setdefault("scripture", scr)
            e.setdefault("show_date", show_date)
        e.update({k: v for k, v in LEGACY_EXTRAS.get(e["file"], {}).items() if k not in e})
        if e["file"] in EP_NUMBER_OVERRIDE:
            e["ep"] = EP_NUMBER_OVERRIDE[e["file"]]
        eps.append(e)
    return eps


def build():
    manifest = load_json(MANIFEST, {}).get("files", {})
    retired = {r["guid"]: r for r in load_json(RETIRED, {"retired": []}).get("retired", [])}
    eps = episodes()
    n_by_file, seen = {}, {}
    for e in eps:
        if e.get("type", "full") == "full" and e.get("ep"):
            n = int(e["ep"])
            if n in seen:
                raise SystemExit("ERROR: itunes:episode %d used by both %s and %s" % (n, seen[n], e["file"]))
            seen[n] = e["file"]
            n_by_file[e["file"]] = n
    items, info = [], []
    for e in eps:
        x, meta = build_item(e, n_by_file, manifest, retired)
        items.append(x)
        info.append(meta)
    guids = [m["guid"] for m in info]
    if len(guids) != len(set(guids)):
        raise SystemExit("ERROR: duplicate GUIDs in feed")
    now = datetime.now(TZ) if TZ else datetime.now().astimezone()
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:podcast="https://podcastindex.org/namespace/1.0">
  <channel>
    <title>Jesse Rich Ministries</title>
    <link>https://JesseRichMinistries.com</link>
    <atom:link href="%(feed)s" rel="self" type="application/rss+xml"/>
    <language>en-us</language>
    <copyright>© Jesse Rich Ministries</copyright>
    <lastBuildDate>%(lbd)s</lastBuildDate>
    <description>%(desc)s</description>
    <image>
      <url>%(cover)s</url>
      <title>Jesse Rich Ministries</title>
      <link>https://JesseRichMinistries.com</link>
    </image>
    <itunes:summary>%(desc)s</itunes:summary>
    <itunes:author>Pastor Jesse Rich</itunes:author>
    <itunes:type>episodic</itunes:type>
    <itunes:owner>
      <itunes:name>Jesse Rich Ministries</itunes:name>
      <itunes:email>%(email)s</itunes:email>
    </itunes:owner>
    <itunes:image href="%(cover)s"/>
    <itunes:category text="Religion &amp; Spirituality">
      <itunes:category text="Christianity"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <podcast:guid>%(pguid)s</podcast:guid>
    <podcast:locked owner="%(email)s">%(locked)s</podcast:locked>
    <podcast:funding url="%(giving)s">Support Jesse Rich Ministries</podcast:funding>
    <podcast:person role="host" href="%(site)s">Pastor Jesse Rich</podcast:person>
%(items)s
  </channel>
</rss>
""" % {"feed": FEED_URL, "lbd": rfc822(now), "desc": escape(CHANNEL_DESC), "cover": COVER_URL,
       "email": OWNER_EMAIL, "pguid": PODCAST_GUID, "locked": LOCKED, "giving": GIVING_URL, "site": SITE,
       "items": "\n".join(items)}
    return feed, info


def validate(feed, info):
    root = ET.fromstring(feed.encode("utf-8"))
    ch = root.find("channel")
    items = ch.findall("item")
    assert len(items) == len(info), "item count mismatch"
    for it in items:
        email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        enc = it.find("enclosure")
        assert int(enc.get("length")) > 0, "empty enclosure"
    return len(items)


def main():
    check = "--check" in sys.argv
    feed, info = build()
    n = validate(feed, info)
    if not check:
        fd, tmp = tempfile.mkstemp(prefix=".feed.", suffix=".xml", dir=str(BASE))
        with os.fdopen(fd, "w") as f:
            f.write(feed)
        os.chmod(tmp, 0o644)
        os.replace(tmp, str(BASE / "feed.xml"))
    rel = sum(1 for m in info if m["url"].startswith(REL_URL))
    print("%s feed.xml with %d episodes (%d on the Release, %d on Pages; %d with chapters, %d with transcripts)"
          % ("checked" if check else "wrote", n, rel, n - rel, sum(1 for m in info if m["chapters"]),
             sum(1 for m in info if m["transcript"])))
    print("feed URL:", FEED_URL)


if __name__ == "__main__":
    main()
