"""Wordnest - Admin panel for the owner and editors."""
import datetime
import json

import pandas as pd
import streamlit as st

import wn_auth
import wn_db
import wn_moderation
import wn_pdf
from wn_seed import BOOK_CATEGORIES, LANGUAGES, NEWS_SECTIONS
from wn_ui import PAGES, decision_badge, esc, fmt_date, rupees, show_review, shrink_image

REMINDER_TEXT = ("A friendly reminder from the Wordnest team: please keep your writing original, respectful and safe. "
                 "Wordnest does not publish sexual or adult content, abusive or hateful language, violence, illegal "
                 "activity, other people's personal details, or anything about governments, political parties or "
                 "politicians. Every submission is checked by our AI review bot and an editor; blocked submissions "
                 "count as strikes, and 3 strikes suspend an account. Writers are responsible for their own content, "
                 "and Wordnest does not endorse or take responsibility for it. Thank you for writing with us!")


def page_admin():
    user = wn_auth.current_user()
    if not wn_auth.is_staff(user):
        st.warning("This area is for Wordnest editors and admins.")
        st.page_link(PAGES["account"], label="Sign in", icon=":material/login:")
        return
    admin = wn_auth.is_admin(user)
    st.markdown('<h1 class="wn-serif" style="font-size:42px;margin-bottom:0">Admin panel</h1>', unsafe_allow_html=True)
    ai_on = wn_moderation.ai_available()
    st.caption(("AI review bot: ON (Gemini)" if ai_on else
                "AI review bot: rule check only. Add GEMINI_API_KEY in Streamlit secrets to switch on the AI layer.")
               + f" · Signed in as {user['email']} ({user['role']})")
    if admin and wn_auth.using_default_admin():
        st.warning("You are using the default admin password. Set ADMIN_EMAIL and ADMIN_PASSWORD in Streamlit secrets.")

    pend_a = wn_db.q("SELECT COUNT(*) n FROM articles WHERE status='pending'", one=True)["n"]
    pend_b = wn_db.q("SELECT COUNT(*) n FROM books WHERE status='pending'", one=True)["n"]
    open_r = wn_db.q("SELECT COUNT(*) n FROM reports WHERE status='open'", one=True)["n"]
    names = [f"Review queue ({pend_a + pend_b})", "Post news", f"Reports ({open_r})", "Manage content"]
    if admin:
        names += ["Upload a book", "Users and reminders", "Sales and royalties", "Settings"]
    tabs = st.tabs(names)
    with tabs[0]:
        _queue(user)
    with tabs[1]:
        _post_news(user)
    with tabs[2]:
        _reports()
    with tabs[3]:
        _manage()
    if admin:
        with tabs[4]:
            _upload_book(user)
        with tabs[5]:
            _users()
        with tabs[6]:
            _sales()
        with tabs[7]:
            _settings()


# ---------------------------------------------------------------- review queue
def _queue(editor):
    show_blocked = st.toggle("Also show items blocked by AI (to double-check)", value=False)
    states = ("pending", "ai_blocked") if show_blocked else ("pending",)
    marks = ",".join("?" * len(states))
    arts = wn_db.q(f"SELECT a.*, u.pen_name, u.email, u.strikes FROM articles a JOIN users u ON u.id=a.author_id "
                   f"WHERE a.status IN ({marks}) ORDER BY a.id", states)
    books = wn_db.q(f"SELECT id, title, subtitle, author_id, author_display, description, category, language, price, pages, "
                    f"status, ai_decision, ai_report, created_at FROM books WHERE status IN ({marks}) ORDER BY id", states)
    if not arts and not books:
        st.success("Nothing waiting. All caught up.")
        return
    for a in arts:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
            c1.markdown(f"**{esc(a['title'])}**  \n<span class='wn-meta'>Article · {esc(a['category'])} · {esc(a['language'])} · "
                        f"by {esc(a['pen_name'])} ({esc(a['email'])}, strikes {a['strikes']}) · {fmt_date(a['created_at'])}</span>",
                        unsafe_allow_html=True)
            c2.markdown(decision_badge(a["ai_decision"]), unsafe_allow_html=True)
            with st.expander("Read the article"):
                st.markdown(f"*{a['summary'] or ''}*")
                st.markdown(a["body"])
            if a["ai_report"]:
                with st.expander("AI review report", expanded=a["ai_decision"] != "pass"):
                    show_review(json.loads(a["ai_report"]))
            _decide("articles", a, editor)
    for b in books:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
            c1.markdown(f"**{esc(b['title'])}**  \n<span class='wn-meta'>Book · {esc(b['category'])} · {esc(b['language'])} · "
                        f"{rupees(b['price'])} · {b['pages']} pages · by {esc(b['author_display'])}</span>",
                        unsafe_allow_html=True)
            c2.markdown(decision_badge(b["ai_decision"]), unsafe_allow_html=True)
            st.caption(b["description"] or "")
            st.page_link(PAGES["book"], label="Open the book preview and reader", query_params={"id": b["id"]})
            if b["ai_report"]:
                with st.expander("AI review report", expanded=b["ai_decision"] != "pass"):
                    show_review(json.loads(b["ai_report"]))
            _decide("books", b, editor)


