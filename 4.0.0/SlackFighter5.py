import asyncio
from email import utils
import wizwalker
from wizwalker.combat import CombatHandler, CombatCard
from typing import Callable, List
from wizwalker import Keycode, utils
from typing import List, Optional, Union
from wizwalker.memory import WindowFlags, Window
from wizwalker.memory.memory_objects.enums import DuelPhase, SpellEffects
from wizwalker.errors import ReadingEnumFailed
from loguru import logger
import time

# Enchants
HIT_ENCHANTS = frozenset(['Strong', 'Giant', 'Monstrous', 'Gargantuan', 'Colossal', 'Epic', 'Keen Eyes', 'Accurate', 'Sniper', 'Unstoppable', 'Extraordinary', 'Solar Surge'])
HEAL_ENCHANTS = frozenset(['Primordial', 'Radical'])
BLADE_ENCHANTS = frozenset(['Sharpened Blade'])
TRAP_ENCHANTS = frozenset(['Potent Trap'])
WARD_ENCHANTS = frozenset(['Bolstered Ward'])
GOLEM_ENCHANT = frozenset(['Golem: Taunt'])

# Auras
HIT_AURAS = frozenset(['Virulence', 'Frenzy', 'Beserk', 'Flawless', 'Infallible', 'Amplify', 'Magnify', 'Vengeance', 'Chastisement', 'Devotion', 'Furnace', 'Galvanic Field', 'Punishment', 'Reliquary', 'Sleet Storm', 'Reinforce', 'Eruption', 'Acrimony', 'Outpouring', 'Apologue', 'Rage', 'Intensify', 'Icewind', 'Recompense', 'Upheaval', 'Quicken'])
DEFENSE_AURAS = frozenset(['Fortify', 'Brace', 'Bulwark', 'Conviction'])
HEAL_AURAS = frozenset(['Cycle of Life', 'Mend', 'Renew', 'Empowerment', 'Adapt'])

# Shields
SELECT_SHIELDS = frozenset(['Bracing Frost', 'Bracing Wind',  'Bracing Breeze', 'Borrowed Time', 'Ancient Wraps', 'Aegis of Artemis', 'Frozen Armor', 'Stun Block', 'Tower Shield', 'Death Shield', 'Life Shield', 'Myth Shield', 'Fire Shield', 'Ice Shield', 'Storm Shield', 'Dream Shield', 'Legend Shield', 'Elemental Shield', 'Spirit Shield', 'Shadow Shield', 'Glacial Shield', 'Volcanic Shield', 'Ether Shield', 'Thermic Shield'])
AOE_SHIELDS = frozenset(['Armory of Artemis I', 'Armory of Artemis', 'Legion Shield', 'Mass Tower Shield'])

# Blades
SELECT_BLADES = frozenset(['Catalyze', 'Fireblade', 'Deathblade', 'Iceblade', 'Stormblade', 'Lifeblade', 'Mythblade', 'Balanceblade', 'Precision', 'Dark Pact', 'Shadowblade', 'Elemental Blade', 'Spirit Blade', 'Aegis Deathblade', 'Aegis Mythblade', 'Aegis Lifeblade', 'Aegis Stormblade', 'Aegis Fireblade', 'Aegis Iceblade', 'Aegis Balanceblade'])
AOE_BLADES = frozenset(['Blind Strike', 'Bladestorm', 'Dragonlance', 'Blade Dance', 'Ion Wind', 'Chromatic Blast'])
SELECT_PIERCE = frozenset(['Deathspear', 'Lifespear', 'Mythspear', 'Firespear', 'Icespear', 'Stormspear', 'Spirit Spear', 'Elemental Spear', 'Balancespear'])
AOE_HEAL_BLADES = frozenset(['Guidance', 'Brilliant Light'])
SELECT_HEAL_BLADES = frozenset(['Guiding Light', 'Precision', 'Guiding Armor'])

# Traps
SELECT_TRAPS = frozenset(['Hex', 'Disarming Trap', 'Curse', 'Spirit Trap', "Elemental Blade", 'Death Trap', 'Life Trap', 'Myth Trap', 'Storm Trap', 'Fire Trap', 'Backdraft', 'Feint', 'Ice Trap'])
AOE_TRAPS = frozenset(['Beastmoon Curse', 'Debilitate', 'Ambush', 'Mass Death Trap', 'Mass Life Trap', 'Mass Feint', 'Mass Myth Trap', 'Mass Fire Trap', 'Mass Ice Trap', 'Mass Storm Trap', 'Mass Hex', 'Malediction'])

# Globals
GLOBALS = frozenset(['Age of Reckoning', 'Astraphobia', 'Balance of Power', 'Balefrost', 'Circle of Thorns', 'Combustion', 'Counterforce', 'Darkwind', 'Deadzone', 'Doom and Gloom', 'Elemental Surge', 'Katabatic Wind', 'Namaste', 'Power Play', 'Saga of Heroes', 'Sanctuary', 'Spiritual Attunement', 'Time of Legend', 'Tide of Battle', 'Wyldfire', 'Elemental Surge', 'Dampen Magic'])

