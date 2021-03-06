import time
import html
import asyncio
import random
from traceback import format_exc
from telethon import utils, events, functions, types, errors
from telethon.tl.patched import Message
import follow
try:
    from speedtest import Speedtest
    speedtest_enabled = True
except ImportError:
    speedtest_enabled = False
import config
import helper
import strings
from classes import flags

@helper.register(strings.cmd_help_text)
async def help_text(e):
    clients = e.pattern_match.group(1)
    if clients:
        clients = helper.give_client(helper.give_id(clients))
    else:
        clients = [e.client]
    for client in clients:
        text = helper.give_help(client)
        if config.help_as_file:
            await e.reply(file=helper.memory_file('help.txt', text))
        else:
            await e.reply(text, link_preview=False)

@helper.register(strings.cmd_deactivate, 10)
async def deactivate(e):
    await e.reply(strings.cmd_deactivate_respond)
    helper.active = False

@helper.register(strings.cmd_followers)
async def followers(e):
    await e.reply(await helper.list_followers())

@helper.register(strings.cmd_send, 20)
async def send(e):
    if e.pattern_match.group(1):
        clients = helper.give_client(helper.give_id(e.pattern_match.group(1)))
        if clients is None:
            await e.reply(strings.follow_who.format(e.pattern_match.group(1)))
            return
    else:
        clients = [e.client]
    chat = e.pattern_match.group(2)
    text = e.pattern_match.group(3)
    chat = helper.give_chat(chat, await e.get_chat())
    for client in clients:
        await client.send_message(chat, text)

@helper.register(strings.cmd_join, 30)
async def join(e):
    if e.pattern_match.group(1):
        clients = helper.give_client(helper.give_id(e.pattern_match.group(1)))
        if clients is None:
            await e.reply(strings.follow_who.format(e.pattern_match.group(1)))
            return
    else:
        clients = [e.client]
    chat = e.pattern_match.group(2)
    chat = helper.give_chat(chat, await e.get_chat())
    try:
        invite_info = utils.resolve_invite_link(chat)
    except Exception:
        invite_info = (None, None, None)
    for client in clients:
        if invite_info[0] is None:
            await client(functions.channels.JoinChannelRequest(chat))
        else:
            await client(functions.messages.ImportChatInviteRequest(chat))
        try:
            await e.reply(strings.cmd_join_respond)
        except Exception:
            pass

@helper.register(strings.cmd_leave, 30)
async def leave(e):
    if e.pattern_match.group(1):
        clients = helper.give_client(helper.give_id(e.pattern_match.group(1)))
        if clients is None:
            await e.reply(strings.follow_who.format(e.pattern_match.group(1)))
            return
    else:
        clients = [e.client]
    chat = e.pattern_match.group(2)
    chat = helper.give_chat(chat, await e.get_chat())
    try:
        invite_info = utils.resolve_invite_link(chat)
    except Exception:
        invite_info = (None, None, None)
    for client in clients:
        if invite_info[0] is None:
            await client(functions.channels.LeaveChannelRequest(chat))
        else:
            await client(functions.channels.LeaveChannelRequest(invite_info[1]))
        try:
            await e.reply(strings.cmd_leave_respond)
        except Exception:
            pass

@helper.register(strings.cmd_speedtest, 10)
async def speedtest(e):
    if not speedtest_enabled:
        await e.reply(strings.speedtest_disabled)
        return
    text = strings.cmd_speedtest_processing
    reply = await e.reply(text)
    def _st():
        speedtester = Speedtest()
        speedtester.download()
        return speedtester
    speedtester = await e.client.loop.run_in_executor(None, _st)
    text += strings.cmd_speedtest_upload
    await reply.edit(text)
    def _st(speedtester):
        speedtester.upload()
        url = speedtester.results.share()
        return url
    url = await e.client.loop.run_in_executor(None, _st, speedtester)
    await reply.delete()
    await e.reply(strings.cmd_speedtest_respond, file=url)

