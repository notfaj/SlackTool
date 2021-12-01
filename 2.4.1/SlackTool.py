import asyncio
import requests
import wget
import wizwalker
from wizwalker import Keycode, HotkeyListener, ModifierKeys, WizWalker, XYZ, utils
from wizwalker.file_readers.wad import Wad
from wizwalker.combat import CombatHandler, CombatMember
from wizwalker.memory.memory_objects.enums import SpellEffects, EffectTarget
from wizwalker.extensions.scripting import teleport_to_friend_from_list
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
from typing import Tuple, Union
import statistics
from wiz_fighter import WizFighter
tool_version = '2.4.1'

def file_len(filepath):
	f = open(filepath, "r")
	return len(f.readlines())

def read_webpage(url):
	response = requests.get(url, allow_redirects=True)
	page_text = response.text
	line_list = page_text.splitlines()
	return line_list

def auto_update(tool_name='SlackTool'):
	if not os.path.exists(f'{tool_name}-config.ini'):
		wget.download(f'https://raw.githubusercontent.com/Slackaduts/{tool_name}/main/{tool_name}-config.ini')
		print('\n')
	elif len(read_webpage(f'https://raw.githubusercontent.com/Slackaduts/{tool_name}/main/{tool_name}-config.ini')) != file_len(f'{tool_name}-config.ini'):
		os.remove(f'{tool_name}-config.ini')
		wget.download(f'https://raw.githubusercontent.com/Slackaduts/{tool_name}/main/{tool_name}-config.ini')
		print('\n')
	if not os.path.exists('README.txt'):
		wget.download('https://raw.githubusercontent.com/Slackaduts/SlackTool/main/README.txt')
		print('\n')
	elif len(read_webpage('https://raw.githubusercontent.com/Slackaduts/SlackTool/main/README.txt')) != file_len('README.txt'):
		os.remove('README.txt')
		wget.download('https://raw.githubusercontent.com/Slackaduts/SlackTool/main/README.txt')
		print('\n')
	local_parser = ConfigParser()
	local_parser.read(f'{tool_name}-config.ini')
	local_version = local_parser.get('version', 'current_version')
	url = f"https://raw.githubusercontent.com/Slackaduts/{tool_name}/main/LatestVersion.txt"
	server_checker = read_webpage(url)
	if server_checker[0] == 'True':
		if local_parser.getboolean('settings', 'auto_updating'):
			latest_version = server_checker[1]
			if tool_version != latest_version:
				if not os.path.exists(f'{tool_name}-copy.exe'):
					os.system(f'copy {tool_name}.exe {tool_name}-copy.exe')
					subprocess.Popen(f'{tool_name}-copy.exe')
					sys.exit()
				else:
					time.sleep(1)
					os.remove(f'{tool_name}.exe')
					print(f'Downloading {tool_name} version {latest_version}.')
					wget.download(f'https://raw.githubusercontent.com/Slackaduts/{tool_name}/main/{latest_version}/{tool_name}.exe')
					version_config = ConfigParser()
					version_config.read(f'{tool_name}-config.ini')
					version_config.set('version', 'current_version', latest_version)
					with open(f'{tool_name}-config.ini', 'w') as updated_config:
						version_config.write(updated_config)
					subprocess.Popen(f'{tool_name}.exe')
					sys.exit()
			else:
				print('\n')
				if os.path.exists(f'{tool_name}-copy.exe'):
					time.sleep(1)
					os.remove(f'{tool_name}-copy.exe')
		else:
			if tool_version != local_version:
				if not os.path.exists(f'{tool_name}-copy.exe'):
					os.system(f'copy {tool_name}.exe {tool_name}-copy.exe')
					subprocess.Popen(f'{tool_name}-copy.exe')
					sys.exit()
				else:
					time.sleep(1)
					os.remove(f'{tool_name}.exe')
					print(f'Downloading {tool_name} version {local_version}.')
					wget.download(f'https://raw.githubusercontent.com/Slackaduts/{tool_name}/main/{local_version}/{tool_name}.exe')
					subprocess.Popen(f'{tool_name}.exe')
					sys.exit()
			else:
				print('\n')
				if os.path.exists(f'{tool_name}-copy.exe'):
					time.sleep(1)
					os.remove(f'{tool_name}-copy.exe')