# Hits
SELECT_DOTS = frozenset(['Creeping Death', 'Cindertooth', 'Broiler', 'Bennu Alight', 'Befouling Brew', 'Link', 'Power Link', 'Inferno Salamander', 'Burning Rampage', 'Heck Hound', 'Wrath of Hades', 'Storm Hound', 'Frost Hound', 'Thunderstorm', 'Avenging Fossil', 'Frostbite', 'Spinysaur', 'Lightning Elf', 'Basilisk', 'Poison', 'Skeletal Dragon'])
SELECT_HITS = frozenset(['Cyclonic Swarm', 'Doggone Frog', 'Disarming Spirit', 'Deadly Sting', 'Consume Life', 'Cripping Blow', 'Crystal Shard', 'Curse-Eater', 'Cursed Kitty', 'Contamination', 'Chill Bug', 'Conflagaration', 'Clever Imp', 'Chill Wind', 'Chilling Touch', 'Cheapshot', 'Chaotic Currents', 'Butcher Bat', 'Bull Rush', 'Blue Moon Bird', 'Bluster Blast', 'Bombardier Beetle', 'Blizzard Wind', 'Blitz Beast', 'Blood Boil', 'Bitter Chill', 'Bio-Gnomes', 'Blistering Bolt', 'Blazing Construct', 'Basic Bruiser', 'Bargain of Brass', 'Ballistic Bat', 'Backdrafter', 'Avenging Marid', 'Angelic Vigor', 'Death Scarab', 'Immolate', 'Efreet', 'King Artorius', 'Scion of Fire', "S'more Machine", 'Fire from Above', 'Sun Serpent', 'Brimstone Revenant', 'Hephaestus', 'Krampus', 'Nautilus Unleashed', 'Fire Cat', 'Fire Elf', 'Sunbird', 'Phoenix', 'Naphtha Scarab', 'Elemental Golem', 'Spirit Golem', 'Dream Golem', 'Ether Golem', 'Legend Golem', 'Volcanic Golem', 'Thermic Golem', 'Glacial Golem', 'Helephant', 'Frost Beetle', 'Snow Serpent', 'Evil Snowman', 'Ice Wyvern', 'Thieving Dragon', 'Colossus', 'Angry Snowpig', 'Handsome Fomori', 'Winter Moon', 'Woolly Mammoth', 'Lord of Winter', 'Abominable Weaver', 'Scion of Ice', 'Shatterhorn', 'Frostfeather', 'Imp', 'Leprechaun', 'Seraph', 'Sacred Charge', 'Centaur', 'Infestation', "Nature's Wrath", 'Goat Monk', 'Luminous Weaver', 'Gnomes!', 'Hungry Caterpillar', 'Grrnadier', 'Thunder Snake', 'Lightning Bats', 'Storm Shark', 'Kraken', 'Stormzilla', 'Stormwing', 'Triton', 'Catalan', 'Queen Calypso', 'Catch of the Day', 'Hammer of Thor', 'Wild Bolt', 'Insane Bolt', 'Leviathan', 'Storm Owl', 'Scion of Storm', "Rusalka's Wrath", 'Thunderman', 'Blood Bat', 'Troll', 'Cyclops', 'Minotaur', 'Vermin Virtuoso', 'Gobbler', 'Athena Battle Sight', 'Keeper of the Flame', 'Ninja Pigs', 'Splashsquatch', 'Medusa', 'Celestial Calendar', 'Scion of Myth', "Witch's House Call", 'Tatzlewurm Terror', 'Dark Sprite', 'Ghoul', 'Banshee', 'Vampire', 'Skeletal Pirate', 'Crimson Phantom', 'Wraith', 'Monster Mash', 'Headless Horseman', 'Lord of Night', "Dr. Von's Monster", 'Winged Sorrow', 'Scion of Death', 'Snack Attack', 'Scarab', 'Scorpion', 'Locust Swarm', 'Spectral Blast', 'Hydra', 'Loremaster', 'Ninja Piglets', 'Samoorai', 'Savage Paw', 'Spiritual Tribunal', 'Judgement', 'Vengeful Seraph', 'Chimera', 'Supernova', 'Mana Burn', 'Sabertooth', 'Gaze of Fate', 'Scion of Balance', 'Mockenspiel', 'Beary Surprise', 'Camp Bandit', 'Obsidian Colossus', 'Grim Reader', 'Dark & Stormy', "Barbarian's Saga", 'Quartermane', 'The Bantam', 'The Shadoe', 'Mandar', 'Dog Tracy', 'Buck Gordon', 'Duck Savage', 'Hunting Wyrm', 'Shift Piscean', 'Shift Grendel', 'Shift Rattlebones', 'Shift Greenoak', 'Shift Thornpaw', 'Shift Ogre', 'Shift Dread Paladin', 'Shift Sugar Glider', 'Shift Fire Dwarf', 'Van Der Borst', 'Shift Bunferatu', 'Shift Ghulture', 'Frost Minotaur', 'Deadly Minotaur', 'Lively Minotaur', 'Natural Attack', 'Storm Sweep', 'Cat Scratch', 'Colossal Uppercut', 'Colossus Crunch', 'Cursed Flame', 'Ignite', 'Flame Strike', 'Firestorm', 'Storm Strike', 'Maelstrom', 'Taco Toss', 'Stinky Salute', 'Ice Breaker', 'Ritual Blade', 'Mander Blast', 'Death Ninja Pig', 'Ninja Slice', 'Ninja Slam', 'Thunder Spike', 'Stomp', 'Swipe', 'Wrath of Aquila', 'Wrath of Cronus', 'Wrath of Apollo', 'Wrath of Zeus', 'Wrath of Poseidon', 'Wrath of Ares'])
AOE_DOTS = frozenset(["Death's Champion", "Champion's Blight", 'Scald', 'Wings of Fate', 'Rain of Fire', 'Fire Dragon', 'Reindeer Knight', 'Snow Angel', 'Deer Knight', 'Iron Curse'])
AOE_HITS = frozenset(['Confounding Fiend', 'Deperate Daimyo', 'Cursed Medusa', 'Cursed Medusa I', 'Cursed Medusa II', 'Confounding Fiend I', 'Colossal Scorpion', 'Cold Harvest', 'Bloodletter', 'Arctic Blast', 'Colossafrog', 'Raging Bull', 'Meteor Strike', 'Blizzard', 'Snowball Barrage', 'Frost Giant', "Ratatoskr's Spin", 'Forest Lord', 'Tempest', 'Storm Lord', 'Sirens', 'Glowbug Squall', 'Sound of Musicology', 'Humongofrog', 'Earthquake', 'Orthrus', 'Mystic Colossus', 'Ship of Fools', 'Scarecrow', 'Call of Khrulhu', 'Leafstorm', 'Sandstorm', 'Power Nova', 'Ra', 'Nested Fury', 'Squall Wyvern', "Morganthe's Will", 'Steel Giant', 'Lycian Chimera', 'Lernaean Hydra', 'Lord of Atonement', "Morganthe's Venom", 'Eirkur Axebreaker', 'Wildfire Treant', 'Lava Giant', 'Fiery Giant', 'Lava Lord', 'Lord of Blazes', 'Snowball Strike', "Morganthe's Gaze", 'Tundra Lord', "Morganthe's Angst", 'Squall Wyvern', 'Lord of the Squall', "Morganthe's Ardor", 'Enraged Forest Lord', "Morganthe's Requiem", 'Death Seraph', 'Ominous Scarecrow', 'Bonetree Lord', 'Fable Lord', 'Lord Humongofrog', 'Noble Humongofrog', "Morganthe's Deceit", 'Lord of the Jungle', 'Freeze Ray', "Old One's Endgame", 'Blast Off!', 'Lava Giant', 'Lava Lord', 'Snowball Strike'])
SELECT_SHADOW_HITS = frozenset(['Ultra Shadowstrike', 'Dark Nova', 'Shadowplume'])
AOE_SHADOW_HITS = frozenset(['Dark Fiend', 'Dark Shepherd'])
DIVIDE_HITS = frozenset(["Qismah's Curse", 'Iron Sultan', 'Sand Wurm', 'Snake Charmer', 'Climcaclysm', 'Scorching Scimitars', 'Lamassu'])
SELECT_WAND_HITS = frozenset(['Agony', 'Arctic Sting', 'Assail', 'Blaze', 'Blitz', 'Burst', 'Clash', 'Cold Slash', 'Conniption', 'Crusade', 'Crush', 'Cyclone', 'Dark Blow', 'Death Blow', 'Death Charge', 'Death Chill', 'Death Touch', 'Dread', 'Fire Scorch', 'Fire Slash', 'Fireball', 'Flare', 'Flash', 'Flux', 'Frostblight', 'Heroic Hit', 'Ice Blast', 'Ice Shard', 'Ice Slash', 'Impact', 'Inferno', 'Jolt', 'Justice Slash', 'Life Fury', 'Life Ire', 'Major Agony', 'Major Arctic Sting', 'Major Assail', 'Major Balance Burst', 'Major Blaze', 'Major Blitz', 'Major Burst', 'Major Chill', 'Major Clash', 'Major Conniption', 'Major Crusade', 'Major Crush', 'Major Cyclone', 'Major Dread', 'Major Fire Scorch', 'Major Fireball', 'Major Flare', 'Major Flash', 'Major Flux', 'Major Frostblight', 'Major Heroic Hit', 'Major Ice Blast', 'Major Ice Shard', 'Major Impact', 'Major Inferno', 'Major Jolt', 'Major Life Fury', 'Major Life Ire', 'Major Nova', 'Major Rage', 'Major Revile', 'Major Scorch', 'Major Scourge', 'Major Shadowplume', 'Major Shadowstrike', 'Major Shock', 'Major Snowburst', 'Major Spark', 'Major Strike', 'Major Surge', 'Major Torment', 'Major Vibrato', 'Major Wrath', 'Mana Burn', 'Mega Agony', 'Mega Arctic Sting', 'Mega Assail', 'Mega Blaze', 'Mega Blitz', 'Mega Burst', 'Mega Conniption', 'Mega Cyclone', 'Mega Dark Blow', 'Mega Frostblight', 'Mega Impact', 'Mega Inferno', 'Mega Jolt', 'Mega Nova', 'Mega Rage', 'Mega Shadowstrike', 'Mega Torment', 'Mighty Rage', 'Minor Chill', 'Minor Clash', 'Minor Cold Slash', 'Minor Crusade', 'Minor Crush', 'Minor Dark Blow', 'Minor Death Tap', 'Minor Fire Flare', 'Minor Fire Scorch', 'Minor Fireball', 'Minor Flash', 'Minor Heroic Hit', 'Minor Ice Blast', 'Minor Ice Shard', 'Minor Ice Slash', 'Minor Life Fury', 'Minor Life Ire', 'Minor Nova', 'Minor Shock', 'Minor Spark', 'Minor Strike', 'Minor Surge', 'Minor Wrath', 'Moon Beam', 'Mystic Slash', 'Rage', 'Revile', 'Rolling Thunder Bolt', 'Scorch', 'Shadow Slash', 'Shadowblast', 'Shadowplume', 'Shadowstrike', 'Shock', 'Sky Slash', 'Snowburst', 'Spark', 'Spirit Slash', 'Strike', 'Super Agony', 'Super Arctic Sting', 'Super Assail', 'Super Blaze', 'Super Blitz', 'Super Burst', 'Super Chill', 'Super Clash', 'Super Conniption', 'Super Crusade', 'Super Crush', 'Super Cyclone', 'Super Dark Blow', 'Super Death Tap', 'Super Dread', 'Super Fire Scorch', 'Super Fireball', 'Super Flare', 'Super Flash', 'Super Flux', 'Super Frostblight', 'Super Heroic Hit', 'Super Ice Blast', 'Super Ice Shard', 'Super Impact', 'Super Inferno', 'Super Jolt', 'Super Life Fury', 'Super Life Ire', 'Super Nova', 'Super Rage', 'Super Revile', 'Super Scorch', 'Super Shadowplume', 'Super Shadowstrike', 'Super Shock', 'Super Snowburst', 'Super Spark', 'Super Strike', 'Super Surge', 'Super Torment', 'Super Vibrato', 'Super Wrath', 'Surge', 'Torment', 'Ultra Agony', 'Ultra Arctic Sting', 'Ultra Assail', 'Ultra Blaze', 'Ultra Blitz', 'Ultra Burst', 'Ultra Conniption', 'Ultra Cyclone', 'Ultra Dark', 'Ultra Frostblight', 'Ultra Impact', 'Ultra Inferno', 'Ultra Jolt', 'Ultra Rage', 'Ultra Shadowstrike', 'Ultra Torment', 'Vibrato', 'Waves of Wrath', 'Wrath'])

