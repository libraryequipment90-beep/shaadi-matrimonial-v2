from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    EmailField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

GENDERS = [("Female", "Female"), ("Male", "Male")]
RELIGIONS = [
    ("Hindu", "Hindu"),
    ("Muslim", "Muslim"),
    ("Sikh", "Sikh"),
    ("Christian", "Christian"),
    ("Jain", "Jain"),
    ("Other", "Other"),
]
EDUCATIONS = [
    ("Graduate", "Graduate"),
    ("Postgraduate", "Postgraduate"),
    ("Professional", "Professional"),
    ("High School", "High School"),
    ("Other", "Other"),
]
CREATED_FOR = [
    ("Self", "Self"),
    ("Son", "Son"),
    ("Daughter", "Daughter"),
    ("Brother", "Brother"),
    ("Sister", "Sister"),
    ("Friend", "Friend"),
]
CITIES = [
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Jaipur",
    "Pune",
    "Hyderabad",
    "Chandigarh",
    "Kolkata",
    "Chennai",
    "Ahmedabad",
]
MANGLIK_CHOICES = [
    ("No", "No"),
    ("Yes", "Yes"),
    ("Don't know", "Don't know"),
    ("Prefer not to say", "Prefer not to say"),
]
CONTACT_TOPICS = [
    ("General question", "General question"),
    ("Account help", "Account help"),
    ("Privacy & safety", "Privacy & safety"),
    ("Membership", "Membership"),
]


def validate_single_photo(form, field):
    value = (field.data or "").strip()
    if not value:
        return
    if "," in value or "\n" in value or " " in value:
        raise ValidationError("Only one photo is allowed. Please provide a single image URL.")
    if not (value.startswith("http://") or value.startswith("https://") or value.startswith("/static/")):
        raise ValidationError("Photo must be a single http(s) image URL.")


def validate_mobile(form, field):
    value = (field.data or "").strip()
    if not value:
        return
    cleaned = value.replace(" ", "").replace("-", "")
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    if not (cleaned.isdigit() and len(cleaned) == 10 and cleaned[0] in "6789"):
        raise ValidationError(
            "Enter a valid 10-digit mobile number (e.g. 9876543210)."
        )


def validate_adult(form, field):
    if not field.data:
        raise ValidationError("Date of birth is required.")
    today = date.today()
    age = today.year - field.data.year - (
        (today.month, today.day) < (field.data.month, field.data.day)
    )
    if field.data > today:
        raise ValidationError("Date of birth cannot be in the future.")
    if age < 18:
        raise ValidationError("You must be at least 18 years old to register.")
    if age > 80:
        raise ValidationError("Please enter a valid date of birth.")


class RegisterForm(FlaskForm):
    created_for = SelectField("Profile created for", choices=CREATED_FOR)
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = EmailField("Email address", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Create password",
        validators=[DataRequired(), Length(min=8, max=128, message="Password must be at least 8 characters.")],
    )
    mobile = StringField("Mobile number", validators=[Optional(), Length(max=20), validate_mobile])
    gender = SelectField("Gender", choices=GENDERS, validators=[DataRequired()])
    date_of_birth = DateField("Date of birth", validators=[DataRequired(), validate_adult])
    religion = SelectField("Religion", choices=RELIGIONS, validators=[DataRequired()])
    gotra = StringField("Gotra", validators=[Optional(), Length(max=80)])
    manglik = SelectField("Manglik", choices=MANGLIK_CHOICES, validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=80)])
    district = StringField("District", validators=[Optional(), Length(max=80)])
    education = SelectField("Education", choices=EDUCATIONS, validators=[DataRequired()])
    profession = StringField("Occupation", validators=[DataRequired(), Length(min=2, max=120)])
    work = StringField("Work / Company", validators=[Optional(), Length(max=160)])
    father_name = StringField("Father's name", validators=[Optional(), Length(max=120)])
    father_occupation = StringField("Father's occupation", validators=[Optional(), Length(max=120)])
    mother_name = StringField("Mother's name", validators=[Optional(), Length(max=120)])
    mother_occupation = StringField("Mother's occupation", validators=[Optional(), Length(max=120)])
    brothers = IntegerField("Brothers", validators=[Optional(), NumberRange(min=0, max=20)], default=0)
    sisters = IntegerField("Sisters", validators=[Optional(), NumberRange(min=0, max=20)], default=0)
    family_village = StringField("Family village / native place", validators=[Optional(), Length(max=120)])
    family_background = TextAreaField("Family background", validators=[Optional(), Length(max=2000)])
    current_address = TextAreaField("Current address", validators=[Optional(), Length(max=1000)])
    about_me = TextAreaField("About me", validators=[Optional(), Length(max=2000)])


