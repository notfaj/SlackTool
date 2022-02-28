from asyncio.windows_events import NULL
from tempfile import TemporaryDirectory
from typing import *
import asyncio
from tkinter import dialog
from tokenize import Triple
import wizwalker
from wizwalker import WizWalker, Keycode, XYZ, utils
from wizwalker.memory import  Window
import math
import os
from os import path
import time
import sys
import subprocess
import traceback
from loguru import logger
import datetime
import re
import random
from configparser import ConfigParser
import io
import struct
import zlib
from io import BytesIO
from SlackTeleport import SlackTeleport, TypedBytes
from SlackFighter5 import SlackFighter
from wizwalker import XYZ, Keycode, MemoryReadError
from wizwalker.memory import DynamicClientObject
from concavehull import concavehull
from wizwalker.file_readers.wad import Wad
from sprinty_client import SprintyClient

type_format_dict = {
"char": "<c",
"signed char": "<b",
"unsigned char": "<B",
"bool": "?",
"short": "<h",
"unsigned short": "<H",
"int": "<i",
"unsigned int": "<I",
"long": "<l",
"unsigned long": "<L",
"long long": "<q",
"unsigned long long": "<Q",
"float": "<f",
"double": "<d",
}

npc_range_path = ['WorldView', 'NPCRangeWin']
decline_quest_path = ['WorldView', 'wndDialogMain', 'btnLeft']
advance_dialog_path = ['WorldView', 'wndDialogMain', 'btnRight']
dialogue_window_path = ['WorldView', 'wndDialogMain']
universe_map_window = ['WorldView', '']
dungeon_warning_path = ['MessageBoxModalWindow', 'messageBoxBG']
multiple_quests_path = ['WorldView', 'NPCServicesWin', 'ControlSprite', 'Layout', 'Option1']
spiral_door_cycle_path = ['WorldView', '', 'messageBoxBG', 'ControlSprite', 'optionWindow', 'rightButton']
spiral_door_teleport_path = ['WorldView', '', 'messageBoxBG', 'ControlSprite', 'teleportButton']
spiral_door_path = ['WorldView', '', 'messageBoxBG', 'ControlSprite', 'optionWindow']
quest_name_path =[ "WorldView", "windowHUD" , "QuestHelperHud", "ElementWindow", "" ,"txtGoalName"]
popup_title_path =["WorldView", "NPCRangeWin","wndTitleBackground","NPCRangeTxtTitle"]


