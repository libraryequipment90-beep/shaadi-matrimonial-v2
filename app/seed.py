from datetime import date

from app import db
from app.models import Profile, SuccessStory, User

DEMO_PASSWORD = "DemoPass123!"

DEMO_USERS = [
    {
        "email": "priya.sharma.demo@example.com",
        "full_name": "Priya Sharma",
        "mobile": "9000000001",
        "gender": "Female",
        "date_of_birth": date(1998, 3, 14),
        "religion": "Hindu",
        "city": "Delhi",
        "education": "Postgraduate",
        "profession": "Marketing Manager",
        "work": "Brand Manager, Bengaluru",
        "gotra": "Kashyap",
        "manglik": "No",
        "family_background": "Fictional demo data. Middle-class business family settled in Delhi.",
        "father_name": "Demo Father Sharma",
        "father_occupation": "Retired Bank Manager",
        "mother_name": "Demo Mother Sharma",
        "mother_occupation": "Homemaker",
        "brothers": 1,
        "sisters": 1,
        "family_village": "Demo village, Sonipat",
        "district": "Sonipat",
        "current_address": "Demo address, New Delhi",
        "about_me": "Fictional demo profile. I enjoy reading, travel, and weekend cooking with family.",
        "photo_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "rohit.verma.demo@example.com",
        "full_name": "Rohit Verma",
        "mobile": "9000000002",
        "gender": "Male",
        "date_of_birth": date(1996, 7, 21),
        "religion": "Hindu",
        "city": "Mumbai",
        "education": "Professional",
        "profession": "Software Engineer",
        "work": "Senior Engineer, Mumbai",
        "gotra": "Bharadwaj",
        "manglik": "Yes",
        "family_background": "Fictional demo data. Service-class family with roots in Mumbai.",
        "father_name": "Demo Father Verma",
        "father_occupation": "Business Owner",
        "mother_name": "Demo Mother Verma",
        "mother_occupation": "Teacher",
        "brothers": 0,
        "sisters": 2,
        "family_village": "Demo village, Ratnagiri",
        "district": "Ratnagiri",
        "current_address": "Demo address, Andheri, Mumbai",
        "about_me": "Fictional demo profile. Cricket on Sundays and filter coffee every morning.",
        "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "sneha.patel.demo@example.com",
        "full_name": "Sneha Patel",
        "mobile": "9000000003",
        "gender": "Female",
        "date_of_birth": date(2000, 1, 9),
        "religion": "Hindu",
        "city": "Bengaluru",
        "education": "Graduate",
        "profession": "UX Designer",
        "work": "Designer, Bengaluru",
        "gotra": "Vashisht",
        "manglik": "No",
        "family_background": "Fictional demo data. Business family based in Ahmedabad.",
        "father_name": "Demo Father Patel",
        "father_occupation": "Shop Owner",
        "mother_name": "Demo Mother Patel",
        "mother_occupation": "Homemaker",
        "brothers": 1,
        "sisters": 0,
        "family_village": "Demo village, Mehsana",
        "district": "Mehsana",
        "current_address": "Demo address, Whitefield, Bengaluru",
        "about_me": "Fictional demo profile. Sketching, long walks, and South Indian breakfasts.",
        "photo_url": "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "amit.singh.demo@example.com",
        "full_name": "Amit Singh",
        "mobile": "9000000004",
        "gender": "Male",
        "date_of_birth": date(1994, 11, 2),
        "religion": "Hindu",
        "city": "Pune",
        "education": "Postgraduate",
        "profession": "Product Manager",
        "work": "Product Manager, Pune",
        "gotra": "Kaushik",
        "manglik": "Don't know",
        "family_background": "Fictional demo data. Agricultural family from western Uttar Pradesh.",
        "father_name": "Demo Father Singh",
        "father_occupation": "Farmer",
        "mother_name": "Demo Mother Singh",
        "mother_occupation": "Homemaker",
        "brothers": 2,
        "sisters": 1,
        "family_village": "Demo village, Meerut",
        "district": "Meerut",
        "current_address": "Demo address, Baner, Pune",
        "about_me": "Fictional demo profile. Trekking, indie music, and home-cooked food.",
        "photo_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "ananya.gupta.demo@example.com",
        "full_name": "Ananya Gupta",
        "mobile": "9000000005",
        "gender": "Female",
        "date_of_birth": date(1999, 5, 18),
        "religion": "Hindu",
        "city": "Hyderabad",
        "education": "Professional",
        "profession": "Chartered Accountant",
        "work": "CA, Hyderabad",
        "gotra": "Gautam",
        "manglik": "No",
        "family_background": "Fictional demo data. Educated family settled in Hyderabad.",
        "father_name": "Demo Father Gupta",
        "father_occupation": "Professor",
        "mother_name": "Demo Mother Gupta",
        "mother_occupation": "Doctor",
        "brothers": 0,
        "sisters": 1,
        "family_village": "Demo village, Varanasi",
        "district": "Varanasi",
        "current_address": "Demo address, Banjara Hills, Hyderabad",
        "about_me": "Fictional demo profile. Classical dance, baking, and family gatherings.",
        "photo_url": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "kabir.khan.demo@example.com",
        "full_name": "Kabir Khan",
        "mobile": "9000000006",
        "gender": "Male",
        "date_of_birth": date(1995, 8, 30),
        "religion": "Muslim",
        "city": "Delhi",
        "education": "Graduate",
        "profession": "Architect",
        "work": "Architect, Delhi",
        "gotra": "",
        "manglik": "Prefer not to say",
        "family_background": "Fictional demo data. Small business family in Delhi.",
        "father_name": "Demo Father Khan",
        "father_occupation": "Contractor",
        "mother_name": "Demo Mother Khan",
        "mother_occupation": "Homemaker",
        "brothers": 1,
        "sisters": 2,
        "family_village": "Demo village, Aligarh",
        "district": "Aligarh",
        "current_address": "Demo address, Jamia Nagar, Delhi",
        "about_me": "Fictional demo profile. Sketching cityscapes and weekend museum visits.",
        "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "meera.kapoor.demo@example.com",
        "full_name": "Meera Kapoor",
        "mobile": "9000000007",
        "gender": "Female",
        "date_of_birth": date(1997, 4, 6),
        "religion": "Sikh",
        "city": "Chandigarh",
        "education": "Postgraduate",
        "profession": "School Teacher",
        "work": "Teacher, Chandigarh",
        "gotra": "Kapoor",
        "manglik": "No",
        "family_background": "Fictional demo data. Family based in Punjab.",
        "father_name": "Demo Father Kapoor",
        "father_occupation": "Retired Officer",
        "mother_name": "Demo Mother Kapoor",
        "mother_occupation": "Homemaker",
        "brothers": 0,
        "sisters": 1,
        "family_village": "Demo village, Ludhiana",
        "district": "Ludhiana",
        "current_address": "Demo address, Sector 22, Chandigarh",
        "about_me": "Fictional demo profile. Poetry, gardening, and community volunteering.",
        "photo_url": "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?auto=format&fit=crop&w=400&q=80",
    },
    {
        "email": "arjun.mehta.demo@example.com",
        "full_name": "Arjun Mehta",
        "mobile": "9000000008",
        "gender": "Male",
        "date_of_birth": date(1993, 12, 12),
        "religion": "Hindu",
        "city": "Jaipur",
        "education": "Professional",
        "profession": "Doctor",
        "work": "Physician, Jaipur",
        "gotra": "Mehta",
        "manglik": "Yes",
        "family_background": "Fictional demo data. Business family from Jaipur.",
        "father_name": "Demo Father Mehta",
        "father_occupation": "Businessman",
        "mother_name": "Demo Mother Mehta",
        "mother_occupation": "Doctor",
        "brothers": 1,
        "sisters": 0,
        "family_village": "Demo village, Ajmer",
        "district": "Ajmer",
        "current_address": "Demo address, Vaishali Nagar, Jaipur",
        "about_me": "Fictional demo profile. Morning runs, travel photography, and Rajasthani food.",
        "photo_url": "https://images.unsplash.com/photo-1504257432389-52332af46080?auto=format&fit=crop&w=400&q=80",
    },
]