# Minions
MINIONS = frozenset(['Call of the Pack', 'Test Dummy', 'Mander Minion', 'Nerys', 'Spectral Minion', 'Animate', 'Malduit', 'Fire Elemental', 'Sir Lamorak', 'Ice Guardian', 'Freddo', 'Sprite Guardian', 'Sir Bedevere', 'Troll Minion', 'Cyclops Minion', 'Minotaur Minion', 'Talos', 'Vassanji', 'Water Elemental', 'Mokompo'])
AOE_GOLEM_MINION = frozenset(['Golem Minion'])

# Shadow Creatures
OFFENSE_SHADOW = frozenset(['Shadow Shrike', 'Shadow Trickster'])
DEFENSE_SHADOW = frozenset(['Dark Protector', 'Shadow Sentinel'])
HEAL_SHADOW = frozenset(['Shadow Seraph'])

# Dispels
DISPELS = frozenset(['Quench', 'Melt', 'Dissipate', 'Vaporize', 'Entangle', 'Strangle', 'Unbalance', 'Spirit Defuse', 'Elemental Defuse'])

# Heals
SELECT_HEALS = frozenset(['Charming Pixie', 'Divine Intervention', 'Divine Spark', 'Dryad of Artemis', 'Cauterize', 'Beastmoon Brownie', 'Fairy', 'Dryad', 'Satyr', 'Guardian Spirit', 'Regenerate', 'Scion of Life', 'Minor Blessing', 'Healing Current', 'Sacrifice', 'Helping Hands', 'Availing Hands', "Grendel's Amends", 'Blessing', 'Cleansing Current', 'Gobble'])
AOE_HEALS = frozenset(['Pixie', 'Unicorn', 'Sprite Swarm', 'Pigsie', 'Rebirth', 'Hamadryad', 'Kiss of Death', 'Helping Hands', 'Availing Hands', 'Cat Nap', 'Restoring Hands'])

# Stuns
SELECT_STUNS = frozenset(['Freeze', 'Stun', 'Decelerate'])
AOE_STUNS = frozenset(['Petrify', 'Choke', 'Blinding Light', 'Blinding Freeze', 'Wall of Smoke', 'Shockwave'])

# Detonates
SELECT_DETONATES = frozenset(['Detonate', 'Solomon Crane', 'Dive-Bomber Beetle'])
AOE_DETONATES = frozenset(['Incindiate'])

# Prisms
SELECT_PRISMS = frozenset(['Elemental Prism', 'Spirit Prism', 'Death Prism', 'Life Prism', 'Myth Prism', 'Ice Prism', 'Fire Prism', 'Storm Prism'])
AOE_PRISMS = frozenset(['Mass Elemental Prism', 'Mass Spirit Prism', 'Mass Fire Prism', 'Mass Ice Prism', 'Mass Storm Prism', 'Mass Death Prism', 'Mass Life Prism', 'Mass Myth Prism'])

# Charm Debuffs
AOE_DEBUFFS = frozenset(['Plague', 'Virulent Plague', 'Smokescreen', 'Malediction', 'Mass Infection', 'Muzzle'])
SELECT_DEBUFFS = frozenset(['Weakness', 'Black Mantle', 'Bad Juju', 'Infection', 'Threefold Fever', 'Atrophy', 'Corruption', 'Diversion'])

# Minion Utilities
SELECT_MINION_UTILITIES = frozenset(['Shield Minion', 'Buff Minion', 'Siphon Health', 'Mend Minion', 'Draw Power', 'Dimension Shift', 'Steal Health', 'Sap Health', 'Take Power', 'Draw Health', 'Drain Health', 'Sap Power', 'Benevolent Bat', 'Cast-Iron Aegis', "Charalatan's Deceit", 'Charmed Scales', 'Cinderbird', 'Demoralize'])
SELECT_PACIFIES = frozenset(['Mega Pacify', 'Mega Distract', 'Mega Subdue', 'Mega Soothe', 'Mega Tranquilize', 'Mega Calm'])
AOE_PACIFIES = frozenset(['Pacify', 'Distract', 'Calm', 'Subdue', 'Soothe', 'Tranquilize'])
AOE_TAUNTS = frozenset(['Taunt', 'Mega Taunt', 'Provoke'])

# Polymorphs (based)
AOE_POLYMORPHS = frozenset(['Polymorph Jaguar', 'Polymorph Gobbler', 'Polymorph Beet', 'Polymorph Carrot', 'Polymorph Cat Bandit', 'Polymorph Colossus', 'Polymorph Disparagus', 'Polymorph Draconian', 'Polymorph Elemental', 'Polymorph Icehorn', 'Polymorph Mander', 'Polymorph Hound', 'Polymorph Ninja', 'Polymorph Peas', 'Polymorph Ptera', 'Polymorph Treant', 'Hatch'])

# Spell Type Utilities
SELECT_ENEMY_WARD_UTILITY = frozenset(['Shatter', 'Pierce'])
SELECT_ENEMY_BLADE_UTILITY = frozenset(['Steal Charm, Double Steal Charm', 'Enfeeble', 'Disarm', 'Backstab'])
SELECT_ENEMY_HOT_UTILITY = frozenset(['Snowdrift'])
SELECT_SELF_DOT_UTILITY = frozenset(['Triage', 'Shift'])
AOE_SELF_DOT_UTILITY = frozenset(['Mass Triage', 'Cooldown'])
SELECT_SELF_WEAKNESS_UTILITY = frozenset(['Cleanse Charm', 'Double Cleanse Charm'])
SELECT_SELF_TRAP_UTILITY = frozenset(['Cleanse Ward', 'Double Cleanse Ward'])
AOE_SELF_WEAKNESS_UTILITY = frozenset(['Empower'])
SELECT_ENEMY_MORE_PIPS_UTILITY = frozenset(['Steal Pip', 'Mana Burn'])
SELECT_RESHUFFLE = frozenset(["Reshuffle"]) 

# Roshambo Utilities
ENEMY_WARD_ROSHAMBO = frozenset(['Betrayal', 'Meltdown', "Oni's Forge", "Jinn's Defense"])
ENEMY_BLADE_ROSHAMBO = frozenset(['Wall of Blades', "Oni's Destruction", 'Putrefaction', "Jinn's Larceny"])
ENEMY_HOT_ROSHAMBO = frozenset(['Energy Transfer', "Jinn's Restoration", 'Contagion', "Oni's Morbidity", "Jinn's Fortune"])
SELF_TRAP_ROSHAMBO = frozenset(['Backfire', "Jinn's Reversal", 'Tranquility', "Oni's Naturalism", 'Righting the Scales'])
SELF_WEAKNESS_ROSHAMBO = frozenset(['Glacial Fortress', "Jinn's Vexation", 'Delusion', "Oni's Projection", 'Eye of Vigilance'])
SELF_DOT_ROSHAMBO = frozenset(['Reap the Whirlwind', "Oni's Attrition", 'Meditation', "Jinn's Affliction", "Jinn's Fortune"])
ONI_SHADOW_ROSHAMBO = frozenset(["Oni's Shadow"])