class SlackQuester():
	def __init__(self, client, clients):
		self.client = client
		self.clients = clients

	async def get_window_from_path(self,root_window: Window, name_path):
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
		
	async def is_visible_by_path(self, path):
		# checks visibility of a window from the path
		root = self.client.root_window
		windows = await self.get_window_from_path(root, path)
		if windows == False:
			return False
		elif await windows.is_visible():
			return True
		else:
			return False

	async def click_window_by_path(self, path):
		# clicks window from path, must actually exist in the UI tree
		root = self.client.root_window
		windows = await self.get_window_from_path(root, path)
		if windows:
			await self.client.mouse_handler.click_window(windows)
		else:
			await asyncio.sleep(0.1)

	async def find_quest_world(self):
		await self.click_window_by_path(path=spiral_door_teleport_path)

	class TypedBytes(BytesIO):
		def split(self, index: int) -> Tuple["TypedBytes", "TypedBytes"]:
			self.seek(0)
			buffer = self.read(index)
			return type(self)(buffer), type(self)(self.read())
		def read_typed(self, type_name: str):
			type_format = type_format_dict[type_name]
			size = struct.calcsize(type_format)
			data = self.read(size)
			return struct.unpack(type_format, data)[0]

	async def parse_quest_stuff(self,quest_name_path):
		quest_name = await self.get_window_from_path(self.client.root_window, quest_name_path)
		unsplitted = await quest_name.maybe_text()

		split1_qst = unsplitted.split("<center>Collect ")
		split2_qst = split1_qst[1].split(" in") #Parsing the quest name
		questnameparsed = split2_qst[0]

		#example of a collect quest the only stuff that change are
		#"Cog", "Triton Avenue" and "(0 of 3)" the rest is static
		#<center>Collect Cog in Triton Avenue (0 of 3)</center>

		split1_amt = unsplitted.split(" (")
		split2_amt = split1_amt[1].replace(")</center>", "")
		amount_to_get_parsed = split2_amt.split("of ")[1] #Parsing the amount of stuff to pick up
		amount_gotten_parsed = split2_amt.split(" of")[0] #Parsing the amount of stuff that has been picked up

		return questnameparsed, f"{amount_gotten_parsed} / {amount_to_get_parsed}"

	async def parse_name_talk_to(self,quest_name_path):
		questnameparsed = []
		quest_name = await self.get_window_from_path(self.client.root_window, quest_name_path)
		unsplitted = await quest_name.maybe_text()
		unsplitted = unsplitted.lower()
		split1_qst = unsplitted.split("<center>talk to ")
		split2_qst = split1_qst[1].split(" in") #Parsing the quest name
		questnameparsed.append(split2_qst[0])
		return questnameparsed

	async def find_quest_type(self,quest_name_path):
		quest_name_path = await self.get_window_from_path(self.client.root_window, quest_name_path)
		quest_msg = await quest_name_path.maybe_text()
		print(quest_msg)

		if "Talk To" in quest_msg:
			#talk to quest
			quest_type = "talk to"
			return quest_type

		elif "Defeat " in quest_msg and not "(" in quest_msg and not "collect" in quest_msg.lower():
			#defeat quests mostly bosses
			quest_type = "defeat & collect"
			return quest_type

		elif "Defeat " in quest_msg and "(" in quest_msg and not "collect" in quest_msg.lower():
			#defeat multiple
			quest_type = "defeat & collect"
			return quest_type

		elif "Defeat " in quest_msg and not "(" in quest_msg and  "collect" in quest_msg.lower():
			# weird collect quest from mob
			quest_type = "defeat & collect"
			return quest_type

		elif "Defeat " in quest_msg and "(" in quest_msg and "collect" in quest_msg.lower():
			# defeat and collect
			quest_type = "defeat & collect"
			return quest_type

		elif not "Defeat " in quest_msg.lower() and "(" in quest_msg and "collect" in quest_msg.lower():
			# collect
			quest_type = "collect"
			return quest_type

		elif "Use" in quest_msg and not "defeat " in quest_msg.lower() and not "(" in quest_msg and not "collect" in quest_msg.lower():
			quest_type = "talk to" #aaaaaaaaah
			return quest_type
	
		
		elif "Find " in quest_msg and not "defeat " in quest_msg.lower() and not "(" in quest_msg and not "collect" in quest_msg.lower():
			#find quest similar to goto
			quest_type = "talk to"
			return quest_type

		elif "Craft " in quest_msg:
			# craft quests
			quest_type = "craft"
			return quest_type

		elif "Go To" in quest_msg.lower():
			# goto quests
			quest_type = "talk to"
			return quest_type

		else:
			quest_type = "talk to"
			return quest_type
	@logger.catch
	async def auto_quest(self):
		teleport = SlackTeleport(self.client)
		await self.loading_check()

		await self.dialog()

		await self.auto_health()

		await self.tp_to_quest_mob()

		await self.combat()

		quest_type = await self.find_quest_type(quest_name_path)
		
		if quest_type == "talk to":
			#TODO add code for going to new world
			while True:
				await self.dialog()
				try:
					await teleport.navmap_tp() #teleports to the npc
				except:
					await asyncio.sleep(0.1)
				await self.loading_check()
				await self.world_door_check()
				await self.dialog()
				#await self.tp_to_quest_mob2()
				if await self.is_visible_by_path(path=npc_range_path) or await self.is_visible_by_path(path=dialogue_window_path): # checks twice for bug fix
					#if await self.parse_name_talk_to(quest_name_path) in await self.read_popup_()
					sigil_msg_check = await self.read_popup_()
					txtmsg = await self.get_window_from_path(self.client.root_window,popup_title_path)
					maybe = await txtmsg.maybe_text()
					quest_name = await self.get_window_from_path(self.client.root_window, quest_name_path)
					quest_msg = await quest_name.maybe_text()
					if not maybe.lower() in quest_msg.lower():
						try:
							await teleport.navmap_tp() #teleports to the npc
						except:
							await asyncio.sleep(0.1)
						await asyncio.sleep(1)#fixes repair bug
					if await self.is_visible_by_path(path=npc_range_path) or await self.is_visible_by_path(path=dialogue_window_path):
						if "to enter" in sigil_msg_check.lower():
							await self.client.send_key(key=Keycode.X, seconds=0.1) #if in npc range press x
							zone_name = await self.client.zone_name()
							countdown = 17
							print("wating for zone change ")
							while await self.client.zone_name() == zone_name and countdown > 0:
								await asyncio.sleep(1)
								countdown -= 1
							await asyncio.sleep(1)
							await self.loading_check()
							await self.dialog()
							await self.client.send_key(key=Keycode.W, seconds=0.3)
							quest_type = await self.find_quest_type(quest_name_path)
							if quest_type == "talk to":
								await self.boss_check()
						else:
							await self.client.send_key(key=Keycode.X, seconds=0.1)
						await asyncio.sleep(0.5)
						await self.world_door_check()
						await self.dialog() # does dialog that may pause and start again
						#for i in range(3):
							#await asyncio.sleep(1)
						#	if await self.is_visible_by_path(path=dialogue_window_path):
								#await self.dialog()
								#break
				for i in range(2):
					await self.combat()
				break
		elif quest_type == "defeat & collect":
			#TODO somehow be able to get mobs
			while True:
				await self.dialog()
				if await self.tp_to_quest_mob():
					for i in range(10):
							await self.combat()
							await asyncio.sleep(0.2)
				else:
					try:
						await teleport.navmap_tp()
					except:
						await asyncio.sleep(0.1)
				await self.tp_to_quest_mob()
				await self.loading_check()
				await self.world_door_check()
				# check for sigil code
				if await self.is_visible_by_path(path=npc_range_path):
					sigil_msg_check = await self.read_popup_()
					await asyncio.sleep(1)
					if "to enter" in sigil_msg_check.lower():
						await self.client.send_key(key=Keycode.X, seconds=0.1)
						zone_name = await self.client.zone_name()
						countdown = 17
						print("wating for zone change ")
						while await self.client.zone_name() == zone_name and countdown > 0:
							await asyncio.sleep(1)
							countdown -= 1
						await asyncio.sleep(1)
						await self.loading_check()
						await self.dialog()
						await self.client.send_key(key=Keycode.W, seconds=0.3)
						try:
							await teleport.navmap_tp()
						except:
							await asyncio.sleep(0.1)
						await self.loading_check()
						await self.dialog()
						print("going into battle")
						for i in range(10):
							await asyncio.sleep(0.35)
							await self.tp_to_quest_mob()
							await self.combat()
					else:
						await self.client.send_key(key=Keycode.X, seconds=0.1)

				break	

		elif quest_type == "go to":
			while quest_type == "go to":
				try:
					await teleport.navmap_tp()
				except:
					await asyncio.sleep(0.1)
				await self.loading_check()
				await self.world_door_check()
				if await self.is_visible_by_path(path=npc_range_path):
					sigil_msg_check = await self.read_popup_()
					if "to enter" in sigil_msg_check.lower():
						await self.client.send_key(key=Keycode.X, seconds=0.1)
						zone_name = await self.client.zone_name()
						countdown = 17
						print("wating for zone change ")
						while await self.client.zone_name() == zone_name and countdown > 0:
							await asyncio.sleep(1)
							countdown -= 1
						await asyncio.sleep(1)
						await self.loading_check()
						await self.dialog()
						await self.client.send_key(key=Keycode.W, seconds=0.3)
						try:
							await teleport.navmap_tp()
						except:
							await asyncio.sleep(0.1)
						await self.loading_check()
						await self.dialog()
						for i in range(10):
							await self.combat()
							await asyncio.sleep(0.2)	
						await asyncio.sleep(1)
						break
					else:
						await self.client.send_key(key=Keycode.X, seconds=0.1)
					quest_type = await self.find_quest_type(quest_name_path)
					for i in range(2):
						await self.dialog()
						await asyncio.sleep(0.5)
					break
		elif quest_type == "collect":
			while True:
				await self.auto_collect()
				break
		elif quest_type == "use":
			while True:
				try:
					await teleport.navmap_tp()
				except:
					await asyncio.sleep(0.1)
				await self.loading_check()
				await self.dialog()
				if await self.is_visible_by_path(path=npc_range_path):
					await self.client.send_key(key=Keycode.X, seconds=0.1) #if in npc range press x
				break

	async def world_door_check(self):
		if await self.is_visible_by_path(path=npc_range_path):
			sigil_msg_check = await self.read_popup_()
			if "interact" in sigil_msg_check.lower():
				await self.client.send_key(key=Keycode.X, seconds=0.1)
				await asyncio.sleep(1)
			if await self.is_visible_by_path(path=spiral_door_path):
					await self.client.mouse_handler.activate_mouseless()
					await self.find_quest_world()
					await self.client.mouse_handler.deactivate_mouseless()
					await asyncio.sleep(0.1)
					await self.loading_check()

	async def loading_check(self):
		await asyncio.sleep(1)
		while await self.client.is_loading():
			await asyncio.sleep(0.1)

	async def boss_check(self):
		sprinty = SprintyClient(self.client)
		try:
			entities=await sprinty.get_mobs()
			for i in entities:
				temp = await i.object_template()
				name= await temp.object_name()
				if "Boss-" in name:
					await sprinty.tp_to(i)
					return True
		except:
			return False
	async def combat(self):
		battle = SlackFighter(self.client)
		if await battle.is_fighting()== True:
			logger.debug(f'Client {self.client.title} in combat, handling combat.')
			await battle.wait_for_combat()
			logger.debug(f'Client {self.client.title} combat ended, closing combat.')
			await asyncio.sleep(4)
			await self.dialog()


	async def read_popup_(self):
		popup_msgtext_path =["WorldView", "NPCRangeWin","imgBackground","NPCRangeTxtMessage"]
		try:
			popup_text_path = await self.get_window_from_path(self.client.root_window,popup_msgtext_path)
			txtmsg = await popup_text_path.maybe_text()
		except:
			txtmsg = ""
		return txtmsg

	async def dialog(self):
		await asyncio.sleep(1)
		if await self.is_visible_by_path(path=dialogue_window_path):
		# dialogue handling
			await self.client.mouse_handler.activate_mouseless()
			while await self.is_visible_by_path(path=dialogue_window_path):
				if await self.is_visible_by_path(path=decline_quest_path):
					await self.click_window_by_path(path=decline_quest_path)
				else:
					await self.click_window_by_path(path=advance_dialog_path)
				await asyncio.sleep(0.1)
			await self.client.mouse_handler.deactivate_mouseless()
		await asyncio.sleep(0.1)
		while await self.is_visible_by_path(path=multiple_quests_path):
			await self.client.mouse_handler.activate_mouseless()
			# if the NPC's quest menu had multiple options, this might break non-dialogue NPCS like bazaar
			await self.click_window_by_path(path=multiple_quests_path)
			await self.client.mouse_handler.deactivate_mouseless()
						
	async def find_safe_entities_from(self,fixed_position1, fixed_position2, safe_distance: float = 700, is_mob: bool = False):
		cli = SprintyClient(self.client)
		mob_positions = []
		can_Teleport = bool
		try: 
			if is_mob:
				for mob in await cli.get_mobs():
					mob_positions.append(await mob.location())
				fixed_position2 = mob_positions
			if fixed_position2:
				pass
			else:
				return True
		except ValueError:
			await asyncio.sleep(0.12)

		for p in fixed_position2:
			dist = math.dist(p, fixed_position1)
		try:
			if dist < safe_distance:
				return False
			else:
				can_Teleport = True
		except TypeError:
			pass 
		return can_Teleport

	async def read_popup_title(self,parsed_quest_info):
		popup_title_path =["WorldView", "NPCRangeWin","wndTitleBackground","NPCRangeTxtTitle"]
		txtmsg = await self.get_window_from_path(self.client.root_window,popup_title_path)
		maybe_collect_item = await txtmsg.maybe_text()
		if maybe_collect_item.lower() in str(parsed_quest_info[0]).lower():
			return True
		return False

	async def find_quest_entites(self, parsed_quest_info:list ,entity: dict):
		types_list = ['BehaviorInstance', 'ObjectStateBehavior', 'RenderBehavior', 'SelectBehavior', 'CollisionBehaviorClient']
		points = await self.Nav_Hull()
		Hull = points [0::2] # TODO remove points that are close to draw distance of each other
		#teleport around the hull and collect rendered objects, add them to a dict and their location
		for points in Hull:
			points = XYZ(points.x, points.y, points.z - 350)
			await self.client.teleport(points,move_after = False)
			await self.client.teleport(points)
			entities = await self.client.get_base_entity_list()
			for e in entities:
				types_app = []
				try:
					temp = await e.object_template()
					name = await temp.object_name()
					if not name == "Basic Positional":	
						name2 = str(name).split("_")
						for i in name2:
							if str(i).lower() in str(parsed_quest_info[0]).lower():
								behaviors=await e.inactive_behaviors()
								for b in behaviors:
									a = await b.read_type_name()
									types_app.append(a)
								if len(types_app) == len(types_list):
									xyz = await e.location()
									if name in entity:
										# append the new number to the existing array at this slot
										entity[name].append(xyz)
									else:
										# create a new array in this slot
										entity[name] = [xyz]
									break
				except MemoryReadError:
					await asyncio.sleep(0.05)
				except AttributeError:
					await asyncio.sleep(0.05)

	async def find_quest_entites1(self, parsed_quest_info:list ,entity: dict):
		points = await self.Nav_Hull()
		Hull = points[0::2] # TODO remove points that are close to draw distance of each other
		#teleport around the hull and collect rendered objects, add them to a dict and their location
		for points in Hull:
			points = XYZ(points.x, points.y, points.z - 350)
			await self.client.teleport(points,move_after = False)
			await self.client.teleport(points)
			entities = await self.client.get_base_entity_list()
			for e in entities:
				try:
					temp = await e.object_template()
					display_name = await temp.display_name()
					if not display_name.strip() == "":
						try:
							name = await self.client.cache_handler.get_langcode_name(display_name)
							print(name+" : "+display_name)
						except:
							name = ""
						if name in parsed_quest_info:
							xyz = await e.location()
							if name in entity:
								# append the new number to the existing array at this slot
								entity[name].append(xyz)
							else:
								# create a new array in this slot
								entity[name] = [xyz]
							break
				except MemoryReadError:
					await asyncio.sleep(0.05)
				except AttributeError:
					await asyncio.sleep(0.05)
					
	def parse_nav_data(self,file_data: Union[bytes, TypedBytes]):
		# ty starrfox for remaking this
		if isinstance(file_data, bytes):
			file_data = TypedBytes(file_data)
		vertex_count = file_data.read_typed("short")
		vertex_max = file_data.read_typed("short")
		# unknown bytes
		file_data.read_typed("short")
		vertices = []
		idx = 0
		while idx <= vertex_max - 1:
			x = file_data.read_typed("float")
			y = file_data.read_typed("float")
			z = file_data.read_typed("float")
			vertices.append(XYZ(x, y, z))
			vertex_index = file_data.read_typed("short")
			if vertex_index != idx:
				vertices.pop()
				vertex_max -= 1
			else:
				idx += 1
		edge_count = file_data.read_typed("int")
		edges = []
		for idx in range(edge_count):
			start = file_data.read_typed("short")
			stop = file_data.read_typed("short")
			edges.append((start, stop))
		return vertices, edges

	async def load_wad(self, path: str):
			return Wad.from_game_data(path.replace("/", "-"))

	async def Nav_Hull(self):
		wad = await self.load_wad(await self.client.zone_name())
		nav_data = await wad.get_file("zone.nav")
		vertices = []
		vertices, _ = self.parse_nav_data(nav_data)
		XY = []
		x_values = []
		y_values = []
		master_list = []
		arr = []
		# print(vertices)
		for v in vertices:
			x_values.append(v.x)
			y_values.append(v.y)
	
		XY = list(zip(x_values, y_values))
		#https://github.com/senhorsolar/concavehull
		glist = concavehull(XY, chi_factor=0.1)

		for a in glist:
			for l in vertices:
				if a[0] == l.x:
					if a[1] == l.y:
						master_list.append(l)
		return master_list

	async def auto_collect(self):
		cli = SprintyClient(self.client)
		quest_name_path =[ "WorldView", "windowHUD" , "QuestHelperHud", "ElementWindow", "" ,"txtGoalName"]
		popup_msgtext_path =["WorldView", "NPCRangeWin","imgBackground","NPCRangeTxtMessage"]
		#popup_title_path =["WorldView", "NPCRangeWin"]
		entity = dict()
		safe_cords = await self.client.body.position()
		completed = False
		parsed_quest_info = await self.parse_quest_stuff(quest_name_path)
		await self.find_quest_entites(parsed_quest_info,entity)
		for key in entity.keys():
			for i in entity[key]:
				# telports under quest items
				print("tp under quest item " + str(key))
				await self.client.teleport(XYZ(i.x, i.y, i.z - 350), move_after = False)
				await asyncio.sleep(0.5)
				await self.client.teleport(XYZ(i.x, i.y, i.z - 350))
				await asyncio.sleep(0.5)
				can_Teleport = await self.find_safe_entities_from(i, NULL , safe_distance=1700, is_mob=True) #checks if it's safe
				if can_Teleport == True:
					await self.client.teleport(XYZ(i.x, i.y, i.z - 230)) #teleports up a little
					for a in range(5):
						await self.client.send_key(Keycode.A, 0.1)
						await self.client.send_key(Keycode.D, 0.1)
					try:
						popup_text_path = await self.get_window_from_path(self.client.root_window,popup_msgtext_path)
						txtmsg = await popup_text_path.maybe_text()
						if await self.read_popup_title(parsed_quest_info) == True: # checks if popup ui has name of quest item or if collect in it's bottom text
							print("Found")
						elif "collect" in txtmsg.lower():
							print("Found")
						else:
							print("Wrong entity") # if it isn't a quest entity it break and checks another entity in the dict
							break
					except AttributeError:
						break
					while completed == False:
						for i in entity[key]: # for every cord in the correct quest name item
							#print("tp under reagent " + str(key))
							await self.client.teleport(XYZ(i.x, i.y, i.z - 350), move_after = False)
							await asyncio.sleep(0.5)
							await self.client.teleport(XYZ(i.x, i.y, i.z - 350))
							await asyncio.sleep(0.5)
						can_Teleport = await self.find_safe_entities_from(i, NULL , safe_distance=1700, is_mob=True) # checks if safe to collect
						if can_Teleport == True:
							await self.client.teleport(XYZ(i.x, i.y, i.z - 230))
							for a in range(4):
								await self.client.send_key(Keycode.A, 0.1)
								await self.client.send_key(Keycode.D, 0.1)
								try:
									popup_text_path = await self.get_window_from_path(self.client.root_window,popup_msgtext_path)
									txtmsg = await popup_text_path.maybe_text()
									await self.read_popup_title(parsed_quest_info or "collect" in txtmsg.lower()) #this is to just check if ui pop up appears
									break
								except:
									pass
							try:
								popup_text_path = await self.get_window_from_path(self.client.root_window,popup_msgtext_path)
								txtmsg = await popup_text_path.maybe_text()
								if await self.read_popup_title(parsed_quest_info) == True or "collect" in txtmsg.lower():
									print("collecting") #actually collects quest item
									await self.client.send_key(Keycode.X, 0.1)
									await self.client.send_key(Keycode.X, 0.1)
								
							except AttributeError:
								print("Ui not seen")
							except MemoryReadError:
								print("Ui not seen")
						try:
							check = await self.parse_quest_stuff( quest_name_path) # breaks when collect quest format for the string under the pointer
						except IndexError:
							completed = True
							await self.client.teleport(safe_cords)
							print("finished quest")
							return True
		
	@logger.catch
	async def auto_health(self):
		sprinty = SprintyClient(self.client)
		if await sprinty.needs_potion(health_percent=65, mana_percent=5)== True:
			x=0
			while await sprinty.needs_potion(health_percent=80, mana_percent=5)== True or x > 5:
				await sprinty.tp_to_closest_health_wisp(only_safe=True)
				await asyncio.sleep(1)
				x=x+1
				if x>5:
					x=0
					break
			while await sprinty.needs_potion(health_percent=5, mana_percent=50) == True or x > 5:
				await sprinty.tp_to_closest_mana_wisp(only_safe=True)
				await asyncio.sleep(1)
				x=x+1
				if x>5:
					x=0
					break
			if await sprinty.needs_potion(health_percent=65, mana_percent=5) and await sprinty.has_potion():
				await self.client.mouse_handler.activate_mouseless()
				await sprinty.use_potion()
				await self.client.mouse_handler.deactivate_mouseless()
			if await sprinty.needs_potion(health_percent=65, mana_percent=5) and not await sprinty.has_potion():
				await self.client.mouse_handler.activate_mouseless()
				await self.auto_buy_potions()
				await self.client.mouse_handler.deactivate_mouseless()
				
	async def auto_buy_potions(self):
		default_house = True
		potion_ui_buy = [
		"fillallpotions",
		"buyAction",
		"btnShopPotions",
		"centerButton",
		"fillonepotion",
		"buyAction",
		"exit"
	]
		# Head to home world gate
		await asyncio.sleep(0.1)
		await self.client.send_key(Keycode.HOME, 0.1)
		await asyncio.sleep(3)
		await self.loading_check()
		house_name = await self.client.zone_name()
		if house_name == "WizardCity/Interiors/WC_Housing_Dorm_Interior":
			default_house == True
		if not default_house:
			while not await self.client.is_in_npc_range():
				await self.client.send_key(Keycode.S, 0.1)
			await self.client.send_key(Keycode.X, 0.1)
			await asyncio.sleep(1.2)
			# Go to Wizard City
			await self.client.mouse_handler.click_window_with_name('wbtnWizardCity')
			await asyncio.sleep(0.15)
			await self.client.mouse_handler.click_window_with_name('teleportButton')
			await self.loading_check()
			# Walk to potion vendor
			await self.client.goto(-0.5264079570770264, -3021.25244140625)
			await self.client.send_key(Keycode.W, 0.5)
			await self.loading_check()
		elif default_house:
			await self.client.send_key(Keycode.S, 3)
			await asyncio.sleep(1.2)
			await self.loading_check()
		recall = await self.get_window_from_path(self.client.root_window,["WorldView","windowHUD","compassAndTeleporterButtons","ResumeInstanceButton"])
		if recall:
			dungeon= True
		#await self.client.goto(11.836355209350586, -1816.455078125)
		await self.client.teleport(XYZ(17.419727325439453, -1792.14453125, -88.03915405273438),6.255690097808838)
		await self.client.send_key(Keycode.W, 0.5)
		await self.loading_check()
		await self.client.goto(-880.2447509765625, 747.2051391601562)
		await self.client.goto(-4272.06884765625, 1251.950927734375)
		await asyncio.sleep(0.3)
		if not await self.client.is_in_npc_range():
			await self.client.teleport(-4442.06005859375, 1001.5532836914062)
		await self.client.send_key(Keycode.X, 0.1)
		await asyncio.sleep(6)
		# Buy potions
		for i in potion_ui_buy:
			await self.client.mouse_handler.click_window_with_name(i)
			await asyncio.sleep(1)
		# Return
		if dungeon:
			await self.client.mouse_handler.click_window(recall)
			await self.loading_check()




	async def tp_to_quest_mob(self):
		await self.loading_check()
		battle = SlackFighter(self.client)
		sprinty = SprintyClient(self.client)
		quest_name = await self.get_window_from_path(self.client.root_window, quest_name_path)
		quest = await quest_name.maybe_text()
		quest_msg = quest.lower()
		quest_parse = quest_msg.split("<center>Defeat ")

		try:
			quest_parse2 = quest_parse[0].split(" and ") 
		except:
			quest_parse2 = quest_parse[0].split(" in ")   

		final_parse = quest_parse2[0]
		ent = await self.client.get_base_entity_list()
		for i in ent:
			k = await i.inactive_behaviors()
			for j in k:
				if await j.read_type_name() == "NPCBehavior":
					if await j.read_value_from_offset(288, "bool") == True:
						mob = await self.behavior_npc_name(j)
						mob_name = await self.mob_name_parser(mob)
						if final_parse.lower() in mob_name.lower():
							while not await battle.is_fighting():
								await sprinty.tp_to(i)
								await asyncio.sleep(0.2)
							return True


	@logger.catch
	async def tp_to_quest_mob2(self):
		sprinty = SprintyClient(self.client)
		quest_name_path =[ "WorldView", "windowHUD" , "QuestHelperHud", "ElementWindow", "" ,"txtGoalName"]
		quest_name_path = await self.get_window_from_path(self.client.root_window, quest_name_path)
		quest_msg = await quest_name_path.maybe_text()
		ent = await sprinty.get_mobs()
		print("hi")
		print(ent)
		display_list = []
		for i in ent:
			ant = await i.object_template()
			display_key = await ant.display_key()
			print(display_key)
			if len(display_key):
				display_list.append(display_key)
		print(display_list)
		for i in display_list:
			print(await self.client.cache_handler.get_langcode_name(i))
			#name =  await self.client.cache_handler.get_langcode_name(display_key)
			#print(name)
			#mob_name = await self.mob_name_parser(name)
			#if mob_name.lower() in quest_msg.lower():
			#	await sprinty.tp_to(i)

	async def behavior_npc_name(self,behavior):
		return await behavior.read_wide_string_from_offset(120)
				
	async def mob_name_parser(self,behavior):
		#"Ronin Mutineer <image;Myth> Rank 5 Elite"
		unsplit = behavior
		split1 = unsplit.split(" <")
		mob_name = split1[0]
		return mob_name