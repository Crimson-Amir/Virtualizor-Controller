from utilities import handle_error, replace_with_space, report_problem_to_admin, human_readable, unix_time_to_datetime
import requests
from datetime import datetime
from database import create_database
create_database('virtualizor')
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters,
                          CallbackQueryHandler)
from private import telegram_bot_token, ADMIN_CHAT_ID
from sqlite_manager import ManageDb
import pytz

check_every_min = 30
END_POINT, API_KEY, API_PASS = range(3)

bandwidth_notification_text = '🔔 [bandWidth Notification] You have consumed {0}% of virtual server {1} bandwidth!\nRemaining traffic: {2} GB'
period_notification_text = '🔔 [Period Notification] {0} days have passed since the registration of virtual server {1}'

sqlite_manager = ManageDb('virtualizor')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def sort_data(json_file, special_vps=None, get_detail=False, get_vs_usage_detail=False):
    final_lines, vps_name, usage_detail, vps_info = [], [], {}, []

    for vps_id, vps_data in json_file.get('vs', {}).items():
        if special_vps and str(special_vps) != vps_id: continue
        final_lines.append(f'\nvirtual server {vps_id}:')
        vps_name.append(vps_id)

        registare_time = unix_time_to_datetime(int(vps_data.get('time')))
        used_band = float(vps_data.get("used_bandwidth"))
        total_band = float(vps_data.get("bandwidth"))
        band_precent = round((used_band / total_band) * 100, 2)
        time_difference = datetime.now(pytz.timezone('Asia/Tehran')) - registare_time
        left_band = round(total_band - used_band, 2)

        if get_vs_usage_detail:
            usage_detail[vps_id] = {'bandwidth_left': band_precent, 'registare_to_now': time_difference.days, 'left_band': left_band}
        elif get_detail:
            vps_info = [f'{replace_with_space(key)} : {values}' for key, values in vps_data.items()]
        else:
            detail = (f'\nHost Name: {vps_data.get("hostname")}'
                      f'\nBand Width: {used_band}/{total_band} GB ({band_precent}%)'
                      f'\nLeft BandWidth: {left_band} GB'
                      f'\nRegistration: {registare_time} ({human_readable(registare_time)} - {time_difference.days} day)'
                      f'\nOS Name: {vps_data.get("os_name")}'
                      f'\nOS Distro: {vps_data.get("os_distro")}'
                      f'\nCPU Cores: {vps_data.get("cores")}'
                      f'\nNetwork Speed: {vps_data.get("network_speed")}'
                      f'\nRam: {vps_data.get("ram")}'
                      f'\nSpace: {vps_data.get("space")} GB'
                      f'\nIPs: {", ".join(vps_data.get("ips").values())}')
            vps_info = [detail]

        final_lines.extend(vps_info)

    final_lines.extend(["\n\n• Select the desired VS to view details ⤵"])
    return '\n'.join(final_lines), vps_name, usage_detail


def get_result_from_api(end_point, api_key, api_pass, act='listvs', special_vps=None, get_detail=False, get_vs_usage_detail=False):

    url = f"{end_point}/index.php"
    params = {
        'act': act,
        'api': 'json',
        'apikey': api_key,
        'apipass': api_pass
    }

    try:
        with requests.get(url, params=params, verify=False, timeout=5) as response:
            if response.ok:
                connection_response_json = response.json()
                connection_response = sort_data(connection_response_json, special_vps=special_vps, get_detail=get_detail, get_vs_usage_detail=get_vs_usage_detail)
                logging.info('connect Success!')
                return 'OK', *connection_response
            else:
                logging.info('connect Failed!')
                return f'error code {response.status_code}', response, [], []


    except Exception as e:
        report_problem_to_admin(f'Error In func [get_result_from_api]\nerror Type:{type(e)}\nreason: {str(e)}')
        return f'exception error {type(e)}', [], []


