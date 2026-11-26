#!/usr/bin/env python3
"""
Additive, non-destructive verification updater for session arena-61867d90 on top of origin/main (13bb30e).
Preserves 100% of upstream site_data/*.json and enriches only missing prices, socials, Guide-listed table,
Brooklyn Bridge Park, MTA/AirTrain 2026 group-fare rules, and 3-night (15-18 Feb) label accuracy.
"""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site_data")
AUDIT = os.path.join(ROOT, "audit_61867d90")
os.makedirs(AUDIT, exist_ok=True)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def haversine_km(lat1, lon1, lat2, lon2):
    la1, lo1, la2, lo2 = map(math.radians, [lat1, lon1, lat2, lon2])
    return 2 * 6371.0 * math.asin(
        math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    )


details = load_json(os.path.join(DATA, "restaurant_details.json"))
hotels = load_json(os.path.join(DATA, "hotels.json"))
activities = load_json(os.path.join(DATA, "activities.json"))
social = load_json(os.path.join(DATA, "social.json"))
framework = load_json(os.path.join(DATA, "framework.json"))
indep = load_json(os.path.join(DATA, "independent_verification.json"))

det = details["details"]

# 1. Fill missing/deposit-only official prices & verified IGs in restaurant_details.json
det["atera"].update({
    "menu_price_usd": 325,
    "price_is_floor": False,
    "price_pairing_usd": 218,
    "price_source": "https://ateranyc.com/",
    "price_note": "Official website (ateranyc.com) & Tock Chef's Counter page read 2026-11-26: Seasonal Tasting Menu $325 per person ($650 for two); wine pairing $218 pp ($200 pp deposit collected on formal dining room booking).",
    "instagram": "https://www.instagram.com/ateranyc/",
})
det["chef-s-table-at-brooklyn-fare"].update({
    "menu_price_usd": 385,
    "price_is_floor": False,
    "price_source": "https://www.brooklynfare.com/chefs-table/",
    "price_note": "Official Chef's Table page (brooklynfare.com/chefs-table/) read 2026-11-26: Tasting Menu $385 per person ($770 for two), plus tax and service.",
    "instagram": "https://www.instagram.com/brooklynfare/",
})
det["masa"].update({
    "menu_price_usd": 750,
    "price_lunch_usd": 495,
    "price_tasting_high_usd": 950,
    "price_is_floor": False,
    "price_source": "https://www.exploretock.com/masa",
    "price_note": "Official Tock page read 2026-11-26: Dinner Table Omakase $750 pp ($1,500 for two); Hinoki Dinner Counter $950 pp ($1,900 for two); Lunch Hinoki Counter $495 pp ($990 for two), hospitality included (no tipping).",
    "instagram": "https://www.instagram.com/chefmasanyc/",
})
det["odo"].update({
    "menu_price_usd": 270,
    "price_lunch_usd": 150,
    "price_is_floor": False,
    "price_source": "https://www.exploretock.com/odo-new-york",
    "price_note": "Official Tock page read 2026-11-26: Dinner Kaiseki $270 pp ($540 for two); Lunch Kaiseki $150 pp ($300 for two).",
    "instagram": "https://www.instagram.com/odo.nyc/",
})
det["cesar"].update({
    "menu_price_usd": 150,
    "price_is_floor": True,
    "price_source": "https://www.exploretock.com/cesarrestaurant",
    "price_note": "Official Tock page read 2026-11-26: Main Dining Room & Kitchen Counter reservations require $150 per person deposit (floor, not full menu price).",
    "instagram": "https://www.instagram.com/cesar.newyork/",
})
det["aquavit"]["instagram"] = "https://www.instagram.com/aquavitnyc/"
det["aska"]["instagram"] = "https://www.instagram.com/askanyc/"
det["sushi-noz"]["instagram"] = "https://www.instagram.com/sushinoznyc/"

