"""Wordnest - demo content created on first start (safe to delete once real content is added)."""
import json

import streamlit as st

import wn_auth
import wn_db
import wn_moderation
import wn_pdf

ARTICLE_CATEGORIES = ["Travel Destinations", "Travel Industry", "Technology", "Careers & Jobs",
                      "Food & Recipes", "Lifestyle"]
NEWS_SECTIONS = ["Geopolitics", "Industry Update", "Job Market", "Economy", "Entertainment", "Sport"]
BOOK_CATEGORIES = ["Fiction", "Career & Learning", "Travel", "Family & Food", "Self-help", "Poetry"]
LANGUAGES = ["English", "Hindi"]

DEMO_AUTHOR = ("author@wordnest.demo", "Author123!")
DEMO_READER = ("reader@wordnest.demo", "Reader123!")

ARTICLES = [
    ("Careers & Jobs", "How to prepare for your first interview in travel operations",
     "The questions recruiters ask about fares, reservation systems and customer handling, and how to answer them clearly.",
     """Your first interview for a travel operations role is less about knowing everything and more about showing how you think.

**1. Know the basics of a booking.** Be ready to explain what a reservation record holds: passenger names, itinerary, contact details, ticketing time limit and the fare. You do not need to type commands from memory, but you should understand each part.

**2. Practise a customer scenario.** A common question is: *"A traveller missed their flight. What do you do?"* A good answer has an order: stay calm, check the ticket and fare rules, explain the options and costs, and confirm the new plan in writing.

**3. Show you can work in shifts.** Many roles support the US, UK or Australia. Say honestly which shifts you can work and for how long.

**4. Ask one good question.** For example: *"How do new joiners get trained on the booking system in the first month?"*

Small, clear answers beat long ones. Practise aloud with a friend before the day."""),
    ("Travel Industry", "What a fare rule really means for your ticket",
     "Changes, refunds and no-shows explained in plain words before you book.",
     """Every airline ticket comes with fare rules. They decide what happens if your plans change.

**Change fee.** Some fares allow a date change for a fee plus any difference in fare. Cheaper fares may not allow changes at all.

**Refund.** A refundable fare returns money (sometimes minus a fee). A non-refundable fare may still return airport taxes, so it is worth asking.

**No-show.** If you do not turn up and do not tell the airline, the rest of the journey can be cancelled. Always inform the airline or your agent if you will miss a flight.

**Validity.** Many fares must be used within a set period from the date of issue.

Before you pay, ask one simple question: *"If I need to change this, what will it cost?"* That single answer saves most travel arguments later."""),
    ("Food & Recipes", "A Sunday dal the whole family can cook together",
     "A simple recipe with jobs for every age, from washing lentils to the final tadka.",
     """Cooking together is one of the easiest ways to spend unhurried time as a family.

**You need (serves 4):** 1 cup toor dal, 1 tomato, 1 onion, 2 green chillies, 1 tsp cumin, a pinch of asafoetida, ½ tsp turmeric, salt, 2 tbsp ghee, fresh coriander.

**Jobs for little hands:** wash the dal three times and tear the coriander leaves.

**Jobs for teenagers:** chop the onion and tomato.

**Jobs for grandparents:** taste and decide the salt. Everyone agrees they know best.

**Method.** Pressure-cook the dal with turmeric and 3 cups of water for 3 whistles. Heat ghee, add cumin and asafoetida, then onion until golden, then tomato and chillies until soft. Pour this tadka into the dal, add salt, simmer for 5 minutes and finish with coriander.

Serve with rice and a story from whoever cooked the most."""),
    ("Technology", "How AI is quietly changing everyday office work",
     "From drafting emails to searching process documents, a practical look at where AI helps and where people still matter.",
     """Artificial intelligence is now part of many ordinary office tools. The useful question is not *"Will AI replace me?"* but *"Which parts of my day can it make easier?"*

**Where it helps today**
- Drafting a first version of an email or report.
- Searching long process documents for the right step.
- Summarising a long meeting into action points.

**Where people still matter**
- Checking facts before anything is sent to a customer.
- Handling upset customers with empathy.
- Making decisions that affect money, safety or people.

**A simple habit:** treat AI output as a draft from a new colleague. Read it, correct it and own the final version."""),
    ("Travel Destinations", "Planning a relaxed family trip with grandparents",
     "Short distances, fewer stairs and a slower pace: a checklist for trips the whole family enjoys.",
     """Travelling with grandparents is about comfort first and sightseeing second.

- **Choose the pace.** One main outing a day, with a rest in the afternoon.
- **Pick the right stay.** Ask for a ground-floor room or a lift, and a bathroom with a grab rail if possible.
- **Plan short journeys.** Two to four hours of travel at a time is easier than a long day.
- **Carry a small health pouch.** Daily medicines, prescriptions and a list of emergency contacts.
- **Book help early.** Airlines and railways offer wheelchair or assistance services when booked in advance.

The best family trips leave everyone with energy for one more story at dinner."""),
    ("Careers & Jobs", "Five habits of a good team lead in the first 90 days",
     "Small, steady habits that build trust with a new team faster than big speeches.",
     """Moving from agent to team lead changes your job from doing the work to helping others do it well.

1. **Listen before you change.** Spend the first two weeks understanding how the team works today.
2. **Hold short one-to-ones.** Fifteen minutes a week with each person builds more trust than a monthly review.
3. **Make the scoreboard visible.** Share the few numbers that matter, such as quality, turnaround and backlog, every day.
4. **Coach on real cases.** Pick one recent transaction and walk through it together.
5. **Protect your team's time.** Push back on unnecessary meetings and reports.

None of these need a budget. All of them need consistency."""),
]