def generate_timestamp():
	time = str(datetime.datetime.now())
	time_list = time.split('.')
	time_stamp = str(time_list[0])
	time_stamp = time_stamp.replace('/', '-').replace(':', '-')
	return time_stamp

def calc_PointOn3DLine(xyz_1, xyz_2, mod_amount):
	distance = math.sqrt((pow(xyz_1.x - xyz_2.x, 2.0)) + (pow(xyz_1.y - xyz_2.y, 2.0)) + (pow(xyz_1.z - xyz_2.z, 2.0)))
	n = ((distance - mod_amount) / distance)
	return XYZ(x=((xyz_2.x - xyz_1.x) * n) + xyz_1.x, y=((xyz_2.y - xyz_1.y) * n) + xyz_1.y, z=((xyz_2.z - xyz_1.z) * n) + xyz_1.z)

def calc_multiplerPointOn3DLine(xyz_1, xyz_2, multiplier):
	return XYZ(x=((xyz_2.x - xyz_1.x) * multiplier) + xyz_1.x, y=((xyz_2.y - xyz_1.y) * multiplier) + xyz_1.y, z=((xyz_2.z - xyz_1.z) * multiplier) + xyz_1.z)

def calc_MidPoint(xyz_1, xyz_2, distance_multiplier=0.5):
	distance = math.sqrt((pow(xyz_1.x - xyz_2.x, 2.0)) + (pow(xyz_1.y - xyz_2.y, 2.0)) + (pow(xyz_1.z - xyz_2.z, 2.0)))
	n = distance_multiplier
	return XYZ(x=((xyz_2.x - xyz_1.x) * n) + xyz_1.x, y=((xyz_2.y - xyz_1.y) * n) + xyz_1.y, z=((xyz_2.z - xyz_1.z) * n) + xyz_1.z)

def calc_AveragePoint(xyz_list):
	x_list = [x.x for x in xyz_list]
	y_list = [y.y for y in xyz_list]
	z_list = [z.z for z in xyz_list]
	return XYZ(x=(sum(x_list) / len(x_list)), y=(sum(y_list) / len(y_list)), z=(sum(z_list) / len(z_list)))

def rotate_point(origin_xyz, point_xyz, theta):
	radians = math.radians(theta)
	cos = math.cos(radians)
	sin = math.sin(radians)
	y_diff = point_xyz.y - origin_xyz.y
	x_diff = point_xyz.x - origin_xyz.x
	x = cos * x_diff - sin * y_diff + origin_xyz.x
	y = sin * x_diff + cos * y_diff + origin_xyz.y
	return XYZ(x=x, y=y, z=point_xyz.z)

def are_xyzs_within_threshold(xyz_1, xyz_2, threshold=200):
	threshold_check = [abs(abs(xyz_1.x) - abs(xyz_2.x)) < threshold, abs(abs(xyz_1.y) - abs(xyz_2.y)) < threshold, abs(abs(xyz_1.z) - abs(xyz_2.z)) < threshold]
	return all(threshold_check)

def calc_Distance(xyz_1, xyz_2):
	return math.sqrt((pow(xyz_1.x - xyz_2.x, 2.0)) + (pow(xyz_1.y - xyz_2.y, 2.0)) + (pow(xyz_1.z - xyz_2.z, 2.0)))

def calc_squareDistance(xyz_1, xyz_2):
	return (pow(xyz_1.x - xyz_2.x, 2.0)) + (pow(xyz_1.y - xyz_2.y, 2.0)) + (pow(xyz_1.z - xyz_2.z, 2.0))

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

