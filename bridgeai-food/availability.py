from datetime import datetime
import random

# Realistic mock data — update with real locations
FOOD_BANKS = [
    {'name': 'Food Bank Singapore - Woodlands',
     'address': 'Woodlands Industrial Park',
     'hotline': '6252 4507',
     'hours': 'Mon-Fri 9am-5pm',
     'status': 'open'},
    {'name': 'Willing Hearts',
     'address': 'Lorong Napiri, Hougang',
     'hotline': '6385 0088',
     'hours': 'Daily 7am-10pm',
     'status': 'open'},
    {'name': 'Food from the Heart',
     'address': 'Geylang East Ave 1',
     'hotline': '6749 0323',
     'hours': 'Mon/Wed/Fri 10am-2pm',
     'status': 'open'},
]

SHELTERS = [
    {'name': 'RSVP Shelter',
     'type': 'Emergency',
     'hotline': '1800-555-5555',
     # Simulate realistic availability
     'beds_available': random.randint(0, 5),
     'status': 'call to check'},
    {'name': 'Salvation Army Gracehaven',
     'type': 'Women & Children',
     'hotline': '6259 9011',
     'beds_available': random.randint(0, 3),
     'status': 'call to check'},
    {'name': 'Singapore After Care Association',
     'type': 'Men',
     'hotline': '6258 3374',
     'beds_available': random.randint(0, 8),
     'status': 'call to check'},
]

def get_food_banks() -> list:
    now = datetime.now()
    for fb in FOOD_BANKS:
        # Simple hour check (can be improved)
        fb['open_now'] = 7 <= now.hour <= 20
    return FOOD_BANKS

def get_shelters() -> list:
    return SHELTERS

def format_food_response() -> str:
    banks = get_food_banks()
    open_banks = [b for b in banks if b.get('open_now')]
    if not open_banks:
        return 'No food banks are currently open. The next opening is 7am tomorrow.'
    lines = ['Here are food banks open right now:\n']
    for b in open_banks:
        lines.append(f"• {b['name']}\n  📍 {b['address']}\n  📞 {b['hotline']}\n  🕐 {b['hours']}\n")
    return '\n'.join(lines)
