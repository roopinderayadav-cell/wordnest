"""Wordnest - public pages: Home, Daily News, Articles, single article."""
import json

import streamlit as st

import wn_auth
import wn_db
from wn_seed import ARTICLE_CATEGORIES, NEWS_SECTIONS
from wn_ui import (CATEGORY_COLORS, PAGES, article_card, book_card, book_cover_html, disclaimer_box, esc,
                   fmt_date, news_row, section_title)


def _qp(name, default=None):
    v = st.query_params.get(name)
    return v if v not in (None, "") else default


# ---------------------------------------------------------------- Home
def page_home():
    user = wn_auth.current_user()
    books = wn_db.list_books()
    top_news = wn_db.list_articles("news", top_only=True, limit=5)
    if len(top_news) < 5:
        ids = {r["id"] for r in top_news}
        top_news += [r for r in wn_db.list_articles("news", limit=8) if r["id"] not in ids][:5 - len(top_news)]
    latest = wn_db.list_articles("article", limit=3)

    left, right = st.columns([1.3, 1], gap="large", vertical_alignment="center")
    with left:
        st.markdown(
            '<span class="wn-eyebrow">Read · Write · Earn</span>'
            '<h1 class="wn-serif" style="font-size:54px;line-height:1.05;margin:10px 0 16px">'
            'A home for stories, news, articles and books from real life.</h1>'
            '<p style="font-size:18px;line-height:1.6;color:#4A5551;max-width:560px">Daily news in plain words, '
            'practical articles on travel, careers, food and technology, and books you can read online or download. '
            'Writers keep up to 70% of every book sale.</p>', unsafe_allow_html=True)
        with st.container(horizontal=True, vertical_alignment="center"):
            with st.container(key="cta_hero", width="content"):
                st.page_link(PAGES["books"], label="Explore books", icon=":material/menu_book:")
            with st.container(horizontal=True, key="links_hero", width="content"):
                st.page_link(PAGES["news"], label="Read today's news", icon=":material/newspaper:")
                st.page_link(PAGES["write"], label="Start writing", icon=":material/edit:")
    with right:
        shelf = "".join(book_cover_html(b, w, h, s) for b, (w, h, s) in
                        zip(books[:3], [(140, 210, 18), (165, 250, 21), (140, 210, 18)]))
        st.markdown(f'<div class="wn-hero" style="padding:20px"><div class="wn-shelf">{shelf}</div>'
                    '<p style="text-align:center;font-size:14px;color:#5F6A66;margin:12px 0 0">'
                    'New on the shelf this month</p></div>', unsafe_allow_html=True)

    # quick categories
    st.write("")
    tiles = [("news", None, "Daily News", ":material/newspaper:"),
             ("articles", "Travel Destinations", "Travel", ":material/travel_explore:"),
             ("articles", "Technology", "Technology", ":material/memory:"),
             ("articles", "Travel Industry", "Travel Industry", ":material/flight:"),
             ("articles", "Food & Recipes", "Food & Recipes", ":material/restaurant:"),
             ("articles", "Careers & Jobs", "Careers", ":material/work:"),
             ("books", None, "Books", ":material/auto_stories:")]
    with st.container(horizontal=True, key="links_tiles"):
        for page, cat, label, icon in tiles:
            st.page_link(PAGES[page], label=label, icon=icon, query_params={"category": cat} if cat else None)

    # today's top news
    section_title("Today's top news", "news", "All news")
    if top_news:
        c1, c2 = st.columns([1.35, 1], gap="large")
        with c1:
            article_card(top_news[0], large=True, news=True)
        with c2:
            for r in top_news[1:5]:
                news_row(r)

    # featured books
    section_title("Featured books", "books", "All books")
    if books:
        cols = st.columns(min(len(books), 5))
        for col, b in zip(cols, books[:5]):
            with col:
                book_card(b, owned=wn_db.owns_book(user["id"] if user else None, b["id"]))

    # latest articles
    section_title("Latest articles", "articles", "All articles")
    cols = st.columns(3, gap="medium")
    for col, r in zip(cols, latest):
        with col:
            article_card(r)

    # writer band
    st.write("")
    c1, c2 = st.columns([1.1, 1], gap="large", vertical_alignment="center")
    with c1:
        st.markdown('<div class="wn-dark"><span class="wn-eyebrow" style="color:#E0A43A">For writers</span>'
                    '<h2 class="wn-serif">Publish on Wordnest. Keep up to 70%.</h2>'
                    '<p>Write articles for free and sell your ebooks. You keep the copyright, set your price and can '
                    'sell your book anywhere else too. Every piece is checked by our AI review bot and an editor '
                    'so readers can trust what they read.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="wn-dark" style="padding:24px">'
                    '<div class="wn-step"><b>1. Write</b>Submit an article or upload your book with its cover.</div>'
                    '<div class="wn-step"><b>2. AI check + editor</b>Our bot checks for unsafe, adult, abusive or political '
                    'content in seconds. An editor gives the final approval.</div>'
                    '<div class="wn-step" style="margin:0"><b>3. Publish and earn</b>Readers buy your book; royalties are '
                    'paid monthly to your bank account.</div></div>', unsafe_allow_html=True)
    with st.container(horizontal=True, key="cta_writer"):
        st.page_link(PAGES["write"], label="Apply to write", icon=":material/edit_note:")
        st.page_link(PAGES["policies"], label="Read the royalty terms", query_params={"p": "royalty"})

    # newsletter
    st.write("")
    with st.container(border=True):
        c1, c2 = st.columns([1, 1.2], vertical_alignment="center")
        c1.markdown("### New stories, every week")
        c1.caption("One email with the best new articles, news and books. No spam.")
        with c2.form("newsletter", border=False):
            e1, e2 = st.columns([3, 1], vertical_alignment="bottom")
            email = e1.text_input("Email address", placeholder="you@example.com")
            if e2.form_submit_button("Subscribe", type="primary"):
                if wn_auth.valid_email(email):
                    wn_db.x("INSERT OR IGNORE INTO newsletter(email, created_at) VALUES (?,?)",
                            (email.strip().lower(), wn_db.now()))
                    st.success("Subscribed. Thank you!")
                else:
                    st.error("Please enter a valid email address.")