# implemented from https://github.com/PeechezNCreem/navwiz/
# this licence covers the below function
# Boost Software License - Version 1.0 - August 17th, 2003
#
# Permission is hereby granted, free of charge, to any person or organization
# obtaining a copy of the software and accompanying documentation covered by
# this license (the "Software") to use, reproduce, display, distribute,
# execute, and transmit the Software, and to prepare derivative works of the
# Software, and to permit third-parties to whom the Software is furnished to
# do so, all subject to the following:
#
# The copyright notices in the Software and this entire statement, including
# the above license grant, this restriction and the following disclaimer,
# must be included in all copies of the Software, in whole or in part, and
# all derivative works of the Software, unless such copies or derivative
# works are solely in the form of machine-executable object code generated by
# a source language processor.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
# SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
# FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
def parse_nav_data(file_data: Union[bytes, TypedBytes]):
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

async def load_wad(path: str):
	return Wad.from_game_data(path.replace("/", "-"))

async def navmap_tp(client, quest_xyz):
	original_zone_name = await client.zone_name()
	original_position = await client.body.position()
	quest_pos = quest_xyz
	minimum_vertex_distance = 250
	await teleport_move_adjust(client, quest_pos)
	while are_xyzs_within_threshold((await client.body.position()), original_position, 100) and await client.zone_name() == original_zone_name:
		minimum_vertex_distance += 250
		wad = await load_wad(await client.zone_name())
		nav_data = await wad.get_file("zone.nav")
		vertices = []
		vertices, _ = parse_nav_data(nav_data)
		squared_distances = [calc_squareDistance(quest_pos, n) for n in vertices]
		sorted_distances = sorted(squared_distances)
		for s in sorted_distances:
			current_index = sorted_distances.index(s)
			if current_index + 1 < len(sorted_distances):
				vertex = vertices[int(squared_distances.index(sorted_distances[current_index]))]
				next_vertex = vertices[int(squared_distances.index(sorted_distances[current_index + 1]))]
				between_vertices = calc_Distance(vertex, next_vertex)
				quest_to_vertex = calc_Distance(quest_pos, next_vertex)
				if between_vertices >= quest_to_vertex or between_vertices < minimum_vertex_distance:
					pass
				elif between_vertices < quest_to_vertex and between_vertices >= minimum_vertex_distance:
					adjusted_pos = calc_AveragePoint([vertex, next_vertex, quest_pos, quest_pos])
					await teleport_move_adjust(client, XYZ(x=adjusted_pos.x, y=adjusted_pos.y, z=max([quest_pos.z, adjusted_pos.z])))
					break
				else:
					pass
			else:
				break
	if await client.zone_name() == original_zone_name:
		points_on_line = [calc_multiplerPointOn3DLine(xyz_1=(await client.body.position()), xyz_2=quest_pos, multiplier=((i + 1) / 5)) for i in range(3)]
		for p in points_on_line:
			if await client.zone_name() == original_zone_name:
				await client.goto(p.x, p.y)
			else:
				break
		if await client.zone_name() == original_zone_name:
			await client.goto(quest_pos.x, quest_pos.y)

# async def random_realm_switcher(client, realm_page=0, realm_number=0):
# 	async def toggle_realm_menu():
# 		keys = [Keycode.CTRL, Keycode.M]
# 		await asyncio.gather(*[client.send_key(key, ((abs(1 - keys.index(key)) / 5) + 0.1)) for key in keys])
# 		await asyncio.sleep(0.25)
# 	await toggle_realm_menu()
# 	for i in range(5):
# 		try:
# 			await client.mouse_handler.click_window_with_name('btnRealmLeft')
# 	for i in range(realm_page):
# 		await client.mouse_handler.click_window_with_name('btnRealmRight')
# 	await asyncio.sleep(0.1)
# 	await client.mouse_handler.click_window_with_name(f'btnRealm{realm_number}')
# 	await client.mouse_handler.click_window_with_name('btnGoToRealm')

async def calc_up_XYZ(client, wizard_speed_constant=580):
	position = await client.body.position()
	additional_speed = await client.client_object.speed_multiplier()
	new_z = position.z + (wizard_speed_constant * ((additional_speed / 100) + 1))
	return XYZ(x=position.x, y=position.y, z=new_z)