@helper.register(strings.cmd_cli, 50)
async def cli(e):
    command = e.pattern_match.group(1)
    stdin = e.pattern_match.group(2)
    output = html.escape(await helper.execute_cli(command, stdin))
    if output:
        await e.reply('<code>' + output + '</code>')
    else:
        await e.reply(strings.cmd_cli_respond)

@helper.register(strings.cmd_notes_add, 10)
async def notes_add(e):
    note = e.pattern_match.group(1)
    content = e.pattern_match.group(2)
    if not content:
        r = await e.get_reply_message()
        if not r:
            await e.reply(strings.reply)
            return
        content = r.text
    helper.db['notes'][note] = content
    if await helper.asave_db(e):
        await e.reply(strings.cmd_notes_add_respond)

@helper.register(strings.cmd_notes_remove, 10)
async def notes_remove(e):
    note = e.pattern_match.group(1)
    try:
        helper.db['notes'].pop(note)
    except KeyError:
        await e.reply(strings.cmd_notes_failed.format(note))
    else:
        if await helper.asave_db(e):
            await e.reply(strings.cmd_notes_remove_respond)

@helper.register(strings.cmd_notes)
async def notes(e):
    note = e.pattern_match.group(1)
    try:
        await e.respond(helper.db['notes'][note], reply_to=e.reply_to_msg_id or e)
    except KeyError:
        await e.reply(strings.cmd_notes_failed.format(note))

@helper.register(strings.cmd_notes_list)
async def notes_list(e):
    n = ', '.join(helper.db['notes'].keys())
    await e.reply(strings.cmd_notes_list_respond.format(n))

@helper.register(strings.cmd_execnotes_add, 50)
async def execnotes_add(e):
    note = e.pattern_match.group(1)
    content = e.pattern_match.group(2)
    if not content:
        r = await e.get_reply_message()
        if not r:
            await e.reply(strings.reply)
            return
        content = html.unescape(r.text)
    helper.db['execnotes'][note] = content
    if await helper.asave_db(e):
        await e.reply(strings.cmd_execnotes_add_respond)

@helper.register(strings.cmd_execnotes_remove, 50)
async def execnotes_remove(e):
    note = e.pattern_match.group(1)
    try:
        helper.db['execnotes'].pop(note)
    except KeyError:
        await e.reply(strings.cmd_execnotes_failed.format(note))
    else:
        if await helper.asave_db(e):
            await e.reply(strings.cmd_execnotes_remove_respond)

@helper.register(strings.cmd_execnotes)
async def execnotes(e):
    note = e.pattern_match.group(1)
    try:
        code = helper.db['execnotes'][note]
    except KeyError:
        await e.reply(strings.cmd_execnotes_failed.format(note))
    else:
        r = await e.reply(strings.cmd_execnotes_processing)
        ret = await helper.run_code(code, e, await e.get_reply_message(), r)
        text = strings.cmd_execnotes_respond
        if ret is not None:
            text = strings.cmd_execnotes_returned.format(html.escape(str(ret)))
        try:
            await r.edit(text)
        except errors.MessageIdInvalidError:
            pass

@helper.register(strings.cmd_execnotes_show)
async def execnotes_show(e):
    note = e.pattern_match.group(1)
    try:
        await e.reply('<code>' + helper.db['execnotes'][note] + '</code>')
    except KeyError:
        await e.reply(strings.cmd_execnotes_failed.format(note))

@helper.register(strings.cmd_execnotes_list)
async def execnotes_list(e):
    execn = ', '.join(helper.db['execnotes'].keys())
    await e.reply(strings.cmd_execnotes_list_respond.format(execn))

@helper.register(strings.cmd_restart, 10)
async def restart(e):
    r = await e.reply(strings.cmd_restart_respond)
    for fwlr in helper.followers:
        if fwlr.client == e.client:
            helper.restart = [str(fwlr.identifier.int_id),
            str(e.chat_id), str(r.id)]
    if e.pattern_match.group(1):
        helper.restart = [['filler data', *helper.restart]]
    follow.mained = True
    helper.active = False

