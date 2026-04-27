import json
import random
import os

hero_data = {
    "Tanks": ["Tigreal", "Akai", "Franco", "Minotaur", "Lolita", "Johnson", "Gatotkaca", "Grock", "Uranus", "Khufra", "Esmeralda", "Baxia", "Atlas", "Barats", "Belerick", "Edith", "Fredrinn", "Gloo", "Hylos", "Carmilla", "Chip", "Hilda"],
    "Fighters": ["Balmond", "Zilong", "Freya", "Chou", "Sun", "Alpha", "Ruby", "Roger", "Jawhead", "Martis", "Aldous", "Leomord", "Thamuz", "Badang", "Guinevere", "Masha", "Silvanna", "Yu Zhong", "Paquito", "Aulus", "Lapu-Lapu", "Phoveus", "Yin", "Xavier", "Julian", "Floryn", "Dyrroth", "Khaleed", "Terizla", "X.Borg", "Dyroth"],
    "Assassins": ["Saber", "Karina", "Alucard", "Fanny", "Hayabusa", "Natalia", "Yi Sun-shin", "Lancelot", "Helcurt", "Lesley", "Selena", "Mathilda", "Ling", "Benedetta", "Natan", "Melissa", "Arlott", "Joy", "Harley", "Gusion", "Hanzo", "Claude"],
    "Mages": ["Nana", "Cyclops", "Kadita", "Gord", "Kagura", "Valir", "Chang'e", "Lunox", "Lylia", "Cecilion", "Yve", "Pharsa", "Zhask", "Vale", "Odette", "Aurora", "Vexana", "Alice", "Eudora", "Luo Yi", "Novaria", "Valentina", "Faramis", "Harith", "Esmeralda", "Julian", "Xavier", "Saber"],
    "Marksmen": ["Layla", "Miya", "Bruno", "Clint", "Moskov", "Irithel", "Karrie", "Granger", "Kimmy", "Beatrix", "Brody", "Popol and Kupa", "Yi Sun-shin", "Wanwan", "Lesley", "Roger", "Claude", "Melissa", "Natan", "Hanabi"],
    "Supports": ["Estes", "Angela", "Rafaela", "Diggie", "Kaja", "Tigreal", "Mathilda", "Floryn", "Faramis", "Carmilla"]
}

all_heroes_data = []
tiers = ["S", "A", "B", "C"]

# Ensure unique hero names across roles, prioritizing primary role for stats
unique_heroes = {}
for role, heroes in hero_data.items():
    for hero in heroes:
        if hero not in unique_heroes:
            unique_heroes[hero] = role

for hero_name, role in unique_heroes.items():
    win_rate = round(random.uniform(0.44, 0.58), 2)
    pick_rate = round(random.uniform(0.05, 0.35), 2)
    ban_rate = round(random.uniform(0.01, 0.25), 2)
    tier = random.choice(tiers)

    all_heroes_data.append({
        "hero_name": hero_name,
        "role": role,
        "win_rate": win_rate,
        "pick_rate": pick_rate,
        "ban_rate": ban_rate,
        "tier": tier
    })

# Create directory if it doesn't exist
output_dir = "data_pipeline"
os.makedirs(output_dir, exist_ok=True)

filepath = os.path.join(output_dir, "heroes_backup.json")
with open(filepath, "w") as f:
    json.dump(all_heroes_data, f, indent=4)

print(f"Generated {len(all_heroes_data)} hero entries in {filepath}")
