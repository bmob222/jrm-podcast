# Jesse Rich Ministries Podcast — Launch Guide (Free Spotify Route)

You chose the **free** route: **Spotify for Podcasters** hosts the audio, gives
you ONE RSS feed for free, and that feed is what you submit to Amazon Music /
Audible (and optionally Apple). After launch, new episodes you upload to Spotify
appear everywhere automatically.

**Everything you need is already in this folder:**

```
jrm_podcast/
├── art/jrm_podcast_cover_3000.png        ← 3000×3000 cover (upload as show art)
├── episodes/
│   ├── ep01_2025-09-07_sunday-message.mp3   (37 min, tagged + artwork)
│   └── ep02_2025-10-12_sunday-message.mp3   (45 min, tagged + artwork)
├── SHOW_METADATA.md                      ← copy/paste title, category, descriptions
├── build_rss.py                          ← only needed if you self-host later
└── feed/feed.xml                         ← sample feed (self-host option)
```

---

## STEP 1 — Create the show on Spotify for Podcasters  (~10 min)

1. Go to **https://podcasters.spotify.com** → log in with the ministry's
   Spotify account (any free Spotify login works; create one if needed).
2. Click **New show** → choose **"I want to create a new show / host here"**
   (NOT "I already have a podcast" — that's for importing an existing feed).
3. Fill in from `SHOW_METADATA.md`:
   - Title: **Jesse Rich Ministries**
   - Author: **Pastor Jesse Rich**
   - Description: paste the **long description**
   - Category: **Religion & Spirituality**
   - Language: **English**
4. Upload cover: **`art/jrm_podcast_cover_3000.png`**
5. Save. The show is created (not public until you publish an episode).

## STEP 2 — Upload the two episodes  (~5 min each)

For each MP3 in `episodes/`:
1. **New episode** → upload the `.mp3`.
2. Title: use the title from `SHOW_METADATA.md` (e.g. "Sunday Message —
   September 7, 2025").
3. Description: use the per-episode template in `SHOW_METADATA.md` — add the
   one-line topic after you've reviewed the message.
4. Publish (or schedule). Upload **ep01 first, then ep02** so the order is right.

➡️ As soon as one episode is published, your show goes live **on Spotify** and
   you get your **RSS feed URL** — find it under **Settings → Availability /
   Distribution** (looks like `https://anchor.fm/s/XXXXXXXX/podcast/rss`).
   **Copy that URL — you need it for Step 3.**

## STEP 3 — Submit the SAME feed to Amazon Music + Audible  (~5 min)

1. Go to **https://music.amazon.com/podcasters**
2. Sign in with an Amazon account → **Add your podcast**.
3. Paste the **Spotify RSS feed URL** from Step 2.
4. Verify ownership (Amazon emails a code to the show's owner email —
   `customerservice@enemiesbynature.com` — or shows an on-screen code).
5. Submit. ✅ This publishes to **both Amazon Music AND the Audible app** —
   Audible has no separate upload; it pulls from Amazon's podcast catalog.

## STEP 4 (optional but recommended) — Apple Podcasts  (~10 min)

Apple feeds dozens of other apps (Overcast, Castro, Pocket Casts, etc.).
1. Go to **https://podcastsconnect.apple.com** (needs a free Apple ID).
2. **+ → New Show → Add a show with an RSS feed** → paste the same Spotify feed.
3. Submit for review.

## STEP 5 — Verify & you're done

| Platform | Review time | Auto-updates after? |
|----------|-------------|---------------------|
| Spotify  | Instant     | ✅ |
| Amazon Music / Audible | a few hours – 5 days | ✅ |
| Apple Podcasts | 1–5 days | ✅ |

After approval, **every new episode you upload to Spotify shows up on all
platforms automatically** — no resubmitting.

---

## Adding future episodes (the weekly routine)

1. Take the new Sunday sermon video.
2. Extract a tagged MP3 — re-run the same ffmpeg pattern used to build these
   (see `MAKE_EPISODE.sh` below for a ready-made command), or just upload the
   raw MP4's audio; Spotify accepts MP3/M4A/WAV.
3. Upload it as a **New episode** in Spotify for Podcasters. Done — it
   propagates everywhere.

---

## If you ever outgrow the free route (owned feed)

The downside of the free route: Spotify owns the feed URL, so moving hosts later
means re-submitting everywhere. If you'd rather own the feed from day one
(RSS.com ~$5/mo, Buzzsprout ~$12/mo), this folder already supports it:

- `build_rss.py` generates a compliant `feed/feed.xml` from `episodes/`.
- Run: `python3 build_rss.py --base-url https://YOURDOMAIN/jrm`
- Host this folder's `episodes/`, `art/`, and `feed/feed.xml` anywhere public
  (S3, your church server, any static host), then submit `feed/feed.xml`'s URL
  to Spotify/Amazon/Apple instead. You then never depend on one host.