@helper.register(strings.cmd_exec_py, 50)
async def exec_py(e):
    code = e.pattern_match.group(1)
    if not code:
        r = await e.get_reply_message()
        if not r:
            await e.reply(strings.reply)
            return
        code = html.unescape(r.text)
    r = await e.reply(strings.cmd_exec_py_processing)
    ret = await helper.run_code(code, e, await e.get_reply_message(), r)
    text = strings.cmd_exec_py_respond
    if ret is not None:
        text = strings.cmd_exec_py_returned.format(html.escape(str(ret)))
    try:
        await r.edit(text)
    except errors.MessageIdInvalidError:
        pass

@helper.register(strings.cmd_insult)
async def insult(e):
    await e.reply(helper.insult(e.pattern_match.group(1)))

@helper.register(strings.cmd_dcinfo)
async def dcinfo(e):
    if e.pattern_match.group(1):
        clients = helper.give_client(helper.give_id(e.pattern_match.group(1)))
        if not clients:
            await e.reply(strings.follow_who.format(e.pattern_match.group(1)))
            return
    else:
        clients = [e.client]
    for client in clients:
        await e.reply('<code>' +
        (await client(functions.help.GetNearestDcRequest())).stringify() +
        '</code>')

@helper.register(strings.cmd_cas)
async def cas(e):
    r = await e.reply(strings.cmd_cas_processing)
    uid = e.pattern_match.group(1)
    uid = await helper.give_user_id(uid, e.client)
    await r.edit(await helper.check_cas(e.client.loop, uid))

@helper.register(strings.cmd_afk)
async def afk(e):
    helper.afk = e.pattern_match.group(1) or strings.cmd_afk_default
    helper.afk_responses = dict()
    await e.reply(strings.cmd_afk_respond)

@helper.register(strings.cmd_unafk)
async def unafk(e):
    helper.afk = None
    await e.reply(strings.cmd_unafk_respond)

@helper.register(events.NewMessage(incoming=True))
async def respond_to_afk(e):
    if (e.is_private or e.mentioned) and helper.afk:
        try:
            times = helper.afk_responses[e.chat_id]
        except KeyError:
            times = 0
            helper.afk_responses[e.chat_id] = times
        if not times % 5:
            helper.afk_responses[e.chat_id] += 1
            user = await e.get_sender()
            if user.verified or user.bot:
                return
            await e.reply(strings.im_afk.format(helper.afk))

@helper.register(events.NewMessage(incoming=True), flags=flags(True, crawler=True))
@helper.register(events.MessageEdited(incoming=True), flags=flags(True, crawler=True))
async def crawler(e):
    try:
        pattern_match = helper.invite_re.findall(e.text)
    except TypeError:
        return
    for invite in set(pattern_match):
        inv_info = utils.resolve_invite_link(invite)
        if inv_info[1]:
            try:
                chat_info = await e.client(functions.messages.CheckChatInviteRequest(invite))
                if isinstance(chat_info, (types.ChatInviteAlready, types.ChatInvite)):
                    await asyncio.sleep(random.randint(0, 10))
                    await e.client(functions.messages.ImportChatInviteRequest(invite))
                    await e.client.send_message(config.log_chat,
                    strings.crawler_joined.format(invite=invite,
                    user=await e.get_sender(), e=e,
                    sanitised_cid=str(e.chat_id)[4:]))
            except errors.UserAlreadyParticipantError:
                pass
            except Exception:
                fyle = helper.memory_file('exception.txt', format_exc())
                await e.client.send_message(config.log_chat,
                strings.crawler_failed.format(invite=invite),
                file=fyle)

@helper.register(strings.cmd_json)
async def json(e):
    r = await e.get_reply_message()
    if not r:
        r = e
    js = r.to_json()
    await e.reply('<code>' +
    html.escape(str(helper.traverse_json(js, e.pattern_match.group(1)))) +
    '</code>')