# 2. Structured 8-venue Guide-listed (no-star) table
rec_hotel = [h for h in hotels["hotels"] if h["id"] == "fairfield-central-park"][0]
guide_listed_table = [
    {
        "id": "one-white-street",
        "name": "One White Street",
        "distinction": "Selected + 🌿 Green Star (0 red stars)",
        "cuisine": "Contemporary / Farm-to-table",
        "area": "Tribeca",
        "address": "1 White St., New York, NY 10013",
        "hours": "Tue–Sat 17:00–21:30 (closed Mon & Sun on MICHELIN; seasonal daily service noted on site)",
        "exceptions": "Holds a MICHELIN Green Star (Rigor Hill Farm produce) without a red cooking star; upstairs tasting vs downstairs à la carte.",
        "cost_2_adults": "$290 tasting ($145 pp) · $110–$158 à la carte",
        "price_source": "https://onewhitestreetnyc.com/tasting",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/one-white-street",
        "lat": 40.719295,
        "lon": -74.006424,
    },
    {
        "id": "tonchin",
        "name": "Tonchin",
        "distinction": "Bib Gourmand (0 stars)",
        "cuisine": "Ramen / Japanese",
        "area": "Midtown South",
        "address": "13 W. 36th St., New York, NY 10018",
        "hours": "Daily 11:30–22:00",
        "exceptions": "Weekday Lunch Set ($28 pp) Mon–Fri until 14:30 excl. holidays; $20 pp minimum on reservations.",
        "cost_2_adults": "$56 weekday lunch set · $56–$96 à la carte",
        "price_source": "https://www.tonchinus.com/new-york-menu",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/tonchin",
        "lat": 40.750298,
        "lon": -73.984512,
    },
    {
        "id": "pranakhon",
        "name": "Pranakhon",
        "distinction": "Bib Gourmand (0 stars)",
        "cuisine": "Thai",
        "area": "Greenwich Village",
        "address": "88 University Pl., New York, NY 10003",
        "hours": "Daily 11:30–22:00 (Fri–Sat to 22:30)",
        "exceptions": "Open 7 days for lunch and dinner; Bangkok street-food format.",
        "cost_2_adults": "$76–$130 à la carte (starters $14–$20, mains $24–$45)",
        "price_source": "https://pranakhonnyc.com/pdf/qrcode_menu.pdf",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/pranakhon",
        "lat": 40.733614,
        "lon": -73.993418,
    },
    {
        "id": "ai-fiori",
        "name": "Ai Fiori",
        "distinction": "MICHELIN Selected (0 stars)",
        "cuisine": "Italian / French Riviera",
        "area": "Midtown Fifth Ave",
        "address": "400 Fifth Ave., Fl. 2 (The Langham), New York, NY 10018",
        "hours": "Mon–Fri 07:30–10:30, 12:00–14:30, 17:00–21:30 (Fri 22:00); Sat–Sun 08:00–11:00, 17:00–22:00 (Sun 21:00)",
        "exceptions": "2-course Business Lunch ($54 pp) Mon–Fri 12:00–14:30; 3-course Sunday Supper ($70 pp).",
        "cost_2_adults": "$108 weekday 2-course lunch · $140 Sunday 3-course supper",
        "price_source": "https://www.aifiorinyc.com/holidays",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ai-fiori",
        "lat": 40.750112,
        "lon": -73.983482,
    },
    {
        "id": "ci-siamo",
        "name": "Ci Siamo",
        "distinction": "MICHELIN Selected (0 stars)",
        "cuisine": "Italian (live-fire)",
        "area": "Manhattan West / Hudson Yards",
        "address": "440 W. 33rd St., Ste. 100, New York, NY 10001",
        "hours": "Mon–Thu & Sun 17:00–21:30 (Sun 21:00); Fri–Sat 17:00–22:00",
        "exceptions": "USHG live-fire dining room; antipasti $15–$27, housemade pastas $25–$35.",
        "cost_2_adults": "$80–$130+ à la carte",
        "price_source": "https://www.cisiamo.com/menus/",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ci-siamo",
        "lat": 40.752874,
        "lon": -73.997719,
    },
    {
        "id": "cafe-carmellini",
        "name": "Café Carmellini",
        "distinction": "MICHELIN Selected (0 stars)",
        "cuisine": "Italian / French",
        "area": "NoMad",
        "address": "250 Fifth Ave., New York, NY 10001",
        "hours": "Sun–Wed 17:00–22:00; Thu–Sat 17:00–22:30 (lunch Wed–Sun 11:30–14:00)",
        "exceptions": "Inside The Fifth Avenue Hotel; starters $24–$38, entrées $52–$84.",
        "cost_2_adults": "$152–$244 à la carte",
        "price_source": "https://www.cafecarmellini.com/menu/dinner/",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/cafe-carmellini",
        "lat": 40.744892,
        "lon": -73.987395,
    },
    {
        "id": "chambers",
        "name": "Chambers",
        "distinction": "MICHELIN Selected (0 stars)",
        "cuisine": "Contemporary",
        "area": "Tribeca",
        "address": "94 Chambers St., New York, NY 10007",
        "hours": "Daily 17:30–22:00",
        "exceptions": "Walk-ins via OpenTable waitlist; starters $24–$36, mains $36–$45 (ribeye for two $180).",
        "cost_2_adults": "$120–$240 à la carte",
        "price_source": "https://www.chambers.nyc/menu",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/chambers",
        "lat": 40.714742,
        "lon": -74.007311,
    },
    {
        "id": "ito-1201767",
        "name": "Ito",
        "distinction": "MICHELIN Selected (0 stars)",
        "cuisine": "Japanese / Omakase",
        "area": "Tribeca",
        "address": "75 Barclay St., New York, NY 10007",
        "hours": "Tue–Sat seatings 18:00–20:00 & 20:30–22:30; closed Mon & Sun",
        "exceptions": "16-seat omakase counter opposite One World Trade Center.",
        "cost_2_adults": "$590 omakase ($295 pp)",
        "price_source": "https://www.ito-omakase.com/ito-new-york",
        "michelin_url": "https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ito-1201767",
        "lat": 40.713561,
        "lon": -74.011482,
    },
]
for g in guide_listed_table:
    km = round(haversine_km(rec_hotel["lat"], rec_hotel["lon"], g["lat"], g["lon"]), 2)
    g["transit_min_modelled"] = round(km / 12.0 * 60 + 8)
    g["walk_min_modelled"] = round(km / 4.5 * 60)
    g["km_from_fairfield"] = km