class LoginForm(FlaskForm):
    email = EmailField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class SearchForm(FlaskForm):
    looking_for = SelectField(
        "I'm looking for",
        choices=[("Female", "Bride / Female"), ("Male", "Groom / Male"), ("Any", "Any")],
        default="Female",
    )
    min_age = IntegerField("Minimum age", validators=[Optional(), NumberRange(min=18, max=80)], default=21)
    max_age = IntegerField("Maximum age", validators=[Optional(), NumberRange(min=18, max=80)], default=35)
    religion = SelectField(
        "Religion",
        choices=[("Any", "Any religion")] + RELIGIONS,
        default="Any",
    )
    gotra = StringField("Gotra", validators=[Optional(), Length(max=80)])
    manglik = SelectField(
        "Manglik",
        choices=[("Any", "Any")] + MANGLIK_CHOICES,
        default="Any",
    )
    city = StringField("City", validators=[Optional(), Length(max=80)])
    district = StringField("District", validators=[Optional(), Length(max=80)])
    education = SelectField(
        "Education",
        choices=[("Any", "Any education")] + EDUCATIONS,
        default="Any",
    )

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        if not ok:
            return False
        min_age = self.min_age.data or 18
        max_age = self.max_age.data or 80
        if min_age > max_age:
            self.max_age.errors.append("Maximum age must be greater than or equal to minimum age.")
            return False
        return True


class ProfileForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    mobile = StringField("Mobile number", validators=[Optional(), Length(max=20), validate_mobile])
    gender = SelectField("Gender", choices=GENDERS, validators=[DataRequired()])
    date_of_birth = DateField("Date of birth", validators=[DataRequired(), validate_adult])
    religion = SelectField("Religion", choices=RELIGIONS, validators=[DataRequired()])
    gotra = StringField("Gotra", validators=[Optional(), Length(max=80)])
    manglik = SelectField("Manglik", choices=MANGLIK_CHOICES, validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=80)])
    district = StringField("District", validators=[Optional(), Length(max=80)])
    education = SelectField("Education", choices=EDUCATIONS, validators=[DataRequired()])
    profession = StringField("Occupation", validators=[DataRequired(), Length(min=2, max=120)])
    work = StringField("Work / Company", validators=[Optional(), Length(max=160)])
    father_name = StringField("Father's name", validators=[Optional(), Length(max=120)])
    father_occupation = StringField("Father's occupation", validators=[Optional(), Length(max=120)])
    mother_name = StringField("Mother's name", validators=[Optional(), Length(max=120)])
    mother_occupation = StringField("Mother's occupation", validators=[Optional(), Length(max=120)])
    brothers = IntegerField("Brothers", validators=[Optional(), NumberRange(min=0, max=20)], default=0)
    sisters = IntegerField("Sisters", validators=[Optional(), NumberRange(min=0, max=20)], default=0)
    family_village = StringField("Family village / native place", validators=[Optional(), Length(max=120)])
    family_background = TextAreaField("Family background", validators=[Optional(), Length(max=2000)])
    current_address = TextAreaField("Current address", validators=[Optional(), Length(max=1000)])
    about_me = TextAreaField("About me", validators=[Optional(), Length(max=2000)])
    photo_url = StringField(
        "Profile photo URL (one photo only)",
        validators=[Optional(), Length(max=500), validate_single_photo],
    )
    is_visible = BooleanField("Show my profile in search and community")


class ContactForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired(), Length(min=2, max=120)])
    email = EmailField("Email address", validators=[DataRequired(), Email()])
    topic = SelectField("Topic", choices=CONTACT_TOPICS, validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=3000)])


class NewsletterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
