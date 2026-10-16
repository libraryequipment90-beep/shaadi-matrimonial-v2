from datetime import datetime
from urllib.parse import urlparse

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app import csrf, db, limiter
from app.forms import (
    CITIES,
    ContactForm,
    LoginForm,
    NewsletterForm,
    ProfileForm,
    RegisterForm,
    SearchForm,
)
from app.models import (
    ContactMessage,
    Favourite,
    Interest,
    Newsletter,
    Profile,
    SuccessStory,
    User,
    date_of_birth_bounds,
)


PLACEHOLDER_PHOTO = "/static/avatar.svg"


def register_routes(app):
    @app.context_processor
    def inject_globals():
        site_url = request.url_root.rstrip("/")
        canonical_url = site_url + request.path
        return {
            "cities": CITIES,
            "now_year": datetime.utcnow().year,
            "placeholder_photo": PLACEHOLDER_PHOTO,
            "site_url": site_url,
            "canonical_url": canonical_url,
            "default_og_image": site_url + url_for("static", filename="favicon.svg"),
        }

    def favourite_ids():
        if not current_user.is_authenticated:
            return set()
        rows = Favourite.query.filter_by(user_id=current_user.id).all()
        return {row.target_user_id for row in rows}

    def visible_profiles():
        return Profile.query.filter(Profile.is_visible.is_(True))

    def apply_filters(
        query,
        looking_for,
        min_age,
        max_age,
        religion,
        city,
        education,
        exclude_id=None,
        gotra=None,
        manglik=None,
        district=None,
    ):
        if looking_for and looking_for not in ("Any", "any"):
            query = query.filter(Profile.gender == looking_for)
        if religion and religion not in ("Any", "Any religion", ""):
            query = query.filter(Profile.religion == religion)
        if gotra:
            query = query.filter(func.lower(Profile.gotra).like("%" + gotra.strip().lower() + "%"))
        if manglik and manglik not in ("Any", ""):
            query = query.filter(Profile.manglik == manglik)
        if city:
            query = query.filter(func.lower(Profile.city).like("%" + city.strip().lower() + "%"))
        if district:
            query = query.filter(func.lower(Profile.district).like("%" + district.strip().lower() + "%"))
        if education and education not in ("Any", "Any education", ""):
            query = query.filter(Profile.education == education)
        if exclude_id:
            query = query.filter(Profile.user_id != exclude_id)
        min_age = int(min_age) if min_age else 18
        max_age = int(max_age) if max_age else 80
        min_age = max(18, min(80, min_age))
        max_age = max(18, min(80, max_age))
        if min_age > max_age:
            min_age, max_age = max_age, min_age
        earliest, latest = date_of_birth_bounds(min_age, max_age)
        query = query.filter(Profile.date_of_birth <= latest, Profile.date_of_birth >= earliest)
        return query

    def parse_age_range(value):
        if not value:
            return 21, 35
        digits = [int(part) for part in "".join(ch if ch.isdigit() else " " for ch in value).split() if part.isdigit()]
        if len(digits) >= 2:
            return digits[0], digits[1]
        if len(digits) == 1:
            return digits[0], digits[0]
        return 21, 35

    def safe_next(target):
        if target:
            parsed = urlparse(target)
            if not parsed.netloc and parsed.path.startswith("/"):
                return target
        return url_for("home")

    @app.route("/")
    def home():
        stories = SuccessStory.query.order_by(SuccessStory.id).limit(4).all()
        profiles = (
            visible_profiles()
            .order_by(Profile.updated_at.desc())
            .limit(3)
            .all()
        )
        return render_template(
            "index.html",
            active="home",
            stories=stories,
            profiles=profiles,
            fav_ids=favourite_ids(),
        )

    @app.route("/search", methods=["GET", "POST"])
    def search():
        form = SearchForm()
        if request.method == "GET":
            looking = request.args.get("looking_for") or request.args.get("seeking")
            if looking in ("Bride", "Female"):
                form.looking_for.data = "Female"
            elif looking in ("Groom", "Male"):
                form.looking_for.data = "Male"
            elif looking == "Any":
                form.looking_for.data = "Any"
            if request.args.get("min_age"):
                form.min_age.data = int(request.args.get("min_age"))
            if request.args.get("max_age"):
                form.max_age.data = int(request.args.get("max_age"))
            if request.args.get("age"):
                low, high = parse_age_range(request.args.get("age"))
                form.min_age.data = low
                form.max_age.data = high
            if request.args.get("religion"):
                form.religion.data = request.args.get("religion")
            if request.args.get("gotra"):
                form.gotra.data = request.args.get("gotra")
            if request.args.get("manglik"):
                form.manglik.data = request.args.get("manglik")
            if request.args.get("city"):
                form.city.data = request.args.get("city")
            if request.args.get("district"):
                form.district.data = request.args.get("district")
            if request.args.get("education"):
                form.education.data = request.args.get("education")

        submitted = request.method == "POST" or any(request.args.get(k) for k in (
            "looking_for", "seeking", "min_age", "max_age", "age", "religion",
            "gotra", "manglik", "city", "district", "education",
        ))
        if request.method == "POST" and not form.validate():
            return render_template(
                "search.html",
                active="search",
                form=form,
                profiles=[],
                total=0,
                page=1,
                pages=1,
                fav_ids=favourite_ids(),
                searched=True,
            )
        if request.method == "POST" and form.validate():
            return redirect(
                url_for(
                    "search",
                    looking_for=form.looking_for.data,
                    min_age=form.min_age.data or 18,
                    max_age=form.max_age.data or 80,
                    religion=form.religion.data,
                    gotra=form.gotra.data or "",
                    manglik=form.manglik.data,
                    city=form.city.data or "",
                    district=form.district.data or "",
                    education=form.education.data,
                )
            )

        page = max(1, request.args.get("page", 1, type=int))
        per_page = app.config.get("PAGE_SIZE", 9)
        query = visible_profiles()
        exclude = current_user.id if current_user.is_authenticated else None
        if submitted:
            query = apply_filters(
                query,
                form.looking_for.data,
                form.min_age.data,
                form.max_age.data,
                form.religion.data,
                form.city.data,
                form.education.data,
                exclude,
                gotra=form.gotra.data,
                manglik=form.manglik.data,
                district=form.district.data,
            )
        else:
            if exclude:
                query = query.filter(Profile.user_id != exclude)
        pagination = query.order_by(Profile.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return render_template(
            "search.html",
            active="search",
            form=form,
            profiles=pagination.items,
            total=pagination.total,
            page=pagination.page,
            pages=pagination.pages,
            fav_ids=favourite_ids(),
            searched=submitted,
        )

    @app.route("/stories")
    def stories():
        items = SuccessStory.query.order_by(SuccessStory.id).all()
        return render_template("stories.html", active="stories", stories=items)

    @app.route("/services")
    def services():
        return render_template("services.html", active="services")

    @app.route("/community")
    def community():
        page = max(1, request.args.get("page", 1, type=int))
        query = visible_profiles()
        if current_user.is_authenticated:
            query = query.filter(Profile.user_id != current_user.id)
        pagination = query.order_by(Profile.updated_at.desc()).paginate(
            page=page, per_page=app.config.get("PAGE_SIZE", 9), error_out=False
        )
        return render_template(
            "community.html",
            active="community",
            profiles=pagination.items,
            total=pagination.total,
            page=pagination.page,
            pages=pagination.pages,
            fav_ids=favourite_ids(),
        )

    @app.route("/help", methods=["GET", "POST"])
    def help():
        form = ContactForm()
        if current_user.is_authenticated and request.method == "GET":
            form.name.data = current_user.profile.full_name if current_user.profile else ""
            form.email.data = current_user.email
        if form.validate_on_submit():
            db.session.add(
                ContactMessage(
                    name=form.name.data.strip(),
                    email=form.email.data.strip().lower(),
                    topic=form.topic.data,
                    message=form.message.data.strip(),
                )
            )
            db.session.commit()
            flash("Your message was saved. We have not sent an email because email delivery is not configured.", "success")
            return redirect(url_for("help"))
        return render_template("help.html", active="help", form=form)

    @app.route("/register", methods=["GET", "POST"])
    @limiter.limit("8 per minute")
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("profile"))
        form = RegisterForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            if User.query.filter(func.lower(User.email) == email).first():
                form.email.errors.append("An account with this email already exists. Please log in.")
                return render_template("register.html", active="register", form=form)
            user = User(email=email, created_for=form.created_for.data, is_demo=False)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()
            profile = Profile(
                user_id=user.id,
                full_name=form.full_name.data.strip(),
                mobile=(form.mobile.data or "").strip(),
                gender=form.gender.data,
                date_of_birth=form.date_of_birth.data,
                religion=form.religion.data,
                gotra=(form.gotra.data or "").strip(),
                manglik=form.manglik.data,
                city=form.city.data.strip(),
                district=(form.district.data or "").strip(),
                education=form.education.data,
                profession=form.profession.data.strip(),
                work=(form.work.data or "").strip(),
                father_name=(form.father_name.data or "").strip(),
                father_occupation=(form.father_occupation.data or "").strip(),
                mother_name=(form.mother_name.data or "").strip(),
                mother_occupation=(form.mother_occupation.data or "").strip(),
                brothers=form.brothers.data or 0,
                sisters=form.sisters.data or 0,
                family_village=(form.family_village.data or "").strip(),
                family_background=(form.family_background.data or "").strip(),
                current_address=(form.current_address.data or "").strip(),
                about_me=(form.about_me.data or "").strip(),
                photo_url="",
                is_visible=True,
            )
            db.session.add(profile)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                form.email.errors.append("An account with this email already exists. Please log in.")
                return render_template("register.html", active="register", form=form)
            login_user(user)
            flash("Welcome. Your profile has been created.", "success")
            return redirect(url_for("profile"))
        return render_template("register.html", active="register", form=form)

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("10 per minute")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("profile"))
        form = LoginForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            user = User.query.filter(func.lower(User.email) == email).first()
            if not user or not user.check_password(form.password.data):
                flash("Invalid email or password.", "error")
                return render_template("login.html", active="login", form=form)
            login_user(user, remember=True)
            flash("You are now logged in.", "success")
            return redirect(safe_next(request.args.get("next")))
        return render_template("login.html", active="login", form=form)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("home"))

    @app.route("/profile")
    @login_required
    def profile():
        me = current_user.profile
        if not me:
            abort(404)
        favs = (
            Profile.query.join(Favourite, Favourite.target_user_id == Profile.user_id)
            .filter(Favourite.user_id == current_user.id)
            .order_by(Favourite.created_at.desc())
            .all()
        )
        return render_template(
            "profile.html",
            active="profile",
            profile=me,
            favs=favs,
            fav_ids=favourite_ids(),
        )

    @app.route("/edit-profile", methods=["GET", "POST"])
    @login_required
    def edit_profile():
        me = current_user.profile
        if not me:
            abort(404)
        form = ProfileForm(obj=me)
        if form.validate_on_submit():
            me.full_name = form.full_name.data.strip()
            me.mobile = (form.mobile.data or "").strip()
            me.gender = form.gender.data
            me.date_of_birth = form.date_of_birth.data
            me.religion = form.religion.data
            me.gotra = (form.gotra.data or "").strip()
            me.manglik = form.manglik.data
            me.city = form.city.data.strip()
            me.district = (form.district.data or "").strip()
            me.education = form.education.data
            me.profession = form.profession.data.strip()
            me.work = (form.work.data or "").strip()
            me.father_name = (form.father_name.data or "").strip()
            me.father_occupation = (form.father_occupation.data or "").strip()
            me.mother_name = (form.mother_name.data or "").strip()
            me.mother_occupation = (form.mother_occupation.data or "").strip()
            me.brothers = form.brothers.data or 0
            me.sisters = form.sisters.data or 0
            me.family_village = (form.family_village.data or "").strip()
            me.family_background = (form.family_background.data or "").strip()
            me.current_address = (form.current_address.data or "").strip()
            me.about_me = (form.about_me.data or "").strip()
            me.photo_url = (form.photo_url.data or "").strip()
            me.is_visible = bool(form.is_visible.data)
            db.session.commit()
            flash("Your profile was updated.", "success")
            return redirect(url_for("profile"))
        if request.method == "GET":
            form.is_visible.data = me.is_visible
        return render_template("edit_profile.html", active="profile", form=form, profile=me)

    @app.route("/members/<int:user_id>")
    def member_detail(user_id):
        member = db.session.get(User, user_id)
        if not member or not member.profile:
            abort(404)
        person = member.profile
        is_owner = current_user.is_authenticated and current_user.id == member.id
        if not person.is_visible and not is_owner:
            abort(404)
        return render_template(
            "member.html",
            active="community",
            person=person,
            member=member,
            is_owner=is_owner,
            is_fav=current_user.is_authenticated and member.id in favourite_ids(),
        )

    @app.route("/favourite/<int:user_id>", methods=["POST"])
    @login_required
    def toggle_favourite(user_id):
        if user_id == current_user.id:
            flash("You cannot shortlist your own profile.", "error")
            return redirect(request.referrer or url_for("community"))
        target = db.session.get(User, user_id)
        if not target or not target.profile or not target.profile.is_visible:
            abort(404)
        existing = Favourite.query.filter_by(user_id=current_user.id, target_user_id=user_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            flash("Removed from your shortlist.", "success")
        else:
            db.session.add(Favourite(user_id=current_user.id, target_user_id=user_id))
            try:
                db.session.commit()
                flash("Added to your shortlist.", "success")
            except IntegrityError:
                db.session.rollback()
                flash("This profile is already in your shortlist.", "error")
        return redirect(request.referrer or url_for("community"))

    @app.route("/interest/<int:user_id>", methods=["POST"])
    @login_required
    def send_interest(user_id):
        if user_id == current_user.id:
            flash("You cannot send interest to yourself.", "error")
            return redirect(request.referrer or url_for("profile"))
        target = db.session.get(User, user_id)
        if not target or not target.profile or not target.profile.is_visible:
            abort(404)
        existing = Interest.query.filter_by(sender_id=current_user.id, receiver_id=user_id).first()
        if existing:
            flash("You already sent interest to this profile.", "error")
            return redirect(request.referrer or url_for("member_detail", user_id=user_id))
        incoming = Interest.query.filter_by(sender_id=user_id, receiver_id=current_user.id).first()
        if incoming and incoming.status == "pending":
            incoming.status = "accepted"
            db.session.commit()
            flash("This member had already sent you interest. You are now connected.", "success")
            return redirect(request.referrer or url_for("member_detail", user_id=user_id))
        db.session.add(Interest(sender_id=current_user.id, receiver_id=user_id, status="pending"))
        try:
            db.session.commit()
            flash("Interest sent. The member can review it from their Connections page.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("You already sent interest to this profile.", "error")
        return redirect(request.referrer or url_for("member_detail", user_id=user_id))

    @app.route("/connections")
    @login_required
    def connections():
        received = (
            Interest.query.filter_by(receiver_id=current_user.id)
            .order_by(Interest.created_at.desc())
            .all()
        )
        sent = (
            Interest.query.filter_by(sender_id=current_user.id)
            .order_by(Interest.created_at.desc())
            .all()
        )
        return render_template(
            "connections.html",
            active="connections",
            received=received,
            sent=sent,
        )

    @app.route("/interest/<int:interest_id>/respond", methods=["POST"])
    @login_required
    def respond_interest(interest_id):
        item = db.session.get(Interest, interest_id)
        if not item or item.receiver_id != current_user.id:
            abort(404)
        action = (request.form.get("action") or "").strip().lower()
        if action not in ("accept", "decline"):
            flash("Invalid action.", "error")
            return redirect(url_for("connections"))
        item.status = "accepted" if action == "accept" else "declined"
        db.session.commit()
        flash("Interest {}".format(item.status), "success")
        return redirect(url_for("connections"))

    @app.route("/subscribe", methods=["POST"])
    def subscribe():
        form = NewsletterForm()
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            if not Newsletter.query.filter(func.lower(Newsletter.email) == email).first():
                db.session.add(Newsletter(email=email))
                db.session.commit()
            flash("Your email was saved for newsletters. No email was sent.", "success")
        else:
            flash("Please enter a valid email address.", "error")
        return redirect(request.referrer or url_for("home"))

    @app.route("/robots.txt")
    def robots_txt():
        site = request.url_root.rstrip("/")
        lines = [
            "User-agent: *",
            "Allow: /",
            "Disallow: /profile",
            "Disallow: /edit-profile",
            "Disallow: /connections",
            "Disallow: /login",
            "Disallow: /logout",
            "Disallow: /favourite/",
            "Disallow: /interest/",
            f"Sitemap: {site}/sitemap.xml",
        ]
        return app.response_class("\n".join(lines) + "\n", mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap_xml():
        site = request.url_root.rstrip("/")
        static_pages = [
            ("home", 1.0),
            ("search", 0.9),
            ("community", 0.9),
            ("stories", 0.7),
            ("services", 0.7),
            ("help", 0.6),
            ("register", 0.6),
        ]
        urls = []
        for endpoint, priority in static_pages:
            urls.append((site + url_for(endpoint), priority, "weekly"))
        members = (
            db.session.query(Profile.user_id, Profile.updated_at)
            .filter(Profile.is_visible.is_(True))
            .order_by(Profile.updated_at.desc())
            .limit(500)
            .all()
        )
        for user_id, updated_at in members:
            lastmod = updated_at.strftime("%Y-%m-%d") if updated_at else None
            urls.append((f"{site}/members/{user_id}", 0.5, "daily", lastmod))

        parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for item in urls:
            loc, priority, changefreq = item[0], item[1], item[2]
            lastmod = item[3] if len(item) > 3 else None
            parts.append("<url>")
            parts.append(f"<loc>{loc}</loc>")
            if lastmod:
                parts.append(f"<lastmod>{lastmod}</lastmod>")
            parts.append(f"<changefreq>{changefreq}</changefreq>")
            parts.append(f"<priority>{priority}</priority>")
            parts.append("</url>")
        parts.append("</urlset>")
        return app.response_class("\n".join(parts), mimetype="application/xml")

    @app.route("/health")
    @csrf.exempt
    def health():
        return {"status": "ok"}