@handle_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    date = datetime.now()
    get_user_detail_from_db = sqlite_manager.select(table='User', where=f'chat_id={user_detail.id}')

    if not get_user_detail_from_db:
        start_text_notif = (f"New Start Bot In <B>{update.message.chat.type}</B>\n\nName: {user_detail['first_name']}\n"
                            f"UserName: @{user_detail['username']}\nID: <a href=\"tg://user?id={user_detail['id']}\">{user_detail['id']}</a>"
                            f"\nDate: {date}")

        context.bot.send_message(ADMIN_CHAT_ID, text=start_text_notif, parse_mode="HTML")
        sqlite_manager.insert('User', rows={'name': user_detail.first_name, 'chat_id': user_detail.id, 'date': date})

    text = '<b>Hi, you can connect your Virtualizor account through the button below:</b>'
    keyboard = [[InlineKeyboardButton('Add Account ➕', callback_data='add_account')],
                [InlineKeyboardButton('My Virtual Server', callback_data='main_menu')]]
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


@handle_error
async def add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.callback_query.answer()
    text = '<b>OK, send me Virtualizor address.\nExample:</b> http://532.632.151.43:4083'
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return END_POINT


@handle_error
async def get_end_point_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['end_point'] = update.message.text
    text = ("<b>Got it! Now i need you'r Api Key.\n\nif you don't have it, following the steps below:\n"
            "then click on your profile on the top right,\nclick on 'API Credentials' and create a new api,\n"
            "you don't need to fill in the ip for the whitelist.\nNow you get api key and api pass,\nEnter your api key.</b>")
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return API_KEY

@handle_error
async def get_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['api_key'] = update.message.text
    text = "<b>excellent! Now send the Api Pass that you got in the previous step.</b>"
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return API_PASS


@handle_error
async def get_api_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    api_pass = update.message.text
    api_key = context.user_data['api_key']
    end_point = context.user_data['end_point']

    get_result = get_result_from_api(end_point, api_key, api_pass)

    if get_result[0] == 'OK':
        keyboard = [[InlineKeyboardButton(f'virtual server {vs}', callback_data=vs)] for vs in get_result[2]]
        text = f"<b>Done! You can view your account details:\n\n{get_result[1]}</b>"

        sqlite_manager.insert(table='API_DETAIL',
                              rows={'api_key': api_key, 'api_pass': api_pass, 'end_point': end_point,
                                    'date': datetime.now(), 'chat_id': chat_id})

    else:
        keyboard = [[InlineKeyboardButton(f'Main Menu', callback_data='main_menu')]]
        text = f"<b>sorry, somthing went wrong!</b>"

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_account, pattern=r'add_account')],
    states={
        END_POINT: [MessageHandler(filters.TEXT, get_end_point_from_user)],
        API_KEY: [MessageHandler(filters.TEXT, get_api_key)],
        API_PASS: [MessageHandler(filters.TEXT, get_api_pass)],
    },
    fallbacks=[],
    per_chat=True,
    allow_reentry=True,
    conversation_timeout=1500,
)


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = update.callback_query
    data = query.data
    get_pattern = data.replace('main_menu', '')
    await query.answer()

    special_vps = get_pattern if get_pattern else None
    get_detail = bool(get_pattern)

    text = "• "
    get_data = sqlite_manager.select(table='API_DETAIL', where=f'chat_id = {chat_id}')
    keyboard = [[InlineKeyboardButton('Refresh ↻', callback_data='main_menu')]]

    if not get_data:
        text += '\nNo server found!'
        keyboard.extend([[InlineKeyboardButton('Add Account ➕', callback_data='add_account')]])

    api_data = [(data[2], data[3], data[4]) for data in get_data]

    for end_point, api_key, api_pass in api_data:
        get_result = get_result_from_api(end_point, api_key, api_pass, special_vps=special_vps, get_detail=get_detail)

        if get_result[0] == 'OK':
            keyboard.extend([[InlineKeyboardButton(f'virtual server {vs}', callback_data=f'main_menu{vs}')] for vs in get_result[2]])
            text += f"{get_result[1]}"
        else:
            keyboard.append([InlineKeyboardButton('Main Menu', callback_data='main_menu')])
            text += "<b>sorry, something went wrong!</b>"

    if get_pattern:
        keyboard = [[InlineKeyboardButton('Main Menu', callback_data='main_menu')]]

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html',
                                   reply_markup=InlineKeyboardMarkup(keyboard))


