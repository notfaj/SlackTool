import asyncio
import time
from wizwalker.combat import CombatHandler, CombatMember
from wizwalker.memory.memory_objects.enums import SpellEffects, EffectTarget, DuelPhase
from loguru import logger

# TODO: Damage Calculations
# TODO: Team Logic

DAMAGE_EFFECTS = [
	SpellEffects.damage,
	SpellEffects.damage_no_crit,
	SpellEffects.damage_over_time,
	SpellEffects.damage_per_total_pip_power,
	SpellEffects.max_health_damage,
	SpellEffects.steal_health
]
DAMAGE_TARGETS = [
	EffectTarget.enemy_team_all_at_once, 
	EffectTarget.enemy_single, 
	EffectTarget.enemy_team
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
HEALING_EFFECTS = [
	SpellEffects.heal,
	SpellEffects.heal_over_time,
	SpellEffects.heal_percent,
	SpellEffects.heal_by_ward,
	SpellEffects.max_health_heal
]
TRAP_ENCHANT_EFFECTS = [
	SpellEffects.modify_card_incoming_damage, 
	SpellEffects.protect_card_harmful,
]
CHARM_ENCHANT_EFFECTS = [
	SpellEffects.modify_card_outgoing_damage, 
	SpellEffects.protect_card_beneficial
]
FRIENDLY_TARGETS = [
	EffectTarget.friendly_single, 
	EffectTarget.friendly_team, 
	EffectTarget.friendly_team_all_at_once
]
ENEMY_TARGETS = [
	EffectTarget.enemy_single, 
	EffectTarget.enemy_team, 
	EffectTarget.enemy_team_all_at_once
]
DAMAGE_AURA_GLOBAL_EFFECTS = [
	SpellEffects.modify_outgoing_damage, 
	SpellEffects.modify_outgoing_armor_piercing
]
AURA_GLOBAL_TARGETS = [
	EffectTarget.self, 
	EffectTarget.target_global
]
AURA_GLOBAL_EFFECTS = [
	SpellEffects.pip_conversion, 
	SpellEffects.power_pip_conversion, 
	SpellEffects.modify_power_pip_chance, 
	SpellEffects.modify_outgoing_armor_piercing, 
	SpellEffects.modify_outgoing_heal, 
	SpellEffects.modify_accuracy
]
CHARM_EFFECTS = [
	SpellEffects.modify_outgoing_damage,
	SpellEffects.modify_accuracy,
	SpellEffects.dispel
]
NONE_TARGETS = [
	EffectTarget.self, 
	EffectTarget.enemy_team, 
	EffectTarget.enemy_team_all_at_once, 
	EffectTarget.target_global, 
	EffectTarget.friendly_team, 
	EffectTarget.friendly_team_all_at_once
]
DAMAGE_AOE_TARGETS = [
	EffectTarget.enemy_team,
	EffectTarget.enemy_team_all_at_once
]

class WizFighter(CombatHandler):
	def __init__(self, client, clients):
		self.client = client
		self.clients = clients
		self._spell_check_boxes = None

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

	async def read_effect_param(self, card):
		effect_params = []

		for effect in await card.get_spell_effects():
			type_name = await effect.maybe_read_type_name()

			if "random" in type_name.lower() or "variable" in type_name.lower():
				subeffects = await effect.maybe_effect_list()

				for subeffect in subeffects:
					effect_params.append(await subeffect.effect_param())

			else:
				effect_params.append(await effect.effect_param())

		return effect_params

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

	async def highest_health_mob(self, mobs):
		to_kill_health = 0

		for mob in mobs:
			if await mob.health() > to_kill_health:
				to_kill_health = await mob.health()
				to_kill = mob
			
		return to_kill 

	async def highest_damage_card(self, cards: list):
		highest_damage = 0
		damagest_card = "empty"

		for card in cards:

			card_effects = await self.read_spell_effect(card)
			card_targets = await self.read_target_effect(card)

			if (any(effects in card_effects for effects in DAMAGE_EFFECTS)) and (any(effects in card_targets for effects in DAMAGE_TARGETS)):
				if await self.average_damage_effect_param(card) > highest_damage:
					highest_damage = await self.average_damage_effect_param(card)
						
					damagest_card = card

		return damagest_card

	async def highest_damage_aoe(self, cards: list):
		highest_damage = 0
		damagest_aoe = "empty"

		for card in cards:

			card_effects = await self.read_spell_effect(card)
			card_targets = await self.read_target_effect(card)

			if (any(effects in card_effects for effects in DAMAGE_EFFECTS)) and (any(effects in card_targets for effects in DAMAGE_AOE_TARGETS)):
				if await self.average_damage_effect_param(card) > highest_damage:
					highest_damage = await self.average_damage_effect_param(card)
						
					damagest_aoe = card

		return damagest_aoe

	async def get_enchanted_spells_by_spell_effect(self, effects: list):
		async def _pred(card):
			card_effects = await self.read_spell_effect(card)
			return (any(effect in card_effects for effect in effects)) and await card.is_castable() and await card.is_enchanted()

		return await self.get_cards_with_predicate(_pred)

	async def get_enchanted_spells_by_target_effect(self, effects: list):
		async def _pred(card):
			card_targets = await self.read_target_effect(card)
			return (any(effect in card_targets for effect in effects)) and await card.is_castable() and await card.is_enchanted()

		return await self.get_cards_with_predicate(_pred)

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
		# start = time.perf_counter()
		if same_as_client:
			thing_to_return = await self.get_members_with_predicate(_on_same_team)
			# end = time.perf_counter()
			# logger.debug(f"_on_same_team took {end - start} seconds to complete")

		else:
			thing_to_return = await self.get_members_with_predicate(_on_other_team)
			# end = time.perf_counter()
			# logger.debug(f"_on_other_team took {end - start} seconds to complete")
		return thing_to_return

	async def handle_round(self):
		await self.client.mouse_handler.activate_mouseless()
		while True:
			try:
				mobs = None
				teammates = None
				client_member = None
				await asyncio.sleep(0.5)


				async def client_member_function():
					nonlocal client_member
					client_member = await self.get_client_member()

				async def get_teammates_on_team_function():
					nonlocal teammates
					teammates = await self.get_members_on_team(same_as_client=True)

				async def get_enemies_on_team_function():
					nonlocal mobs
					mobs = await self.get_members_on_team(same_as_client=False)

				await asyncio.gather(*[client_member_function(), get_teammates_on_team_function(), get_enemies_on_team_function()])
				to_kill = await self.highest_health_mob(mobs)

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

				# Need Heals
				to_heal = None
				for teammate in teammates:
					if (await teammate.health() / await teammate.max_health()) < 0.33:
						to_heal = teammate

				# Sorting Enchants and Normals
				enchants = []
				normals = []
				for card in await self.get_cards():
					if await card.is_castable():
						enchant_target = await self.read_target_effect(card)

						if EffectTarget.spell in enchant_target:
							enchants.append(card)
						else:
							normals.append(card)

				# Sorting enchants
				heal_enchants = []   
				damage_enchants = []
				strict_damage_enchants = []
				trap_enchants = [] 
				charm_enchants = []
				for enchant in enchants:
					enchant_types = await self.read_spell_effect(enchant)

					if SpellEffects.modify_card_heal in enchant_types:
						heal_enchants.append(enchant)
					if any(effects in enchant_types for effects in DAMAGE_ENCHANT_EFFECTS):
						damage_enchants.append(enchant)
					if any(effects in enchant_types for effects in STRICT_DAMAGE_ENCHANT_EFFECTS):
						strict_damage_enchants.append(enchant)
					if any(effects in enchant_types for effects in TRAP_ENCHANT_EFFECTS):
						trap_enchants.append(enchant)
					if any(effects in enchant_types for effects in CHARM_ENCHANT_EFFECTS):
						charm_enchants.append(enchant)

				# Finding Highest Damage card
				damagest_card = None
				damagest_aoe = None

				async def highest_damage_card_function():
					nonlocal damagest_card
					damagest_card = await self.highest_damage_card(normals)
				async def highest_damage_aoe_function():
					nonlocal damagest_aoe
					damagest_aoe = await self.highest_damage_aoe(normals)
				# start = time.perf_counter()
				await asyncio.gather(*[highest_damage_card_function(), highest_damage_aoe_function()])
				# end = time.perf_counter()
				# logger.debug(f'highest damage card shit took {end - start} seconds to complete')
				## Find card to cast
				final_cast = None
				card_value = 0

				# for card in normals:
				async def card_shit_function(card):
					nonlocal final_cast
					nonlocal card_value
					# Spell Effects
					effect_types = None
					effect_targets = None
					async def effect_types_function():
						nonlocal effect_types
						effect_types = await self.read_spell_effect(card)
					async def effect_targets_function():
						nonlocal effect_targets
						effect_targets = await self.read_target_effect(card)
					await asyncio.gather(*[effect_targets_function(), effect_types_function()])

					# Heals
					if (any(effects in effect_types for effects in HEALING_EFFECTS)) and (to_heal != None):
						await asyncio.sleep(0.3)
						card_value = 12
						final_cast = card

					# Prisms
					if (is_boss) and (card_value < 11):
						if (SpellEffects.modify_incoming_damage_type in effect_types) and (await self.get_school_template_name(boss) == await self.get_school_template_name(client_member)):
							await asyncio.sleep(0.3)
							card_value = 11
							final_cast = card

					# Damage Positive Charms
					if (SpellEffects.modify_outgoing_damage in effect_types) and (any(effects in effect_targets for effects in FRIENDLY_TARGETS)) and (card_value < 10):
						await asyncio.sleep(0.3)
						card_value = 10
						final_cast = card

					# Positive Wards
					if (SpellEffects.modify_incoming_damage in effect_types) and (any(effects in effect_targets for effects in ENEMY_TARGETS)) and (card_value < 9):
						await asyncio.sleep(0.3)
						card_value = 9
						final_cast = card

					# Damage Auras/Globals
					if (any(effects in effect_types for effects in DAMAGE_AURA_GLOBAL_EFFECTS)) and (any(effects in effect_targets for effects in AURA_GLOBAL_TARGETS)) and (card_value < 8):
						await asyncio.sleep(0.3)
						card_value = 8
						final_cast = card

					# Other Positive Charms
					if (any(effects in effect_types for effects in CHARM_EFFECTS)) and (any(effects in effect_targets for effects in FRIENDLY_TARGETS)) and (card_value < 7):
						await asyncio.sleep(0.3)
						card_value = 7
						final_cast = card

					# Damage AOEs
					if (any(effects in effect_types for effects in DAMAGE_EFFECTS)) and (any(effects in effect_targets for effects in DAMAGE_AOE_TARGETS)) and (card == damagest_aoe) and (card_value < 6):
						await asyncio.sleep(0.3)
						card_value = 6
						final_cast = card

					# Damage spells
					if (any(effects in effect_types for effects in DAMAGE_EFFECTS)) and (any(effects in effect_targets for effects in DAMAGE_TARGETS)) and (card == damagest_card) and (card_value < 5):
						await asyncio.sleep(0.3)
						card_value = 5
						final_cast = card
					
					# Negative Charms
					if (any(effects in effect_types for effects in CHARM_EFFECTS)) and (any(effects in effect_targets for effects in ENEMY_TARGETS)) and (card_value < 4):
						await asyncio.sleep(0.3)
						card_value = 4
						final_cast = card

					# Negative Wards
					if (SpellEffects.modify_incoming_damage in effect_types) and (any(effects in effect_targets for effects in FRIENDLY_TARGETS)) and (card_value < 3):
						await asyncio.sleep(0.3)
						card_value = 3
						final_cast = card

					# Steal Pip
					if (SpellEffects.modify_pips in effect_types) and (any(effects in effect_targets for effects in ENEMY_TARGETS)) and (card_value < 2):
						await asyncio.sleep(0.3)
						card_value = 2
						final_cast = card

					# Other Auras/Globals
					if (any(effects in effect_types for effects in AURA_GLOBAL_EFFECTS)) and (any(effects in effect_targets for effects in AURA_GLOBAL_TARGETS)) and (card_value < 1):
						await asyncio.sleep(0.3)
						card_value = 1
						final_cast = card

				# start = time.perf_counter()
				await asyncio.gather(*[card_shit_function(card) for card in normals])
				# end = time.perf_counter()
				# logger.debug(f"card shit took {end - start} seconds to complete")
				if final_cast:
					final_cast_types = await self.read_spell_effect(final_cast)
					final_cast_targets = await self.read_target_effect(final_cast)

					## Enchanting
					if not await final_cast.is_item_card() and not await final_cast.is_treasure_card() and not await final_cast.is_enchanted():

						# Heals
						return_effects = None
						if (any(effects in final_cast_types for effects in HEALING_EFFECTS)) and heal_enchants:
							logger.debug(f"Client {self.client.title} Enchanting {await final_cast.display_name()} with {await heal_enchants[0].display_name()}")
							await heal_enchants[0].cast(final_cast, sleep_time=0.25)
							return_effects = HEALING_EFFECTS

						# Positive charms
						elif (SpellEffects.modify_outgoing_damage in final_cast_types) and (any(effects in final_cast_targets for effects in FRIENDLY_TARGETS)) and charm_enchants:
							logger.debug(f"Client {self.client.title} Enchanting {await final_cast.display_name()} with {await charm_enchants[0].display_name()}")
							await charm_enchants[0].cast(final_cast, sleep_time=0.25)
							return_effects = [SpellEffects.modify_outgoing_damage]  

						# Positive Wards
						elif (SpellEffects.modify_incoming_damage in final_cast_types) and (any(effects in final_cast_targets for effects in ENEMY_TARGETS)) and trap_enchants:
							logger.debug(f"Client {self.client.title} Enchanting {await final_cast.display_name()} with {await trap_enchants[0].display_name()}")
							await trap_enchants[0].cast(final_cast, sleep_time=0.25)
							return_effects = [SpellEffects.modify_incoming_damage]

						# Damage
						elif (any(effects in final_cast_types for effects in DAMAGE_EFFECTS)) and (any(effects in final_cast_targets for effects in ENEMY_TARGETS)) and damage_enchants:
							logger.debug(f"Client {self.client.title} Enchanting {await final_cast.display_name()} with {await damage_enchants[0].display_name()}")
							await damage_enchants[0].cast(final_cast, sleep_time=0.25)
							return_effects = DAMAGE_EFFECTS

						# Reget new cards
						if return_effects != None:
							enchanted_cards = await self.get_enchanted_spells_by_spell_effect(return_effects)
							if len(enchanted_cards) != 0:
								final_cast = enchanted_cards[0]

					## Targeting
					if EffectTarget.enemy_single in final_cast_targets:
						if is_boss:
							target = boss
						else:
							target = to_kill
						
					elif (EffectTarget.friendly_single in final_cast_targets) and any(effects in final_cast_types for effects in HEALING_EFFECTS) and (to_heal != None):
						target = to_heal

					elif EffectTarget.friendly_single in final_cast_targets:
						target = client_member

					elif any(effects in final_cast_targets for effects in NONE_TARGETS):
						target = None

					# Casting
					if target != None:
						logger.debug(f"Client {self.client.title} Casting {await final_cast.display_name()} at {await target.name()}")
					else:
						logger.debug(f"Client {self.client.title} Casting {await final_cast.display_name()}")
					await final_cast.cast(target, sleep_time=0.25)

				else:
					logger.debug(f"Client {self.client.title} No available spells, passing")
					cards = await self.get_cards()
					enchant_names = ['Strong', 'Giant', 'Monstrous', 'Gargantuan', 'Colossal', 'Epic', 'Aegis', 'Indemnity', 'Primordial', 'Sharpened Blade', 'Potent Trap', 'Daybreaker', 'Nightbringer', 'Radical', 'Keen Eyes', 'Accurate', 'Sniper', 'Unstoppable', 'Extraordinary']
					castable_cards = [c for c in cards if await c.is_castable() and await c.display_name() not in enchant_names]
					while len(castable_cards) > 0:
						await castable_cards[0].discard(sleep_time=0.25)
						await asyncio.sleep(0.25)
						cards = await self.get_cards()
						castable_cards = [c for c in cards if await c.is_castable() and await c.display_name() not in enchant_names]
					await self.pass_button()

				await asyncio.sleep(len(self.clients))
				if await self.client.duel.duel_phase() == DuelPhase.planning:
					pass
				else:
					break
			except:
				logger.error(f"Client {self.client.title} - Invalid spell effect, discarding all castable cards.")
				cards = await self.get_cards()
				enchant_names = ['Strong', 'Giant', 'Monstrous', 'Gargantuan', 'Colossal', 'Epic', 'Aegis', 'Indemnity', 'Primordial', 'Sharpened Blade', 'Potent Trap', 'Daybreaker', 'Nightbringer', 'Radical', 'Keen Eyes', 'Accurate', 'Sniper', 'Unstoppable', 'Extraordinary']
				castable_cards = [c for c in cards if await c.is_castable() and await c.display_name() not in enchant_names]
				while len(castable_cards) > 0:
					await castable_cards[0].discard(sleep_time=0.25)
					await asyncio.sleep(0.25)
					cards = await self.get_cards()
					castable_cards = [c for c in cards if await c.is_castable() and await c.display_name() not in enchant_names]
				await self.pass_button()
				await asyncio.sleep(len(self.clients))
				if await self.client.duel.duel_phase() == DuelPhase.planning:
					pass
				else:
					break
		await self.client.mouse_handler.deactivate_mouseless()
		await asyncio.sleep(0.1)
		return