def _decide(table, item, editor):
    kind = "article" if table == "articles" else "book"
    note = st.text_input("Note to the writer (shown to them)", key=f"note_{table}_{item['id']}",
                         placeholder="Optional for approval, recommended for rejection")
    c = st.columns([1, 1, 1, 2])
    if c[0].button("Approve and publish", type="primary", key=f"ok_{table}_{item['id']}"):
        wn_db.x(f"UPDATE {table} SET status='published', published_at=?, admin_note=? WHERE id=?",
                (wn_db.now(), note or None, item["id"]))
        wn_db.notify(item["author_id"], f"Published: {item['title']}",
                     f"An editor approved your {kind}. It is now live." + (f" Note: {note}" if note else ""))
        wn_db.log_moderation(kind, item["id"], "approved", f"editor:{editor['email']}", {"note": note})
        st.rerun()
    if c[1].button("Reject", key=f"no_{table}_{item['id']}"):
        wn_db.x(f"UPDATE {table} SET status='rejected', admin_note=? WHERE id=?", (note or "Does not meet our guidelines.", item["id"]))
        wn_db.notify(item["author_id"], f"Not approved: {item['title']}",
                     f"An editor did not approve your {kind}. Reason: {note or 'it does not meet our guidelines.'} "
                     "You can edit it from My dashboard and submit again.")
        wn_db.log_moderation(kind, item["id"], "rejected", f"editor:{editor['email']}", {"note": note})
        st.rerun()
    if c[2].button("Run AI check again", key=f"ai_{table}_{item['id']}"):
        if table == "articles":
            full = wn_db.q("SELECT title, summary, body FROM articles WHERE id=?", (item["id"],), one=True)
            text = f"{full['title']}\n{full['summary']}\n{full['body']}"
        else:
            text = f"{item['title']}\n{item.get('subtitle') or ''}\n{item['description']}\n" + \
                   wn_pdf.first_pages_text(wn_db.get_book_pdf(item["id"]) or b"")
        with st.spinner("Checking..."):
            rep = wn_moderation.review(text, kind)
        wn_db.x(f"UPDATE {table} SET ai_decision=?, ai_report=? WHERE id=?", (rep["decision"], json.dumps(rep), item["id"]))
        wn_db.log_moderation(kind, item["id"], rep["decision"], rep["engine"], rep)
        st.rerun()