SAMPLE_STORIES = [
    {
        "couple_names": "Rohit & Priya",
        "quote": "We are truly grateful we found each other!",
        "city": "Delhi",
        "image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=700&q=80",
    },
    {
        "couple_names": "Amit & Neha",
        "quote": "It was a perfect match for both our families.",
        "city": "Bengaluru",
        "image_url": "https://images.unsplash.com/photo-1583939003579-730e3918a45a?auto=format&fit=crop&w=700&q=80",
    },
    {
        "couple_names": "Vikram & Sneha",
        "quote": "Thank you for helping us meet someone special.",
        "city": "Mumbai",
        "image_url": "https://images.unsplash.com/photo-1522673607200-164d1b6ce486?auto=format&fit=crop&w=700&q=80",
    },
    {
        "couple_names": "Arjun & Pooja",
        "quote": "Our journey continues with love and trust.",
        "city": "Jaipur",
        "image_url": "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?auto=format&fit=crop&w=700&q=80",
    },
]


def seed_demo_data():
    created = 0
    for item in DEMO_USERS:
        user = User.query.filter_by(email=item["email"]).first()
        if not user:
            user = User(email=item["email"], created_for="Self", is_demo=True)
            user.set_password(DEMO_PASSWORD)
            db.session.add(user)
            db.session.flush()
            created += 1
        if not user.profile:
            profile = Profile(user_id=user.id, **{k: v for k, v in item.items() if k != "email"})
            db.session.add(profile)
        else:
            for key, value in item.items():
                if key != "email":
                    setattr(user.profile, key, value)
            user.is_demo = True

    if SuccessStory.query.count() == 0:
        for story in SAMPLE_STORIES:
            db.session.add(SuccessStory(is_sample=True, **story))

    db.session.commit()
    return created


def reset_demo_data():
    emails = [item["email"] for item in DEMO_USERS]
    users = User.query.filter(User.email.in_(emails)).all()
    count = len(users)
    for user in users:
        db.session.delete(user)
    SuccessStory.query.filter_by(is_sample=True).delete()
    db.session.commit()
    return count
