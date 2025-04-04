import re

DONATION_PATTERNS = {
    'clothes': r'(cloth|shirt|pant|dress|jacket|shoe)',
    'food': r'(food|meal|grocery|fruit|vegetable)',
    'medicine': r'(medic|drug|pill|prescription)',
    'electronics': r'(electronic|phone|laptop|computer|device)',
    'books': r'(book|textbook|novel|magazine)',
    'toys': r'(toy|game|puzzle|doll)',
    'furniture': r'(furniture|chair|table|desk|bed)',
    'hygiene': r'(hygiene|soap|sanitizer|toothpaste)',
    'school_supplies': r'(school|pen|pencil|notebook|backpack)',
}

def match_donation_text(text):
    text = text.lower()
    matches = []
    
    for category, pattern in DONATION_PATTERNS.items():
        if re.search(pattern, text):
            matches.append(category)
    
    return matches