NEWS = {
    "Geopolitics": ["[Demo] Weekly brief: what to watch in world affairs", "[Demo] Explainer: how trade agreements affect travel"],
    "Industry Update": ["[Demo] Travel industry roundup for this week", "[Demo] What changed for travel agents this month"],
    "Job Market": ["[Demo] Hiring snapshot: roles in demand this week", "[Demo] Freshers: skills employers asked for this month"],
    "Economy": ["[Demo] Prices and spending: this week in numbers", "[Demo] Explainer: what an interest rate change means for you"],
    "Entertainment": ["[Demo] New releases to watch this weekend", "[Demo] Books and films people are talking about"],
    "Sport": ["[Demo] Weekend sports round-up", "[Demo] Fixtures to watch this week"],
}
NEWS_BODY = ("This is a sample story that shows how the Daily News section looks. "
             "An editor replaces it with a short, neutral summary written in their own words, "
             "states only facts confirmed by the source, and links the original report below.\n\n"
             "**How Wordnest writes news:** short summaries, no political opinions, every story credited to its source, "
             "and corrections added openly when something changes.")

BOOKS = [
    ("The Way Back", None, "R.K. Yadav", "Fiction", "English", 299, "#1F6F5C",
     "A novel by R.K. Yadav. Replace this text with the book's back-cover description."),
    ("The Love We Never Lost", None, "R.K. Yadav", "Fiction", "English", 299, "#8C2F39",
     "A novel by R.K. Yadav, available in English and Hindi. Replace this text with the back-cover description."),
    ("The Travel Career Starter", "Your first job in airline reservations and travel", "R.K. Yadav", "Career & Learning",
     "English", 249, "#B7791F",
     "A course-like guide to airline reservations, fares, booking systems and landing your first travel job."),
    ("The Middle Management Blueprint", "From Fresher to Operational Excellence Leader", "R.K. Yadav",
     "Career & Learning", "English", 299, "#2B3A55",
     "A practical guide for people moving from frontline roles into team lead and management positions."),
    ("Wordnest Free Reading Collection", "Short pieces from Wordnest writers", "Various authors", "Self-help",
     "English", 0, "#5B6B3A",
     "A free collection of short reads from Wordnest writers. Read online or download as PDF."),
]


@st.cache_resource(show_spinner="Setting up Wordnest...")
def setup():
    """Create tables, the admin account and demo content once per server start."""
    wn_db.init()
    wn_auth.ensure_admin()
    if wn_db.q("SELECT COUNT(*) n FROM articles", one=True)["n"] == 0:
        _seed()
    return True


