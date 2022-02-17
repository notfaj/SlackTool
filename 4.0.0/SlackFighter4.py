import asyncio
from email import utils
from wizwalker.combat import CombatHandler, CombatMember
from typing import Callable, List
from wizwalker import Keycode, utils
from wizwalker.memory.memory_objects.enums import DuelPhase
from wizwalker.errors import ReadingEnumFailed
from loguru import logger
import time

HIT_ENCHANTS = frozenset(['Strong', 'Giant', 'Monstrous', 'Gargantuan', 'Colossal', 'Epic', 'Keen Eyes', 'Accurate', 'Sniper', 'Unstoppable', 'Extraordinary'])
HEAL_ENCHANTS = frozenset(['Primordial', 'Radical'])
BLADE_ENCHANTS = frozenset(['Sharpened Blade'])
TRAP_ENCHANTS = frozenset(['Potent Trap'])
HIT_AURAS = frozenset(['Virulence', 'Frenzy', 'Beserk', 'Flawless', 'Infallible', 'Amplify', 'Magnify', 'Vengeance', 'Chastisement', 'Devotion', 'Furnace', 'Galvanic Field', 'Punishment', 'Reliquary', 'Sleet Storm', 'Reinforce', 'Eruption', 'Acrimony', 'Outpouring', 'Apologue', 'Rage', 'Intensify', 'Icewind', 'Recompense', 'Upheaval', 'Quicken'])
DEFENSE_AURAS = frozenset(['Fortify', 'Brace', 'Bulwark', 'Conviction'])
HEAL_AURAS = frozenset(['Cycle of Life', 'Mend', 'Renew', 'Empowerment', 'Adapt'])
SELECT_SHIELDS = frozenset(['Bracing Frost', 'Bracing Wind',  'Bracing Breeze', 'Borrowed Time', 'Ancient Wraps', 'Aegis of Artemis', 'Frozen Armor', 'Stun Block', 'Tower Shield', 'Death Shield', 'Life Shield', 'Myth Shield', 'Fire Shield', 'Ice Shield', 'Storm Shield', 'Dream Shield', 'Legend Shield', 'Elemental Shield', 'Spirit Shield', 'Shadow Shield', 'Glacial Shield', 'Volcanic Shield', 'Ether Shield', 'Thermic Shield'])
AOE_SHIELDS = frozenset(['Armory of Artemis I', 'Armory of Artemis', 'Legion Shield', 'Mass Tower Shield'])
SELECT_BLADES = frozenset(['Catalyze', 'Fireblade', 'Deathblade', 'Iceblade', 'Stormblade', 'Lifeblade', 'Mythblade', 'Balanceblade', 'Precision', 'Dark Pact', 'Shadowblade', 'Elemental Blade', 'Spirit Blade', 'Aegis Deathblade', 'Aegis Mythblade', 'Aegis Lifeblade', 'Aegis Stormblade', 'Aegis Fireblade', 'Aegis Iceblade', 'Aegis Balanceblade'])
AOE_BLADES = frozenset(['Blind Strike', 'Bladestorm', 'Dragonlance', 'Blade Dance', 'Ion Wind', 'Chromatic Blast'])
SELECT_PIERCE = frozenset(['Deathspear', 'Lifespear', 'Mythspear', 'Firespear', 'Icespear', 'Stormspear', 'Spirit Spear', 'Elemental Spear', 'Balancespear'])
SELECT_TRAPS = frozenset(['Hex', 'Disarming Trap', 'Curse', 'Spirit Trap', "Elemental Blade", 'Death Trap', 'Life Trap', 'Myth Trap', 'Storm Trap', 'Fire Trap', 'Backdraft', 'Feint', 'Ice Trap'])
AOE_TRAPS = frozenset(['Beastmoon Curse', 'Debilitate', 'Ambush', 'Mass Death Trap', 'Mass Life Trap', 'Mass Feint', 'Mass Myth Trap', 'Mass Fire Trap', 'Mass Ice Trap', 'Mass Storm Trap', 'Mass Hex', 'Malediction'])
GLOBALS = frozenset(['Age of Reckoning', 'Astraphobia', 'Balance of Power', 'Balefrost', 'Circle of Thorns', 'Combustion', 'Counterforce', 'Darkwind', 'Deadzone', 'Doom and Gloom', 'Elemental Surge', 'Katabatic Wind', 'Namaste', 'Power Play', 'Saga of Heroes', 'Sanctuary', 'Spiritual Attunement', 'Time of Legend', 'Tide of Battle', 'Wyldfire', 'Elemental Surge', 'Dampen Magic'])
SELECT_DOTS = frozenset(['Creeping Death', 'Cindertooth', 'Broiler', 'Bennu Alight', 'Befouling Brew', 'Link', 'Power Link', 'Inferno Salamander', 'Burning Rampage', 'Heck Hound', 'Wrath of Hades', 'Storm Hound', 'Frost Hound', 'Thunderstorm', 'Avenging Fossil', 'Frostbite', 'Spinysaur', 'Lightning Elf', 'Basilisk', 'Poison', 'Skeletal Dragon'])
SELECT_HITS = frozenset(['Cyclonic Swarm', 'Doggone Frog', 'Disarming Spirit', 'Deadly Sting', 'Consume Life', 'Cripping Blow', 'Crystal Shard', 'Curse-Eater', 'Cursed Kitty', 'Contamination', 'Chill Bug', 'Conflagaration', 'Clever Imp', 'Chill Wind', 'Chilling Touch', 'Cheapshot', 'Chaotic Currents', 'Butcher Bat', 'Bull Rush', 'Blue Moon Bird', 'Bluster Blast', 'Bombardier Beetle', 'Blizzard Wind', 'Blitz Beast', 'Blood Boil', 'Bitter Chill', 'Bio-Gnomes', 'Blistering Bolt', 'Blazing Construct', 'Basic Bruiser', 'Bargain of Brass', 'Ballistic Bat', 'Backdrafter', 'Avenging Marid', 'Angelic Vigor', 'Death Scarab', 'Immolate', 'Efreet', 'King Artorius', 'Scion of Fire', "S'more Machine", 'Fire from Above', 'Sun Serpent', 'Brimstone Revenant', 'Hephaestus', 'Krampus', 'Nautilus Unleashed', 'Fire Cat', 'Fire Elf', 'Sunbird', 'Phoenix', 'Naphtha Scarab', 'Elemental Golem', 'Spirit Golem', 'Dream Golem', 'Ether Golem', 'Legend Golem', 'Volcanic Golem', 'Thermic Golem', 'Glacial Golem', 'Helephant', 'Frost Beetle', 'Snow Serpent', 'Evil Snowman', 'Ice Wyvern', 'Thieving Dragon', 'Colossus', 'Angry Snowpig', 'Handsome Fomori', 'Winter Moon', 'Woolly Mammoth', 'Lord of Winter', 'Abominable Weaver', 'Scion of Ice', 'Shatterhorn', 'Frostfeather', 'Imp', 'Leprechaun', 'Seraph', 'Sacred Charge', 'Centaur', 'Infestation', "Nature's Wrath", 'Goat Monk', 'Luminous Weaver', 'Gnomes!', 'Hungry Caterpillar', 'Grrnadier', 'Thunder Snake', 'Lightning Bats', 'Storm Shark', 'Kraken', 'Stormzilla', 'Stormwing', 'Triton', 'Catalan', 'Queen Calypso', 'Catch of the Day', 'Hammer of Thor', 'Wild Bolt', 'Insane Bolt', 'Leviathan', 'Storm Owl', 'Scion of Storm', "Rusalka's Wrath", 'Thunderman', 'Blood Bat', 'Troll', 'Cyclops', 'Minotaur', 'Vermin Virtuoso', 'Gobbler', 'Athena Battle Sight', 'Keeper of the Flame', 'Ninja Pigs', 'Splashsquatch', 'Medusa', 'Celestial Calendar', 'Scion of Myth', "Witch's House Call", 'Tatzlewurm Terror', 'Dark Sprite', 'Ghoul', 'Banshee', 'Vampire', 'Skeletal Pirate', 'Crimson Phantom', 'Wraith', 'Monster Mash', 'Headless Horseman', 'Lord of Night', "Dr. Von's Monster", 'Winged Sorrow', 'Scion of Death', 'Snack Attack', 'Scarab', 'Scorpion', 'Locust Swarm', 'Spectral Blast', 'Hydra', 'Loremaster', 'Ninja Piglets', 'Samoorai', 'Savage Paw', 'Spiritual Tribunal', 'Judgement', 'Vengeful Seraph', 'Chimera', 'Supernova', 'Mana Burn', 'Sabertooth', 'Gaze of Fate', 'Scion of Balance', 'Mockenspiel', 'Beary Surprise', 'Camp Bandit', 'Obsidian Colossus', 'Grim Reader', 'Dark & Stormy', "Barbarian's Saga", 'Quartermane', 'The Bantam', 'The Shadoe', 'Mandar', 'Dog Tracy', 'Buck Gordon', 'Duck Savage', 'Caldera Jinn', 'Infernal Oni', 'Iceburn Jinn', 'Everwinter Oni', 'Thundering Jinn', 'Turmoil Oni', 'Macabre Jinn', 'Doom Oni', 'Verdurous Jinn', 'Primal Oni', 'Phantastic Jinn', 'Trickster Oni', 'Duststorm Jinn', 'Tribunal Oni', 'Hunting Wyrm', 'Shift Piscean', 'Shift Grendel', 'Shift Rattlebones', 'Shift Greenoak', 'Shift Thornpaw', 'Shift Ogre', 'Shift Dread Paladin', 'Shift Sugar Glider', 'Shift Fire Dwarf', 'Van Der Borst', 'Shift Bunferatu', 'Shift Ghulture', 'Frost Minotaur', 'Deadly Minotaur', 'Lively Minotaur', 'Natural Attack', 'Storm Sweep', 'Cat Scratch', 'Colossal Uppercut', 'Colossus Crunch', 'Cursed Flame', 'Ignite', 'Flame Strike', 'Firestorm', 'Storm Strike', 'Maelstrom', 'Taco Toss', 'Stinky Salute', 'Ice Breaker', 'Ritual Blade', 'Mander Blast', 'Death Ninja Pig', 'Ninja Slice', 'Ninja Slam', 'Thunder Spike', 'Stomp', 'Swipe', 'Wrath of Aquila', 'Wrath of Cronus', 'Wrath of Apollo', 'Wrath of Zeus', 'Wrath of Poseidon', 'Wrath of Ares'])
AOE_DOTS = frozenset(["Death's Champion", "Champion's Blight", 'Scald', 'Wings of Fate', 'Rain of Fire', 'Fire Dragon', 'Reindeer Knight', 'Snow Angel', 'Deer Knight', 'Iron Curse'])
AOE_HITS = frozenset(['Confounding Fiend', 'Deperate Daimyo', 'Cursed Medusa', 'Cursed Medusa I', 'Cursed Medusa II', 'Confounding Fiend I', 'Colossal Scorpion', 'Cold Harvest', 'Bloodletter', 'Arctic Blast', 'Colossafrog', 'Raging Bull', 'Meteor Strike', 'Blizzard', 'Snowball Barrage', 'Frost Giant', "Ratatoskr's Spin", 'Forest Lord', 'Tempest', 'Storm Lord', 'Sirens', 'Glowbug Squall', 'Sound of Musicology', 'Humongofrog', 'Earthquake', 'Orthrus', 'Mystic Colossus', 'Ship of Fools', 'Scarecrow', 'Call of Khrulhu', 'Leafstorm', 'Sandstorm', 'Power Nova', 'Ra', 'Nested Fury', 'Squall Wyvern', "Morganthe's Will", 'Steel Giant', 'Lycian Chimera', 'Lernaean Hydra', 'Lord of Atonement', "Morganthe's Venom", 'Eirkur Axebreaker', 'Wildfire Treant', 'Lava Giant', 'Fiery Giant', 'Lava Lord', 'Lord of Blazes', 'Snowball Strike', "Morganthe's Gaze", 'Tundra Lord', "Morganthe's Angst", 'Squall Wyvern', 'Lord of the Squall', "Morganthe's Ardor", 'Enraged Forest Lord', "Morganthe's Requiem", 'Death Seraph', 'Ominous Scarecrow', 'Bonetree Lord', 'Fable Lord', 'Lord Humongofrog', 'Noble Humongofrog', "Morganthe's Deceit", 'Lord of the Jungle', 'Freeze Ray', "Old One's Endgame", 'Blast Off!', 'Lava Giant', 'Lava Lord', 'Snowball Strike'])
MINIONS = frozenset(['Call of the Pack', 'Test Dummy', 'Mander Minion', 'Nerys', 'Spectral Minion', 'Animate', 'Malduit', 'Fire Elemental', 'Sir Lamorak', 'Ice Guardian', 'Freddo', 'Sprite Guardian', 'Sir Bedevere', 'Troll Minion', 'Cyclops Minion', 'Minotaur Minion', 'Talos', 'Vassanji', 'Water Elemental', 'Mokompo'])
OFFENSE_SHADOW = frozenset(['Shadow Shrike', 'Shadow Trickster'])
DEFENSE_SHADOW = frozenset(['Dark Protector', 'Shadow Sentinel'])
HEAL_SHADOW = frozenset(['Shadow Seraph'])
SELECT_SHADOW_HITS = frozenset(['Ultra Shadowstrike', 'Dark Nova', 'Shadowplume'])
AOE_SHADOW_HITS = frozenset(['Dark Fiend', 'Dark Shepherd'])
DISPELS = frozenset(['Quench', 'Melt', 'Dissipate', 'Vaporize', 'Entangle', 'Strangle', 'Unbalance', 'Spirit Defuse', 'Elemental Defuse'])
SELECT_HEALS = frozenset(['Charming Pixie', 'Divine Intervention', 'Divine Spark', 'Dryad of Artemis', 'Cauterize', 'Beastmoon Brownie', 'Fairy', 'Dryad', 'Satyr', 'Guardian Spirit', 'Regenerate', 'Scion of Life', 'Minor Blessing', 'Healing Current', 'Sacrifice', 'Helping Hands', 'Availing Hands', "Grendel's Amends", 'Blessing', 'Cleansing Current', 'Gobble'])
AOE_HEALS = frozenset(['Pixie', 'Unicorn', 'Sprite Swarm', 'Pigsie', 'Rebirth', 'Hamadryad', 'Kiss of Death', 'Helping Hands', 'Availing Hands', 'Cat Nap', 'Restoring Hands'])
SELECT_STUNS = frozenset(['Freeze', 'Stun', 'Decelerate'])
AOE_STUNS = frozenset(['Petrify', 'Choke', 'Blinding Light', 'Blinding Freeze', 'Wall of Smoke', 'Shockwave'])
SELECT_DETONATES = frozenset(['Detonate', 'Solomon Crane', 'Dive-Bomber Beetle'])
AOE_DETONATES = frozenset(['Incindiate'])
SELECT_PRISMS = frozenset(['Elemental Prism', 'Spirit Prism', 'Death Prism', 'Life Prism', 'Myth Prism', 'Ice Prism', 'Fire Prism', 'Storm Prism'])
AOE_PRISMS = frozenset(['Mass Elemental Prism', 'Mass Spirit Prism', 'Mass Fire Prism', 'Mass Ice Prism', 'Mass Storm Prism', 'Mass Death Prism', 'Mass Life Prism', 'Mass Myth Prism'])
DIVIDE_HITS = frozenset(["Qismah's Curse", 'Iron Sultan', 'Sand Wurm', 'Snake Charmer', 'Climcaclysm', 'Scorching Scimitars', 'Lamassu'])
AOE_DEBUFFS = frozenset(['Plague', 'Virulent Plague', 'Smokescreen', 'Malediction', 'Mass Infection', 'Muzzle'])
SELECT_DEBUFFS = frozenset(['Weakness', 'Black Mantle', 'Bad Juju', 'Infection', 'Threefold Fever', 'Atrophy', 'Corruption', 'Diversion'])
SELECT_MINION_UTILITIES = frozenset(['Shield Minion', 'Buff Minion', 'Siphon Health', 'Mend Minion', 'Draw Power', 'Dimension Shift', 'Steal Health', 'Sap Health', 'Take Power', 'Draw Health', 'Drain Health', 'Sap Power', 'Benevolent Bat', 'Cast-Iron Aegis', "Charalatan's Deceit", 'Charmed Scales', 'Cinderbird', 'Demoralize'])
SELECT_PACIFIES = frozenset(['Mega Pacify', 'Mega Distract', 'Mega Subdue', 'Mega Soothe', 'Mega Tranquilize', 'Mega Calm'])
AOE_PACIFIES = frozenset(['Pacify', 'Distract', 'Calm', 'Subdue', 'Soothe', 'Tranquilize'])
AOE_TAUNTS = frozenset(['Taunt', 'Mega Taunt', 'Provoke'])
AOE_POLYMORPHS = frozenset(['Polymorph Jaguar', 'Polymorph Gobbler', 'Polymorph Beet', 'Polymorph Carrot', 'Polymorph Cat Bandit', 'Polymorph Colossus', 'Polymorph Disparagus', 'Polymorph Draconian', 'Polymorph Elemental', 'Polymorph Icehorn', 'Polymorph Mander', 'Polymorph Hound', 'Polymorph Ninja', 'Polymorph Peas', 'Polymorph Ptera', 'Polymorph Treant', 'Hatch'])
AOE_HEAL_BLADES = frozenset(['Guidance', 'Brilliant Light'])
SELECT_HEAL_BLADES = frozenset(['Guiding Light', 'Precision', 'Guiding Armor'])
GOLEM_ENCHANT = frozenset(['Golem: Taunt'])
AOE_GOLEM_MINION = frozenset(['Golem Minion'])
SELECT_WAND_HITS = frozenset(['Agony', 'Arctic Sting', 'Assail', 'Blaze', 'Blitz', 'Burst', 'Clash', 'Cold Slash', 'Conniption', 'Crusade', 'Crush', 'Cyclone', 'Dark Blow', 'Death Blow', 'Death Charge', 'Death Chill', 'Death Touch', 'Dread', 'Fire Scorch', 'Fire Slash', 'Fireball', 'Flare', 'Flash', 'Flux', 'Frostblight', 'Heroic Hit', 'Ice Blast', 'Ice Shard', 'Ice Slash', 'Impact', 'Inferno', 'Jolt', 'Justice Slash', 'Life Fury', 'Life Ire', 'Major Agony', 'Major Arctic Sting', 'Major Assail', 'Major Balance Burst', 'Major Blaze', 'Major Blitz', 'Major Burst', 'Major Chill', 'Major Clash', 'Major Conniption', 'Major Crusade', 'Major Crush', 'Major Cyclone', 'Major Dread', 'Major Fire Scorch', 'Major Fireball', 'Major Flare', 'Major Flash', 'Major Flux', 'Major Frostblight', 'Major Heroic Hit', 'Major Ice Blast', 'Major Ice Shard', 'Major Impact', 'Major Inferno', 'Major Jolt', 'Major Life Fury', 'Major Life Ire', 'Major Nova', 'Major Rage', 'Major Revile', 'Major Scorch', 'Major Scourge', 'Major Shadowplume', 'Major Shadowstrike', 'Major Shock', 'Major Snowburst', 'Major Spark', 'Major Strike', 'Major Surge', 'Major Torment', 'Major Vibrato', 'Major Wrath', 'Mana Burn', 'Mega Agony', 'Mega Arctic Sting', 'Mega Assail', 'Mega Blaze', 'Mega Blitz', 'Mega Burst', 'Mega Conniption', 'Mega Cyclone', 'Mega Dark Blow', 'Mega Frostblight', 'Mega Impact', 'Mega Inferno', 'Mega Jolt', 'Mega Nova', 'Mega Rage', 'Mega Shadowstrike', 'Mega Torment', 'Mighty Rage', 'Minor Chill', 'Minor Clash', 'Minor Cold Slash', 'Minor Crusade', 'Minor Crush', 'Minor Dark Blow', 'Minor Death Tap', 'Minor Fire Flare', 'Minor Fire Scorch', 'Minor Fireball', 'Minor Flash', 'Minor Heroic Hit', 'Minor Ice Blast', 'Minor Ice Shard', 'Minor Ice Slash', 'Minor Life Fury', 'Minor Life Ire', 'Minor Nova', 'Minor Shock', 'Minor Spark', 'Minor Strike', 'Minor Surge', 'Minor Wrath', 'Moon Beam', 'Mystic Slash', 'Rage', 'Revile', 'Rolling Thunder Bolt', 'Scorch', 'Shadow Slash', 'Shadowblast', 'Shadowplume', 'Shadowstrike', 'Shock', 'Sky Slash', 'Snowburst', 'Spark', 'Spirit Slash', 'Strike', 'Super Agony', 'Super Arctic Sting', 'Super Assail', 'Super Blaze', 'Super Blitz', 'Super Burst', 'Super Chill', 'Super Clash', 'Super Conniption', 'Super Crusade', 'Super Crush', 'Super Cyclone', 'Super Dark Blow', 'Super Death Tap', 'Super Dread', 'Super Fire Scorch', 'Super Fireball', 'Super Flare', 'Super Flash', 'Super Flux', 'Super Frostblight', 'Super Heroic Hit', 'Super Ice Blast', 'Super Ice Shard', 'Super Impact', 'Super Inferno', 'Super Jolt', 'Super Life Fury', 'Super Life Ire', 'Super Nova', 'Super Rage', 'Super Revile', 'Super Scorch', 'Super Shadowplume', 'Super Shadowstrike', 'Super Shock', 'Super Snowburst', 'Super Spark', 'Super Strike', 'Super Surge', 'Super Torment', 'Super Vibrato', 'Super Wrath', 'Surge', 'Torment', 'Ultra Agony', 'Ultra Arctic Sting', 'Ultra Assail', 'Ultra Blaze', 'Ultra Blitz', 'Ultra Burst', 'Ultra Conniption', 'Ultra Cyclone', 'Ultra Dark', 'Ultra Frostblight', 'Ultra Impact', 'Ultra Inferno', 'Ultra Jolt', 'Ultra Rage', 'Ultra Shadowstrike', 'Ultra Torment', 'Vibrato', 'Waves of Wrath', 'Wrath'])
SELECT_ENEMY_WARD_UTILITY = frozenset(['Betrayal', 'Meltdown', "Oni's Forge", "Jinn's Defense", 'Righting the Scales', 'Steal Ward', 'Double Steal Ward', 'Shatter', 'Pierce'])
SELECT_ENEMY_BLADE_UTILITY = frozenset(['Wall of Blades', "Oni's Destruction", 'Putrefaction', "Jinn's Larceny", 'Eye of Vigilance', 'Steal Charm, Double Steal Charm', 'Enfeeble', 'Disarm', 'Backstab'])
SELECT_ENEMY_TRAP_UTILITY = frozenset(['Backfire', "Jinn's Reversal", 'Tranquility', "Oni's Naturalism", 'Righting the Scales'])
SELECT_ENEMY_WEAKNESS_UTILITY = frozenset(['Glacial Fortress', "Jinn's Vexation", 'Delusion', "Oni's Projection", 'Eye of Vigilance'])
SELECT_ENEMY_HOT_UTILITY = frozenset(['Energy Transfer', "Jinn's Restoration", 'Contagion', "Oni's Morbidity", "Jinn's Fortune", 'Snowdrift'])
SELECT_SELF_DOT_UTILITY = frozenset(['Reap the Whirlwind', "Oni's Attrition", 'Meditation', "Jinn's Affliction", "Jinn's Fortune", 'Triage', 'Shift'])
SELECT_ALLY_HOT_UTILITY = frozenset(['Accelerate'])
AOE_SELF_DOT_UTILITY = frozenset(['Mass Triage', 'Cooldown'])
SELECT_ENEMY_MORE_PIPS_UTILITY = frozenset(['Steal Pip', 'Mana Burn'])
SELECT_ENEMY_SELF_WARD_GAMBIT = frozenset(['Scion of Ice', 'Doom Oni', 'Phantastic Jinn', 'Brisk Blast', 'Cold-Fired Phoenix'])
SELECT_ENEMY_SELF_BLADE_GAMBIT = frozenset(['Scion of Storm', 'Macabre Jinn', 'Primal Oni', 'Dark Animism'])
SELECT_ENEMY_ENEMY_TRAP_GAMBIT = frozenset(['Caldera Jinn', 'Everwinter Oni', 'Scion of Myth'])
SELECT_ENEMY_ENEMY_WEAKNESS_GAMBIT = frozenset(['Iceburn Jinn', 'Turmoil Oni', 'Scion of Death'])
SELECT_ENEMY_ENEMY_DOT_GAMBIT = frozenset(['Scion of Fire', 'Verdurous Jinn', 'Trickster Oni', 'Duststorm Jinn', 'Blood-Thristy Bat'])
SELECT_ENEMY_SELF_HOT_GAMBIT = frozenset(['Infernal Oni', 'Thundering Jinn', 'Scion of Life', 'Duststorm Jinn'])
SELECT_ENEMY_ENEMY_2_SHADS_GAMBIT = frozenset(['Tribunal Oni'])
SELECT_ENEMY_ENEMY_11_PIPS_GAMBIT = frozenset(['Scion of Balance'])
SELECT_ENEMY_MINION_GAMBIT = frozenset(['Arboreal Vengeance'])
SELECT_ENEMY_SELF_DOT_UTILITY = frozenset(['Big Bad Butterfly'])
AOE_GENERAL_UTILITY = frozenset(['Blaze of Glory', 'Bracing Cold', 'Brisk and Reward'])
ANTI_ENEMY_SELECT = frozenset(['Cost of Life'])
ANTI_ALLY_SELECT = frozenset([])
ANTI_AOE = frozenset([])
ANTI_DIVIDE = frozenset([])
SELECT_RESHUFFLE = frozenset(['Reshuffle'])