details["guide_listed_table"] = guide_listed_table
save_json(os.path.join(DATA, "restaurant_details.json"), details)

# 3. Add Brooklyn Bridge Park to activities.json
if not any(a["id"] == "brooklyn-bridge-park" for a in activities["activities"]):
    bbp_km = round(haversine_km(rec_hotel["lat"], rec_hotel["lon"], 40.7003, -73.9967), 2)
    activities["activities"].append({
        "id": "brooklyn-bridge-park",
        "name": "Brooklyn Bridge Park (DUMBO / Piers 1–6)",
        "category": "Waterfront park",
        "area": "Brooklyn (DUMBO / Brooklyn Heights)",
        "address": "334 Furman Street, Brooklyn, NY 11201",
        "hours": "Daily 06:00–01:00",
        "days_open": "Mon–Sun",
        "exceptions": "Free entry. Pier 2 08:00–21:00 (seasonal), Pier 5 06:00–23:00, playgrounds sunrise–sunset.",
        "adult_usd": 0,
        "cost_2_adults_usd": 0,
        "official_url": "https://brooklynbridgepark.org/",
        "verification": "VERIFIED - hours (06:00-01:00 daily), free entry, and official IG/TikTok links read on brooklynbridgepark.org on 2026-11-26",
        "lat": 40.7003,
        "lon": -73.9967,
        "from_hotel": {
            "hotel": rec_hotel["name"],
            "km": bbp_km,
            "walk_min_modelled": round(bbp_km / 4.5 * 60),
            "transit_min_modelled": round(bbp_km / 12.0 * 60 + 8),
            "within_one_hour": True,
            "method": "MODEL: great-circle km / 4.5 km/h walking, or /12 km/h effective subway speed plus 8 minutes platform access and wait.",
        },
    })
save_json(os.path.join(DATA, "activities.json"), activities)

# 4. Additive social enrichment (never deletes any existing verified review/account!)
acc = social["accounts"]


def add_soc(slug, platform, kind, url, evidence):
    lst = acc.setdefault(slug, [])
    if not any(x["url"] == url for x in lst):
        lst.append({"platform": platform, "kind": kind, "url": url, "evidence": evidence})