# ---------------------------------------------------------------- news
def _post_news(editor):
    st.markdown("Post a story to **Daily News**. Write a short summary in your own words, keep it neutral, and always "
                "credit the original source. Do not copy text or photos from other news sites.")
    result = st.session_state.pop("news_result", None)
    if result:
        st.success(result)
    with st.form(f"news_form_{st.session_state.get('news_n', 0)}"):
        c1, c2 = st.columns(2)
        section = c1.selectbox("Section", NEWS_SECTIONS)
        lang = c2.selectbox("Language", LANGUAGES)
        title = st.text_input("Headline", max_chars=140)
        summary = st.text_area("Summary (1 to 2 sentences)", max_chars=300, height=80)
        body = st.text_area("Story", height=260)
        s1, s2 = st.columns(2)
        src_name = s1.text_input("Source name (required)", placeholder="e.g. Press release, ministry website, agency")
        src_url = s2.text_input("Source link (required)", placeholder="https://")
        cover = st.file_uploader("Picture (optional: your own, licensed or free-to-use only)", type=["jpg", "jpeg", "png", "webp"])
        top = st.checkbox("Show in Today's top news")
        override = st.checkbox("Publish even if the AI asks for review (I have checked the facts and source)")
        b1, b2 = st.columns(2)
        check = b1.form_submit_button("Check with AI", width="stretch")
        publish = b2.form_submit_button("Publish story", type="primary", width="stretch")
    if not (check or publish):
        return
    if len(title.strip()) < 10 or len(body.split()) < 30 or not src_name.strip() or not src_url.strip().startswith("http"):
        st.error("Please add a headline, a story of at least 30 words, a source name and a source link starting with http.")
        return
    with st.spinner("AI review bot is checking the story..."):
        rep = wn_moderation.review(f"{title}\n{summary}\n{body}\nSource: {src_name} {src_url}", "news")
    show_review(rep)
    if check:
        return
    if rep["decision"] == "block":
        st.error("Blocked: this story breaks the universal rules (adult, abusive, violent or illegal content). Not published.")
        return
    if rep["decision"] == "review" and not override:
        st.warning("The AI asks for a second look. Fix the points above, or tick 'Publish even if the AI asks for review'.")
        return
    cover_bytes, mime = (shrink_image(cover.getvalue()) if cover else (None, None))
    nid = wn_db.x("INSERT INTO articles(kind, title, summary, body, category, language, author_id, cover, cover_mime, "
                  "source_name, source_url, is_top, status, ai_decision, ai_report, created_at, published_at) "
                  "VALUES ('news',?,?,?,?,?,?,?,?,?,?,?, 'published', ?, ?, ?, ?)",
                  (title.strip(), summary.strip(), body.strip(), section, lang, editor["id"], cover_bytes, mime,
                   src_name.strip(), src_url.strip(), int(top), rep["decision"], json.dumps(rep), wn_db.now(), wn_db.now()))
    wn_db.log_moderation("news", nid, rep["decision"], rep["engine"], rep)
    st.session_state["news_result"] = f"Published in {section}: {title.strip()}"
    st.session_state["news_n"] = st.session_state.get("news_n", 0) + 1
    st.rerun()


# ---------------------------------------------------------------- reports
def _reports():
    rows = wn_db.q("SELECT * FROM reports WHERE status='open' ORDER BY id DESC")
    if not rows:
        st.success("No open reports.")
    for r in rows:
        table = "articles" if r["item_type"] == "article" else "books"
        item = wn_db.q(f"SELECT id, title, status FROM {table} WHERE id=?", (r["item_id"],), one=True)
        with st.container(border=True):
            st.markdown(f"**{esc(r['reason'])}** on {r['item_type']}: **{esc(item['title'] if item else 'deleted item')}**  \n"
                        f"<span class='wn-meta'>{fmt_date(r['created_at'])}</span>", unsafe_allow_html=True)
            if r["details"]:
                st.write(r["details"])
            c = st.columns([1.2, 1, 1, 2])
            if item:
                c[0].page_link(PAGES["article" if table == "articles" else "book"], label="Open it", query_params={"id": item["id"]})
            if item and c[1].button("Take it down", type="primary", key=f"down_{r['id']}"):
                wn_db.x(f"UPDATE {table} SET status='unpublished' WHERE id=?", (item["id"],))
                wn_db.x("UPDATE reports SET status='resolved', action='taken down' WHERE id=?", (r["id"],))
                owner = wn_db.q(f"SELECT author_id FROM {table} WHERE id=?", (item["id"],), one=True)
                if owner and owner["author_id"]:
                    wn_db.notify(owner["author_id"], f"Taken down: {item['title']}",
                                 f"After a reader report ({r['reason']}), an editor removed this from Wordnest.")
                st.rerun()
            if c[2].button("Dismiss", key=f"dismiss_{r['id']}"):
                wn_db.x("UPDATE reports SET status='resolved', action='dismissed' WHERE id=?", (r["id"],))
                st.rerun()
    done = wn_db.q("SELECT reason, item_type, item_id, action, created_at FROM reports WHERE status='resolved' ORDER BY id DESC LIMIT 50")
    if done:
        with st.expander("Resolved reports"):
            st.dataframe(pd.DataFrame(done), hide_index=True)


