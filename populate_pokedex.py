import os
import django
import requests

# 1. Hook into your Django project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damage_calc.settings')
django.setup()

from calculator.models import Pokemon

print("Fetching the complete Pokédex list from PokeAPI...")

# Fetch all Pokemon (Limit 1500 covers all current generations and alternate forms)
list_response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=1500")

if list_response.status_code == 200:
    pokemon_list = list_response.json()['results']
    total_pokemon = len(pokemon_list)
    print(f"Found {total_pokemon} Pokémon. Starting download (this will take a few minutes)...")
    
    for i, entry in enumerate(pokemon_list, 1):
        name = entry['name']
        url = entry['url']
        
        # Print a progress update every 50 Pokemon so you know it hasn't frozen
        if i % 50 == 0 or i == total_pokemon:
            print(f"Processing {i}/{total_pokemon}...")
            
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                
                # Extract the specific stats
                stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
                
                # Save to the database
                Pokemon.objects.get_or_create(
                    name=name.replace('-', ' ').title(),
                    defaults={
                        'attack_type': 'physical', # Defaulting to physical
                        'base_hp': stats.get('hp', 0),
                        'base_attack': stats.get('attack', 0),
                        'base_defense': stats.get('defense', 0),
                        'base_sp_atk': stats.get('special-attack', 0),
                        'base_sp_def': stats.get('special-defense', 0),
                    }
                )
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    print("Done! Your entire Pokédex is successfully populated.")
else:
    print("Could not connect to PokeAPI to get the master list.")