@helper.register(events.NewMessage(incoming=True), flags=flags(True, lydia=True))
async def lydia_respond(e):
    if not e.is_private:
        return
    if e.from_id in helper.db['nolydia']:
        return
    if not helper.coffeehouse_enabled:
        return
    if e.from_id in helper.lydia_rate:
        return
    helper.lydia_rate.add(e.from_id)
    chat = await e.get_sender()
    if chat.verified or chat.bot:
        return
    async with e.client.action(e.chat_id, 'typing'):
        session = await helper.give_lydia_session(e.client.loop, e.chat_id)
        respond = await helper.lydia_think(e.client.loop, session, e.text)
        # If lydia is disabled while it's processing,
        if e.from_id in helper.db['nolydia']:
            helper.lydia_rate.remove(e.from_id)
            return
        await e.respond(html.escape(respond), reply_to=None if not e.is_reply else e.id)
    helper.lydia_rate.remove(e.from_id)

@helper.register(strings.cmd_info)
async def info(e):
    async def afc(fwlr):
        if await fwlr.online():
            afc.fwlr_count += 1
    afc.fwlr_count = 0
    await asyncio.wait([
        afc(fwlr)
        for fwlr in helper.followers
    ])
    me = await helper.give_self_id(e)
    for f in helper.followers:
        if f.me.id == me:
            fwlr = f
    await e.reply(strings.cmd_info_respond.format(
    fwlr_count=afc.fwlr_count, fwlr=fwlr, source=strings.source,
    message_count=len(helper.messages)), link_preview=False)

@helper.register(strings.cmd_lydia_enable)
async def lydia_enable(e):
    if not config.lydia_api or not helper.coffeehouse_enabled:
        await e.reply(strings.no_lydia)
        return
    r = await e.get_reply_message()
    if r:
        user = r.from_id
    else:
        user = e.pattern_match.group(1)
        if not user:
            if not e.is_private:
                await e.reply(strings.user_required)
                return
            user = e.chat_id
        else:
            user = await helper.give_user_id(user, e.client)
    if user in helper.db['nolydia']:
        helper.db['nolydia'].remove(user)
        if await helper.asave_db(e):
            await e.reply(strings.cmd_lydia_enable_respond)
    else:
        await e.reply(strings.cmd_lydia_enable_already)

@helper.register(strings.cmd_lydia_disable)
async def lydia_disable(e):
    if not config.lydia_api or not helper.coffeehouse_enabled:
        await e.reply(strings.no_lydia)
        return
    r = await e.get_reply_message()
    if r:
        user = r.from_id
    else:
        user = e.pattern_match.group(1)
        if not user:
            if not e.is_private:
                await e.reply(strings.user_required)
                return
            user = e.chat_id
        else:
            user = await helper.give_user_id(user, e.client)
    if user not in helper.db['nolydia']:
        helper.db['nolydia'].append(user)
        if await helper.asave_db(e):
            await e.reply(strings.cmd_lydia_disable_respond)
    else:
        await e.reply(strings.cmd_lydia_disable_already)

@helper.register(events.NewMessage(pattern=strings.cmd_admin_report, incoming=True),
flags=flags(True, adminreport=True, noerr=True))
@helper.register(events.MessageEdited(pattern=strings.cmd_admin_report, incoming=True),
flags=flags(True, adminreport=True, noerr=True))
async def admin_report(e):
    if e.is_private:
        return
    if e.chat_id == config.log_chat:
#        No recursion please
        return
    reporter = await e.get_sender()
    reporter_name = html.escape(utils.get_display_name(reporter))
    chat = await e.get_chat()
    if not getattr(chat, 'username', None):
        unmark_cid = await e.client.get_peer_id(chat.id, False)
        link = f'https://t.me/c/{unmark_cid}/{e.id}'
    else:
        link = f'https://t.me/{chat.username}/{e.id}'
    if e.is_reply:
        r = await e.get_reply_message()
        try:
            reportee = await r.get_sender()
            reportee_name = html.escape(utils.get_display_name(reportee))
        except AttributeError:
            await e.client.send_message(config.log_chat,
            strings.admin_report_no_reportee.format(
            reporter=reporter, chat=chat, e=e,
            remark=html.escape(str(e.text)), link=link,
            reporter_name=reporter_name),
            link_preview=False)
            return

        await e.client.send_message(config.log_chat, strings.admin_report.format(
        reporter=reporter, reportee=reportee, chat=chat, e=e, r=r,
        remark=html.escape(str(e.text)), link=link,
        reported_message=html.escape(str(r.text)), reporter_name=reporter_name,
        reportee_name=reportee_name), link_preview=False)
    else:
        await e.client.send_message(config.log_chat, strings.admin_report_no_reportee.format(
        reporter=reporter, chat=chat, e=e, remark=html.escape(str(e.text)),
        link=link, reporter_name=reporter_name), link_preview=False)

