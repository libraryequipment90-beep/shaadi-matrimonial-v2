from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_for = db.Column(db.String(40), default="Self")
    is_demo = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    favourites = db.relationship(
        "Favourite",
        foreign_keys="Favourite.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), default="")
    gender = db.Column(db.String(20), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    religion = db.Column(db.String(40), nullable=False, index=True)
    city = db.Column(db.String(80), nullable=False, index=True)
    education = db.Column(db.String(80), nullable=False)
    profession = db.Column(db.String(120), nullable=False)
    work = db.Column(db.String(160), default="")
    gotra = db.Column(db.String(80), default="")
    manglik = db.Column(db.String(20), default="")
    family_background = db.Column(db.Text, default="")
    father_name = db.Column(db.String(120), default="")
    father_occupation = db.Column(db.String(120), default="")
    mother_name = db.Column(db.String(120), default="")
    mother_occupation = db.Column(db.String(120), default="")
    brothers = db.Column(db.Integer, default=0)
    sisters = db.Column(db.Integer, default=0)
    family_village = db.Column(db.String(120), default="")
    district = db.Column(db.String(80), default="")
    current_address = db.Column(db.Text, default="")
    about_me = db.Column(db.Text, default="")
    photo_url = db.Column(db.String(500), default="")
    is_visible = db.Column(db.Boolean, default=True, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")

    __table_args__ = (
        db.Index("ix_profiles_search", "gender", "religion", "city", "is_visible"),
    )

    @property
    def age(self):
        return calculate_age(self.date_of_birth)

    def completeness(self):
        fields = [
            self.full_name,
            self.gender,
            self.date_of_birth,
            self.religion,
            self.city,
            self.education,
            self.profession,
            self.work,
            self.mobile,
            self.gotra,
            self.manglik,
            self.family_background,
            self.father_name,
            self.father_occupation,
            self.mother_name,
            self.mother_occupation,
            self.family_village,
            self.district,
            self.current_address,
            self.about_me,
            self.photo_url,
        ]
        filled = sum(1 for value in fields if value)
        return int((filled / len(fields)) * 100)


class Favourite(db.Model):
    __tablename__ = "favourites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="favourites")
    target = db.relationship("User", foreign_keys=[target_user_id])

    __table_args__ = (
        db.UniqueConstraint("user_id", "target_user_id", name="uq_favourite_pair"),
        db.CheckConstraint("user_id != target_user_id", name="ck_no_self_favourite"),
    )


class Interest(db.Model):
    __tablename__ = "interests"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    __table_args__ = (
        db.UniqueConstraint("sender_id", "receiver_id", name="uq_interest_pair"),
        db.CheckConstraint("sender_id != receiver_id", name="ck_no_self_interest"),
    )


class SuccessStory(db.Model):
    __tablename__ = "success_stories"

    id = db.Column(db.Integer, primary_key=True)
    couple_names = db.Column(db.String(120), nullable=False)
    quote = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(80), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_sample = db.Column(db.Boolean, default=True, nullable=False)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Newsletter(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


def calculate_age(born):
    if not born:
        return None
    today = date.today()
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


def date_of_birth_bounds(min_age, max_age):
    today = date.today()

    def shift_years(years):
        try:
            return today.replace(year=today.year - years)
        except ValueError:
            return today.replace(month=2, day=28, year=today.year - years)

    latest_dob = shift_years(min_age)
    earliest_dob = shift_years(max_age + 1)
    return earliest_dob, latest_dob