# Gambit Hits
SELF_WARD_ROSHAMBO_GAMBIT = frozenset(['Scion of Ice', 'Doom Oni', 'Phantastic Jinn'])
SELF_BLADE_ROSHAMBO_GAMBIT = frozenset(['Scion of Storm', 'Macabre Jinn', 'Primal Oni'])
ENEMY_TRAP_ROSHAMBO_GAMBIT = frozenset(['Caldera Jinn', 'Everwinter Oni', 'Scion of Myth'])
ENEMY_WEAKNESS_ROSHAMBO_GAMBIT = frozenset(['Iceburn Jinn', 'Turmoil Oni', 'Scion of Death'])
ENEMY_DOT_ROSHAMBO_GAMBIT = frozenset(['Scion of Fire', 'Verdurous Jinn', 'Trickster Oni', 'Duststorm Jinn'])
SELF_HOT_ROSHAMBO_GAMBIT = frozenset(['Infernal Oni', 'Thundering Jinn', 'Scion of Life'])
ENEMY_2_SHADS_ROSHAMBO_GAMBIT = frozenset(['Tribunal Oni'])
ENEMY_11_PIPS_ROSHAMBO_GAMBIT = frozenset(['Scion of Balance'])


# For spells with different spell logics in pvp
pvp_casting_logic_dict = {
	'Scion of Balance': 'Enemy Select Enemy 11 Pips Roshambo Hit',
	"Scion of Fire": 'Enemy Select Enemy DOT Roshambo Hit',
	"Scion of Death": 'Enemy Select Enemy Weakness Roshambo Hit',
	"Scion of Life": 'Enemy Select Self HOT Roshambo Hit',
	"Scion of Myth": 'Enemy Select Enemy Trap Roshambo Hit',
	"Scion of Ice": 'Enemy Select Self Ward Roshambo Hit',
	"Scion of Storm": 'Enemy Select Self Blade Roshambo Hit'
}

# For spells that cannot be enchanted only in pvp
pvp_no_enchant_logic_list = [
	"Abominable Weaver",
	"Barbarian's Saga",
	"Blast Off!",
	"Call of Khrulhu",
	"Climaclysm",
	"Dark & Stormy",
	"Fire from Above",
	"Freeze Ray",
	"Gaze of Fate",
	"Glowbug Squall",
	"Grim Reader",
	"Grrnadier",
	"Hungry Caterpillar",
	"Iron Sultan",
	"Lamassu",
	"Lord of the Jungle",
	"Mockenspiel",
	"Mystic Colossus",
	"Nested Fury",
	"Old One's Endgame",
	"Qismah's Curse",
	"Raging Bull",
	"Rusalka's Wrath",
	"S'more Machine",
	"Sand Wurm",
	"Scorching Scimitars",
	"Shatterhorn",
	"Snack Attack",
	"Snake Charmer",
	"Snowball Barrage",
	"Sound of Musicology",
	"Tatzlewurm Terror",
	"Winged Sorrow",
	"Wings of Fate",
	"Witch's House Call"
]

# Assigns a casting logic to a spell's origin set
casting_logic_dict = {
	SELECT_RESHUFFLE: 'Ally Select Reshuffle',
	HIT_ENCHANTS: 'Hit Enchant',
	HEAL_ENCHANTS: 'Heal Enchant',
	BLADE_ENCHANTS: 'Blade Enchant',
	TRAP_ENCHANTS: 'Trap Enchant',
	WARD_ENCHANTS: 'Ward Enchant',
	HIT_AURAS: 'AOE Hit Aura',
	DEFENSE_AURAS: 'AOE Defense Aura',
	HEAL_AURAS: 'AOE Heal Aura',
	SELECT_SHIELDS: 'Ally Select Shield',
	AOE_SHIELDS: 'AOE Shield',
	SELECT_BLADES: 'Ally Select Blade',
	AOE_BLADES: 'AOE Blade',
	SELECT_PIERCE: 'Ally Select Pierce',
	SELECT_TRAPS: 'Enemy Select Trap',
	AOE_TRAPS: 'AOE Trap',
	GLOBALS: 'AOE Global',
	SELECT_DOTS: 'Enemy Select DOT',
	SELECT_HITS: 'Enemy Select Hit',
	AOE_DOTS: 'AOE DOT',
	AOE_HITS: 'AOE Hit',
	MINIONS: 'AOE Minion',
	OFFENSE_SHADOW: 'AOE Offensive Shadow Creature',
	DEFENSE_SHADOW: 'AOE Defensive Shadow Creature',
	HEAL_SHADOW: 'AOE Heal Shadow Creature',
	DISPELS: 'Enemy Select Dispel',
	SELECT_HEALS: 'Ally Select Heal',
	AOE_HEALS: 'AOE Heal',
	SELECT_STUNS: 'Enemy Select Stun',
	AOE_STUNS: 'AOE Stun',
	SELECT_DETONATES: 'Enemy Select Detonate',
	SELECT_PRISMS: 'Enemy Select Prism',
	AOE_PRISMS: 'AOE Prism',
	DIVIDE_HITS: 'Enemy Select Hit Divide',
	AOE_DEBUFFS: 'AOE Debuff',
	SELECT_DEBUFFS: 'Enemy Select Debuff',
	AOE_SHADOW_HITS: 'AOE Hit Shadow',
	SELECT_SHADOW_HITS: 'Enemy Select Hit Shadow',
	SELECT_MINION_UTILITIES: 'Ally Select Minion Utility',
	SELECT_PACIFIES: 'Ally Select Pacify',
	AOE_PACIFIES: 'AOE Pacify',
	AOE_TAUNTS: 'AOE Taunt',
	AOE_DETONATES: 'AOE Detonate',
	AOE_POLYMORPHS: 'AOE Polymorphs',
	AOE_HEAL_BLADES: 'AOE Heal Blade',
	SELECT_HEAL_BLADES: 'Ally Select Heal Blade',
	GOLEM_ENCHANT: 'Golem Enchant',
	AOE_GOLEM_MINION: 'AOE Golem Minion',
	SELECT_WAND_HITS: 'Enemy Select Wand Hit',
	SELECT_SELF_WEAKNESS_UTILITY: 'Ally Select Weakness Counter Utility',
	AOE_SELF_WEAKNESS_UTILITY: 'AOE Weakness Counter Utility',
	SELECT_SELF_TRAP_UTILITY: 'Ally Select Trap Counter Utility',
	SELECT_ENEMY_WARD_UTILITY: 'Enemy Select Ward Counter Utility',
	SELECT_ENEMY_BLADE_UTILITY: 'Enemy Select Blade Counter Utility',
	SELECT_ENEMY_HOT_UTILITY: 'Enemy Select HOT Counter Utility',
	SELECT_SELF_DOT_UTILITY: 'Ally Select DOT Counter Utility',
	AOE_SELF_DOT_UTILITY: 'AOE DOT Counter Utility',
	SELECT_ENEMY_MORE_PIPS_UTILITY: 'Enemy Select More Pips Counter Utilty',
	SELF_WEAKNESS_ROSHAMBO: 'Enemy Select Weakness Roshambo',
	ENEMY_WARD_ROSHAMBO: 'Enemy Select Ward Roshambo',
	ENEMY_BLADE_ROSHAMBO: 'Enemy Select Blade Roshambo',
	SELF_TRAP_ROSHAMBO: 'Enemy Select Trap Roshambo',
	ENEMY_HOT_ROSHAMBO: 'Enemy Select HOT Roshambo',
	SELF_DOT_ROSHAMBO: 'Enemy Select DOT Roshambo',
	SELF_WARD_ROSHAMBO_GAMBIT: 'Enemy Select Self Ward Roshambo Hit',
	SELF_BLADE_ROSHAMBO_GAMBIT: 'Enemy Select Self Blade Roshambo Hit',
	ENEMY_TRAP_ROSHAMBO_GAMBIT: 'Enemy Select Enemy Trap Roshambo Hit',
	ENEMY_WEAKNESS_ROSHAMBO_GAMBIT: 'Enemy Select Enemy Weakness Roshambo Hit',
	ENEMY_DOT_ROSHAMBO_GAMBIT: 'Enemy Select Enemy DOT Roshambo Hit',
	SELF_HOT_ROSHAMBO_GAMBIT: 'Enemy Select Self HOT Roshambo Hit',
	ENEMY_2_SHADS_ROSHAMBO_GAMBIT: 'Enemy Select Enemy 2 Shads Roshambo Hit',
	ENEMY_11_PIPS_ROSHAMBO_GAMBIT: 'Enemy Select Enemy 11 Pips Roshambo Hit',
	ONI_SHADOW_ROSHAMBO: 'Enemy Select Oni Shadow Roshambo'
}