@helper.register(strings.cmd_brief)
async def brief(e):
    brief_time = e.pattern_match.group(1)
    brief_time = float(brief_time or 1)
    content = e.pattern_match.group(2)
    await e.edit(content)
    await asyncio.sleep(brief_time)
    await e.delete()

@helper.register(events.NewMessage(), flags=flags(True, msgcount=True, noerr=True))
async def message_counter(e):
    helper.messages.add((e.chat_id, e.id))

@helper.register(strings.cmd_ignore_enable)
async def ignore_enable(e):
    r = await e.get_reply_message()
    if r:
        user = r.from_id
    else:
        user = e.pattern_match.group(1)
        if not user:
            if not e.is_private:
                await e.reply(strings.user_required)
                return
            user = e.chat_id
        else:
            user = await helper.give_user_id(user, e.client)
    if user not in helper.db['ignored']:
        helper.db['ignored'].append(user)
        if await helper.asave_db(e):
            await e.reply(strings.cmd_ignore_enable_respond)
    else:
        await e.reply(strings.cmd_ignore_enable_already)

@helper.register(strings.cmd_ignore_disable)
async def ignore_disable(e):
    r = await e.get_reply_message()
    if r:
        user = r.from_id
    else:
        user = e.pattern_match.group(1)
        if not user:
            if not e.is_private:
                await e.reply(strings.user_required)
                return
            user = e.chat_id
        else:
            user = await helper.give_user_id(user, e.client)
    if user in helper.db['ignored']:
        helper.db['ignored'].remove(user)
        if await helper.asave_db(e):
            await e.reply(strings.cmd_ignore_disable_respond)
    else:
        await e.reply(strings.cmd_ignore_disable_already)

@helper.register(events.NewMessage(incoming=True), flags=flags(True, ignore=True))
async def ignore(e):
    if e.is_private or e.mentioned:
        if e.from_id in helper.db['ignored']:
            await e.client.send_read_acknowledge(e.chat_id, e, clear_mentions=True)

@helper.register(events.NewMessage(incoming=True), flags=flags(True, flydia=True))
async def flydia_respond(e):
    if e.is_private or not helper.coffeehouse_enabled or not e.mentioned:
        return
    cid = await e.client.get_peer_id(e.chat_id)
    if e.from_id not in helper.db['flydia'] and cid not in helper.db['flydia']:
        return
    if e.from_id in helper.lydia_rate:
        return
    activator = e.from_id
    if cid in helper.db['flydia']:
        activator = cid
    helper.lydia_rate.add(activator)
    chat = await e.get_sender()
    if chat.verified or chat.bot:
        return
    async with e.client.action(e.chat_id, 'typing'):
        session = await helper.give_lydia_session(e.client.loop, e.chat_id)
        respond = await helper.lydia_think(e.client.loop, session, e.text)
        # If lydia is disabled in groups while it's processing,
        if e.from_id not in helper.db['flydia'] and cid not in helper.db['flydia']:
            helper.lydia_rate.remove(activator)
            return
        await e.respond(html.escape(respond), reply_to=None if not e.is_reply else e.id)
    helper.lydia_rate.remove(activator)

@helper.register(strings.cmd_flydia_enable)
async def flydia_enable(e):
    if not config.lydia_api or not helper.coffeehouse_enabled:
        await e.reply(strings.no_lydia)
        return
    r = await e.get_reply_message()
    if r:
        user = r.from_id
    else:
        user = e.pattern_match.group(1)
        if not user:
            await e.reply(strings.user_required)
            return
        user = await helper.give_user_id(user, e.client)
    if user not in helper.db['flydia']:
        helper.db['flydia'].append(user)
        if await helper.asave_db(e):
            await e.reply(strings.cmd_flydia_enable_respond)
    else:
        await e.reply(strings.cmd_flydia_enable_already)