async def notification_job(context: ContextTypes.DEFAULT_TYPE):
    get_all_api = sqlite_manager.select(table='API_DETAIL')
    get_all_notification = sqlite_manager.select(table='VS_NOTIFICATION')
    get_notification_setting = sqlite_manager.select(column='chat_id,notification_band,notification_day', table='User')

    api_data = [(data[1], data[2], data[3], data[4]) for data in get_all_api]

    for chat_id, end_point, api_key, api_pass in api_data:

        get_user_notif_setting = [(search[1], search[2]) for search in get_notification_setting if search[0] == chat_id]
        bandwidth_notification_precent = get_user_notif_setting[0][0]
        period_notification_day = get_user_notif_setting[0][1]

        get_result = get_result_from_api(end_point, api_key, api_pass, get_vs_usage_detail=True)
        if get_result[0] == 'OK':
            for vs_id, details in get_result[3].items():
                check_notif = [(search[3], search[4]) for search in get_all_notification if search[2] == chat_id and search[1] == int(vs_id)]

                if not check_notif:
                    sqlite_manager.insert('VS_NOTIFICATION', {'vps_id': int(vs_id) ,'chat_id': chat_id, 'notification_band': 0, 'notification_day': 0, 'date': datetime.now()})
                    check_notif = [(0, 0)]

                bandwidth_precent = details.get('bandwidth_left')
                registare_to_now = details.get('registare_to_now')
                left_band = details.get('left_band')

                if bandwidth_precent >= bandwidth_notification_precent and not check_notif[0][0]:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 1}}, where=f'vps_id = {vs_id}')
                    text = bandwidth_notification_text.format(bandwidth_precent, vs_id, left_band)
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][0] and bandwidth_precent < bandwidth_notification_precent:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 0}}, where=f'vps_id = {vs_id}')

                if registare_to_now >= period_notification_day and not check_notif[0][1]:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_day': 1}}, where=f'vps_id = {vs_id}')
                    text = period_notification_text.format(registare_to_now, vs_id)
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][1] and registare_to_now < period_notification_day:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_day': 0}}, where=f'vps_id = {vs_id}')

@handle_error
async def set_bandwith_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_precent = int(context.args[0])
    if get_precent <= 0 or get_precent > 100:
        raise ValueError('precent higher or lighter 0 and 100')
    chat_id = update.effective_chat.id

    sqlite_manager.update({'User': {'notification_band': get_precent}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 0}}, where=f'chat_id = {chat_id}')

    await context.bot.send_message(text='Notification Setting Changed successfully!', chat_id=chat_id)


@handle_error
async def set_period_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_day = int(context.args[0])
    if get_day <= 0:
        raise ValueError('day lighter than 0')
    chat_id = update.effective_chat.id

    sqlite_manager.update({'User': {'notification_day': get_day}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_day': 0}}, where=f'chat_id = {chat_id}')

    await context.bot.send_message(text='Notification Setting Changed successfully!', chat_id=chat_id)


@handle_error
async def clear_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 0, 'notification_day': 0}}, where=f'chat_id = {chat_id}')
    await context.bot.send_message(text='Notification Clear successfully!', chat_id=chat_id)


if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('set_bandwith_notification', set_bandwith_notification))
    application.add_handler(CommandHandler('set_period_notification', set_period_notification))
    application.add_handler(CommandHandler('clear_notification', clear_notification))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(main_menu, 'main_menu'))
    application.job_queue.run_repeating(notification_job, interval=check_every_min * 60, first=0)
    application.run_polling()