def _user(email, password, name, pen, role="reader", bio=None):
    r = wn_db.q("SELECT id FROM users WHERE email=?", (email,), one=True)
    if r:
        return r["id"]
    return wn_db.x("INSERT INTO users(email, name, pen_name, bio, password_hash, role, created_at) VALUES (?,?,?,?,?,?,?)",
                   (email, name, pen, bio, wn_auth.hash_password(password), role, wn_db.now()))


def _seed():
    author = _user(DEMO_AUTHOR[0], DEMO_AUTHOR[1], "R.K. Yadav", "R.K. Yadav",
                   bio="Writer with more than two decades in the travel industry, writing fiction and practical career guides.")
    _user(DEMO_READER[0], DEMO_READER[1], "Demo Reader", "Demo Reader")
    guest = _user("guest@wordnest.demo", "Guest123!", "Guest Writer", "Guest Writer",
                  bio="Community writer (demo account).")
    admin = wn_db.q("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1", one=True)["id"]

    days = 0
    for cat, title, summary, body in ARTICLES:
        rep = wn_moderation.rule_check(f"{title}\n{summary}\n{body}", "article")
        ts = f"2026-10-{17 - days:02d}T09:{10 + days:02d}:00"
        wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, status, ai_decision, "
                "ai_report, created_at, published_at) VALUES ('article',?,?,?,?, 'English', ?, 'published', ?, ?, ?, ?)",
                (title, summary, body, cat, author, rep["decision"], json.dumps(rep), ts, ts))
        days += 1

    # one community article waiting in the editor's queue
    t, s = "A weekend walk through old Delhi's food lanes", "Where to start, what to eat first and how to avoid the crowds."
    b = ("Start early, around 8 am, before the lanes fill up. Begin with hot jalebi, then move to a plate of chole "
         "bhature. Wear comfortable shoes, carry small change and a water bottle, and keep your bag in front of you "
         "in busy lanes. Go with a friend and share plates so you can taste more.")
    rep = wn_moderation.rule_check(f"{t}\n{s}\n{b}", "article")
    wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, status, ai_decision, "
            "ai_report, created_at) VALUES ('article',?,?,?, 'Food & Recipes', 'English', ?, 'pending', ?, ?, ?)",
            (t, s, b, guest, rep["decision"], json.dumps(rep), wn_db.now()))

    hour = 0
    for section, titles in NEWS.items():
        for i, title in enumerate(titles):
            ts = f"2026-10-17T{8 + (hour % 10):02d}:{(hour * 7) % 60:02d}:00"
            wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, source_name, "
                    "source_url, is_top, status, ai_decision, created_at, published_at) "
                    "VALUES ('news',?,?,?,?, 'English', ?, ?, ?, ?, 'published', 'pass', ?, ?)",
                    (title, "Sample story to show the layout. Editors replace it with a verified summary and a source link.",
                     NEWS_BODY, section, admin, "Source name goes here", "https://example.com",
                     1 if i == 0 and section in ("Job Market", "Industry Update", "Economy", "Geopolitics") else 0, ts, ts))
            hour += 1

    for title, sub, by, cat, lang, price, color, desc in BOOKS:
        pdf = wn_pdf.demo_book_pdf(title, by, color)
        wn_db.x("INSERT INTO books(title, subtitle, author_id, author_display, description, category, language, price, "
                "pages, cover_color, pdf, status, ai_decision, created_at, published_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?, 'published', 'pass', ?, ?)",
                (title, sub, author if by == "R.K. Yadav" else admin, by, desc, cat, lang, price,
                 wn_pdf.page_count(pdf), color, pdf, "2026-10-16T10:00:00", "2026-10-16T10:00:00"))

    # a sample sale so the author dashboard shows earnings
    book = wn_db.q("SELECT id, price FROM books WHERE title='The Way Back'", one=True)
    reader = wn_db.q("SELECT id FROM users WHERE email=?", (DEMO_READER[0],), one=True)
    wn_db.create_order(reader["id"], book["id"], book["price"], "DEMO-0001")