# ---------------------------------------------------------------- manage content
def _manage():
    kind = st.segmented_control("Show", ["Articles", "News", "Books"], default="Articles", required=True)
    if kind == "Books":
        rows = wn_db.q("SELECT id, title, author_display AS author, category, price, status, published_at FROM books ORDER BY id DESC")
        table = "books"
    else:
        rows = wn_db.q("SELECT a.id, a.title, COALESCE(u.pen_name, u.name) AS author, a.category, a.status, a.is_top, a.views, "
                       "a.published_at FROM articles a LEFT JOIN users u ON u.id=a.author_id WHERE a.kind=? ORDER BY a.id DESC",
                       ("news" if kind == "News" else "article",))
        table = "articles"
    if not rows:
        st.caption("Nothing here yet.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, height=320)
    pick = st.selectbox("Choose an item", rows, format_func=lambda r: f"#{r['id']} · {r['title']} ({r['status']})")
    c = st.columns(5)
    if c[0].button("Publish", key="m_pub"):
        wn_db.x(f"UPDATE {table} SET status='published', published_at=COALESCE(published_at, ?) WHERE id=?", (wn_db.now(), pick["id"]))
        st.rerun()
    if c[1].button("Take down", key="m_down"):
        wn_db.x(f"UPDATE {table} SET status='unpublished' WHERE id=?", (pick["id"],))
        st.rerun()
    if kind == "News" and c[2].button("Toggle top story", key="m_top"):
        wn_db.x("UPDATE articles SET is_top = 1 - is_top WHERE id=?", (pick["id"],))
        st.rerun()
    if c[3].button("Delete forever", key="m_del"):
        st.session_state["confirm_delete"] = (table, pick["id"])
    conf = st.session_state.get("confirm_delete")
    if conf and conf == (table, pick["id"]):
        st.warning(f"Delete '{pick['title']}' permanently? This cannot be undone.")
        if st.button("Yes, delete", type="primary"):
            if table == "books":
                wn_db.x("DELETE FROM orders WHERE book_id=?", (pick["id"],))
            wn_db.x(f"DELETE FROM {table} WHERE id=?", (pick["id"],))
            st.session_state.pop("confirm_delete", None)
            st.rerun()


# ---------------------------------------------------------------- upload a book (owner's catalogue)
def _upload_book(admin):
    st.markdown("Add a book to the store directly (for example your own books). It is checked by the AI bot first.")
    msg = st.session_state.pop("book_msg", None)
    if msg:
        st.success(msg)
    with st.form("admin_book", clear_on_submit=False):
        c1, c2 = st.columns(2)
        title = c1.text_input("Title")
        author = c2.text_input("Author name shown", value="R.K. Yadav")
        subtitle = st.text_input("Subtitle (optional)")
        c3, c4, c5, c6 = st.columns(4)
        cat = c3.selectbox("Category", BOOK_CATEGORIES)
        lang = c4.selectbox("Language", LANGUAGES)
        price = c5.number_input("Price ₹ (0 = free)", 0, 5000, 299, step=10)
        sample = c6.number_input("Free sample pages", 1, 100, int(wn_db.get_setting_num("sample_pages")))
        desc = st.text_area("Description")
        c7, c8, c9 = st.columns(3)
        isbn = c7.text_input("ISBN")
        pub_on = c8.date_input("Published on", value=datetime.date.today())
        color = c9.color_picker("Cover colour (used when no cover image)", "#1F6F5C")
        pdf = st.file_uploader("Book PDF", type=["pdf"])
        cover = st.file_uploader("Cover image", type=["jpg", "jpeg", "png", "webp"])
        mine = st.checkbox("Link this book to my account for royalty reports", value=True)
        sent = st.form_submit_button("Check and publish", type="primary")
    if not sent:
        return
    if not title.strip() or not pdf:
        st.error("Title and PDF are required.")
        return
    pdf_bytes = pdf.getvalue()
    pages = wn_pdf.page_count(pdf_bytes)
    if not pages:
        st.error("That PDF could not be read.")
        return
    with st.spinner("AI review bot is checking the book..."):
        rep = wn_moderation.review(f"{title}\n{subtitle}\n{desc}\n{wn_pdf.first_pages_text(pdf_bytes)}", "book")
    show_review(rep)
    status = "published" if rep["decision"] != "block" else "ai_blocked"
    cover_bytes, mime = (shrink_image(cover.getvalue(), 1600) if cover else (None, None))
    bid = wn_db.x("INSERT INTO books(title, subtitle, author_id, author_display, description, category, language, price, pages, "
                  "isbn, published_on, cover, cover_mime, cover_color, pdf, sample_pages, status, ai_decision, ai_report, "
                  "created_at, published_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (title.strip(), subtitle.strip() or None, admin["id"] if mine else None, author.strip() or "Wordnest",
                   desc.strip(), cat, lang, int(price), pages, isbn.strip() or None, pub_on.isoformat(), cover_bytes, mime,
                   color, pdf_bytes, int(sample), status, rep["decision"], json.dumps(rep), wn_db.now(),
                   wn_db.now() if status == "published" else None))
    wn_db.log_moderation("book", bid, rep["decision"], rep["engine"], rep)
    if status == "published":
        st.session_state["book_msg"] = f"Published '{title.strip()}' ({pages} pages)."
        st.rerun()
    st.error("Blocked by the AI review. It was saved as blocked; you can publish it from Manage content after checking.")


