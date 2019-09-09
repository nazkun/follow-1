## follow

2nd (that I know of) open-source multi client Telegram Userbot ([friendly-tg](https://github.com/friendly-tg/friendly-tg) beat me)

## DISCLAIMER

Used this userbot to spam in chats (or something) and now most of your alts deleted?
1. Well we now have something in common.
2. Don't blame me, blame yourself.
3. If you still blame me, we'll both cry ;_;

### Table of Contents

- [Installation](#installation)
- [Features](#features)
- [FAQn't](#faqnt)
- [Credits](#credits)

### Installation

- `git clone https://gitlab.com/blankX/follow`
- `cd follow`
- Copy `sample.config.py` to `config.py` (`cp sample.config.py config.py`)
- Edit `config.py` (`nano config.py`)
- Install dependencies (`pip3 install -r requirements.txt`)
- You can also install the optional ones if you like (`pip3 install -r optional.txt`)
- Get the followers/sessions ready
  - Add your followers/sessions to `followers/` (or anywhere else you put them, I don't care)
  - `python3 sessions.py`
- Start the bot (`python3 follow.py`)

### Features

Just send `follow help` in a chat  
FYI, it'll only show features the follower can do (based on trust level).  
So do it on an infinity trust level follower.

### FAQn't

##### How to run in Heroku?

Boi, this is gonna be hard.

- Fork this repo (private please)
- Follow the [installation steps](#installation) (pull your repo instead of mine)
- Create a file named `Procfile` with the contents `app: python3 follow.py`
- Login to Heroku
- New App
- Push to Heroku  
You might find that the database (very amazing DB I know) is periodically cleared.  
Heroku restarts your dyno at least once per day (and deletes files).

##### how run???

Get out.

##### Why not use an actual database?

1. I'm too lazy
2. I don't fucking know actual databases.

##### you cursed, i triggered

Read this book called 'Why swearing is good for you'  
I give it a 10/10.  
Because it's like literally the only book I read (except for school)

##### SELLOUT!!1

[...](#how-run)

##### What's this 'auto recovery'?

It (tries to) auto recovers itself (aka calling `await client.get_me()` every minute)  
Why? I host it on my phone, which, if you don't know already, isn't a very reliable hosting solution.

##### Why does speedtest do blocking calls?

I tried to make it async, but it wouldn't show results if I did D:

##### I don't like this certain string.

Then change it!  
Most strings are in `strings.py`, so you can just edit that.

##### How'd I change the source code location?

[I don't like this certain string.](#i-dont-like-this-certain-string)

##### Why's the name 'FAQn't'?

I just released this userbot, you expect it to blow up seconds after pushing?  
Also, I don't expect it to get big.

##### What's with these random parts in the FAQn't?

1. To try to make you laugh (which doesn't seem to make you laugh)
2. Come on, I gotta shitpost in READMEs

##### Why MIT and not GPL?

[Too lazy to sue people.](https://t.me/UserbotSpamChat/121)

##### Ew, you use tabs instead of spaces.

1. It's easier to navigate
2. If you don't like it, create follow-notabs
3. Can we stop the Tabs vs. Spaces war now?

##### Support chat?

As I said in [Why's the name 'FAQn't'?](#whys-the-name-faqnt), I don't expect it to get big.  
So I guess [The Unity Chat](https://t.me/TheUnityChat) works. 

### Credits

Thanks to:
- [lonami](https://lonami.dev) for creating [Telethon](https://github.com/lonamiwebs/Telethon)
- [twitface](https://t.me/twitface) for:
  - Giving his old exec code (it's old but... still works nicely)
  - [dunno what to say for this one](https://t.me/UserbotTestingSpam/581584)
  - Making me paranoid to include trust levels
- [Intellivoid](https://intellivoid.info) for Coffeehouse/Lydia
- [Hackintosh](https://t.me/hackintosh5) for the `loop.run_in_executor` code
- (omg im gonna so cringe)  
  The Adventure Time episodes Preboot and Reboot (instant cringe) for inspiring me to make the userbot (imma stop writing before i cringe more
