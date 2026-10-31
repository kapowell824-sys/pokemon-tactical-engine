import os
import django
import requests

# Hook into your Django project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damage_calc.settings')
django.setup()

from calculator.models import HeldItem

print("Downloading Items from PokeAPI...")

# Fetch the master list of items
response = requests.get("https://pokeapi.co/api/v2/item?limit=1000")

if response.status_code == 200:
    items_data = response.json()['results']
    print(f"Found {len(items_data)} items. Saving to database...")
    
    for entry in items_data:
        # Clean up the names (e.g., "choice-band" -> "Choice Band")
        name = entry['name'].replace('-', ' ').title()
        
        HeldItem.objects.get_or_create(
            name=name,
            defaults={
                'flat_attack': 0,
                'flat_sp_atk': 0,
                'flat_defense': 0,
                'flat_sp_def': 0,
            }
        )
    print("Done! Items are fully populated.")
else:
    print("Could not connect to PokeAPI.")