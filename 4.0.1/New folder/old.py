import asyncio
from asyncio.windows_events import NULL
from http.client import NON_AUTHORITATIVE_INFORMATION
import math
from pickle import NONE

from wizwalker import ClientHandler
from wizwalker.combat import CombatHandler, CombatMember
from wizwalker.memory.memory_objects.enums import SpellEffects, EffectTarget

DAMAGE_EFFECTS = [
  SpellEffects.damage,
  SpellEffects.damage_no_crit,
  SpellEffects.damage_over_time,
  SpellEffects.damage_per_total_pip_power,
  SpellEffects.max_health_damage,
  SpellEffects.steal_health
]
DAMAGE_ENCHANT_EFFECTS = [
  SpellEffects.modify_card_damage,
  SpellEffects.modify_card_accuracy,
  SpellEffects.modify_card_armor_piercing, 
  SpellEffects.modify_card_damage_by_rank
]
STRICT_DAMAGE_ENCHANT_EFFECTS = [
  SpellEffects.modify_card_damage,
  SpellEffects.modify_card_damage_by_rank
]
DAMAGE_TARGETS = [
  EffectTarget.enemy_team_all_at_once, 
  EffectTarget.enemy_single, 
  EffectTarget.enemy_team
]
TEMPLATE_SCHOOLS = [
  "MagicSchools/FireSchool.xml",
  "MagicSchools/IceSchool.xml",
  "MagicSchools/StormSchool.xml",
  "MagicSchools/MythSchool.xml",
  "MagicSchools/LifeSchool.xml",
  "MagicSchools/DeathSchool.xml",
  "MagicSchools/BalanceSchool.xml"
]
DAMAGE_TYPE_SCHOOLS = [
  "Fire",
  "Ice",
  "Storm",
  "Myth",
  "Life",
  "Death",
  "Balance"
]


