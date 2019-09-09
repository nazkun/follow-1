import asyncio
import logging
from telethon import TelegramClient
import config
import classes
logging.basicConfig(
format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
level=logging.INFO)

clients = logging.getLogger('clients')

async def main():
	print('''Welcome! Please input your API ID and Hash.
What is an API ID/Hash?
i cannot bother explaining, and for what?

How do I get them?
Go to https://me.telegram.org
Log in
'API Development Tools'
Enter anything you like for Application Name and Short Name and Platform
There you go :)

**DON"T SHARE YOUR API HASH TO ANYONE**''')
	api_id = int(input('API ID: '))
	api_hash = input('API Hash: ')
	fwlrs = []
	for i in config.followers:
		clients.info('Testing client %s, if it asks for your phone number please login', i.name)
		client = TelegramClient(i.session_path, api_id, api_hash, base_logger=i.name)
		await client.start()
		fwlrs.append(client)
	await asyncio.wait([
		client.disconnect()
		for client in fwlrs
	])

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(main())
	except KeyboardInterrupt:
		print()
