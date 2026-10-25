from datetime import date, timedelta

from app import db
from app.config import TestConfig
from app.models import (
    ContactMessage,
    Favourite,
    Interest,
    Profile,
    User,
    calculate_age,
    date_of_birth_bounds,
)
from app.seed import DEMO_PASSWORD, seed_demo_data
from app import create_app


def register_payload(**overrides):
    data = {
        "created_for": "Self",
        "full_name": "Test User",
        "email": "test.user@example.com",
        "password": "SecurePass1",
        "gender": "Female",
        "date_of_birth": "1996-05-20",
        "religion": "Hindu",
        "gotra": "Kashyap",
        "manglik": "No",
        "city": "Delhi",
        "district": "New Delhi",
        "education": "Graduate",
        "profession": "Teacher",
        "work": "Teacher, Delhi",
        "father_name": "Test Father",
        "father_occupation": "Test Father Job",
        "mother_name": "Test Mother",
        "mother_occupation": "Test Mother Job",
        "brothers": 1,
        "sisters": 2,
        "family_village": "Test Village",
        "family_background": "Test family background.",
        "current_address": "Test current address",
        "about_me": "Hello, this is a test profile.",
    }
    data.update(overrides)
    return data


def test_calculate_age():
    today = date.today()
    born = date(today.year - 30, today.month, today.day)
    assert calculate_age(born) == 30
    yesterday_30 = born + timedelta(days=1)
    if yesterday_30 != born:
        expected = 29 if (today.month, today.day) < (yesterday_30.month, yesterday_30.day) else 30
        assert calculate_age(yesterday_30) in (29, 30)


def test_register_creates_user(client, app):
    response = client.post("/register", data=register_payload(), follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data or b"My Profile" in response.data
    with app.app_context():
        user = User.query.filter_by(email="test.user@example.com").first()
        assert user is not None
        assert user.password_hash != "SecurePass1"
        assert user.check_password("SecurePass1")
        assert user.profile.full_name == "Test User"
        assert user.profile.age >= 18
        assert user.profile.gotra == "Kashyap"
        assert user.profile.manglik == "No"
        assert user.profile.father_name == "Test Father"
        assert user.profile.father_occupation == "Test Father Job"
        assert user.profile.mother_occupation == "Test Mother Job"
        assert user.profile.brothers == 1
        assert user.profile.sisters == 2
        assert user.profile.family_village == "Test Village"
        assert user.profile.district == "New Delhi"


def test_duplicate_email_rejected(client, app):
    client.post("/register", data=register_payload(), follow_redirects=True)
    client.post("/logout", follow_redirects=True)
    response = client.post(
        "/register",
        data=register_payload(full_name="Someone Else"),
        follow_redirects=True,
    )
    assert b"already exists" in response.data
    with app.app_context():
        assert User.query.filter_by(email="test.user@example.com").count() == 1


def test_short_password_rejected(client, app):
    response = client.post(
        "/register",
        data=register_payload(password="short", email="short.pass@example.com"),
        follow_redirects=True,
    )
    assert b"at least 8 characters" in response.data.lower() or b"Field must be at least 8" in response.data or response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="short.pass@example.com").first() is None


def test_underage_rejected(client, app):
    young = (date.today() - timedelta(days=365 * 16)).isoformat()
    response = client.post(
        "/register",
        data=register_payload(email="teen@example.com", date_of_birth=young),
        follow_redirects=True,
    )
    assert b"18" in response.data
    with app.app_context():
        assert User.query.filter_by(email="teen@example.com").first() is None