casting_logic_dict = {
	SELECT_RESHUFFLE: 'Ally Select Reshuffle',
	HIT_ENCHANTS: 'Hit Enchant',
	HEAL_ENCHANTS: 'Heal Enchant',
	BLADE_ENCHANTS: 'Blade Enchant',
	TRAP_ENCHANTS: 'Trap Enchant',
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
	AOE_GOLEM_MINION: 'AOE Golem Minion'
}
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
	AOE_GOLEM_MINION: str(casting_logic_dict[GOLEM_ENCHANT])
}

master_list = list(casting_logic_dict.keys())

school_ids = {0: 2343174, 1: 72777, 2: 83375795, 3: 2448141, 4: 2330892, 5: 78318724, 6: 1027491821, 7: 2625203, 8: 78483, 9: 2504141, 10: 663550619, 11: 1429009101, 12: 1488274711, 13: 1760873841, 14: 806477568, 15: 931528087}
school_list_ids = {index: i for i, index in school_ids.items()}
school_id_list = list(school_ids.values())

# define the master hitting strategy
master_strategy = ['AOE Golem Minion', 'Ally Select Blade', 'Enemy Select Trap', 'AOE Minion', 'AOE Global', 'AOE Blade', 'AOE Trap', 'AOE Hit Aura', 'AOE Offensive Shadow Creature', 'AOE DOT', 'AOE Hit', 'Enemy Select DOT', 'Enemy Select Hit', 'Enemy Select Hit Divide', 'AOE Polymorph']
mob_strategy = ['Ally Select Blade', 'AOE DOT', 'AOE Hit', 'Enemy Select DOT', 'Enemy Select Hit', 'Enemy Select Hit Divide', 'AOE Hit Aura', 'AOE Trap', 'AOE Global', 'AOE Blade', 'Enemy Select Trap','AOE Golem Minion' ,'AOE Minion', 'AOE Offensive Shadow Creature', 'AOE Polymorph']
# TODO: Change the master strategy based on if there's just a boss, just mobs, or mixture of both. Mobs only strat should be AOE spamming.


