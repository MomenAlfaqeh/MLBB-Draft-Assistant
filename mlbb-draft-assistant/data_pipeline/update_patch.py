#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from datetime import datetime

PATCH_FILE = Path(__file__).parent / 'patch_data' / 'current_patch.json'


def load_patch_data():
    """Load current patch data"""
    if not PATCH_FILE.exists():
        print(f"Patch file not found: {PATCH_FILE}")
        return None
    
    with open(PATCH_FILE, 'r') as f:
        return json.load(f)


def save_patch_data(data):
    """Save patch data to file"""
    with open(PATCH_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {PATCH_FILE}")


def show_current_stats():
    """Show current patch stats for all heroes"""
    data = load_patch_data()
    if not data:
        return
    
    print(f"\nPatch: {data['patch']}")
    print(f"Release Date: {data.get('release_date', 'N/A')}")
    print(f"Total Heroes: {len(data['heroes'])}\n")
    
    print(f"{'Name':<20} {'Role':<12} {'WR':<8} {'PR':<8} {'BR':<8} {'Tier':<6}")
    print("-" * 70)
    
    for hero in data['heroes']:
        name = hero.get('name', 'Unknown')[:20]
        role = hero.get('role', 'N/A')[:12]
        wr = hero.get('win_rate', 0)
        pr = hero.get('pick_rate', 0)
        br = hero.get('ban_rate', 0)
        tier = hero.get('tier', 'N/A')
        
        print(f"{name:<20} {role:<12} {wr:<8.3f} {pr:<8.3f} {br:<8.3f} {tier:<6}")


def update_hero_stats(hero_name, win_rate=None, pick_rate=None, ban_rate=None, tier=None):
    """Update a hero's stats in the patch data"""
    data = load_patch_data()
    if not data:
        return
    
    # Find the hero
    hero_found = None
    for hero in data['heroes']:
        if hero['name'].lower() == hero_name.lower():
            hero_found = hero
            break
    
    if not hero_found:
        print(f"Hero '{hero_name}' not found!")
        return
    
    # Update stats
    if win_rate is not None:
        hero_found['win_rate'] = float(win_rate)
        print(f"Updated {hero_name} win_rate to {win_rate}")
    
    if pick_rate is not None:
        hero_found['pick_rate'] = float(pick_rate)
        print(f"Updated {hero_name} pick_rate to {pick_rate}")
    
    if ban_rate is not None:
        hero_found['ban_rate'] = float(ban_rate)
        print(f"Updated {hero_name} ban_rate to {ban_rate}")
    
    if tier is not None:
        hero_found['tier'] = tier
        print(f"Updated {hero_name} tier to {tier}")
    
    save_patch_data(data)


def bump_patch(new_patch_version):
    """Bump the patch version"""
    data = load_patch_data()
    if not data:
        return
    
    old_patch = data['patch']
    data['patch'] = new_patch_version
    data['release_date'] = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Patch version: {old_patch} -> {new_patch_version}")
    save_patch_data(data)


def main():
    parser = argparse.ArgumentParser(description='Update MLBB patch data')
    parser.add_argument('--show', action='store_true', help='Show current patch stats')
    parser.add_argument('--hero', type=str, help='Hero name to update')
    parser.add_argument('--wr', type=float, help='Win rate (0-1)')
    parser.add_argument('--pr', type=float, help='Pick rate (0-1)')
    parser.add_argument('--br', type=float, help='Ban rate (0-1)')
    parser.add_argument('--tier', type=str, help='Tier (S+, S, A, B, C)')
    parser.add_argument('--new-patch', type=str, help='Bump patch version (e.g., 1.9.46)')
    
    args = parser.parse_args()
    
    if args.show:
        show_current_stats()
    elif args.new_patch:
        bump_patch(args.new_patch)
    elif args.hero:
        update_hero_stats(
            args.hero,
            win_rate=args.wr,
            pick_rate=args.pr,
            ban_rate=args.br,
            tier=args.tier
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