# Assigns enchanting logic to enchantable spells based on their origin set
enchant_logic_dict = {
	DIVIDE_HITS: str(casting_logic_dict[HIT_ENCHANTS]),
	SELECT_DOTS: str(casting_logic_dict[HIT_ENCHANTS]),
	SELECT_HITS: str(casting_logic_dict[HIT_ENCHANTS]),
	AOE_DOTS: str(casting_logic_dict[HIT_ENCHANTS]),
	AOE_HITS: str(casting_logic_dict[HIT_ENCHANTS]),
	SELECT_HEALS: str(casting_logic_dict[HEAL_ENCHANTS]),
	AOE_HEALS: str(casting_logic_dict[HEAL_ENCHANTS]),
	SELECT_BLADES: str(casting_logic_dict[BLADE_ENCHANTS]),
	AOE_BLADES: str(casting_logic_dict[BLADE_ENCHANTS]),
	SELECT_TRAPS: str(casting_logic_dict[TRAP_ENCHANTS]),
	AOE_TRAPS: str(casting_logic_dict[TRAP_ENCHANTS]),
	SELF_WARD_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	SELF_BLADE_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	ENEMY_TRAP_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	ENEMY_WEAKNESS_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	ENEMY_DOT_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	SELF_HOT_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	ENEMY_2_SHADS_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	ENEMY_11_PIPS_ROSHAMBO_GAMBIT: str(casting_logic_dict[HIT_ENCHANTS]),
	AOE_GOLEM_MINION: str(casting_logic_dict[GOLEM_ENCHANT]),
	SELECT_SHIELDS: str(casting_logic_dict[WARD_ENCHANTS]),
	AOE_SHIELDS: str(casting_logic_dict[WARD_ENCHANTS])
}

# List of all valid spell names
master_list = list(casting_logic_dict.keys())

# For converting stat indices to school IDs and vice versa
school_ids = {0: 2343174, 1: 72777, 2: 83375795, 3: 2448141, 4: 2330892, 5: 78318724, 6: 1027491821, 7: 2625203, 8: 78483, 9: 2504141, 10: 663550619, 11: 1429009101, 12: 1488274711, 13: 1760873841, 14: 806477568, 15: 931528087}
school_list_ids = {index: i for i, index in school_ids.items()}
school_id_list = list(school_ids.values())

# define the master hitting strategy
master_strategy = ['AOE Golem Minion', 'Ally Select Blade', 'Enemy Select Trap', 'AOE Minion', 'AOE Global', 'AOE Blade', 'AOE Trap', 'AOE Hit Aura', 'AOE Offensive Shadow Creature', 'AOE DOT', 'AOE Hit', 'Enemy Select DOT', 'Enemy Select Hit', 'Enemy Select Hit Divide', 'AOE Polymorph']
mob_strategy = ['Ally Select Blade', 'AOE DOT', 'AOE Hit', 'Enemy Select DOT', 'Enemy Select Hit', 'Enemy Select Hit Divide', 'AOE Hit Aura', 'AOE Trap', 'AOE Global', 'AOE Blade', 'Enemy Select Trap','AOE Golem Minion' ,'AOE Minion', 'AOE Offensive Shadow Creature', 'AOE Polymorph']
pvp_strategy = ['AOE Golem Minion', 'Ally Select Shield', 'Ally Select Weakness Counter Utility', 'AOE Weakness Counter Utility', 'AOE Defense Aura', 'Enemy Select Trap', 'AOE Minion', 'AOE Global', 'AOE Hit Aura', 'Ally Select Blade', 'AOE Offensive Shadow Creature', 'AOE DOT', 'AOE Hit', 'Enemy Select DOT', 'Enemy Select Hit', 'Enemy Select Hit Divide']

# Basic types
heal_types = ['AOE Heal Blade', 'Ally Select Heal Blade', 'AOE Heal Shadow Creature', 'AOE Heal', 'Ally Select Heal']
reshuffle_types = ['Ally Select Reshuffle']
defensive_types = ['AOE Defense Aura', 'AOE Defensive Shadow Creature', 'AOE Shield', 'Enemy Select Debuff', 'AOE Debuff', 'AOE Stun', 'Enemy Select Stun', 'Ally Select Shield']
prism_types = ['AOE Prism', 'Enemy Select Prism']
minion_utility_types = ['Ally Select Minion Utility', 'Ally Select Pacify', 'AOE Pacify', 'AOE Taunt']

# Utilities for negative types
weakness_counter_types = ['Ally Select Weakness Counter Utility', 'AOE Weakness Counter Utility', 'Enemy Select Wand Hit']
weakness_roshambo_types = ['Enemy Select Weakness Roshambo']
weakness_roshambo_gambit_types = ['Enemy Select Enemy Weakness Roshambo Hit']
trap_counter_types = ['Ally Select Trap Counter Utility']
trap_roshambo_types = ['Enemy Select Trap Roshambo']
trap_roshambo_gambit_types = ['Enemy Select Enemy Trap Roshambo Hit']
dot_counter_types = ['Ally Select DOT Counter Utility', 'AOE DOT Counter Utility']
dot_roshambo_types = ['Enemy Select DOT Roshambo']
dot_roshambo_gambit_types = ['Enemy Select Enemy DOT Roshambo Hit']

# Utilities for positive types
blade_counter_types = ['Enemy Select Blade Counter Utility']
blade_roshambo_types = ['Enemy Select Blade Roshambo']
blade_roshambo_gambit_types = ['Enemy Select Self Blade Roshambo Hit']
ward_counter_types = ['Enemy Select Ward Counter Utility']
ward_roshambo_types = ['Enemy Select Ward Roshambo']
ward_roshambo_gambit_types = ['Enemy Select Self Ward Roshambo Hit']
hot_counter_types = ['Enemy Select HOT Counter Utility']
hot_roshambo_types = ['Enemy Select HOT Roshambo']
hot_roshambo_gambit_types = ['Enemy Select Self HOT Roshambo Hit']

# Utilities for pip conditions (most of this will take a while to implement)
more_pips_counter_types = ['Enemy Select More Pips Counter Utilty']
two_shad_roshambo_gambit_types = ['Enemy Select Enemy 2 Shads Roshambo Hit']
eleven_pips_roshambo_gambit_types = ['Enemy Select Enemy 11 Pips Roshambo Hit']
oni_shadow_roshambo_types = ['Enemy Select Oni Shadow Roshambo']


# Spell Types each school has no utility counter for
cannot_counter_school_types = {
	2343174: ['HOT', 'Enemy Select Debuff', 'AOE Debuff', 'Enemy Select DOT', 'AOE DOT'],
	72777: ['Enemy Select DOT', 'AOE DOT', 'Enemy Select Trap', 'AOE Trap'],
	8337579: ['Ally Select Shield', 'AOE Shield', 'Enemy Select Trap', 'AOE Trap'],
	78318724: ['Ally Select Shield', 'AOE Shield', 'Enemy Select Trap', 'AOE Trap', 'Enemy Select DOT', 'AOE DOT'],
	2330892: ['Ally Select Shield', 'AOE Shield', 'Ally Select Blade', 'AOE Blade', 'Enemy Select Debuff', 'AOE Debuff'],
	2448141: ['Ally Select Blade', 'AOE Blade'],
	1027491821: []
}

# Spell Types each school's gambits buff off of, excluding types that are bad to spam in pvp
gambit_school_types = {
	2343174: ['Enemy Select Trap', 'AOE Trap', 'Enemy Select DOT', 'AOE DOT'],
	72777: ['Enemy Select Trap', 'AOE Trap', 'Ally Select Shield', 'AOE Shield', 'Enemy Select Debuff', 'AOE Debuff'],
	8337579: ['Enemy Select Debuff', 'AOE Debuff', 'Ally Select Blade', 'AOE Blade'],
	78318724: ['Enemy Select Debuff', 'AOE Debuff', 'Ally Select Blade', 'AOE Blade', 'Ally Select Shield', 'AOE Shield'],
	2330892: ['Enemy Select DOT', 'AOE DOT', 'Ally Select Blade', 'AOE Blade'],
	2448141: ['Enemy Select Trap', 'AOE Trap', 'Ally Select Shield', 'AOE Shield', 'Enemy Select DOT', 'AOE DOT'],
	1027491821: []
}