@helper.register(strings.cmd_flydia_disable)
async def flydia_disable(e):
    if not config.lydia_api or not helper.coffeehouse_enabled:
        await e.reply(strings.no_lydia)
        return
    r = await e.get_reply_message()
    if r:
        user = r.from_id
    else:
        user = e.pattern_match.group(1)
        if not user:
            await e.reply(strings.user_required)
            return
        user = await helper.give_user_id(user, e.client)
    if user in helper.db['flydia']:
        helper.db['flydia'].remove(user)
        if await helper.asave_db(e):
            await e.reply(strings.cmd_flydia_disable_respond)
    else:
        await e.reply(strings.cmd_flydia_disable_already)

@helper.register(strings.cmd_read, 10)
async def read_messages(e):
    quick = e.pattern_match.group(1)
    chat = helper.give_chat(e.pattern_match.group(3), await e.get_chat())
    clients = e.pattern_match.group(2)
    if clients:
        clients = helper.give_client(helper.give_id(clients))
        if not clients:
            await e.reply(strings.follow_who.format(e.pattern_match.group(1)))
            return
    else:
        clients = [e.client]
    async def _read_messages(client, chat):
        await client.send_read_acknowledge(chat, clear_mentions=True)
    if quick:
        await asyncio.wait([
            _read_messages(client, chat)
            for client in clients
        ])
        await e.reply(strings.cmd_read_respond)
    else:
        for client in clients:
            await _read_messages(client, chat)
            await e.reply(strings.cmd_read_respond)

@helper.register(strings.cmd_log)
async def log_messages(e):
    superl = e.pattern_match.group(1)
    silent = e.pattern_match.group(2)
    r = await e.get_reply_message()
    if not r:
        await e.reply(strings.reply)
        return
    if not superl:
        await e.delete()
        await r.forward_to(config.log_chat)
        return
    if silent:
        await e.delete()
    msgs = []
    end = int(e.pattern_match.group(3) or e.id - 1) + 1
    _msgs = await e.client.get_messages(e.chat_id, min_id=r.id-1, max_id=end,
    reverse=True)
    async def _fwd(fwd):
        await e.client.forward_messages(config.log_chat, fwd)
    lf = await e.client.send_message(config.log_chat, strings.cmd_slog_log_from)
    for msg in _msgs:
        if isinstance(msg, Message):
            msgs.append(msg)
        if len(msgs) >= 100:
            await _fwd(msgs)
            msgs.clear()
    if msgs:
        await _fwd(msgs)
    await lf.respond(strings.cmd_slog_log_to)
    cid = await e.client.get_peer_id(lf.chat_id, False)
    link = f'https://t.me/c/{cid}/{lf.id}'
    if not silent:
        await e.reply(strings.cmd_slog_respond.format(link))

@helper.register(strings.cmd_stickertext)
async def stickertext(e):
    r = await e.get_reply_message()
    if not r:
        await e.reply(strings.reply)
        return
    if not r.sticker:
        await e.reply(strings.cmd_stickertext_sticker)
        return
    await r.respond(e.pattern_match.group(1), file=r.media)
    msgs = {e.id}
    if r.out:
        msgs.add(r.id)
    await e.client.delete_messages(e.chat_id, msgs)

@helper.register(strings.cmd_selfpurge)
async def selfpurge(e):
    async def _purge(msgs):
        await e.client.delete_messages(e.chat_id, msgs)
    _msgs = {e.id}
    rid = e.reply_to_msg_id
    mid = e.pattern_match.group(1)
    try:
        amount = int(mid or rid)
    except TypeError:
        await e.reply(strings.reply)
        return
    if mid:
        msgs = await e.client.get_messages(e.chat_id, limit=amount, from_user='me',
        max_id=e.id)
    elif rid:
        msgs = await e.client.get_messages(e.chat_id, min_id=amount-1, from_user='me',
        max_id=e.id)
    for msg in msgs:
        _msgs.add(msg.id)
    if _msgs:
        await _purge(_msgs)