new_socials = [
    ("atera", "Instagram", "official", "https://www.instagram.com/ateranyc/", "Verified 2026-11-26: @ateranyc (65K followers)."),
    ("chef-s-table-at-brooklyn-fare", "Instagram", "official", "https://www.instagram.com/brooklynfare/", "Verified 2026-11-26: @brooklynfare (5,184 followers)."),
    ("masa", "Instagram", "official", "https://www.instagram.com/chefmasanyc/", "Linked directly on Masa's official Tock page (exploretock.com/masa)."),
    ("odo", "Instagram", "official", "https://www.instagram.com/odo.nyc/", "Linked directly on Odo's official Tock page (exploretock.com/odo-new-york)."),
    ("cesar", "Instagram", "official", "https://www.instagram.com/cesar.newyork/", "Linked directly on César's official Tock page (exploretock.com/cesarrestaurant)."),
    ("aquavit", "Instagram", "official", "https://www.instagram.com/aquavitnyc/", "Linked directly on Aquavit's official Tock page (exploretock.com/aquavit)."),
    ("aska", "Instagram", "official", "https://www.instagram.com/askanyc/", "Linked directly in footer of askanyc.com."),
    ("sushi-noz", "Instagram", "official", "https://www.instagram.com/sushinoznyc/", "Verified 2026-11-26: @sushinoznyc (51K followers)."),
    ("tonchin", "Instagram", "official", "https://www.instagram.com/tonchinus/", "Verified 2026-11-26: @tonchinus (39K followers)."),
    ("ai-fiori", "Instagram", "official", "https://www.instagram.com/aifiori/", "Verified 2026-11-26: @aifiori (28K followers)."),
    ("ci-siamo", "Instagram", "official", "https://www.instagram.com/cisiamonyc/", "Verified 2026-11-26: @cisiamonyc (58K followers)."),
    ("cafe-carmellini", "Instagram", "official", "https://www.instagram.com/cafecarmellini/", "Verified 2026-11-26: @cafecarmellini (28K followers)."),
    ("chambers", "Instagram", "official", "https://www.instagram.com/chambers.nyc/", "Verified 2026-11-26: @chambers.nyc (19K followers)."),
    ("ito-1201767", "Instagram", "official", "https://www.instagram.com/ito_tribeca/", "Linked directly in footer of ito-omakase.com/ito-new-york."),
    ("brooklyn-bridge-park", "Instagram", "official", "https://www.instagram.com/brooklynbridgepark/", "Linked directly in header of brooklynbridgepark.org."),
    ("brooklyn-bridge-park", "TikTok", "official", "https://www.tiktok.com/@brooklynbridgepark", "Linked directly in header of brooklynbridgepark.org."),
    ("moma", "YouTube", "official", "https://www.youtube.com/@themuseumofmodernart", "Official MoMA YouTube channel (@themuseumofmodernart)."),
    ("met", "YouTube", "official", "https://www.youtube.com/@metmuseum", "Official Met YouTube channel (@metmuseum)."),
    ("amnh", "YouTube", "official", "https://www.youtube.com/@AmericanMuseumofNaturalHistory", "Official AMNH YouTube channel (@AmericanMuseumofNaturalHistory)."),
    ("top-of-the-rock", "YouTube", "official", "https://www.youtube.com/@RockefellerCenterNYC", "Official Rockefeller Center YouTube channel (@RockefellerCenterNYC)."),
]
for slug, plat, kind, url, ev in new_socials:
    add_soc(slug, plat, kind, url, ev)

social["coverage"]["venues_with_a_verified_official_social_account"] = sum(
    1 for grp in acc.values() if any(s["kind"] == "official" for s in grp)
)
save_json(os.path.join(DATA, "social.json"), social)

# 5. Fix 3-night (4-day) preferred window label & add F-27 (MTA Jan 1 2026 MetroCard cutoff + AirTrain JFK $13.25 OMNY Group Fare)
for it in framework["itineraries"]:
    if it["id"] == "four":
        it["title"] = "3 nights (4 days) - the literal preferred window (15-18 Feb 2027)"

if not any(f["id"] == "F-30" for f in framework["flags"]):
    framework["flags"].append({
        "id": "F-30",
        "severity": "LOW",
        "title": "MetroCard sales ended 1 Jan 2026; OMNY cap requires separate cards while AirTrain JFK discounts same-card groups",
        "detail": (
            "Official MTA pages (mta.info/fares-tolls/subway-bus/tap-and-ride) confirm MetroCard purchase/refill ended 1 Jan 2026 and each adult must tap a separate "
            "contactless card/device to earn the $35 7-day subway/bus cap. Conversely, JFK AirTrain ($8.75 single) offers a 2026 OMNY Group Fare ($8.75 + $4.50 = $13.25 "
            "each way / $26.50 return for 2 adults) when tapping the SAME card within 5 minutes."
        ),
        "source": "https://www.jfkairport.com/transportation/airtrain",
        "settle_by": "Tap ONE card twice at AirTrain JFK ($13.25), then TWO separate cards/phones on MTA subways ($35 cap each)",
        "status": "Documented",
    })
