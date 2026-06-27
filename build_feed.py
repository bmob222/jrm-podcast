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
     "title": "Sunday Message — October 12, 2025",
     "pub": "Sun, 12 Oct 2025 12:00:00 -0400",
     "desc": ("A full Sunday message from Pastor Jesse Rich — uncompromised King James Bible teaching to "
              "build your faith and send you out stronger.")},
    {"file": "ep01_2025-09-07_sunday-message.mp3", "ep": 1,
     "title": "Sunday Message — September 7, 2025",
     "pub": "Sun, 07 Sep 2025 12:00:00 -0400",
     "desc": ("A full Sunday message from Pastor Jesse Rich — uncompromised King James Bible teaching to "
              "build your faith and send you out stronger.")},
]


def dur_hhmmss(f):
    s = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],
                             capture_output=True, text=True).stdout.strip() or 0)
    s = int(s); return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


items = []
for e in EPISODES:
    fp = AUDIO / e["file"]
    size = fp.stat().st_size
    items.append(f"""    <item>
      <title>{escape(e['title'])}</title>
      <itunes:title>{escape(e['title'])}</itunes:title>
      <description>{escape(e['desc'] + CTA)}</description>
      <itunes:summary>{escape(e['desc'] + CTA)}</itunes:summary>
      <itunes:author>Pastor Jesse Rich</itunes:author>
      <enclosure url="{PUB}/audio/{e['file']}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">jrm-{e['file']}</guid>
      <pubDate>{e['pub']}</pubDate>
      <itunes:duration>{dur_hhmmss(fp)}</itunes:duration>
      <itunes:episode>{e['ep']}</itunes:episode>
      <itunes:episodeType>full</itunes:episodeType>
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