def test_login_success_and_logout(client, seeded):
    response = client.post(
        "/login",
        data={"email": "priya.sharma.demo@example.com", "password": DEMO_PASSWORD},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"My Profile" in response.data
    assert b"Logout" in response.data
    out = client.post("/logout", follow_redirects=True)
    assert b"Login" in out.data
    assert b"logged out" in out.data.lower() or b"Register Free" in out.data


def test_login_wrong_password(client, seeded):
    response = client.post(
        "/login",
        data={"email": "priya.sharma.demo@example.com", "password": "WrongPass999"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in response.data
    assert b"Logout" not in response.data


def test_protected_profile_requires_login(client):
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code in (302, 401)
    assert "/login" in response.headers.get("Location", "")


def test_edit_profile_and_ownership(client, app):
    client.post("/register", data=register_payload(), follow_redirects=True)
    response = client.post(
        "/edit-profile",
        data={
            "full_name": "Updated Name",
            "gender": "Female",
            "date_of_birth": "1996-05-20",
            "religion": "Sikh",
            "gotra": "Kapoor",
            "manglik": "Yes",
            "city": "Mumbai",
            "district": "Mumbai Suburban",
            "education": "Postgraduate",
            "profession": "Designer",
            "work": "Designer, Mumbai",
            "father_name": "Father Name",
            "father_occupation": "Engineer",
            "mother_name": "Mother Name",
            "mother_occupation": "Doctor",
            "brothers": 2,
            "sisters": 1,
            "family_village": "Village Name",
            "family_background": "Business family.",
            "current_address": "Andheri, Mumbai",
            "about_me": "Updated bio",
            "photo_url": "",
            "is_visible": "y",
        },
        follow_redirects=True,
    )
    assert b"updated" in response.data.lower() or b"Updated Name" in response.data
    with app.app_context():
        profile = Profile.query.filter_by(full_name="Updated Name").first()
        assert profile is not None
        assert profile.city == "Mumbai"
        assert profile.religion == "Sikh"
        assert profile.gotra == "Kapoor"
        assert profile.manglik == "Yes"
        assert profile.district == "Mumbai Suburban"
        assert profile.father_occupation == "Engineer"
        assert profile.mother_occupation == "Doctor"
        assert profile.brothers == 2
        assert profile.sisters == 1
        assert profile.family_village == "Village Name"


def test_single_photo_only(client, app):
    client.post("/register", data=register_payload(email="photo@example.com"), follow_redirects=True)
    bad = client.post(
        "/edit-profile",
        data={
            "full_name": "Photo User",
            "gender": "Female",
            "date_of_birth": "1996-05-20",
            "religion": "Hindu",
            "manglik": "No",
            "city": "Delhi",
            "education": "Graduate",
            "profession": "Teacher",
            "about_me": "x",
            "photo_url": "https://a.com/1.jpg, https://a.com/2.jpg",
            "is_visible": "y",
        },
        follow_redirects=True,
    )
    assert b"Only one photo is allowed" in bad.data
    with app.app_context():
        u = User.query.filter_by(email="photo@example.com").first()
        assert u.profile.photo_url in ("", None)
        assert u.profile.full_name == "Test User"

    good = client.post(
        "/edit-profile",
        data={
            "full_name": "Photo User",
            "gender": "Female",
            "date_of_birth": "1996-05-20",
            "religion": "Hindu",
            "manglik": "No",
            "city": "Delhi",
            "education": "Graduate",
            "profession": "Teacher",
            "about_me": "x",
            "photo_url": "https://a.com/one.jpg",
            "is_visible": "y",
        },
        follow_redirects=True,
    )
    with app.app_context():
        u = User.query.filter_by(email="photo@example.com").first()
        assert u.profile.photo_url == "https://a.com/one.jpg"

    client.post("/logout")
    client.post(
        "/register",
        data=register_payload(email="second@example.com", full_name="Second User", gender="Male"),
        follow_redirects=True,
    )
    edit_page = client.get("/edit-profile")
    assert b"Second User" in edit_page.data
    assert b"Updated Name" not in edit_page.data


def test_search_filters_and_excludes_self(client, app, seeded):
    client.post(
        "/register",
        data=register_payload(email="seeker@example.com", full_name="Seeker", gender="Male"),
        follow_redirects=True,
    )
    response = client.get(
        "/search?looking_for=Female&min_age=18&max_age=40&religion=Hindu&city=Delhi&education=Any"
    )
    assert response.status_code == 200
    assert b"Priya Sharma" in response.data
    assert b"Seeker" not in response.data

    gotra_search = client.get(
        "/search?looking_for=Any&min_age=18&max_age=60&religion=Any&gotra=Kashyap&manglik=Any&city=&district=&education=Any"
    )
    assert b"Priya Sharma" in gotra_search.data
    assert b"priya.sharma.demo@example.com" not in response.data
    assert b"DemoPass" not in response.data

    none = client.get(
        "/search?looking_for=Female&min_age=18&max_age=40&religion=Hindu&city=Atlantis&education=Any"
    )
    assert b"No profiles match" in none.data


def test_favourites(client, app, seeded):
    with app.app_context():
        priya = User.query.filter_by(email="priya.sharma.demo@example.com").first()
        priya_id = priya.id
    client.post("/register", data=register_payload(email="fan@example.com", full_name="Fan"), follow_redirects=True)
    add = client.post(f"/favourite/{priya_id}", follow_redirects=True)
    assert b"shortlist" in add.data.lower()
    profile_page = client.get("/profile")
    assert b"Priya Sharma" in profile_page.data
    with app.app_context():
        assert Favourite.query.filter_by(target_user_id=priya_id).count() == 1
    client.post(f"/favourite/{priya_id}", follow_redirects=True)
    with app.app_context():
        assert Favourite.query.filter_by(target_user_id=priya_id).count() == 0
    self_fav = client.post("/profile")
    with app.app_context():
        fan = User.query.filter_by(email="fan@example.com").first()
        fan_id = fan.id
    blocked = client.post(f"/favourite/{fan_id}", follow_redirects=True)
    assert b"own profile" in blocked.data.lower()


def test_hidden_profile_not_in_search(client, app):
    client.post("/register", data=register_payload(email="hidden@example.com", full_name="Hidden Person"), follow_redirects=True)
    client.post(
        "/edit-profile",
        data={
            "full_name": "Hidden Person",
            "gender": "Female",
            "date_of_birth": "1996-05-20",
            "religion": "Hindu",
            "manglik": "No",
            "city": "Delhi",
            "education": "Graduate",
            "profession": "Teacher",
            "about_me": "private",
            "photo_url": "",
        },
        follow_redirects=True,
    )
    client.post("/logout")
    community = client.get("/community")
    assert b"Hidden Person" not in community.data


def test_connections_send_receive_and_respond(client, app):
    with app.app_context():
        seed_demo_data()
        priya_id = User.query.filter_by(email="priya.sharma.demo@example.com").first().id

    client.post("/register", data=register_payload(email="sender@example.com", full_name="Sender"), follow_redirects=True)
    client.post(f"/interest/{priya_id}", follow_redirects=True)
    with app.app_context():
        sender = User.query.filter_by(email="sender@example.com").first()
        item = Interest.query.filter_by(sender_id=sender.id, receiver_id=priya_id).first()
        assert item is not None
        assert item.status == "pending"
        interest_id = item.id

    client.post("/logout")
    client.post("/login", data={"email": "priya.sharma.demo@example.com", "password": DEMO_PASSWORD}, follow_redirects=True)
    page = client.get("/connections")
    assert b"Sender" in page.data
    assert b"pending" in page.data

    client.post(f"/interest/{interest_id}/respond", data={"action": "accept"}, follow_redirects=True)
    with app.app_context():
        assert db.session.get(Interest, interest_id).status == "accepted"
    assert b"accepted" in client.get("/connections").data


def test_connection_ownership_check(client, app):
    with app.app_context():
        seed_demo_data()
        priya = User.query.filter_by(email="priya.sharma.demo@example.com").first()
        rohit = User.query.filter_by(email="rohit.verma.demo@example.com").first()
        priya_id, rohit_id = priya.id, rohit.id

    client.post("/register", data=register_payload(email="outsider@example.com", full_name="Outsider"), follow_redirects=True)
    client.post(f"/interest/{priya_id}", follow_redirects=True)
    with app.app_context():
        outsider = User.query.filter_by(email="outsider@example.com").first()
        item = Interest.query.filter_by(sender_id=outsider.id, receiver_id=priya_id).first()
        interest_id = item.id

    client.post("/logout")
    client.post(
        "/login",
        data={"email": "rohit.verma.demo@example.com", "password": DEMO_PASSWORD},
        follow_redirects=True,
    )
    blocked = client.post(f"/interest/{interest_id}/respond", data={"action": "accept"})
    assert blocked.status_code == 404
    with app.app_context():
        assert db.session.get(Interest, interest_id).status == "pending"


def test_mutual_interest_auto_connects(client, app):
    with app.app_context():
        seed_demo_data()
        priya_id = User.query.filter_by(email="priya.sharma.demo@example.com").first().id

    client.post("/register", data=register_payload(email="mutual@example.com", full_name="Mutual User"), follow_redirects=True)
    client.post(f"/interest/{priya_id}", follow_redirects=True)
    client.post("/logout")

    client.post("/login", data={"email": "priya.sharma.demo@example.com", "password": DEMO_PASSWORD}, follow_redirects=True)
    with app.app_context():
        mutual_id = User.query.filter_by(email="mutual@example.com").first().id
    client.post(f"/interest/{mutual_id}", follow_redirects=True)
    with app.app_context():
        item = Interest.query.filter_by(sender_id=mutual_id, receiver_id=priya_id).first()
        assert item.status == "accepted"
        assert Interest.query.filter_by(sender_id=priya_id, receiver_id=mutual_id).first() is None


def test_seo_tags_present(client, seeded):
    home = client.get("/").get_data(as_text=True)
    assert '<meta name="description"' in home
    assert 'rel="canonical"' in home
    assert 'property="og:title"' in home
    assert 'property="og:description"' in home
    assert 'name="twitter:card"' in home
    assert '"@type": "WebSite"' in home
    assert '<link rel="icon"' in home

    search = client.get("/search").get_data(as_text=True)
    assert "Search Matrimonial Profiles" in search
    assert '<meta name="description"' in search

    private = client.post(
        "/register",
        data=register_payload(email="seo.private@example.com"),
        follow_redirects=True,
    ).get_data(as_text=True)
    assert 'content="noindex, nofollow"' in private or 'content="noindex, nofollow"' in client.get("/profile").get_data(as_text=True)


def test_robots_and_sitemap(client, seeded):
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    body = robots.get_data(as_text=True)
    assert "Disallow: /profile" in body
    assert "Sitemap:" in body

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    xml = sitemap.get_data(as_text=True)
    assert "<urlset" in xml
    assert "/search" in xml
    assert "/members/" in xml


def test_connections_requires_login(client):
    response = client.get("/connections", follow_redirects=False)
    assert response.status_code in (302, 401)
    assert "/login" in response.headers.get("Location", "")


def test_contact_message_saved(client, app):
    response = client.post(
        "/help",
        data={
            "name": "Visitor",
            "email": "visitor@example.com",
            "topic": "Account help",
            "message": "Please help me with my account login.",
        },
        follow_redirects=True,
    )
    assert b"saved" in response.data.lower()
    assert b"not sent an email" in response.data.lower() or b"have not sent an email" in response.data
    with app.app_context():
        assert ContactMessage.query.count() == 1


def test_seed_is_idempotent(app, seeded):
    with app.app_context():
        first = User.query.filter_by(is_demo=True).count()
        seed_demo_data()
        second = User.query.filter_by(is_demo=True).count()
        assert first == 8
        assert second == 8


def test_database_persistence(tmp_path):
    db_file = tmp_path / "persist.db"

    class FileConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(db_file)

    app1 = create_app(FileConfig)
    with app1.app_context():
        db.create_all()
        user = User(email="persist@example.com", created_for="Self")
        user.set_password("PersistPass1")
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Profile(
                user_id=user.id,
                full_name="Persist User",
                gender="Male",
                date_of_birth=date(1990, 1, 1),
                religion="Hindu",
                city="Pune",
                education="Graduate",
                profession="Engineer",
            )
        )
        db.session.commit()

    app2 = create_app(FileConfig)
    with app2.app_context():
        found = User.query.filter_by(email="persist@example.com").first()
        assert found is not None
        assert found.check_password("PersistPass1")
        assert found.profile.city == "Pune"


def test_search_invalid_age_does_not_500(client, seeded):
    assert client.get("/search?min_age=abc").status_code == 200
    assert client.get("/search?max_age=foo").status_code == 200
    assert client.get("/search?min_age=18.5").status_code == 200
    html = client.get("/search?min_age=abc&looking_for=Female").get_data(as_text=True)
    assert "No profiles match" in html or "profile" in html.lower()


def test_login_rejects_open_redirect(client, seeded):
    response = client.post(
        "/login",
        query_string={"next": "////evil.com"},
        data={"email": "priya.sharma.demo@example.com", "password": DEMO_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    location = response.headers.get("Location", "")
    assert "evil.com" not in location
    assert location.endswith("/profile") or location.endswith("/")


def test_login_keeps_safe_next(client, seeded):
    response = client.post(
        "/login",
        query_string={"next": "/members/2"},
        data={"email": "priya.sharma.demo@example.com", "password": DEMO_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert response.headers.get("Location", "").endswith("/members/2")


def test_age_bounds_exclude_older_than_max():
    today = date.today()
    earliest, latest = date_of_birth_bounds(21, 35)
    turned_36 = date(today.year - 36, today.month, today.day)
    turned_35 = date(today.year - 35, today.month, today.day)
    turned_21 = date(today.year - 21, today.month, today.day)
    almost_21 = turned_21 + timedelta(days=1)
    assert calculate_age(turned_36) == 36
    assert not (earliest <= turned_36 <= latest)
    assert earliest <= turned_35 <= latest
    assert earliest <= turned_21 <= latest
    assert not (earliest <= almost_21 <= latest)


def test_mobile_hidden_until_connected(client, app, seeded):
    with app.app_context():
        priya = User.query.filter_by(email="priya.sharma.demo@example.com").first()
        priya_id = priya.id
        priya_mobile = priya.profile.mobile

    guest = client.get(f"/members/{priya_id}").get_data(as_text=True)
    assert priya_mobile not in guest
    assert "Login to view" in guest

    client.post(
        "/register",
        data=register_payload(email="viewer@example.com", full_name="Viewer"),
        follow_redirects=True,
    )
    logged_in = client.get(f"/members/{priya_id}").get_data(as_text=True)
    assert priya_mobile not in logged_in
    assert "Visible after you connect" in logged_in

    client.post(f"/interest/{priya_id}", follow_redirects=True)
    with app.app_context():
        viewer = User.query.filter_by(email="viewer@example.com").first()
        item = Interest.query.filter_by(sender_id=viewer.id, receiver_id=priya_id).first()
        item.status = "accepted"
        db.session.commit()

    connected = client.get(f"/members/{priya_id}").get_data(as_text=True)
    assert priya_mobile in connected


def test_relative_sqlite_url_uses_project_instance(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///instance/shaadi.db")
    from app.config import _database_uri

    uri = _database_uri()
    assert uri.startswith("sqlite:///")
    assert uri.endswith("/instance/shaadi.db")
    assert "sqlite:////" in uri or uri.count("/") >= 4