async def calc_FrontalVector(client, xyz):
	wizard_speed_constant = 580
	current_speed = await client.client_object.speed_multiplier()
	additional_distance = (((current_speed / 100) + 1) * wizard_speed_constant)
	yaw = await client.body.yaw()
	new_x = (xyz.x - (additional_distance * math.sin(yaw)))
	new_y = (xyz.y - (additional_distance * math.cos(yaw)))
	new_xyz = XYZ(x=new_x, y=new_y, z=xyz.z)
	distance = calc_Distance(xyz, new_xyz)
	final_xyz = calc_PointOn3DLine(xyz_1=xyz, xyz_2=new_xyz, mod_amount=(additional_distance - distance))
	return final_xyz

async def teleport_move_adjust(client, xyz):
	await client.teleport(xyz)
	await client.send_key(Keycode.A, 0.05)
	await client.send_key(Keycode.D, 0.05)
	await asyncio.sleep(0.8)

async def is_teleport_valid(client, destination_xyz, origin_xyz):
	original_zone_name = await client.zone_name()
	await teleport_move_adjust(destination_xyz)
	if are_xyzs_within_threshold(await client.body.position(), origin_xyz, 50) and await client.zone_name() == original_zone_name:
		return False
	else:
		return True

async def auto_adjusting_teleport(client):
	original_zone_name = await client.zone_name()
	original_position = await client.body.position()
	quest_position = await client.quest_position.position()
	adjusted_position = quest_position
	mod_amount = 50
	current_angle = 0
	await teleport_move_adjust(client, quest_position)
	while are_xyzs_within_threshold((await client.body.position()), original_position, 50) and await client.zone_name() == original_zone_name:
		adjusted_position = calc_PointOn3DLine(original_position, quest_position, mod_amount)
		rotated_position = rotate_point(quest_position, adjusted_position, current_angle)
		await teleport_move_adjust(client, rotated_position)
		mod_amount += 100
		current_angle += 92

# class Spell_Logic(CombatHandler):
# 	async def handle_round(self):
# 		await self.client.mouse_handler.activate_mouseless()
# 		start = time.perf_counter()
# 		cards = await self.get_cards()
# 		end = time.perf_counter()
# 		logger.debug(f"thing took {end - start} seconds to complete")
# 		castable_cards = [c for c in cards if await c.is_castable()]
# 		aoes = [c for c in castable_cards if (await c.type_name()).lower() == 'aoe']
# 		steal_aoes = [c for c in castable_cards if (await c.type_name()).lower() == 'steal']
# 		enchants = await self.get_damage_enchants(sort_by_damage=True)
# 		all_aoes = aoes + steal_aoes
# 		if all_aoes != []:
# 			if not any([(await a.is_item_card() or await a.is_enchanted()) for a in aoes]):
# 				all_aoes = steal_aoes + aoes
# 				if enchants != []:
# 					await enchants[0].cast(all_aoes[0])
# 					cards = await self.get_cards()
# 					castable_cards = [c for c in cards if await c.is_castable()]
# 					aoes = [c for c in castable_cards if (await c.type_name()).lower() == 'aoe']
# 					steal_aoes = [c for c in castable_cards if (await c.type_name()).lower() == 'steal']
# 					all_aoes = steal_aoes + aoes
# 				if all_aoes != []:  
# 					await all_aoes[0].cast(None, sleep_time=0.25, debug_paint=True)
# 			else:
# 				item_card_aoes = [a for a in all_aoes if await a.is_item_card() or await a.is_enchanted()]
# 				if item_card_aoes != []:
# 					await item_card_aoes[0].cast(None, sleep_time=0.25, debug_paint=True)
# 		else:
# 			await self.pass_button()
# 		await self.client.mouse_handler.deactivate_mouseless()