# ---------------------------------------------------------------- users and reminders
def _users():
    users = wn_db.q("SELECT id, email, name, pen_name, role, status, strikes, created_at FROM users ORDER BY id")
    st.dataframe(pd.DataFrame(users), hide_index=True, height=260)
    pick = st.selectbox("Choose a user", users, format_func=lambda u: f"{u['email']} ({u['role']}, {u['status']})")
    c = st.columns(4)
    role = c[0].selectbox("Role", ["reader", "editor", "admin"], index=["reader", "editor", "admin"].index(pick["role"]))
    status = c[1].selectbox("Status", ["active", "suspended"], index=["active", "suspended"].index(pick["status"]))
    reset = c[2].checkbox("Reset strikes to 0")
    if c[3].button("Save user", type="primary"):
        wn_db.x("UPDATE users SET role=?, status=?, strikes=CASE WHEN ? THEN 0 ELSE strikes END WHERE id=?",
                (role, status, int(reset), pick["id"]))
        st.success("Saved.")
        st.rerun()

    st.divider()
    st.markdown("### Send a reminder")
    st.caption("Sends an in-app message to everyone's Messages tab. Email reminders will be added on the live website.")
    with st.form("reminder"):
        who = st.radio("Send to", ["Everyone who has written", "All users"], horizontal=True)
        title = st.text_input("Title", value="Reminder: Wordnest content guidelines")
        msg = st.text_area("Message", value=REMINDER_TEXT, height=170)
        if st.form_submit_button("Send reminder", type="primary"):
            if who == "All users":
                ids = [u["id"] for u in users]
            else:
                ids = [r["author_id"] for r in wn_db.q(
                    "SELECT DISTINCT author_id FROM articles WHERE kind='article' "
                    "UNION SELECT DISTINCT author_id FROM books WHERE author_id IS NOT NULL")]
            for uid in ids:
                wn_db.notify(uid, title, msg)
            st.success(f"Reminder sent to {len(ids)} people.")