@helper.register(strings.cmd_user_link)
async def user_link(e):
    r = await e.get_reply_message()
    if not r:
        user_id = e.pattern_match.group(1)
        if not user_id:
            await e.reply(strings.reply)
            return
        user_id = await helper.give_user_id(user_id, e.client)
    else:
        user_id = r.from_id
        if r.fwd_from:
            user_id = r.fwd_from.from_id
    link = f'tg://user?id={user_id}'
    await e.reply(strings.cmd_user_link_respond.format(link=link, user_id=user_id))

@helper.register(strings.cmd_ping)
async def ping(e):
    s = time.time()
    z = await e.reply(strings.cmd_ping_respond)
    e = time.time()
    s = s * 1000 - int(s)
    e = e * 1000 - int(e)
    await z.edit(strings.cmd_pong_respond.format(int(e - s)))

@helper.register(strings.cmd_admins)
async def admins(e):
    mention = e.pattern_match.group(1)
    chat = e.pattern_match.group(2) or e.chat_id
    chat = await helper.give_user_id(helper.give_chat(chat, await e.get_chat()), e.client)
    chat_admins = await e.client.get_participants(chat,
    filter=types.ChannelParticipantsAdmins())
    text = strings.cmd_admins_respond
    for admin in chat_admins:
        if not admin.bot and not admin.deleted:
            aname = html.escape(utils.get_display_name(admin))
            text += strings.cmd_admins_sub.format(admin=admin, aname=aname)
    mtext = strings.cmd_admins_respond
    for admin in chat_admins:
        if not admin.bot and not admin.deleted:
            aname = html.escape(utils.get_display_name(admin))
            mtext += strings.cmd_admins_msub.format(admin=admin, aname=aname)
    if mention:
        await e.reply(mtext)
        return
    z = await e.reply(text)
    if text != mtext:
        await z.edit(mtext)

@helper.register(strings.cmd_purge)
async def purge(e):
    async def _purge(msgs):
        await e.client.delete_messages(e.chat_id, msgs)
    _msgs = {e.id}
    rid = e.reply_to_msg_id
    mid = e.pattern_match.group(1)
    try:
        amount = int(mid or rid)
    except TypeError:
        await e.reply(strings.reply)
        return
    if mid:
        msgs = await e.client.get_messages(e.chat_id, limit=amount, max_id=e.id)
    elif rid:
        msgs = await e.client.get_messages(e.chat_id, min_id=amount-1, max_id=e.id)
    for msg in msgs:
        _msgs.add(msg.id)
    if _msgs:
        await _purge(_msgs)

@helper.register(strings.cmd_delete)
async def delete(e):
    rid = e.reply_to_msg_id
    if not rid:
        rid = (await e.client.get_messages(e.chat_id, limit=1, from_user='me', max_id=e.id))[0].id
    await e.client.delete_messages(e.chat_id, {e.id, rid})

@helper.register(strings.cmd_edit)
async def edit(e):
    await e.delete()
    r = None
    rid = e.reply_to_msg_id
    if not rid:
        r = (await e.client.get_messages(e.chat_id, limit=1, from_user='me', max_id=e.id))[0]
        rid = r.id
    text = e.pattern_match.group(1)
    if not text:
        if not r:
            r = await e.client.get_messages(e.chat_id, ids=rid)
        text = strings.cmd_edit_draft.format(r.text)
        await e.client(functions.messages.SaveDraftRequest(e.chat_id, text, reply_to_msg_id=rid))
        return
    await e.client.edit_message(e.chat_id, rid, text)

@helper.register(events.ChatAction, flags=flags(True, noerr=True, logadded=True))
async def logadded(e):
    if (not e.user_added) and (not e.created):
        return
    me = await e.client.get_peer_id('me')
    if e.added_by == me:
        return
    a = e.action_message
    if not e.created:
        if me not in a.action.users:
            return
    chat = await e.client.get_entity(utils.get_peer_id(a.to_id))
#    print(a.stringify())
    adder = await e.client.get_entity(a.from_id)
    adder_name = utils.get_display_name(adder)
    text = strings.logadded_text.format(e=e, chat=chat, adder=adder, adder_name=adder_name)
    await e.client.send_message(config.log_chat, text)