# ---------------------------------------------------------------- Daily News
def page_news():
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Daily News</h1>', unsafe_allow_html=True)
    st.caption("Short, neutral summaries on world affairs, industry, jobs, the economy, entertainment and sport. "
               "Every story names its source.")
    start = _qp("category", "All")
    options = ["All"] + NEWS_SECTIONS
    section = st.pills("Section", options, default=start if start in options else "All", required=True,
                       label_visibility="collapsed", key="news_section")
    items = wn_db.list_articles("news", category=section, limit=60)
    if not items:
        st.info("No stories in this section yet.")
        return
    c1, c2 = st.columns([1.35, 1], gap="large")
    with c1:
        article_card(items[0], large=True, news=True)
    with c2:
        for r in items[1:5]:
            news_row(r)
    rest = items[5:]
    if rest:
        st.markdown("## More stories")
        for i in range(0, len(rest), 3):
            cols = st.columns(3, gap="medium")
            for col, r in zip(cols, rest[i:i + 3]):
                with col:
                    article_card(r, news=True)
    st.markdown('<div class="wn-disclaimer" style="margin-top:24px"><b>How Wordnest covers news:</b> editors write short '
                'summaries in their own words, credit and link the original source, avoid political opinions, and add '
                'corrections openly. Spotted an error? Use "Report this content" on the story.</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- Articles
def page_articles():
    st.markdown('<h1 class="wn-serif" style="font-size:46px;margin-bottom:0">Articles</h1>', unsafe_allow_html=True)
    st.caption("Practical ideas, guides and stories from Wordnest writers.")
    start = _qp("category", "All")
    options = ["All"] + ARTICLE_CATEGORIES
    c1, c2, c3 = st.columns([3.2, 1, 1.4], vertical_alignment="bottom")
    with c1:
        cat = st.pills("Category", options, default=start if start in options else "All", required=True,
                       label_visibility="collapsed", key="art_cat")
    lang = c2.selectbox("Language", ["All", "English", "Hindi"], label_visibility="collapsed")
    search = c3.text_input("Search", placeholder="Search articles", label_visibility="collapsed")
    items = wn_db.list_articles("article", category=cat, language=lang, search=search.strip() or None)
    if not items:
        st.info("No articles found. Try another category, or be the first to write one.")
        st.page_link(PAGES["write"], label="Write an article", icon=":material/edit:")
        return
    for i in range(0, len(items), 3):
        cols = st.columns(3, gap="medium")
        for col, r in zip(cols, items[i:i + 3]):
            with col:
                article_card(r)


# ---------------------------------------------------------------- Single article / news story
def page_article():
    user = wn_auth.current_user()
    try:
        aid = int(_qp("id", 0))
    except ValueError:
        aid = 0
    a = wn_db.get_article(aid) if aid else None
    can_preview = a and user and (wn_auth.is_staff(user) or user["id"] == a["author_id"])
    if not a or (a["status"] != "published" and not can_preview):
        st.warning("This article is not available.")
        st.page_link(PAGES["articles"], label="Back to articles", icon=":material/arrow_back:")
        return
    news = a["kind"] == "news"
    if a["status"] == "published" and not st.session_state.get(f"viewed_{aid}"):
        wn_db.x("UPDATE articles SET views = views + 1 WHERE id=?", (aid,))
        st.session_state[f"viewed_{aid}"] = True
    if a["status"] != "published":
        st.info(f"Preview only. Status: {a['status'].replace('_', ' ')}.")

    back = "news" if news else "articles"
    st.page_link(PAGES[back], label="Daily News" if news else "Articles", icon=":material/arrow_back:",
                 query_params={"category": a["category"]})
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        color = CATEGORY_COLORS.get(a["category"], "#1F6F5C")
        words = len((a["body"] or "").split())
        by = esc(a["source_name"]) if news else esc(a.get("pen_name") or a.get("user_name"))
        st.markdown(f'<span class="wn-kicker" style="color:{color}">{esc(a["category"])}'
                    f'{" · हिन्दी" if a["language"] == "Hindi" else ""}</span>'
                    f'<h1 class="wn-serif" style="font-size:44px;line-height:1.1;margin:8px 0 12px">{esc(a["title"])}</h1>'
                    f'<p style="font-size:19px;color:#4A5551;line-height:1.55">{esc(a["summary"])}</p>'
                    f'<p class="wn-meta">{"Source: " if news else "By "}{by} · {fmt_date(a["published_at"] or a["created_at"])}'
                    f' · {max(words // 200, 1)} min read</p>', unsafe_allow_html=True)
        cover = wn_db.get_cover("articles", aid)
        if cover:
            st.image(cover[0], width="stretch")
        st.markdown(a["body"])
        if news and a.get("source_url"):
            st.markdown(f"**Source:** [{a['source_name'] or 'Original report'}]({a['source_url']})")
        st.write("")
        disclaimer_box("article", aid, f"a{aid}")
    with right:
        if not news:
            with st.container(border=True):
                st.markdown(f"**About {esc(a.get('pen_name') or a.get('user_name'))}**")
                st.caption(a.get("bio") or "Wordnest writer.")
        st.markdown("**More in " + a["category"] + "**")
        for r in wn_db.list_articles(a["kind"], category=a["category"], limit=5):
            if r["id"] != aid:
                st.page_link(PAGES["article"], label=r["title"], query_params={"id": r["id"]})
        if a.get("ai_report") and user and wn_auth.is_staff(user):
            with st.expander("AI review (editors only)"):
                st.json(json.loads(a["ai_report"]))
