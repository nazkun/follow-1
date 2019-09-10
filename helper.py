import functools
import subprocess
import asyncio
import logging
import random
import time
import html
import json
import sys
import re
from traceback import format_exc
from io import BytesIO
import requests
try:
	from coffeehouse import API
	from coffeehouse.exception import SessionInvalidError, SessionNotFoundError
	coffeehouse_enabled = True
except ImportError:
	coffeehouse_enabled = False
from telethon import events
try:
	import aiocron
	aiocron_enabled = True
except ImportError:
	aiocron_enabled = False
import strings
import config
import classes
logging.basicConfig(
format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
level=logging.INFO)

invite_re = re.compile(
r'(?:(?:telegram\.(?:org|me|dog)|t\.me)/joinchat|feed|join|crawl)/([a-z0-9\-_]{22})',
re.IGNORECASE)

recovering = [False, 0]
followers = []
active = True
afk = None
afk_responses = {}
blank_space = '\u200b'
handlers = []
restart = []
lydia_sessions = {}
try:
	with open('db.json') as fyle:
		db = json.load(fyle)
except Exception:
	db = {'version': 1, 'notes': {}, 'execnotes': {}, 'nolydia': []}
with open('insults.txt', encoding='utf-8') as fyle:
	insults = fyle.readlines()
modules = logging.getLogger('modules')
autorec = logging.getLogger('autorecover')

if getattr(config, 'lydia_api', None):
	_ch = API(config.lydia_api)
	async def give_lydia_session(loop, user):
		def _give_lydia_session(user):
			def _new_lydia_session():
				return _ch.create_session()
			if user in lydia_sessions.keys():
				try:
					current_time = time.time()
					expire_time = lydia_sessions[user].expires
					if expire_time > current_time:
						lydia_sessions[user] = _ch.get_session(lydia_sessions[user])
					else:
						raise SessionInvalidError
				except (SessionInvalidError, SessionNotFoundError):
					lydia_sessions[user] = _new_lydia_session()
			else:
					lydia_sessions[user] = _new_lydia_session()
			return lydia_sessions[user]
#		Thanks to Hackintosh (httpa://t.me/hackintosh5) for `loop.run_in_executor` code
		fut = loop.run_in_executor(None, _give_lydia_session, user)
		return await fut
	async def lydia_think(loop, session, text):
		def _lydia_think(session, text):
			return session.think_thought(text or 'hi')
		fut = loop.run_in_executor(None, _lydia_think, session, text)
		return await fut
if not coffeehouse_enabled:
	config.lydia_api = None

async def list_followers():
	text = ''
	fwlrs = []
	async def isfo(fwlr):
		if await fwlr[1].online():
			fwlrs.append(fwlr)
	await asyncio.wait([
		isfo(fwlr)
		for fwlr in enumerate(followers)
	])
	for f in enumerate(followers):
		for ff in fwlrs:
			if ff[0] == f[0]:
				fwlr = f[1]
				text += html.escape(
				strings.cmd_followers_sub.format(
				num=fwlr.identifier.int_id,
				name=fwlr.identifier.name,
				trust=fwlr.identifier.trust))
	return strings.cmd_followers_respond.format(text)

def give_chat(chat, original_chat):
	if chat == strings.here_chat:
		if original_chat.username:
			return original_chat.username
		return original_chat.id
	for chat_name in config.internal_chat_names:
		if chat_name == chat:
			return chat_name.actual_chat
	try:
		return int(chat)
	except ValueError:
		return chat

def give_id(ids_text):
	ids = []
	if ids_text == strings.all_followers:
		for fwlr in followers:
			if not fwlr.identifier.flags.noall:
				ids.append(fwlr.identifier.int_id)
		return ids
	ids_array = ids_text.split(strings.ids_seperator)
	for internal_id in ids_array:
		try:
			internal_id = int(internal_id)
			for fwlr in followers:
				if fwlr == internal_id:
					ids.append(internal_id)
		except ValueError:
			for fwlr in followers:
				if fwlr.identifier.name == internal_id:
					ids.append(fwlr.identifier.int_id)
	if ids:
		return ids
	return None

def give_client(ids_array):
	if ids_array is None:
		return None
	clients = []
	for internal_id in ids_array:
		for fwlr in followers:
			if fwlr == internal_id:
				clients.append(fwlr.client)
	if clients:
		return clients
	return None

def give_help(you):
	help_text = ''
	for handler in [i[0] for i in you.list_event_handlers()]:
		if handler.doc:
			help_text += handler.doc
	return help_text.expandtabs()

