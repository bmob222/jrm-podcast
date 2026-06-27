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