@logger.catch
async def main():
	parser = ConfigParser()
	parser.read('SlackTool-config.ini')
	listener = HotkeyListener()
	allow_combat = False
	speed_enabled = False
	noclip_in_use = False
	forward_noclip_usage = False
	clients_in_background = []
	client_in_foreground = None

	x_press_key = parser.get('hotkeys', 'x_press', fallback='X')
	space_press_key = parser.get('hotkeys', 'spacebar_press', fallback='SPACEBAR')
	sync_locations_key = parser.get('hotkeys', 'sync_client_locations', fallback='F8')
	quest_teleport_key = parser.get('hotkeys', 'quest_teleport', fallback='F7')
	mass_quest_teleport_key = parser.get('hotkeys', 'mass_quest_teleport', fallback='F6')
	toggle_speed_key = parser.get('hotkeys', 'toggle_speed_multiplier', fallback='F5')
	friend_teleport_key = parser.get('hotkeys', 'friend_teleport', fallback='EIGHT')
	kill_tool_key = parser.get('hotkeys', 'kill_slacktool', fallback='F9')
	toggle_auto_combat_key = parser.get('hotkeys', 'toggle_auto_combat', fallback='NINE')
	up_noclip_key = parser.get('hotkeys', 'up_noclip', fallback='ONE')
	forward_noclip_key = parser.get('hotkeys', 'forward_noclip', fallback='TWO')
	noclip_down_key = parser.get('hotkeys', 'down_noclip', fallback='THREE')

	async def x_press():
		logger.debug(f'{x_press_key} key pressed, sending X key press to all clients.')
		await asyncio.gather(*[p.send_key(key=Keycode.X, seconds=0.1) for p in clients_in_background])
		await client_in_foreground.send_key(key=Keycode.X, seconds=0.1)

	async def space_press():
		logger.debug(f'{space_press_key} key pressed, sending spacebar press to all clients.')
		await asyncio.gather(*[p.send_key(key=Keycode.SPACEBAR, seconds=0.1) for p in clients_in_background])
		await client_in_foreground.send_key(key=Keycode.SPACEBAR, seconds=0.1)

	async def sync_locations():
		logger.debug(f'{sync_locations_key} key pressed, syncing client locations.')
		xyz = await client_in_foreground.body.position()
		for p in clients_in_background:
			await p.teleport(xyz)
			await asyncio.sleep(0.15)

	async def teleport_hotkey():
		logger.debug(f'{quest_teleport_key} key pressed, teleporting {client_in_foreground.title} to quest. This may take a while depending on location.')
		await navmap_tp(client_in_foreground, (await client_in_foreground.quest_position.position()))

	async def mass_teleport_hotkey():
		logger.debug(f'{mass_quest_teleport_key} key pressed, teleporting all clients to quests. This may take a while depending on location.')
		list_modes = statistics.multimode([await c.quest_position.position() for c in clients])
		zone_names = [await p.zone_name() for p in clients]
		if len(list_modes) == 1:
			await asyncio.gather(*[navmap_tp(p, list_modes[0]) for p in clients])
		elif zone_names.count(zone_names[0]) == len(zone_names):
			await asyncio.gather(*[navmap_tp(p, (await client_in_foreground.quest_position.position())) for p in clients])
		else:
			await asyncio.gather(*[navmap_tp(p, (await p.quest_position.position())) for p in clients])

	async def enable_speed():
		logger.debug(f'{toggle_speed_key} key pressed, enabling speed multiplier.')
		await asyncio.gather(*[p.client_object.write_speed_multiplier(int(((parser.getfloat('settings', 'speed_multiplier') - 1) * 100))) for p in clients])

	async def disable_speed():
		logger.debug(f'{toggle_speed_key} key pressed, disabling speed multiplier.')
		await asyncio.gather(*[p.client_object.write_speed_multiplier(original_speeds[p]) for p in clients])

	async def toggle_speed():
		nonlocal speed_enabled
		speed_enabled ^= True
		client_speed = await p1.client_object.speed_multiplier()
		if speed_enabled:
			await enable_speed()
		else:
			await disable_speed()

	async def friend_teleport_sync():
		logger.debug(f'{friend_teleport_key} key pressed, friend teleporting all clients to p1.')
		await asyncio.gather(*[p.mouse_handler.activate_mouseless() for p in child_clients])
		await asyncio.sleep(0.25)
		try:
			[await teleport_to_friend_from_list(client=p, icon_list=1, icon_index=50) for p in child_clients]
		except:
			await asyncio.gather(*[p.mouse_handler.deactivate_mouseless() for p in child_clients])
		else:
			await asyncio.gather(*[p.mouse_handler.deactivate_mouseless() for p in child_clients])
		await asyncio.gather(*[p.mouse_handler.deactivate_mouseless() for p in child_clients])

	async def kill_tool():
		await asyncio.sleep(0)
		await asyncio.sleep(0)
		logger.debug(f'{kill_tool_key} key pressed, Killing SlackTool.')
		raise KeyboardInterrupt

	async def toggle_combat():
		nonlocal allow_combat
		allow_combat ^= True
		if allow_combat:
			logger.debug(f'{toggle_auto_combat_key} key pressed, enabling auto combat.')
		else:
			logger.debug(f'{toggle_auto_combat_key} key pressed, disabling auto combat.')

	async def noclip_forward():
		logger.debug(f'{forward_noclip_key} key pressed, noclipping forward.')
		selected_client_position = await client_in_foreground.body.position()
		frontal_xyz = await calc_FrontalVector(client_in_foreground, selected_client_position)
		await client_in_foreground.teleport(xyz=frontal_xyz, move_after=False)

	async def noclip_up():
		logger.debug(f'{up_noclip_key} key pressed, noclipping up.')
		selected_client_position = await client_in_foreground.body.position()
		new_xyz = await calc_up_XYZ(client_in_foreground, wizard_speed_constant=580)
		await client_in_foreground.teleport(new_xyz, move_after=False)

	async def noclip_down():
		logger.debug(f'{noclip_down_key} key pressed, noclipping down.')
		selected_client_position = await client_in_foreground.body.position()
		new_xyz = await calc_up_XYZ(client_in_foreground, wizard_speed_constant=-580)
		await client_in_foreground.teleport(new_xyz, move_after=False)

	async def enable_hotkeys():
		await listener.set_global_message_loop_delay(0)
		await listener.add_hotkey(Keycode[x_press_key], x_press, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[space_press_key], space_press, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[sync_locations_key], sync_locations, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[quest_teleport_key], teleport_hotkey, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[mass_quest_teleport_key], mass_teleport_hotkey, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[toggle_speed_key], toggle_speed, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[friend_teleport_key], friend_teleport_sync, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[kill_tool_key], kill_tool, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[toggle_auto_combat_key], toggle_combat, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[forward_noclip_key], noclip_forward, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[up_noclip_key], noclip_up, modifiers=ModifierKeys.NOREPEAT)
		await listener.add_hotkey(Keycode[noclip_down_key], noclip_down, modifiers=ModifierKeys.NOREPEAT)

	async def disable_hotkeys():
		await listener.remove_hotkey(Keycode[x_press_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[space_press_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[sync_locations_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[quest_teleport_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[mass_quest_teleport_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[toggle_speed_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[friend_teleport_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[kill_tool_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[toggle_auto_combat_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[forward_noclip_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[up_noclip_key], modifiers=ModifierKeys.NOREPEAT)
		await listener.remove_hotkey(Keycode[noclip_down_key], modifiers=ModifierKeys.NOREPEAT)

	async def speed_multiplier_zone_check():
		while True:
			bot_speed_multiplier = parser.getfloat('settings', 'speed_multiplier')
			all_client_zone_names = {}
			for p in clients:
				all_client_zone_names[p] = await p.zone_name()
			await asyncio.sleep(0.55)
			for p in clients:
				if all_client_zone_names[p] != await p.zone_name():
					if await p.client_object.speed_multiplier() != int(((bot_speed_multiplier - 1) * 100)):
						original_speeds[p] = await p.client_object.speed_multiplier()
					if speed_enabled:
						if await p.client_object.speed_multiplier() != int(((bot_speed_multiplier - 1) * 100)):
							await p.client_object.write_speed_multiplier(int(((bot_speed_multiplier - 1) * 100)))
					else:
						if await p.client_object.speed_multiplier() != int(((bot_speed_multiplier - 1) * 100)):
							await p.client_object.write_speed_multiplier(original_speeds[p])
				else:
					if speed_enabled:
						if await p.client_object.speed_multiplier() != int(((bot_speed_multiplier - 1) * 100)):
							await p.client_object.write_speed_multiplier(int(((bot_speed_multiplier - 1) * 100)))

	async def client_foreground_check():
		while True:
			await asyncio.sleep(random.randint(0, len(clients)))
			if sum([c.is_foreground for c in clients]) == 0:
				logger.debug('Client not selected, stopping hotkey listener.')
				await disable_hotkeys()
				while sum([c.is_foreground for c in clients]) == 0:
					await asyncio.sleep(0.1)
				logger.debug('Client selected, starting hotkey listener.')
				await enable_hotkeys()

	async def combat_loop():
		async def async_combat(client):
			while not await CombatHandler(client).in_combat() and allow_combat:
				await asyncio.sleep(1)
			if await CombatHandler(client).in_combat() and allow_combat:
				logger.debug(f'Client {client.title} in combat, handling combat.')
				battle = WizFighter(client, clients)
				await battle.wait_for_combat()
		while True:
			await asyncio.sleep(0.25)
			if allow_combat:
				await asyncio.gather(*[async_combat(p) for p in clients])


	async def client_background_check():
		# i should probably name this something different, I don't really care though
		nonlocal clients_in_background
		nonlocal client_in_foreground
		while True:
			clients_in_background = [c for c in clients if not c.is_foreground]
			clients_in_foreground = [c for c in clients if c.is_foreground]
			if len(clients_in_foreground) != 0:
				client_in_foreground = clients_in_foreground[0]
			await asyncio.sleep(0.1)

	await asyncio.sleep(0)
	listener.start()
	await asyncio.sleep(0)
	await listener.set_global_message_loop_delay(0)
	await asyncio.sleep(0)
	walker = WizWalker()
	clients = walker.get_new_clients()
	clients = walker.get_ordered_clients()
	p1, p2, p3, p4 = [*clients, None, None, None, None][:4]
	child_clients = clients[1:]
	for i, p in enumerate(clients, 1):
		title = 'p' + str(i)
		p.title = title
	print('\n')
	print('SlackTool now has a discord! Join here:')
	print('https://discord.gg/HKY9X7d6pH')
	print('Be sure to join the WizWalker discord, as this project is built using it. Join here:')
	print('https://discord.gg/JHrdCNK')
	print('\n')
	logger.debug(f'Welcome to SlackTool version {tool_version}!')
	logger.debug('Activating hooks, please be patient...')
	await asyncio.gather(*[p.activate_hooks() for p in clients])
	logger.debug('Hooks activated, hotkeys ready!')
	logger.warning('WizFighter in SlackTool is UNSTABLE with certain spells. May not be entirely effective in this version.')
	logger.info('For friend teleports, be sure the clients you want teleported have the one that isnt friended and exclusively set with the purple gem icon.')
	await enable_hotkeys()
	original_speeds = {}
	for p in clients:
		original_speeds[p] = await p.client_object.speed_multiplier()
	try:
		combat_task = asyncio.create_task(combat_loop())
		foreground_check_task = asyncio.create_task(client_foreground_check())
		speed_multiplier_zone_check_task = asyncio.create_task(speed_multiplier_zone_check())
		client_background_check_task = asyncio.create_task(client_background_check())
		while True:
			await asyncio.wait([combat_task, foreground_check_task, speed_multiplier_zone_check_task, client_background_check_task])
			
	finally:
		await asyncio.gather(*[p.client_object.write_speed_multiplier(original_speeds[p]) for p in clients])
		for p in clients:
			p.title = 'Wizard101'
		logger.remove(current_log)
		await listener.stop()
		await walker.close()
		await asyncio.sleep(0)

if __name__ == "__main__":
	auto_update()
	current_log = logger.add(f"logs/SlackTool - {generate_timestamp()}.log", encoding='utf-8', enqueue=True)
	if not os.path.exists(r'C:\Program Files (x86)\Steam\steamapps\common\Wizard101'):
		utils.override_wiz_install_location(r'C:\ProgramData\KingsIsle Entertainment\Wizard101')
	# if not os.path.exists(r'C:\ProgramData\KingsIsle Entertainment\Wizard101'):
	# 	utils.override_wiz_install_location(r'C:\Program Files (x86)\Steam\steamapps\common\Wizard101')
	asyncio.run(main())
