import json
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Pokemon, HeldItem, Move, Team, TeamMember

# 1. OFFICIAL TYPE EFFECTIVENESS CHART
TYPE_CHART = {
    'normal': {'rock': 0.5, 'ghost': 0.0, 'steel': 0.5},
    'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2.0, 'ice': 2.0, 'bug': 2.0, 'rock': 0.5, 'dragon': 0.5, 'steel': 2.0},
    'water': {'fire': 2.0, 'water': 0.5, 'grass': 0.5, 'ground': 2.0, 'rock': 2.0, 'dragon': 0.5},
    'electric': {'water': 2.0, 'electric': 0.5, 'grass': 0.5, 'ground': 0.0, 'flying': 2.0, 'dragon': 0.5},
    'grass': {'fire': 0.5, 'water': 2.0, 'grass': 0.5, 'poison': 0.5, 'ground': 2.0, 'flying': 0.5, 'bug': 0.5, 'rock': 2.0, 'dragon': 0.5, 'steel': 0.5},
    'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2.0, 'ice': 0.5, 'ground': 2.0, 'flying': 2.0, 'dragon': 2.0, 'steel': 0.5},
    'fighting': {'normal': 2.0, 'ice': 2.0, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2.0, 'ghost': 0.0, 'dark': 2.0, 'steel': 2.0, 'fairy': 0.5},
    'poison': {'grass': 2.0, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0.0, 'fairy': 2.0},
    'ground': {'fire': 2.0, 'electric': 2.0, 'grass': 0.5, 'poison': 2.0, 'flying': 0.0, 'bug': 0.5, 'rock': 2.0, 'steel': 2.0},
    'flying': {'electric': 0.5, 'grass': 2.0, 'fighting': 2.0, 'bug': 2.0, 'rock': 0.5, 'steel': 0.5},
    'psychic': {'fighting': 2.0, 'poison': 2.0, 'psychic': 0.5, 'dark': 0.0, 'steel': 0.5},
    'bug': {'fire': 0.5, 'grass': 2.0, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2.0, 'ghost': 0.5, 'dark': 2.0, 'steel': 0.5, 'fairy': 0.5},
    'rock': {'fire': 2.0, 'ice': 2.0, 'fighting': 0.5, 'ground': 0.5, 'flying': 2.0, 'bug': 2.0, 'steel': 0.5},
    'ghost': {'normal': 0.0, 'psychic': 2.0, 'ghost': 2.0, 'dark': 0.5},
    'dragon': {'dragon': 2.0, 'steel': 0.5, 'fairy': 0.0},
    'dark': {'fighting': 0.5, 'psychic': 2.0, 'ghost': 2.0, 'dark': 0.5, 'fairy': 0.5},
    'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2.0, 'rock': 2.0, 'steel': 0.5, 'fairy': 2.0},
    'fairy': {'fire': 0.5, 'fighting': 2.0, 'poison': 0.5, 'dragon': 2.0, 'dark': 2.0, 'steel': 0.5}
}

# Spread Moves in Doubles (0.75x modifier ONLY in Doubles)
SPREAD_MOVES = {
    'make it rain', 'earthquake', 'rock slide', 'muddy water', 'dazzling gleam',
    'heat wave', 'icy wind', 'snarl', 'hyper voice', 'blizzard', 'eruption',
    'water spout', 'bulldoze', 'electroweb', 'breaking swipe', 'discharge', 'surf'
}

ALLY_HIT_MOVES = {'earthquake', 'bulldoze', 'discharge', 'surf'}

def get_type_effectiveness(move_type, def_type1, def_type2):
    multiplier = 1.0
    move_type = move_type.lower()
    if move_type in TYPE_CHART:
        if def_type1 and def_type1.lower() in TYPE_CHART[move_type]:
            multiplier *= TYPE_CHART[move_type][def_type1.lower()]
        if def_type2 and def_type2.lower() in TYPE_CHART[move_type]:
            multiplier *= TYPE_CHART[move_type][def_type2.lower()]
    return multiplier

# 2. AUTO-FETCH STATS FROM POKEAPI IF MISSING
def ensure_pokemon_stats(pokemon):
    if pokemon.hp == 50 and pokemon.attack == 50:
        slug = pokemon.name.lower().replace(' ', '-')
        try:
            res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{slug}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                pokemon.hp = stats.get('hp', 50)
                pokemon.attack = stats.get('attack', 50)
                pokemon.defense = stats.get('defense', 50)
                pokemon.sp_atk = stats.get('special-attack', 50)
                pokemon.sp_def = stats.get('special-defense', 50)
                pokemon.speed = stats.get('speed', 50)
                
                types = [t['type']['name'] for t in data['types']]
                pokemon.type1 = types[0]
                pokemon.type2 = types[1] if len(types) > 1 else None
                pokemon.save()
        except Exception:
            pass
    return pokemon