class ReadCards(CombatHandler):
  async def get_school_template_name(self, member: CombatMember):
    part = await member.get_participant()
    school_id = await part.primary_magic_school_id()
    return await self.client.cache_handler.get_template_name(school_id)

  async def read_target_effect(self, card):
    card_targets = []

    for effect in await card.get_spell_effects():
      type_name = await effect.maybe_read_type_name()

      if "random" in type_name.lower() or "variable" in type_name.lower():
        subeffects = await effect.maybe_effect_list()
        card_targets.append(await subeffects[0].effect_target())

      else:
        card_targets.append(await effect.effect_target())

    return card_targets

  async def read_spell_effect(self, card):
    spell_effects = []

    for effect in await card.get_spell_effects():
      type_name = await effect.maybe_read_type_name()

      if "random" in type_name.lower() or "variable" in type_name.lower():
        subeffects = await effect.maybe_effect_list()
        spell_effects.append(await subeffects[0].effect_type())

      else:
        spell_effects.append(await effect.effect_type())

    return spell_effects

  async def read_damage_type(self, card):
    spell_effects = []

    for effect in await card.get_spell_effects():
      type_name = await effect.maybe_read_type_name()

      if "random" in type_name.lower() or "variable" in type_name.lower():
        subeffects = await effect.maybe_effect_list()
        spell_effects.append(await subeffects[0].string_damage_type())

      else:
        spell_effects.append(await effect.string_damage_type())

    return spell_effects

  async def average_damage_effect_param(self, card):
    subeffect_params = []
    effect_params = []

    for effect in await card.get_spell_effects():
      type_name = await effect.maybe_read_type_name()

      if "random" in type_name.lower() or "variable" in type_name.lower():
        subeffects = await effect.maybe_effect_list()

        for subeffect in subeffects:

          subeffect_type = await subeffect.effect_type()

          if subeffect_type in DAMAGE_EFFECTS:
            subeffect_params.append(await subeffect.effect_param())
        
        if subeffect_params:
          total = 0
          for effect_param in subeffect_params:
            total += effect_param
        
          return (total / len(subeffect_params))

      else:
        
        effect_type = await effect.effect_type()

        if effect_type in DAMAGE_EFFECTS:
          effect_params.append(await effect.effect_param())

    total_param = 0
    for effect_param in effect_params:
      total_param += effect_param

    return total_param

  async def highest_damage_card(self, cards: list):
    highest_damage = 0
    damagest_card = None
    for card in cards:

      card_effects = await self.read_spell_effect(card)
      card_targets = await self.read_target_effect(card)

      if (any(effects in card_effects for effects in DAMAGE_EFFECTS)) and (any(effects in card_targets for effects in DAMAGE_TARGETS)):
        if await self.average_damage_effect_param(card) > highest_damage:
          highest_damage = await self.average_damage_effect_param(card)
            
          damagest_card = card

    return damagest_card

  async def get_index_from_list(self, name, list):
    for i, x in enumerate(list):
      if name == x:
        return i

  # From WizWalker 2.0 Branch 
  async def get_members_on_team(self, same_as_client: bool = True) -> list[CombatMember]:
    client_member = await self.get_client_member()

    part = await client_member.get_participant()
    client_team_id = await part.team_id()

    async def _on_other_team(member):
      member_part = await member.get_participant()
      member_team_id = await member_part.team_id()

      return member_team_id != client_team_id

    async def _on_same_team(member):
      member_part = await member.get_participant()
      member_team_id = await member_part.team_id()

      return member_team_id == client_team_id

    if same_as_client:
      return await self.get_members_with_predicate(_on_same_team)

    else:
      return await self.get_members_with_predicate(_on_other_team)

  async def is_enough_damage(self, card, *, enchant_card=None, overkill=False):
    """
    Calculates damage from a card and enchant card

    Args:
      card: a damage card
      enchant_card: a damage enchant
      overkill: if True, it will multiply the mob's health by 1.1 as an added safety
    """
    kills = False
    damage_list = []
    member = await self.get_client_member()
    player_part = await member.get_participant()
    mobs = await self.get_members_on_team(same_as_client=False)
    #school_index = await self.get_index_from_list(await self.get_school_template_name(member), TEMPLATE_SCHOOLS)

      ## Declaring card stats
    card_damage_type = (await self.read_damage_type(card))[0]
    print(card_damage_type)
    card_school = await self.get_index_from_list(card_damage_type, DAMAGE_TYPE_SCHOOLS)
    base_damage = await self.average_damage_effect_param(card)


      ## Declaring player stats
    # School
    school_index = await self.get_index_from_list(await self.get_school_template_name(member), TEMPLATE_SCHOOLS)

    # Damage
    school_stats = await self.client.stats.dmg_bonus_percent()
    universal_stat = await self.client.stats.dmg_bonus_percent_all()
    damage_stat = school_stats[school_index] + universal_stat
    damage_stat = damage_stat * 100

    if damage_stat > 1.50:
        l = float(await self.client.duel.damage_limit())
        k = float(await self.client.duel.d_k0())
        n = float(await self.client.duel.d_n0())
        print(f"Damage Limit {l} \n duel.d_k0 {k} \n duel.d_n0 {n}")
        calculated_stat = float(200 - 536.43*(math.e**(-0.0158 * damage_stat)))
        calculated_stat = calculated_stat / 100
    else:
        calculated_stat = damage_stat

    print(
        f"{damage_stat}\nSchool Damage {school_stats} \n Universal Damage {universal_stat} \n School + Universal Damage {calculated_stat}")

    # Flat
    school_flats = await self.client.stats.dmg_bonus_flat()
    universal_flat = await self.client.stats.dmg_bonus_flat_all() 
    damage_flat = school_flats[school_index] + universal_flat

    # Crit
    crit_chance = 0.95
    crit_multiplier = 2.0
    block_chance = 0.0
    #for mob in mobs:
      #if 2:
        #crit_chance = 0.0 # TODO: Need mob specific crit stuff
      #if 2:
        #crit_multiplier = 2.0
      #if 2:
        #block_chance = 0.0
    mob = NONE
    boss_list = []
    mob_list = []
    #TODO pick highest health mob to compare dmg
    for enemy in mobs:
      if enemy.is_boss():
        boss_list.append(enemy)
      else:
        mob_list.append(enemy)
    if mobs:
      if boss_list and not mob_list:
        mob = boss_list[0]
      elif boss_list and mob_list:
        mob = mob_list[0]
      elif mob_list:
        mob = mob_list[0]

    mob_stats = await mob.get_stats()
    client_school_critical = await self.client.stats.critical_hit_rating_by_school()
    _client_school_critical = client_school_critical[school_index]
    mob_block_rating = await mob_stats.block_rating_all()
    _mob_block = mob_block_rating[school_index]


    client_school_critical = (0.03 * 1 * _client_school_critical)
    mob_block = (3 * _client_school_critical + _mob_block)
    crit_multiplier = _client_school_critical / _mob_block

    crit_multiplier = (2 - ((mob_block_rating)/((_client_school_critical/3) + mob_block_rating)))

    print(
          f"\n Clients {_mob_block}")
    print(f"Client school rating{client_school_critical} \n Mob Critical Block Rating {mob_block} \n Critical Calcuation {crit_multiplier}")

    final_damage = int(final_damage * crit_multiplier)

    # Pierce
    player_pierce_school = await self.client.stats.ap_bonus_percent()
    player_pierce_all = await self.client.stats.ap_bonus_percent_all()
    player_pierce = player_pierce_school[card_school] + player_pierce_all
    

      ## Calculating Damage
    # Base damage
    print(f"Base Damage: {base_damage}")
    final_damage = base_damage
    # Add predicted enchant
    if (enchant_card != None) and not await card.is_enchanted() and not await card.is_item_card() and not await card.is_treasure_card():
      enchant_damage = await self.average_damage_effect_param(enchant_card)

      print(f"Enchant Damage: {enchant_damage}")
      final_damage += enchant_damage
    # Percent damage
    print(f"Damage stat: {calculated_stat * 100}%")
    final_damage = int(final_damage * (calculated_stat + 1))

    # Flat damage
    print(f"Flat stat: {damage_flat}")
    final_damage += damage_flat
 
    # Criticals
    full_chance = crit_chance - block_chance
    if full_chance >= 0.85:
      final_damage = int(final_damage * crit_multiplier)

    # Player effects
    hanging_effects = await player_part.hanging_effects() ## TODO: Need to figure out why its reading incorrect values ##
    combat_resolver = await self.client.duel.combat_resolver()
    aura_effects = await player_part.aura_effects()

    outgoing_effects = []
    ap_effects = []

    print(f"Hanging Effects: {hanging_effects}")
    for effect in hanging_effects: # Charms
      effect_type = await effect.effect_type()
      damage_type = await effect.string_damage_type()
      effect_school = await self.get_index_from_list(damage_type, DAMAGE_TYPE_SCHOOLS)
      print(F"Effect Type: {effect_type.name} [{damage_type}]")

      if (SpellEffects.modify_outgoing_damage == effect_type) and ((card_school == effect_school) or (damage_type == "All")):
        outgoing_effects.append(await effect.effect_param())

      if (SpellEffects.modify_outgoing_armor_piercing == effect_type) and ((card_school == effect_school) or (damage_type == "All")):
        ap_effects.append(await effect.effect_param())

    if combat_resolver is not None: # Globals
      global_effect = await combat_resolver.global_effect()
      print(f"Global Effect: {global_effect}")

      if global_effect:
        global_effect_type = await global_effect.effect_type()
        global_damage_type = await global_effect.string_damage_type()
        global_effect_school = await self.get_index_from_list(global_damage_type, DAMAGE_TYPE_SCHOOLS)
        print(F"Effect Type: {global_effect_type.name} [{global_damage_type}]")

        if (SpellEffects.modify_outgoing_damage == global_effect_type) and ((card_school == global_effect_school) or (global_damage_type == "All")):
          outgoing_effects.append(await global_effect.effect_param())

    print(f"Aura Effects: {aura_effects}")
    for effect in aura_effects: # Auras
      effect_type = await effect.effect_type()
      damage_type = await effect.string_damage_type()
      effect_school = await self.get_index_from_list(damage_type, DAMAGE_TYPE_SCHOOLS)
      print(F"Effect Type: {effect_type.name} [{damage_type}]")

      if (SpellEffects.modify_outgoing_damage == effect_type) and ((card_school == effect_school) or (damage_type == "All")):
        outgoing_effects.append(await effect.effect_param())

    print(f"Outgoing effects: {outgoing_effects}")
    for effect in outgoing_effects:
      decimal_effect = (effect / 100) + 1
      if decimal_effect < 1:
        decimal_effect = 1 - decimal_effect
      final_damage = int(final_damage * decimal_effect)

    for effect in ap_effects:
      player_pierce += effect
    print(f"Player Pierce: {player_pierce}")

    # Compare to Mobs 
    for mob in mobs:
      mob_damage = final_damage

      mob_part = await mob.get_participant()
      mob_hanging_effects = await mob_part.hanging_effects()
      mob_aura_effects = await mob_part.aura_effects()

      incoming_effects = []
      for effect in mob_hanging_effects:
        effect_type = await effect.effect_type()
        damage_type = await effect.string_damage_type()
        effect_school = await self.get_index_from_list(damage_type, DAMAGE_TYPE_SCHOOLS)
        print(f"Effect Type: {effect_type.name} [{damage_type}]")

        if (SpellEffects.modify_incoming_damage_type == effect_type) and (card_school == effect_school):
          if card_school < 6:
            if (card_school % 2) == 1:
              card_school -= 1
              print(f"Card School after Prism: {card_school}")

            elif (card_school % 2) == 0:
              card_school += 1
              print(f"Card School after Prism: {card_school}")

        if (SpellEffects.modify_incoming_damage == effect_type) and ((card_school == effect_school) or (damage_type == "All")):
          hanging_param = await effect.effect_param()

          if hanging_param < 0:
            hanging_param += player_pierce

            if hanging_param > 0:
              player_pierce = hanging_param
              hanging_param = 0

          incoming_effects.append(hanging_param)

      for effect in mob_aura_effects:
        effect_type = await effect.effect_type()
        damage_type = await effect.string_damage_type()
        effect_school = await self.get_index_from_list(damage_type, DAMAGE_TYPE_SCHOOLS)
        print(f"Effect Type: {effect_type.name} [{damage_type}]")

        if (SpellEffects.modify_incoming_damage == effect_type) and ((card_school == effect_school) or (damage_type == "All")):
          hanging_param = await effect.effect_param()

          if hanging_param < 0:
            hanging_param += player_pierce

            if hanging_param > 0:
              player_pierce = hanging_param
              hanging_param = 0

          incoming_effects.append(hanging_param)
          

      print(f"Incoming effects: {incoming_effects}")  
      for effect in incoming_effects:
        decimal_effect = (effect / 100) + 1
        if decimal_effect < 1:
          decimal_effect = 1 - decimal_effect
        mob_damage = int(mob_damage * decimal_effect)

      mob_stats = await mob.get_stats()
      mob_resist_school = await mob_stats.dmg_reduce_percent()
      mob_resist_all = await mob_stats.dmg_reduce_percent_all()
      mob_resist = mob_resist_school[card_school] + mob_resist_all

      if mob_resist > 0:
        mob_resist -= player_pierce

        if mob_resist < 0:
          mob_resist = 0
      
      elif mob_resist < 0:
        mob_resist = abs(mob_resist) + 1

      if mob_resist != 0:
        mob_damage = int(mob_damage * mob_resist)

      print(f"Mob Resist/Boost: {mob_resist}")

      mob_health = await mob.health()
      #if overkill:
        #mob_health *= 1.10

      print(f"{await mob.name()}'s Health: {mob_health} vs your calculated damage: {mob_damage}")
      if mob_health < mob_damage:
       return True
    return False
    












  async def handle_round(self,cards):
    await asyncio.sleep(0.5)

    mobs = await self.get_all_monster_members()

    # Finds the boss(es)
    is_boss = False
    is_multi_boss = False
    for mob in mobs:
      if await mob.is_boss():
        if is_boss == True:
          is_multi_boss = True
        is_boss = True
        boss = mob
    if is_multi_boss:
      is_boss = False

    # Sorting Enchants and Normals
    enchants = []
    normals = []
    for card in cards:
      if await card.is_castable():
        enchant_target = await self.read_target_effect(card)

        if EffectTarget.spell in enchant_target:
          enchants.append(card)
        else:
          normals.append(card)

    # Sorting enchants  
    damage_enchants = []
    strict_damage_enchants = []
    for enchant in enchants:
      enchant_types = await self.read_spell_effect(enchant)

      if any(effects in enchant_types for effects in DAMAGE_ENCHANT_EFFECTS):
        damage_enchants.append(enchant)
      if any(effects in enchant_types for effects in STRICT_DAMAGE_ENCHANT_EFFECTS):
        strict_damage_enchants.append(enchant)

    # Finding Highest Damage card
    damagest_card = await self.highest_damage_card(normals)

    if strict_damage_enchants:
      enchant_damage = strict_damage_enchants[0]
    else:
      enchant_damage = None

    if damagest_card:
      if result := await self.is_enough_damage(damagest_card, enchant_card=enchant_damage, overkill=True):
        return damagest_card,result
    print("Ready to cast")
    return None,False