# Lists of SpellEffects that align to a specific spell type
charm_effect_types = [
	SpellEffects.modify_outgoing_damage,
	SpellEffects.modify_outgoing_damage_flat,
	SpellEffects.modify_outgoing_heal,
	SpellEffects.modify_outgoing_heal_flat,
	SpellEffects.modify_outgoing_damage_type,
	SpellEffects.modify_outgoing_armor_piercing
	]

ward_effect_types = [
	SpellEffects.modify_incoming_damage,
	SpellEffects.modify_incoming_damage_flat,
	SpellEffects.maximum_incoming_damage,
	SpellEffects.modify_incoming_heal,
	SpellEffects.modify_incoming_heal_flat,
	SpellEffects.modify_incoming_damage_type,
	SpellEffects.modify_incoming_armor_piercing
	]


class SlackFighter(CombatHandler):
	def __init__(self, client):
		self.client = client

	async def new_get_cards(self) -> List[CombatCard]:
			"""
			List of active CombatCards
			"""
			ncounter = 0
			spell_checkbox_windows = await self._get_card_windows()

			for spell_checkbox in spell_checkbox_windows[::-1]:
				if ncounter > 3:
					break
				elif not WindowFlags.visible in await spell_checkbox.flags():
					await asyncio.sleep(0.045)
					ncounter = ncounter + 1
					
			cards = []
			# cards are ordered right to left so we need to flip them
			for spell_checkbox in spell_checkbox_windows[::-1]:
				if WindowFlags.visible in await spell_checkbox.flags():
					card = CombatCard(self, spell_checkbox)
					cards.append(card)

			return cards
	CombatHandler.get_cards = new_get_cards

	async def new_cast(
			self,
			target: Union["CombatCard", "wizwalker.combat.CombatMember", None],
			*,
			sleep_time: Optional[float] = 1.0,
			debug_paint: bool = False,
		):
			"""
			Cast this Card on another Card; a Member or with no target
			Args:
				target: Card, Member, or None if there is no target
				sleep_time: How long to sleep after enchants and between multicasts or None for no sleep
				debug_paint: If the card should be highlighted before clicking
			"""
			if isinstance(target, CombatCard):
				cards_len_before = len(await self.combat_handler.get_cards())

				await self.combat_handler.client.mouse_handler.click_window(
					self._spell_window
				)

				await asyncio.sleep(sleep_time)

				await self.combat_handler.client.mouse_handler.set_mouse_position_to_window(
					target._spell_window
				)

				await asyncio.sleep(sleep_time)

				if debug_paint:
					await target._spell_window.debug_paint()

				await self.combat_handler.client.mouse_handler.click_window(
					target._spell_window
				)

				# wait until card number goes down
				while len(await self.combat_handler.get_cards()) > cards_len_before:
					await asyncio.sleep(0.1)

				# wiz can't keep up with how fast we can cast
				if sleep_time is not None:
					await asyncio.sleep(sleep_time)

			elif target is None:
				await self.combat_handler.client.mouse_handler.click_window(
					self._spell_window
				)
				# we don't need to sleep because nothing will be casted after

			else:
				await self.combat_handler.client.mouse_handler.click_window(
					self._spell_window
				)

				# see above
				if sleep_time is not None:
					await asyncio.sleep(sleep_time)

				await self.combat_handler.client.mouse_handler.click_window(
					await target.get_name_text_window()
				)

	CombatCard.cast = new_cast

	async def new_wait_for_non_error(coro, sleep_time: float = 0.5):
		"""
		Wait for a coro to not error

		Args:
			coro: Coro to wait for
			sleep_time: Time between calls
		"""
		while True:
			# noinspection PyBroadException
			try:
				now = await coro()
				return now

			except Exception as e:
				print(e)
				await asyncio.sleep(sleep_time)

	utils.wait_for_non_error = new_wait_for_non_error
	@logger.catch()
	async def is_fighting(self):
		check = await self.get_members()
		if len(check): 
			return True
		else:
			return False

	@logger.catch()
	async def wait_for_next_round(self, current_round: int, sleep_time: float = 0.5):
		"""
		Wait for the round number to change
		"""
		# can't use wait_for_value bc of the special in_combat condition
		# so we don't get stuck waiting if combat ends
		while await self.is_fighting():
			new_round_number = await self.round_number()
			if new_round_number > current_round:
				return
			await asyncio.sleep(sleep_time)

	@logger.catch()
	async def wait_for_combat(self, sleep_time: float = 0.5):
		"""
		Wait until in combat
		"""
		await utils.wait_for_value(self.is_fighting, True, sleep_time)
		await self.handle_combat()


	@logger.catch()
	async def handle_combat(self):
		"""Handles an entire combat interaction"""
		self.cards = []
		self.card_names = {}
		self.spell_logic = {}
		self.enchant_logic = {}
		self._spell_check_boxes = None
		self.prev_hit_types = []
		while await self.is_fighting():
			await self.wait_for_planning_phase()
			round_number = await self.round_number()
			# TODO: handle this taking longer than planning timer time
			try:
				await self.client.mouse_handler.activate_mouseless()
			except:
				await asyncio.sleep(0.1)
			start = time.perf_counter()
			self.cards = await self.get_cards()
			if self.cards:
				await self.assign_card_names()
				await self.discard_unsupported()
				await self.assign_spell_logic()
				await self.enchant_all()
				await self.discard_duplicate_types()
				await self.get_tc()
				await self.handle_round()
			end = time.perf_counter()
			logger.debug(f'Turn logic took {end - start} seconds')
			try:
				await self.client.mouse_handler.deactivate_mouseless()
			except:
				await asyncio.sleep(0.01)
			await self.wait_for_next_round(round_number)


	@logger.catch()
	async def assign_card_names(self):
		"""Assigns the name for each card in a dict to avoid over reading"""
		self.card_names = {}
		for c in self.cards:
			if c not in self.card_names:
				self.card_names[c] = await c.display_name()


	@logger.catch()
	async def discard_unsupported(self):
		"""Discards all spells not in the master spell list"""
		discarded = True
		while discarded:
			discarded = False
			for c in self.cards.copy():
				if all([self.card_names[c] not in s for s in master_list]):
					logger.debug(f"Client {self.client.title} - Discarding {self.card_names[c]}")
					await c.discard(sleep_time=0.1)
					self.cards = await self.get_cards()
					await self.assign_card_names()
					discarded = True
					break


	@logger.catch()
	async def assign_spell_logic(self):
		"""Assigns spell logic string and enchanting logic strings to all spells """
		self.spell_logic = {}
		self.enchant_logic = {}
		for c in self.cards:
			for s in master_list:
				if self.card_names[c] in s:
					self.spell_logic[c] = casting_logic_dict[s]
					if s in enchant_logic_dict:
						self.enchant_logic[c] = enchant_logic_dict[s]


	@logger.catch()
	async def enchant_all(self):
		"""Enchants all compatible cards with any compatible enchants"""
		enchanted = True
		while enchanted:
			enchanted = False
			enchants = []
			enchantable_cards = []
			for c in self.cards:
				if 'Enchant' in self.spell_logic[c]:
					enchants.append(c)
				else:
					if c not in self.enchant_logic or await c.is_enchanted() or await c.is_item_card() or await c.is_treasure_card():
						pass
					else:
						enchantable_cards.append(c)
					
			for e in enchants.copy():
				for c in enchantable_cards.copy():
					if self.spell_logic[e] == self.enchant_logic[c]:
						logger.debug(f"Client {self.client.title} - Enchanting {self.card_names[c]} with {self.card_names[e]}")
						await e.cast(c, sleep_time=0.25)
						self.cards = await self.get_cards()
						await self.assign_card_names()
						await self.assign_spell_logic()
						enchanted = True
						break
				if enchanted:
					break


	@logger.catch()
	async def discard_duplicate_types(self, iterations: int = 1):
		"""Discards duplicate spell types in hand"""
		for i in range(iterations):
			discarded = True
			prev_checked_logics = []
			while discarded:
				discarded = False
				card_list = self.cards.copy()
				card_list.reverse()
				for c in card_list:
					if self.spell_logic[c] not in prev_checked_logics:
						prev_checked_logics.append(self.spell_logic[c])
						if len([s for s in list(self.spell_logic.values()) if s == self.spell_logic[c]]) > 2:
							logger.debug(f"Client {self.client.title} - Discarding {self.card_names[c]}")
							await c.discard(sleep_time=0.1)
							self.cards = await self.get_cards()
							await self.assign_card_names()
							await self.assign_spell_logic()
							discarded = True
							break


	@logger.catch()
	async def get_window_from_path(self, root_window: Window, name_path):
		async def _recurse_follow_path(window, path):
			if len(path) == 0:
				return window

			for child in await window.children():
				if await child.name() == path[0]:
					found_window = await _recurse_follow_path(child, path[1:])
					if not found_window is False:
						return found_window

			return False

		return await _recurse_follow_path(root_window, name_path)


	@logger.catch()
	async def get_tc(self):
		draw_path = ["WorldView","PlanningPhase","Alignment","PlanningPhaseSubWindow","SpellSelection","ActionButtons","Draw"]
		num_cards = 7 - len(self.cards) # changed from int
		if num_cards > 1:
			num_cards = int(num_cards/2)
		if num_cards > 0:
			draw_button = await self.get_window_from_path(self.client.root_window,draw_path)
			for i in range(num_cards):
				await self.client.mouse_handler.click_window(draw_button)
			await asyncio.sleep(0.25)
			self.cards = await self.get_cards()
			await self.assign_card_names()
			await self.assign_spell_logic()
			await self.enchant_all()


	@logger.catch()
	async def handle_round(self):
		"""Uses strategy lists and conditional strategies to decide on the best spell to cast, then casts it."""


		# Assign client-specific stats and member
		members = await self.get_members()
		client_member = None
		member_participants = {}
		for m in members:
			if await m.is_client():
				client_member = m
			member_participants[m] = await m.get_participant()
		client_participant = await client_member.get_participant()
		client_school_id = await client_participant.primary_magic_school_id()
		client_team_id = await client_participant.team_id()


		# Assign lists of ally members and enemy members
		allies = []
		mobs = []
		for member in members:
			member_id = await member_participants[member].team_id()
			if member_id == client_team_id:
				allies.append(member)
			else:
				mobs.append(member)
		
		# assign combat member stat dictionaries and such
		member_stats = {}
		member_resistances = {}
		member_damages = {}
		member_hanging_effects = {}
		for m in members:
			member_stats[m] = await m.get_stats()
			m_damages = await member_stats[m].dmg_bonus_percent()
			m_universal_damage = await member_stats[m].dmg_bonus_percent_all()
			member_damages[m] = [r + m_universal_damage for r in m_damages]
			m_resistances = await member_stats[m].dmg_reduce_percent()
			m_universal_resistance = await member_stats[m].dmg_reduce_percent_all()
			member_resistances[m] = [r + m_universal_resistance for r in m_resistances]
			member_hanging_effects[m] = await member_participants[m].hanging_effects()


		# get a list of bosses, and assigns a strategy
		# TODO: PVP detection, possibly beastmoon detection. Right now this only does boss and mob only fights.
		in_pvp = False
		bosses = [m for m in mobs if await m.is_boss()]
		strategy = None
		if bosses:
			strategy = master_strategy.copy()
		elif all([await m.is_monster() for m in mobs]):
			strategy = mob_strategy.copy()
		else:
			in_pvp = True
			strategy = pvp_strategy.copy()
		clean_strategy = strategy.copy()


		# de-prioritize any spell types that were previously casted, avoids spamming the same spell type. Playstyle modifications bypass this.
		for p in self.prev_hit_types:
			if p in strategy:
				strategy.remove(p)
			strategy.append(p)


		# assign pvp-only spell logic modifications, and delete enchant logic from spells that cannot be enchanted in only pvp
		if in_pvp:
			for c in self.cards:
				if self.card_names[c] in pvp_casting_logic_dict:
					self.spell_logic[c] = pvp_casting_logic_dict[self.card_names[c]]
				if self.card_names[c] in pvp_no_enchant_logic_list:
					del self.enchant_logic[c]


		# Conditional playstyle modifications. Allows for changing playstyle based on conditions like healing, enemy schools, and hanging effects (not implemented)
		# Priority types is the list of spell types it inserts at the front of the list, the selected ally is the ally that these spells will be used on.
		priority_types = []
		selected_ally = None
		selected_enemy = None


		# Healing logic
		player_members = [a for a in allies if await a.is_player() == True]
		health_percentages = {}
		for a in player_members:
			health_percentages[a] = float(await a.health()) / float(await a.max_health())
		# chooses ally with lowest health percent
		highest_priority_ally = min(health_percentages, key= lambda a: health_percentages[a])
		# only prioritizes healing if below the threshold float (0.51 by default)
		if health_percentages[highest_priority_ally] < 0.51:
			selected_ally = highest_priority_ally
			priority_types += heal_types

		if len([c for c in self.cards if self.card_names[c] == "Reshuffle"]) > len([c for c in self.cards if not self.card_names[c] == "Reshuffle" and not await c.is_treasure_card()]) or [a for a in heal_types if a in priority_types] and not [c for c in self.cards if self.card_names[c] in AOE_HEALS and SELECT_HEALS and SELECT_SHIELDS] and len([self.cards]) < 5:
			selected_ally = client_member
			priority_types += reshuffle_types


		# Self - Charm (Positive/Negative) counter/roshambo logic
		self_charms = [e for e in member_hanging_effects[client_member] if await e.effect_type() in charm_effect_types]
		if self_charms and (selected_ally == client_member or not selected_ally):
			self_weaknesses = [c for c in self_charms if await c.effect_param() <= 0]
			self_blades = [c for c in self_charms if c not in self_weaknesses]
			if self_weaknesses:
				priority_types += weakness_counter_types
				if len(self_weaknesses) >= 2:
					priority_types += weakness_roshambo_types
			if len(self_blades) >= 4:
				priority_types += blade_roshambo_gambit_types


		# Self - Ward (Positive/Negative) counter/roshambo logic
		self_wards = [e for e in member_hanging_effects[client_member] if await e.effect_type() in ward_effect_types]
		if self_wards and (selected_ally == client_member or not selected_ally):
			self_traps = [c for c in self_wards if await c.effect_param() > 0]
			self_shields = [c for c in self_wards if c not in self_traps]
			if self_traps:
				priority_types += trap_counter_types
				if len(self_traps) >= 2:
					priority_types += trap_roshambo_types
			if len(self_shields) >= 4:
				priority_types += ward_roshambo_gambit_types


		# Self - DOT counter/roshambo logic
		self_dots = [e for e in member_hanging_effects[client_member] if await e.effect_type() == SpellEffects.damage_over_time]
		if self_dots:
			priority_types += dot_roshambo_types
			priority_types += dot_counter_types


		# Self - HOT roshambo gambit logic
		self_hots = [e for e in member_hanging_effects[client_member] if await e.effect_type() == SpellEffects.heal_over_time]
		if len(self_hots) >= 2:
			priority_types += hot_roshambo_gambit_types


		# Defensive logic, works same as healing but with diff spells and diff threshold
		if health_percentages[highest_priority_ally] < 0.61 and not in_pvp:
			selected_ally = highest_priority_ally
			priority_types += defensive_types


		# Enemy Selection, if not done via playstyle mods already
		mob_healths = {}
		for m in mobs:
			mob_healths[m] = await m.health()
		if not selected_enemy:
			selected_enemy = max(mob_healths, key = lambda h: mob_healths[h])


		# Get selected enemy's masteries
		selected_enemy_masteries = []
		selected_enemy_school_id = await member_participants[selected_enemy].primary_magic_school_id()
		selected_enemy_masteries.append(selected_enemy_school_id)
		if await member_stats[selected_enemy].fire_mastery():
			selected_enemy_masteries.append(2343174)
		elif await member_stats[selected_enemy].ice_mastery():
			selected_enemy_masteries.append(72777)
		elif await member_stats[selected_enemy].storm_mastery():
			selected_enemy_masteries.append(83375795)
		elif await member_stats[selected_enemy].death_mastery():
			selected_enemy_masteries.append(78318724)
		elif await member_stats[selected_enemy].life_mastery():
			selected_enemy_masteries.append(2330892)
		elif await member_stats[selected_enemy].myth_mastery():
			selected_enemy_masteries.append(2448141)
		elif await member_stats[selected_enemy].balance_mastery():
			selected_enemy_masteries.append(1027491821)


		# PVP Spelltype spam logic
		if in_pvp:
			self_gambit_types = gambit_school_types[client_school_id]
			school_non_counter_types = cannot_counter_school_types[selected_enemy_school_id]
			mastery_non_counter_types = cannot_counter_school_types[selected_enemy_masteries[0]]
			enemy_non_counter_types = [s for s in school_non_counter_types if s in mastery_non_counter_types]
			spammable_types = [s for s in self_gambit_types if s in enemy_non_counter_types]
			priority_types += spammable_types





		# Prism logic
		if not [e for e in member_hanging_effects[selected_enemy] if await e.effect_type() == SpellEffects.modify_incoming_damage_type]:
			if [e for e in member_hanging_effects[selected_enemy] if await e.damage_type() == client_school_id and await e.effect_type() == SpellEffects.modify_incoming_damage]:
				priority_types += prism_types
			else:
				selected_enemy_resistances = member_resistances[selected_enemy]
				max_enemy_resistance = max(selected_enemy_resistances)
				selected_enemy_resistances_ids = {i: r for i, r in zip(school_id_list, selected_enemy_resistances)}
				if max_enemy_resistance > 0.35:
					if max_enemy_resistance - selected_enemy_resistances_ids[client_school_id] < 0.1:
						priority_types += prism_types


		# Enemy - Charm (Positive/Negative) counter/roshambo logic
		enemy_charms = [e for e in member_hanging_effects[selected_enemy] if await e.effect_type() in charm_effect_types]
		if enemy_charms:
			enemy_weaknesses = [c for c in enemy_charms if await c.effect_param() <= 0]
			enemy_blades = [c for c in enemy_charms if c not in enemy_weaknesses]
			if enemy_blades:
				priority_types += blade_counter_types
				if len(enemy_blades) >= 2:
					priority_types += blade_roshambo_types
			if len(enemy_weaknesses) >= 4:
				priority_types += weakness_roshambo_gambit_types


		# Enemy - Ward (Positive/Negative) counter/roshambo logic
		enemy_wards = [e for e in member_hanging_effects[selected_enemy] if await e.effect_type() in ward_effect_types]
		if enemy_wards:
			enemy_traps = [c for c in enemy_wards if await c.effect_param() >= 0]
			enemy_shields = [c for c in enemy_wards if c not in enemy_traps]
			if enemy_shields:
				priority_types += ward_counter_types
				if len(enemy_shields) >= 2:
					priority_types += ward_roshambo_types
			if len(enemy_traps) >= 4:
				priority_types += trap_roshambo_gambit_types


		# Enemy - DOT roshambo gambit logic
		self_dots = [e for e in member_hanging_effects[selected_enemy] if await e.effect_type() == SpellEffects.damage_over_time]
		if len(self_dots) >= 2:
			priority_types += dot_roshambo_gambit_types


		# Enemy - Hot counter/roshambo logic
		self_hots = [e for e in member_hanging_effects[selected_enemy] if await e.effect_type() == SpellEffects.heal_over_time]
		if self_hots:
			priority_types += hot_roshambo_types
			priority_types += hot_counter_types


		# Assign pips/shadow pips for self and selected enemy
		self_pips = (await client_member.power_pips() * 2) + await client_member.normal_pips()
		self_shadow_pips = await client_member.shadow_pips()
		enemy_pips = (await selected_enemy.power_pips() * 2) + await selected_enemy.normal_pips()
		enemy_shadow_pips = await selected_enemy.shadow_pips()


		# Enemy - More pips counter/roshambo logic
		if enemy_pips >= self_pips:
			priority_types += more_pips_counter_types


		# Enemy - 11 pips roshambo gambit logic
		if enemy_pips >= 11:
			priority_types += eleven_pips_roshambo_gambit_types


		# Enemy - 2 shadow pips roshambo gambit logic
		if enemy_shadow_pips >= 2:
			priority_types += two_shad_roshambo_gambit_types


		# Enemy - Oni's shadow roshambo logic
		if enemy_shadow_pips >= 2 or (enemy_shadow_pips == 1 and enemy_pips < self_pips):
			priority_types += oni_shadow_roshambo_types


		# Prioritize priority spells by placing them front of the priority list
		print(priority_types)
		priority_types.reverse()
		for t in priority_types:
			strategy.insert(0, t)


		# Spell Selection Logic
		selected_spell = None
		spell_matches = []
		castable_cards = [c for c in self.cards if await c.is_castable()]
		# search cards for matching spell type, finds all matches and then breaks.
		for t in strategy:
			for c in castable_cards:
				c_spell_logic = self.spell_logic[c]
				if c_spell_logic == t:
					spell_matches.append(c)
			if spell_matches:
				break
		if not spell_matches:
			priority_types = []
			priority_types += defensive_types
			priority_types.reverse()
			for t in priority_types:
				strategy.insert(0, t)
			for t in strategy:
				for c in castable_cards:
					c_spell_logic = self.spell_logic[c]
					if c_spell_logic == t:
						spell_matches.append(c)
				if spell_matches:
					break


		# Selects the highest pip value among the matched cards, prevents smaller hits being preferred. Shads are counted as 4 regular pips, as they are less pip heavy overall and should be preferred.
		if spell_matches:
			spell_matches_ranks = {}
			for s in spell_matches:
				await s.wait_for_graphical_spell()
				g_spell = await s.get_graphical_spell()
				regular_rank = await g_spell.read_value_from_offset(176 + 72, "unsigned char")
				shadow_rank = await g_spell.read_value_from_offset(176 + 73, "unsigned char")
				card_rank = regular_rank + (4 * shadow_rank)
				spell_matches_ranks[s] = int(card_rank)
			selected_spell = max(spell_matches_ranks, key= lambda s: spell_matches_ranks[s])


		# Ally Selection, if not done via playstyle mods already
		if not selected_ally and selected_spell:
			non_balance_uni_blade_names = ['Dark Pact']
			selected_graphical_spell = await selected_spell.get_graphical_spell()
			selected_spell_school = await selected_graphical_spell.magic_school_id()
			allies_to_compare = [a for a in allies if await a.is_player() == True if await member_participants[a].primary_magic_school_id() == selected_spell_school or selected_spell_school == 1027491821 or self.card_names[selected_spell] in non_balance_uni_blade_names]
			if allies_to_compare:
				max_ally_damages = {}
				for a in allies_to_compare:
					max_ally_damages[a] = max(member_damages[a])
				# return the ally with the max damage, school matched
				selected_ally = max(max_ally_damages, key = lambda a: max_ally_damages[a])
			else:
				selected_ally = client_member


		# Minion Utility logic
		minion = [a for a in allies if await a.is_minion()]
		if minion and not selected_ally:
			selected_ally = minion[0]
			priority_types += minion_utility_types


		# update previously used spell types, and those that aren't purely done by conditionals
		if selected_spell:
			if self.spell_logic[selected_spell] in clean_strategy:
				self.prev_hit_types.append(self.spell_logic[selected_spell])


		# Casting logic
		while True:
			if selected_spell:
				selected_spell_logic = self.spell_logic[selected_spell]
				if 'AOE' in selected_spell_logic:
					logger.debug(f"Client {self.client.title} - Casting {self.card_names[selected_spell]}")
					await selected_spell.cast(None, sleep_time=0.1)
				elif 'Enemy Select' in selected_spell_logic:
					logger.debug(f"Client {self.client.title} - Casting {self.card_names[selected_spell]} on {await selected_enemy.name()}")
					await selected_spell.cast(selected_enemy, sleep_time=0.1)
				elif 'Ally Select' in selected_spell_logic:
					logger.debug(f"Client {self.client.title} - Casting {self.card_names[selected_spell]} on {await selected_ally.name()}")
					await selected_spell.cast(selected_ally, sleep_time=0.1)
				if 'Divide' in selected_spell_logic:
					await asyncio.sleep(0.2)
					try:
						await self.client.mouse_handler.click_window_with_name(name='ConfirmTargetsConfirm')
					except:
						await asyncio.sleep(0.1)
			else:
				logger.debug(f"Client {self.client.title} - Passing")
				await self.pass_button()

			# detect failed cast, only if the client is soloing and is not in pvp as to avoid issues
			await asyncio.sleep(0.5)
			if len(player_members) == 1 and not in_pvp:
				if await self.client.duel.duel_phase() == DuelPhase.planning:
					await asyncio.sleep(0.5)
					pass
				else:
					break
			else:
				break