heal_types = ['AOE Heal Blade', 'Ally Select Heal Blade', 'AOE Heal Shadow Creature', 'AOE Heal', 'Ally Select Heal']
reshuffle_types = ['Ally Select Reshuffle']
defensive_types = ['AOE Defense Aura', 'AOE Defensive Shadow Creature', 'AOE Shield', 'Enemy Select Debuff', 'AOE Debuff', 'AOE Stun', 'Enemy Select Stun', 'Ally Select Shield']
prism_types = ['AOE Prism', 'Enemy Select Prism']
minion_utility_types = ['Ally Select Minion Utility', 'Ally Select Pacify', 'AOE Pacify', 'AOE Taunt']

@logger.catch
class SlackFighter(CombatHandler):
	def __init__(self, client):
		self.client = client

	async def is_fighting(self):
		check = await self.get_members()
		if len(check): 
			return True
		else:
			return False


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
		for c in self.cards:
			if c not in self.card_names:
				self.card_names[c] = await c.display_name()
			



	@logger.catch
	async def discard_unsupported(self):
		"""Discards all spells not in the master spell list"""
		discarded = True
		while discarded:
			discarded = False
			for c in self.cards.copy():
				if all([self.card_names[c] not in s for s in master_list]):
					logger.debug(f"Client {self.client.title} - Discarding {self.card_names[c]}")
					await c.discard(sleep_time=0.25)
					self.cards = await self.get_cards()
					await self.assign_card_names()
					discarded = True
					break


	@logger.catch()
	async def assign_spell_logic(self):
		"""Assigns spell logic string and enchanting logic strings to all spells """
		for c in self.cards:
			for s in master_list:
				if self.card_names[c] in s:
					self.spell_logic[c] = casting_logic_dict[s]
					if s in enchant_logic_dict:
						self.enchant_logic[c] = enchant_logic_dict[s]


	@logger.catch
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
	async def handle_round(self):
		"""Uses strategy lists and conditional strategies to decide on the best spell to cast, then casts it."""

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

		allies = []
		mobs = []
		for member in members:
			member_id = await member_participants[member].team_id()
			if member_id == client_team_id:
				allies.append(member)
			else:
				mobs.append(member)

		ally_participants = {}
		ally_stats = {}
		ally_damages = {}
		ally_hanging_effects = {}
		for ally in allies:
			ally_participants[ally] = member_participants[ally]
			ally_stats[ally] = await ally.get_stats()
			a_damages = await ally_stats[ally].dmg_bonus_percent()
			a_universal_damage = await ally_stats[ally].dmg_bonus_percent_all()
			ally_damages[ally] = [r + a_universal_damage for r in a_damages]

		mob_participants = {}
		mob_stats = {}
		mob_resistances = {}
		mob_hanging_effects = {}
		for mob in mobs:
			mob_participants[mob] = member_participants[mob]
			mob_stats[mob] = await mob.get_stats()
			mob_hanging_effects[mob] = await mob_participants[mob].hanging_effects()
			m_resistances = await mob_stats[mob].dmg_reduce_percent()
			m_universal_resistance = await mob_stats[mob].dmg_reduce_percent_all()
			mob_resistances[mob] = [r + m_universal_resistance for r in m_resistances]

		# for a in allies:
		# 	while True:
		# 		ally_hanging_effects[a] = await ally_participants[a].hanging_effects()
		# 		for e in ally_hanging_effects[a]:
		# 			try:
		# 				type_check = await e.effect_type()
		# 			except ReadingEnumFailed:
		# 				logger.error('Effect reading invalid, re-getting hanging effects.')
		# 				await asyncio.sleep(0.1)
		# 				break
		# 			else:
		# 				pass
		# 		else:
		# 			break
		# 		await asyncio.sleep(0.1)

		# for m in mobs:
		# 	while True:
		# 		mob_hanging_effects[m] = await mob_participants[m].hanging_effects()
		# 		for e in mob_hanging_effects[m]:
		# 			try:
		# 				type_check = await e.effect_type()
		# 			except ReadingEnumFailed:
		# 				logger.error('Effect reading invalid, re-getting hanging effects.')
		# 				await asyncio.sleep(0.1)
		# 				break
		# 			else:
		# 				pass
		# 		else:
		# 			break
		# 		await asyncio.sleep(0.1)

		bosses = [m for m in mobs if await m.is_boss()]
		strategy = None
		if bosses:
			strategy = master_strategy.copy()
		else:
			strategy = mob_strategy.copy()

		# de-prioritize any spell types that were previously casted, avoids spamming the same spell type. Playstyle modifications bypass this.
		for p in self.prev_hit_types:
			if p in strategy:
				strategy.remove(p)
			strategy.append(p)

		# Conditional playstyle modifications. Allows for changing playstyle based on conditions like healing, enemy schools, and hanging effects (not implemented)
		# TODO: Hanging effects shittery
		
		# Priority types is the list of spell types it inserts at the front of the list, the selected ally is the ally that these spells will be used on.
		priority_types = []
		selected_ally = None
		selected_enemy = None



		# Healing logic
		player_members = [ a for a in allies if await a.is_player() == True ]
		health_percentages = {}
		for a in player_members:
			health_percentages[a] = float(await a.health()) / float(await a.max_health())
		print(str(health_percentages[a]))
		# chooses ally with lowest health percent
		highest_priority_ally = min(health_percentages, key= lambda a: health_percentages[a])



		# only prioritizes healing if below the threshold float (0.51 by default)
		if health_percentages[highest_priority_ally] < 0.51:
			print(str(health_percentages[highest_priority_ally]))
			selected_ally = highest_priority_ally
			priority_types += heal_types
			
		
		 
		if len([c for c in self.cards if self.card_names[c] == "Reshuffle"]) > len([c for c in self.cards if not self.card_names[c] == "Reshuffle"]) or [a for a in heal_types if a in priority_types] and not [c for c in self.cards if self.card_names[c] in AOE_HEALS and SELECT_HEALS and SELECT_SHIELDS] and len([self.cards]) < 7:
			selected_ally = client_member
			priority_types += reshuffle_types


		# Defensive logic, works same as healing but with diff spells and diff threshold
		if health_percentages[highest_priority_ally] < 0.61:
			selected_ally = highest_priority_ally
			priority_types += defensive_types

		
		# Enemy Selection, if not done via playstyle mods already
		mob_healths = {}
		for m in mobs:
			mob_healths[m] = await m.health()
		if not selected_enemy:
			selected_enemy = max(mob_healths, key = lambda h: mob_healths[h])

		# Prism logic
		selected_enemy_resistances = mob_resistances[selected_enemy]
		max_enemy_resistance = max(selected_enemy_resistances)
		selected_enemy_resistances_ids = {i: r for i, r in zip(school_id_list, selected_enemy_resistances)}
		if max_enemy_resistance > 0.35:
			if max_enemy_resistance - selected_enemy_resistances_ids[client_school_id] < 0.1:
				priority_types += prism_types
		
		# [print(await m.effect_type()) for m in mob_hanging_effects[selected_enemy]]

		# Prioritize priority spells
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
			allies_to_compare = [a for a in allies if await a.is_player() == True if await ally_participants[a].primary_magic_school_id() == selected_spell_school or selected_spell_school == 1027491821 or self.card_names[selected_spell] in non_balance_uni_blade_names]
			if allies_to_compare:
				max_ally_damages = {}
				for a in allies_to_compare:
					max_ally_damages[a] = max(ally_damages[a])
				# return the ally with the max damage, school matched
				selected_ally = max(max_ally_damages, key = lambda a: max_ally_damages[a])
			else:
				selected_ally = client_member



		# Minion Utility logic
		minion = [a for a in allies if await a.is_minion()]
		if minion and not selected_ally:
			selected_ally = minion[0]
			priority_types += minion_utility_types

		# update previously used spell types
		if selected_spell:
			self.prev_hit_types.append(self.spell_logic[selected_spell])

		# Casting logic


		while True:
			if selected_spell:
				selected_spell_logic = self.spell_logic[selected_spell]
				if 'AOE' in selected_spell_logic:
					logger.debug(f"Client {self.client.title} - Casting {self.card_names[selected_spell]}")
					await selected_spell.cast(None, sleep_time=0.15)
				elif 'Enemy Select' in selected_spell_logic:
					logger.debug(f"Client {self.client.title} - Casting {self.card_names[selected_spell]} on {await selected_enemy.name()}")
					await selected_spell.cast(selected_enemy, sleep_time=0.15)
				elif 'Ally Select' in selected_spell_logic:
					logger.debug(f"Client {self.client.title} - Casting {self.card_names[selected_spell]} on {await selected_ally.name()}")
					await selected_spell.cast(selected_ally, sleep_time=0.15)
				if 'Divide' in selected_spell_logic:
					await asyncio.sleep(0.2)
					try:
						await self.client.mouse_handler.click_window_with_name(name='ConfirmTargetsConfirm')
					except:
						await asyncio.sleep(0.1)
			else:
				logger.debug(f"Client {self.client.title} - Passing")
				await self.pass_button()

			# detect failed cast, only if the client is soloing as to avoid issues
			await asyncio.sleep(0.5)
			if len(player_members) == 1:
				if await self.client.duel.duel_phase() == DuelPhase.planning:
					await asyncio.sleep(0.5)
					pass
				else:
					break
			else:
				break