def execute_cli(command):
	command = command.split(' ')
	try:
		output = subprocess.check_output(command,
		universal_newlines=True, stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as error:
		output = error.output
	return output

def memory_file(file_name, file_content):
	fyle = BytesIO()
	fyle.name = file_name
	if isinstance(file_content, str):
		if config.windows_newlines:
			file_content = convert_windows_newlines(file_content)
		file_content = bytes(file_content, 'utf-8')
	fyle.write(file_content)
	fyle.seek(0)
	return fyle

def register(pattern, trust=-float('inf'), doc=None, flags=classes.flags()):
	def decorator(func):
		global handlers
		func.__trust__ = trust
		if not doc:
			func.doc = getattr(strings, 'cmd_'+func.__name__+'_help', None)
		else:
			func.doc = doc
		func.flags = flags
		if not func.doc:
			modules.warning('%s does not have a doc string.', func.__name__)
		if not isinstance(pattern, str):
			event_to_listen = pattern
		else:
			event_to_listen = events.NewMessage(pattern=pattern, outgoing=True)
		@events.register(event_to_listen)
		@functools.wraps(func)
		async def async_wrapper(e):
			try:
				await func(e)
			except Exception:
				fyle = memory_file('exception.txt', format_exc())
				try:
					if func.flags.noerr:
						raise Exception
					me = await give_self_id(e)
					for fwlr in followers:
						if fwlr.me.id == me:
							if fwlr.identifier.flags.noerr:
								raise Exception
					await e.reply(file=fyle)
				except Exception:
					await e.client.send_message(config.log_chat, file=fyle)
		handlers.append(async_wrapper)
		messy_handlers = [[handler.__name__, handler] for handler in handlers]
		handlers = [handler[1] for handler in sorted(messy_handlers)]
		modules.info('Loaded %s', func.__name__)
		return async_wrapper
	return decorator

def save_db():
	global db
	db = json.loads(json.dumps(db, sort_keys=True))
	with open('db.json', 'w+') as fyle:
		json.dump(db, fyle, indent=4)

async def show_restarted():
	if len(sys.argv) == 4:
		try:
			client = give_client(give_id(sys.argv[1]))[0]
			await client.edit_message(int(sys.argv[2]),
			int(sys.argv[3]), strings.cmd_restart_restarted)
		except Exception:
			logging.error('Failed to show restart')
			print(format_exc())

def insult(name):
	return re.sub('##name##', name, random.choice(insults))

def check_cas(user_id):
	user_id = int(user_id)
	response = requests.get('https://combot.org/api/cas/check?user_id={}'.format(user_id))
	js_response = json.loads(response.text)
	if not js_response['ok']:
		return js_response['description']
	return strings.cmd_cas_respond.format(user_id=user_id, offenses=js_response['result']['offenses'])

async def auto_recover():
	global recovering
	autorec.info('Auto-recovery engaged. Recoveries: %s', str(recovering[1]))
	if recovering[0]:
		autorec.warning('A recovery is on-going')
		autorec.info('Auto-recovery disengaged. Recoveries: %s', str(recovering[1]))
		return
	recovering[0] = True
	recovering[1] += 0.5
	async def internal_recover(fwlr):
		autorec.info('Recovering: %s', fwlr.identifier.name)
		try:
			followers[fwlr.enu].me = await fwlr.client.get_me()
			autorec.info('%s recovered.', fwlr.identifier.name)
		except Exception:
			autorec.error('Got exception')
			print(format_exc())
	await asyncio.wait([
		internal_recover(fwlr)
		for fwlr in followers
	])
	recovering[0] = False
	recovering[1] += 0.5
	recovering[1] = int(recovering[1])
	autorec.info('Auto-recovery disengaged. Recoveries: %s', str(recovering[1]))

if not getattr(config, 'dont_cron', False):
	if aiocron_enabled:
		auto_recover = aiocron.crontab('* * * * *', start=False, func=auto_recover)

def traverse_json(json_to_be_traversed, traverse_path):
	js = json_to_be_traversed
	if isinstance(js, str):
		js = json.loads(js)
	if not traverse_path:
		return json.dumps(js, indent=2, sort_keys=True)
	for traverse in traverse_path.split(strings.traverse_seperator):
		js = js[traverse]
	return json.dumps(js, indent=2, sort_keys=True) if isinstance(js, dict) else js

def convert_windows_newlines(text):
	return re.sub('\n', '\r\n', text)

async def give_self_id(e):
	me = e.from_id
	if me:
		return me
	try:
		return (await e.client.get_input_entity('me')).user_id
	except Exception:
		return (await e.client.get_me()).id