save_json(os.path.join(DATA, "framework.json"), framework)

# 6. Append newly verified official sources to independent_verification.json
extra_indep = [
    ("Atera official website", "https://ateranyc.com/", "Seasonal Tasting Menu $325 pp ($650 for two); wine pairing $218 pp."),
    ("Chef's Table at Brooklyn Fare", "https://www.brooklynfare.com/chefs-table/", "Tasting Menu $385 pp ($770 for two); Tue–Sun hours verified."),
    ("Masa on Tock", "https://www.exploretock.com/masa", "Dinner Table $750 pp, Hinoki Dinner Counter $950 pp, Lunch Counter $495 pp (hospitality included)."),
    ("Odo on Tock", "https://www.exploretock.com/odo-new-york", "Dinner Kaiseki $270 pp ($540 for two); Lunch Kaiseki $150 pp ($300 for two)."),
    ("César on Tock", "https://www.exploretock.com/cesarrestaurant", "$150 pp reservation deposit floor verified; IG @cesar.newyork."),
    ("Tonchin NYC official menu", "https://www.tonchinus.com/new-york-menu", "Bib Gourmand: Mon–Fri Lunch Set $28 pp ($56 for two); ramen $22–$25."),
    ("Pranakhon official menu PDF", "https://pranakhonnyc.com/pdf/qrcode_menu.pdf", "Bib Gourmand: starters $14–$20, noodles/curries/mains $24–$45."),
    ("Ai Fiori official menus", "https://www.aifiorinyc.com/holidays", "MICHELIN Selected: 2-course Business Lunch $54 pp ($108/2); 3-course Sunday Supper $70 pp ($140/2)."),
    ("Ci Siamo official menu", "https://www.cisiamo.com/menus/", "MICHELIN Selected: antipasti $15–$27, pastas $25–$35."),
    ("Café Carmellini dinner menu", "https://www.cafecarmellini.com/menu/dinner/", "MICHELIN Selected: starters $24–$38, entrées $52–$84."),
    ("Chambers official menu", "https://www.chambers.nyc/menu", "MICHELIN Selected: starters $24–$36, mains $36–$45, ribeye for two $180."),
    ("Ito New York official page", "https://www.ito-omakase.com/ito-new-york", "MICHELIN Selected: Omakase $295 pp ($590 for two)."),
    ("Brooklyn Bridge Park official site", "https://brooklynbridgepark.org/", "Open daily 06:00–01:00, free entry, official IG & TikTok @brooklynbridgepark in header."),
    ("AirTrain JFK official page", "https://www.jfkairport.com/transportation/airtrain", "Single ride $8.75; 2026 OMNY Group Fare $8.75 + $4.50 = $13.25 each way ($26.50 RT for 2 adults)."),
    ("MTA Tap & Ride official page", "https://www.mta.info/fares-tolls/subway-bus/tap-and-ride", "MetroCard sales ended 1 Jan 2026; $35 7-day cap requires separate cards/devices per rider."),
    ("Pod 51 official rooms & FAQ", "https://www.thepodhotel.com/pod-51/rooms", "Confirms Bunk/Single Pods use shared bathrooms (Queen/Studio Pods have private baths; $29.84/nt facility fee)."),
]
existing_urls = {x["url"] for x in indep["official_sources"]}
for pub, url, ver in extra_indep:
    if url not in existing_urls:
        indep["official_sources"].append({
            "publisher": pub,
            "url": url,
            "verified": ver,
            "kind": "official",
            "read_on": "2026-11-26",
        })
save_json(os.path.join(DATA, "independent_verification.json"), indep)

print("Additive updates applied cleanly on top of origin/main!")
print("Starred priced count:", sum(1 for v in det.values() if v.get("menu_price_usd")))
print("Guide-listed table rows:", len(guide_listed_table))
print("Activities count:", len(activities["activities"]))
print("Independent official sources count:", len(indep["official_sources"]))