# ---------------------------------------------------------------- sales
def _sales():
    rows = wn_db.q("SELECT o.id, o.created_at, b.title, b.author_display AS author, u.email AS buyer, o.amount, o.gst, "
                   "o.gateway_fee, o.author_share, o.platform_share, o.payment_ref FROM orders o "
                   "JOIN books b ON b.id=o.book_id JOIN users u ON u.id=o.user_id ORDER BY o.id DESC")
    paid = [r for r in rows if r["amount"]]
    m = st.columns(5)
    m[0].metric("Paid orders", len(paid))
    m[1].metric("Sales (incl. GST)", rupees(sum(r["amount"] for r in paid)))
    m[2].metric("GST collected", rupees(sum(r["gst"] for r in paid)))
    m[3].metric("Royalties owed to authors", rupees(sum(r["author_share"] for r in paid)))
    m[4].metric("Wordnest share", rupees(sum(r["platform_share"] for r in paid)))
    st.caption("All demo orders are simulated. GST rate and fees come from Settings; confirm them with your CA.")
    if rows:
        df = pd.DataFrame(rows)
        st.markdown("**Royalty payable by author**")
        st.dataframe(df.groupby("author", as_index=False)[["amount", "author_share"]].sum()
                     .rename(columns={"amount": "sales", "author_share": "royalty_payable"}), hide_index=True)
        st.markdown("**All orders**")
        st.dataframe(df, hide_index=True)
        st.download_button("Download orders (CSV)", df.to_csv(index=False).encode(), "wordnest_orders.csv", "text/csv")


# ---------------------------------------------------------------- settings
def _settings():
    with st.form("settings"):
        st.markdown("**Content review**")
        auto = st.toggle("Publish community articles automatically when the AI passes them (no editor step)",
                         value=wn_db.get_setting("auto_publish_on_pass") == "1",
                         help="Only works when the Gemini AI layer is on. Recommended OFF while the site is new.")
        strict = st.toggle("Strict government rule: block ANY mention of government or politics in community writing",
                           value=wn_db.get_setting("strict_government") == "1",
                           help="OFF: neutral practical mentions (e.g. 'apply on the government e-visa website') are allowed; "
                                "opinions or discussion about governments and politics are blocked. ON: every mention is blocked.")
        strikes = st.number_input("Strikes before suspension", 1, 10, int(wn_db.get_setting_num("max_strikes")))
        st.markdown("**Books and money**")
        c = st.columns(4)
        roy = c[0].number_input("Author royalty %", 0, 100, int(wn_db.get_setting_num("royalty_pct")))
        gst = c[1].number_input("GST % in price", 0.0, 28.0, wn_db.get_setting_num("gst_pct"), step=1.0)
        fee = c[2].number_input("Gateway fee %", 0.0, 10.0, wn_db.get_setting_num("gateway_fee_pct"), step=0.5)
        sample = c[3].number_input("Default free sample pages", 1, 100, int(wn_db.get_setting_num("sample_pages")))
        if st.form_submit_button("Save settings", type="primary"):
            for k, v in [("auto_publish_on_pass", int(auto)), ("strict_government", int(strict)), ("max_strikes", strikes),
                         ("royalty_pct", roy), ("gst_pct", gst), ("gateway_fee_pct", fee), ("sample_pages", sample)]:
                wn_db.set_setting(k, v)
            st.success("Settings saved.")
    st.divider()
    st.markdown("**Test the AI review bot**")
    sample_text = st.text_area("Paste any text", value="A simple guide to packing for a family trip to Kerala in the monsoon.")
    kind = st.radio("Check as", ["article", "news", "book"], horizontal=True)
    if st.button("Run check"):
        with st.spinner("Checking..."):
            show_review(wn_moderation.review(sample_text, kind))
    log = wn_db.q("SELECT created_at, item_type, item_id, decision, engine FROM moderation_log ORDER BY id DESC LIMIT 100")
    if log:
        with st.expander("Moderation log (last 100 decisions)"):
            st.dataframe(pd.DataFrame(log), hide_index=True)