def ensure_move_stats(move):
    if move.base_damage == 0 and move.damage_type == 'physical':
        slug = move.name.lower().replace(' ', '-')
        try:
            res = requests.get(f"https://pokeapi.co/api/v2/move/{slug}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                move.base_damage = data.get('power') or 0
                move.accuracy = data.get('accuracy') or 100
                move.move_type = data['type']['name']
                move.damage_type = data['damage_class']['name']
                move.save()
        except Exception:
            pass
    return move

# 3. UNIFIED BUILDER & TEAM MANAGER HUB
def team_builder(request):
    pokemons = Pokemon.objects.exclude(name__contains=' Mega').order_by('name')
    items = HeldItem.objects.all().order_by('name')
    teams = Team.objects.all().order_by('-id')
    return render(request, 'calculator/builder.html', {
        'pokemons': pokemons,
        'items': items,
        'teams': teams
    })

def team_manager(request):
    return redirect('team_builder')

@csrf_exempt
def save_team(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        team_name = data['team_name'].strip()
        
        team = Team.objects.filter(name__iexact=team_name).first()
        if not team:
            team = Team.objects.create(name=team_name)
            
        pokemon = Pokemon.objects.filter(name__iexact=data['pokemon_name'].strip()).first()
        if not pokemon:
            return JsonResponse({'status': 'error', 'message': 'Pokémon not found in database.'}, status=400)
            
        ensure_pokemon_stats(pokemon)
        item = HeldItem.objects.filter(name__iexact=data['item_name'].strip()).first()
        
        move_objs = []
        for move_name in data['moves']:
            if move_name:
                move, _ = Move.objects.get_or_create(
                    name=move_name.strip().title(),
                    pokemon=pokemon,
                    defaults={'damage_type': 'physical', 'base_damage': 0, 'scaling_ratio': 1.0}
                )
                ensure_move_stats(move)
                move_objs.append(move)
                
        while len(move_objs) < 4:
            move_objs.append(None)

        member_id = data.get('member_id')
        if member_id:
            member = get_object_or_404(TeamMember, id=member_id)
            member.team = team
            member.pokemon = pokemon
            member.held_item = item
            member.move1 = move_objs[0]
            member.move2 = move_objs[1]
            member.move3 = move_objs[2]
            member.move4 = move_objs[3]
            member.save()
        else:
            TeamMember.objects.create(
                team=team,
                pokemon=pokemon,
                held_item=item,
                move1=move_objs[0],
                move2=move_objs[1],
                move3=move_objs[2],
                move4=move_objs[3]
            )
        return JsonResponse({'status': 'success'})

@csrf_exempt
def delete_team(request, team_id):
    if request.method == 'POST':
        Team.objects.filter(id=team_id).delete()
        return JsonResponse({'status': 'success'})

@csrf_exempt
def delete_member(request, member_id):
    if request.method == 'POST':
        TeamMember.objects.filter(id=member_id).delete()
        return JsonResponse({'status': 'success'})

# 4. SINGLES (3v3) & DOUBLES (4v4) TACTICAL BATTLE SIMULATOR
def battle_simulator(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    pokemons = Pokemon.objects.exclude(name__contains=' Mega').order_by('name')
    return render(request, 'calculator/battle.html', {'team': team, 'pokemons': pokemons})

def get_combatant_stats(pokemon, held_item=None):
    pokemon = ensure_pokemon_stats(pokemon)
    stats = {
        'name': pokemon.name,
        'hp': pokemon.hp, 'atk': pokemon.attack, 'def': pokemon.defense,
        'sp_atk': pokemon.sp_atk, 'sp_def': pokemon.sp_def, 'speed': pokemon.speed,
        'type1': pokemon.type1, 'type2': pokemon.type2
    }
    if held_item and 'ite' in held_item.name.lower():
        mega_slug = pokemon.name.lower().replace(' ', '-') + '-mega'
        if ' x' in held_item.name.lower(): mega_slug += '-x'
        if ' y' in held_item.name.lower(): mega_slug += '-y'
        try:
            res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{mega_slug}", timeout=4)
            if res.status_code == 200:
                m_data = res.json()
                m_stats = {s['stat']['name']: s['base_stat'] for s in m_data['stats']}
                stats['name'] = pokemon.name + " (Mega)"
                stats['atk'] = m_stats.get('attack', stats['atk'])
                stats['def'] = m_stats.get('defense', stats['def'])
                stats['sp_atk'] = m_stats.get('special-attack', stats['sp_atk'])
                stats['sp_def'] = m_stats.get('special-defense', stats['sp_def'])
                stats['speed'] = m_stats.get('speed', stats['speed'])
                m_types = [t['type']['name'] for t in m_data['types']]
                stats['type1'] = m_types[0]
                stats['type2'] = m_types[1] if len(m_types) > 1 else None
        except Exception:
            pass

    def calc_lv50(base, is_hp=False):
        if is_hp:
            return int(((2 * base + 31) * 50 / 100) + 50 + 10)
        return int(((2 * base + 31) * 50 / 100) + 5)

    return {
        'name': stats['name'],
        'type1': stats['type1'],
        'type2': stats['type2'],
        'max_hp': calc_lv50(stats['hp'], True),
        'atk': calc_lv50(stats['atk']),
        'def': calc_lv50(stats['def']),
        'sp_atk': calc_lv50(stats['sp_atk']),
        'sp_def': calc_lv50(stats['sp_def']),
        'speed': calc_lv50(stats['speed']),
    }

def evaluate_member_actions(member, my_stats, partner_stats, opp1_stats, opp2_stats, state, is_singles=False):
    moves = [member.move1, member.move2, member.move3, member.move4]
    actions = []

    threat_from_1 = max(
        get_type_effectiveness(opp1_stats['type1'], my_stats['type1'], my_stats['type2']),
        get_type_effectiveness(opp1_stats['type2'], my_stats['type1'], my_stats['type2']) if opp1_stats['type2'] else 0
    ) if state['opp1_hp'] > 0 else 0

    threat_from_2 = 0
    if not is_singles and opp2_stats and state['opp2_hp'] > 0:
        threat_from_2 = max(
            get_type_effectiveness(opp2_stats['type1'], my_stats['type1'], my_stats['type2']),
            get_type_effectiveness(opp2_stats['type2'], my_stats['type1'], my_stats['type2']) if opp2_stats['type2'] else 0
        )

    max_incoming_threat = max(threat_from_1, threat_from_2)

    for m in moves:
        if not m:
            continue
        m = ensure_move_stats(m)
        m_lower = m.name.lower()

        # 1. TACTICAL & STATUS MOVES
        if m_lower in ['protect', 'detect', 'spiky shield']:
            if is_singles:
                score = 45 if max_incoming_threat >= 2.0 else 15
                reason = "Scouts opponent's move in Singles, though switching to a Bench resist is often safer."
            else:
                score = 85 if max_incoming_threat >= 2.0 else 25
                reason = "High-value Doubles stall! Baits super-effective attacks while partner attacks freely."
            actions.append({
                'move': m.name, 'target': 'Self', 'target_slot': 'self',
                'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                'score': score, 'reason': reason, 'is_spread': False
            })
            continue

        if m_lower == 'fake out':
            if state['turn'] == 1:
                opp_list = [(opp1_stats, 'opp1_hp')] if is_singles else [(opp1_stats, 'opp1_hp'), (opp2_stats, 'opp2_hp')]
                for idx, (opp, opp_hp_key) in enumerate(opp_list, start=1):
                    if not opp or state[opp_hp_key] <= 0:
                        continue
                    eff = get_type_effectiveness('normal', opp['type1'], opp['type2'])
                    if eff == 0:
                        actions.append({
                            'move': m.name, 'target': opp['name'], 'target_slot': f'opp{idx}',
                            'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                            'score': -50, 'reason': f"{opp['name']} is Ghost-type (Immune to Fake Out)!", 'is_spread': False
                        })
                    else:
                        flinch_score = 115 if is_singles else 135
                        flinch_note = "Free Turn 1 priority chip damage + flinch!" if is_singles else f"Turn 1 Priority Flinch! Shuts down {opp['name']} while partner acts freely."
                        actions.append({
                            'move': m.name, 'target': opp['name'], 'target_slot': f'opp{idx}',
                            'dmg_opp1': 12 if idx == 1 else 0, 'dmg_opp2': 12 if idx == 2 else 0, 'dmg_ally': 0,
                            'score': flinch_score, 'reason': flinch_note, 'is_spread': False
                        })
            else:
                actions.append({
                    'move': m.name, 'target': 'None', 'target_slot': 'none',
                    'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                    'score': -100, 'reason': "Fake Out FAILS after Turn 1!", 'is_spread': False
                })
            continue

        if m_lower == 'trick room':
            if is_singles:
                slower = my_stats['speed'] < opp1_stats['speed']
            else:
                slower = ((my_stats['speed'] + partner_stats['speed']) / 2) < ((opp1_stats['speed'] + opp2_stats['speed']) / 2)
            if not state['trick_room'] and slower:
                actions.append({
                    'move': m.name, 'target': 'Field', 'target_slot': 'field',
                    'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                    'score': 135, 'reason': "Elite Speed Control! Reverses turn order so your slower Pokémon moves first.", 'is_spread': False
                })
            else:
                actions.append({
                    'move': m.name, 'target': 'Field', 'target_slot': 'field',
                    'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                    'score': 10, 'reason': "Trick Room is already active or you already outspeed.", 'is_spread': False
                })
            continue

        if m_lower == 'tailwind':
            score = 120 if not state['tailwind'] else 10
            actions.append({
                'move': m.name, 'target': 'Team', 'target_slot': 'field',
                'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                'score': score, 'reason': "Doubles your team's Speed stat for 4 turns!", 'is_spread': False
            })
            continue

        if m_lower == 'helping hand':
            if is_singles:
                actions.append({
                    'move': m.name, 'target': 'None', 'target_slot': 'none',
                    'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                    'score': -100, 'reason': "Helping Hand has no ally target in 3v3 Singles!", 'is_spread': False
                })
            else:
                actions.append({
                    'move': m.name, 'target': partner_stats['name'], 'target_slot': 'ally',
                    'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                    'score': 90, 'reason': f"Boosts {partner_stats['name']}'s attack damage by 1.5x this turn!", 'is_spread': False
                })
            continue

        if m.damage_type == 'status' or m.base_damage == 0:
            actions.append({
                'move': m.name, 'target': 'Opponent / Field', 'target_slot': 'status',
                'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
                'score': 60, 'reason': f"Tactical status/setup move ({m.name}).", 'is_spread': False
            })
            continue

        # 2. DAMAGING MOVES EVALUATION
        # In Singles, spread moves do full 1.0x damage!
        is_spread = (m_lower in SPREAD_MOVES) and (not is_singles)
        spread_mod = 0.75 if is_spread else 1.0
        stab = 1.5 if m.move_type in [my_stats['type1'], my_stats['type2']] else 1.0

        weather_mod = 1.0
        if state['weather'] == 'rain':
            if m.move_type == 'water': weather_mod = 1.5
            elif m.move_type == 'fire': weather_mod = 0.5
        elif state['weather'] == 'sun':
            if m.move_type == 'fire': weather_mod = 1.5
            elif m.move_type == 'water': weather_mod = 0.5

        def calc_pct_against(target_stats):
            atk_val = my_stats['atk'] if m.damage_type == 'physical' else my_stats['sp_atk']
            def_val = target_stats['def'] if m.damage_type == 'physical' else target_stats['sp_def']
            base_dmg = (((2 * 50 / 5 + 2) * m.base_damage * (atk_val / def_val)) / 50) + 2
            eff = get_type_effectiveness(m.move_type, target_stats['type1'], target_stats['type2'])
            avg_dmg = base_dmg * stab * eff * spread_mod * weather_mod * 0.925
            return round((avg_dmg / target_stats['max_hp']) * 100, 1), eff

        if is_spread:
            d1, eff1 = calc_pct_against(opp1_stats) if state['opp1_hp'] > 0 else (0, 1)
            d2, eff2 = calc_pct_against(opp2_stats) if state['opp2_hp'] > 0 else (0, 1)
            d_ally = 0
            ally_note = ""
            if m_lower in ALLY_HIT_MOVES and partner_stats:
                d_ally, eff_ally = calc_pct_against(partner_stats)
                if d_ally > 0:
                    ally_note = f" (WARNING: Hits ally {partner_stats['name']} for {d_ally}%!)"

            ko_bonus = 0
            if state['opp1_hp'] > 0 and d1 >= state['opp1_hp']: ko_bonus += 45
            if state['opp2_hp'] > 0 and d2 >= state['opp2_hp']: ko_bonus += 45

            score = round(d1 + d2 + ko_bonus - (d_ally * 1.3), 1)
            actions.append({
                'move': m.name, 'target': 'Both Opponents (Spread)', 'target_slot': 'both',
                'dmg_opp1': d1, 'dmg_opp2': d2, 'dmg_ally': d_ally,
                'score': score,
                'reason': f"Spread AoE (0.75x): Hits {opp1_stats['name']} for {d1}% and {opp2_stats['name']} for {d2}%.{ally_note}",
                'is_spread': True
            })
        else:
            opp_list = [(opp1_stats, 'opp1_hp')] if is_singles else [(opp1_stats, 'opp1_hp'), (opp2_stats, 'opp2_hp')]
            for idx, (opp, opp_hp_key) in enumerate(opp_list, start=1):
                if not opp or state[opp_hp_key] <= 0:
                    continue
                d_pct, eff = calc_pct_against(opp)
                effective_dmg = min(d_pct, state[opp_hp_key])
                ko_bonus = 50 if d_pct >= state[opp_hp_key] else 0
                acc_mod = (m.accuracy / 100.0) if m.accuracy else 1.0
                score = round((effective_dmg + ko_bonus) * acc_mod, 1)

                verdict_str = f"KO's {opp['name']}! ({d_pct}% dmg)" if ko_bonus > 0 else f"Deals {d_pct}% ({eff}x effective)."
                actions.append({
                    'move': m.name, 'target': opp['name'], 'target_slot': f'opp{idx}',
                    'dmg_opp1': d_pct if idx == 1 else 0,
                    'dmg_opp2': d_pct if idx == 2 else 0,
                    'dmg_ally': 0,
                    'score': score,
                    'reason': verdict_str,
                    'is_spread': False
                })

    # In Singles, also check if switching to Bench 1 or Bench 2 is a smarter tactical play!
    if is_singles and max_incoming_threat >= 2.0 and opp1_stats['speed'] > my_stats['speed']:
        actions.append({
            'move': '🔄 Switch to Bench Resist',
            'target': 'Your Bench',
            'target_slot': 'self',
            'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0,
            'score': 95,
            'reason': f"DANGER: {opp1_stats['name']} outspeeds and threatens {max_incoming_threat}x super-effective STAB! Consider pivoting to a Bench Pokémon.",
            'is_spread': False
        })

    actions.sort(key=lambda x: x['score'], reverse=True)
    return actions

@csrf_exempt
def simulate_turn(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        battle_format = data.get('battle_format', 'doubles')
        is_singles = (battle_format == 'singles')

        member_a = get_object_or_404(TeamMember, id=data['active_a_id'])
        opp1_pkm = get_object_or_404(Pokemon, name__iexact=data['opp1_name'].strip())

        state = {
            'turn': int(data.get('turn', 1)),
            'opp1_hp': float(data.get('opp1_hp', 100)),
            'opp2_hp': float(data.get('opp2_hp', 100)) if not is_singles else 0,
            'my_a_hp': float(data.get('my_a_hp', 100)),
            'my_b_hp': float(data.get('my_b_hp', 100)) if not is_singles else 0,
            'weather': data.get('weather', 'none'),
            'trick_room': bool(data.get('trick_room', False)),
            'tailwind': bool(data.get('tailwind', False)),
        }

        stats_a = get_combatant_stats(member_a.pokemon, member_a.held_item)
        stats_opp1 = get_combatant_stats(opp1_pkm)

        spd_mult = 2.0 if state['tailwind'] else 1.0

        # SINGLES (3v3) EVALUATION
        if is_singles:
            actions_a = evaluate_member_actions(member_a, stats_a, None, stats_opp1, None, state, is_singles=True)
            best_act = actions_a[0] if actions_a else {
                'move': 'No Move', 'target': stats_opp1['name'], 'dmg_opp1': 0, 'dmg_opp2': 0, 'dmg_ally': 0, 'score': 0, 'reason': 'No moves assigned.'
            }
            best_pair = {
                'slot_a': best_act,
                'slot_b': None,
                'proj_opp1_hp': max(0, round(state['opp1_hp'] - best_act['dmg_opp1'], 1)),
                'proj_opp2_hp': 0,
                'proj_my_a_hp': state['my_a_hp'],
                'proj_my_b_hp': 0,
            }
            order_list = [
                {'name': f"Your {stats_a['name']}", 'speed': int(stats_a['speed'] * spd_mult)},
                {'name': f"Opp {stats_opp1['name']}", 'speed': stats_opp1['speed']},
            ]
            order_list.sort(key=lambda x: x['speed'], reverse=not state['trick_room'])

            return JsonResponse({
                'battle_format': 'singles',
                'turn': state['turn'],
                'speed_order': order_list,
                'best_pair': best_pair,
                'actions_a': actions_a,
                'actions_b': [],
                'names': {
                    'a': stats_a['name'],
                    'b': '',
                    'opp1': stats_opp1['name'],
                    'opp2': ''
                }
            })

        # DOUBLES (4v4) EVALUATION
        member_b = get_object_or_404(TeamMember, id=data['active_b_id'])
        opp2_pkm = get_object_or_404(Pokemon, name__iexact=data['opp2_name'].strip())
        stats_b = get_combatant_stats(member_b.pokemon, member_b.held_item)
        stats_opp2 = get_combatant_stats(opp2_pkm)

        actions_a = evaluate_member_actions(member_a, stats_a, stats_b, stats_opp1, stats_opp2, state, is_singles=False)
        actions_b = evaluate_member_actions(member_b, stats_b, stats_a, stats_opp1, stats_opp2, state, is_singles=False)

        best_pair = None
        best_pair_score = -999

        for act_a in actions_a[:4]:
            for act_b in actions_b[:4]:
                if act_a['move'].lower() == 'fake out' and act_b['move'].lower() == 'fake out' and act_a['target_slot'] == act_b['target_slot']:
                    continue
                if act_a['move'].lower() == 'trick room' and act_b['move'].lower() == 'trick room':
                    continue

                comb_dmg_1 = act_a['dmg_opp1'] + act_b['dmg_opp1']
                comb_dmg_2 = act_a['dmg_opp2'] + act_b['dmg_opp2']

                if act_a['move'].lower() == 'helping hand':
                    comb_dmg_1 = round(act_b['dmg_opp1'] * 1.5, 1)
                    comb_dmg_2 = round(act_b['dmg_opp2'] * 1.5, 1)
                elif act_b['move'].lower() == 'helping hand':
                    comb_dmg_1 = round(act_a['dmg_opp1'] * 1.5, 1)
                    comb_dmg_2 = round(act_a['dmg_opp2'] * 1.5, 1)

                pair_score = act_a['score'] + act_b['score']

                if state['opp1_hp'] > 0 and act_a['dmg_opp1'] >= state['opp1_hp'] and act_b['target_slot'] == 'opp1':
                    pair_score -= 60
                if state['opp2_hp'] > 0 and act_a['dmg_opp2'] >= state['opp2_hp'] and act_b['target_slot'] == 'opp2':
                    pair_score -= 60

                if state['opp1_hp'] > 0 and act_a['dmg_opp1'] < state['opp1_hp'] and act_b['dmg_opp1'] < state['opp1_hp'] and comb_dmg_1 >= state['opp1_hp']:
                    pair_score += 55
                if state['opp2_hp'] > 0 and act_a['dmg_opp2'] < state['opp2_hp'] and act_b['dmg_opp2'] < state['opp2_hp'] and comb_dmg_2 >= state['opp2_hp']:
                    pair_score += 55

                if pair_score > best_pair_score:
                    best_pair_score = pair_score
                    best_pair = {
                        'slot_a': act_a,
                        'slot_b': act_b,
                        'proj_opp1_hp': max(0, round(state['opp1_hp'] - comb_dmg_1, 1)),
                        'proj_opp2_hp': max(0, round(state['opp2_hp'] - comb_dmg_2, 1)),
                        'proj_my_a_hp': max(0, round(state['my_a_hp'] - act_b['dmg_ally'], 1)),
                        'proj_my_b_hp': max(0, round(state['my_b_hp'] - act_a['dmg_ally'], 1)),
                    }

        order_list = [
            {'name': f"Your {stats_a['name']}", 'speed': int(stats_a['speed'] * spd_mult)},
            {'name': f"Your {stats_b['name']}", 'speed': int(stats_b['speed'] * spd_mult)},
            {'name': f"Opp {stats_opp1['name']}", 'speed': stats_opp1['speed']},
            {'name': f"Opp {stats_opp2['name']}", 'speed': stats_opp2['speed']},
        ]
        order_list.sort(key=lambda x: x['speed'], reverse=not state['trick_room'])

        return JsonResponse({
            'battle_format': 'doubles',
            'turn': state['turn'],
            'speed_order': order_list,
            'best_pair': best_pair,
            'actions_a': actions_a,
            'actions_b': actions_b,
            'names': {
                'a': stats_a['name'],
                'b': stats_b['name'],
                'opp1': stats_opp1['name'],
                'opp2': stats_opp2['name']
            }
        })