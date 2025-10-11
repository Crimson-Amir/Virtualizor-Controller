import asyncio
from utilities import handle_error
from datetime import datetime
from database import create_database
create_database('virtualizor')
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters,
                          CallbackQueryHandler)
from private import telegram_bot_token, ADMIN_CHAT_ID
from sqlite_manager import ManageDb
from virtualizorApi import run as virtualizor_run
from solusvmApi import run as solusvm_run


check_every_min = 10

# Virtualizor conversation states
VIRT_END_POINT, VIRT_API_KEY, VIRT_API_PASS = range(3)

# SolusVM conversation states
SOLUS_BASE_URL, SOLUS_API_KEY, SOLUS_SERVER_ID = range(3, 6)

bandwidth_notification_text = '🔔 [bandWidth Notification] You have consumed {0}% of virtual server {1} bandwidth!\nRemaining traffic: {2} GB'
period_notification_text = '🔔 [Period Notification] {0} days have passed since the registration of virtual server {1}'
traffic_notification_text = '🔔 [Traffic Notification] The remaining traffic is {0} GB. virtual server {1}'

sqlite_manager = ManageDb('virtualizor')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


@handle_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    date = datetime.now()
    get_user_detail_from_db = sqlite_manager.select(table='User', where=f'chat_id={user_detail.id}')

    if not get_user_detail_from_db:
        start_text_notif = (f"New Start Bot In <B>{update.message.chat.type}</B>\n\nName: {user_detail['first_name']}\n"
                            f"UserName: @{user_detail['username']}\nID: <a href=\"tg://user?id={user_detail['id']}\">{user_detail['id']}</a>"
                            f"\nDate: {date}")

        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=start_text_notif, parse_mode="HTML")
        sqlite_manager.insert('User', rows={'name': user_detail.first_name, 'chat_id': user_detail.id, 'date': date})

    text = '<b>Hi, you can connect your VPS accounts through the buttons below:</b>'
    keyboard = [
        [InlineKeyboardButton('Add Virtualizor Account ➕', callback_data='add_virtualizor')],
        [InlineKeyboardButton('Add SolusVM Account ➕', callback_data='add_solusvm')],
        [InlineKeyboardButton('My Virtual Servers', callback_data='main_menu')]
    ]
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


# ==================== VIRTUALIZOR HANDLERS ====================

@handle_error
async def add_virtualizor_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.callback_query.answer()
    text = '<b>OK, send me Virtualizor address.\nExample:</b> http://532.632.151.43:4083'
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return VIRT_END_POINT


@handle_error
async def get_virt_end_point_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['virt_end_point'] = update.message.text
    text = ("<b>Got it! Now I need your Api Key.\n\nIf you don't have it, follow the steps below:\n"
            "Click on your profile on the top right,\nclick on 'API Credentials' and create a new api,\n"
            "you don't need to fill in the ip for the whitelist.\nNow you get api key and api pass,\nEnter your api key.</b>")
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return VIRT_API_KEY


@handle_error
async def get_virt_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['virt_api_key'] = update.message.text
    text = "<b>Excellent! Now send the Api Pass that you got in the previous step.</b>"
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return VIRT_API_PASS


@handle_error
async def get_virt_api_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    api_pass = update.message.text
    api_key = context.user_data['virt_api_key']
    end_point = context.user_data['virt_end_point']

    get_result = await virtualizor_run([end_point], api_key, api_pass)

    if get_result:
        keyboard = []
        for vs in get_result[0][1]:
            keyboard.append([InlineKeyboardButton(f'virtual server {vs}', callback_data=f'virt_{vs}')])
            sqlite_manager.insert('VS_NOTIFICATION', {'vps_id': int(vs), 'chat_id': chat_id, 'notification_band': 0,
                                   'notification_day': 0, 'date': datetime.now()})

        text = f"Done! Virtualizor account added:\n\n{get_result[0][0]}"
        sqlite_manager.insert(table='API_DETAIL',
                              rows={'api_key': api_key, 'api_pass': api_pass, 'end_point': end_point,
                                    'date': datetime.now(), 'chat_id': chat_id})
    else:
        keyboard = [[InlineKeyboardButton(f'Main Menu', callback_data='main_menu')]]
        text = f"<b>Sorry, something went wrong!</b>"

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


# ==================== SOLUSVM HANDLERS ====================

@handle_error
async def add_solusvm_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.callback_query.answer()
    text = '<b>OK, send me SolusVM base URL.\nExample:</b> https://master.example.com'
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return SOLUS_BASE_URL


@handle_error
async def get_solus_base_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['solus_base_url'] = update.message.text
    text = ("<b>Got it! Now I need your SolusVM API Key (Bearer token).\n\n"
            "To get your API key:\n"
            "1. Log into your SolusVM panel\n"
            "2. Go to Settings → API Tokens\n"
            "3. Create a new token\n"
            "4. Copy the token and send it to me</b>")
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return SOLUS_API_KEY


@handle_error
async def get_solus_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['solus_api_key'] = update.message.text
    text = "<b>Excellent! Now send me your Server ID.\n\nYou can find it in the URL when viewing your server or in the server list.</b>"
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')
    return SOLUS_SERVER_ID


@handle_error
async def get_solus_server_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    server_id = update.message.text
    api_key = context.user_data['solus_api_key']
    base_url = context.user_data['solus_base_url']

    get_result = await solusvm_run(base_url, api_key, server_id)

    if get_result and get_result[0][1]:
        keyboard = []
        for vs in get_result[0][1]:
            keyboard.append([InlineKeyboardButton(f'virtual server {vs}', callback_data=f'solus_{vs}')])
            sqlite_manager.insert('SOLUSVM_VS_NOTIFICATION', {'vps_id': int(vs), 'chat_id': chat_id, 'notification_band': 0,
                                   'notification_day': 0, 'date': datetime.now()})

        text = f"Done! SolusVM account added:\n\n{get_result[0][0]}"
        sqlite_manager.insert(table='SOLUSVM_API_DETAIL',
                              rows={'api_key': api_key, 'base_url': base_url, 'server_id': server_id,
                                    'date': datetime.now(), 'chat_id': chat_id})
    else:
        keyboard = [[InlineKeyboardButton(f'Main Menu', callback_data='main_menu')]]
        text = f"<b>Sorry, something went wrong! Please check your credentials.</b>"

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


# ==================== CONVERSATION HANDLERS ====================

virt_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_virtualizor_account, pattern=r'add_virtualizor')],
    states={
        VIRT_END_POINT: [MessageHandler(filters.TEXT, get_virt_end_point_from_user)],
        VIRT_API_KEY: [MessageHandler(filters.TEXT, get_virt_api_key)],
        VIRT_API_PASS: [MessageHandler(filters.TEXT, get_virt_api_pass)],
    },
    fallbacks=[],
    per_chat=True,
    allow_reentry=True,
    conversation_timeout=1500,
)

solus_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_solusvm_account, pattern=r'add_solusvm')],
    states={
        SOLUS_BASE_URL: [MessageHandler(filters.TEXT, get_solus_base_url)],
        SOLUS_API_KEY: [MessageHandler(filters.TEXT, get_solus_api_key)],
        SOLUS_SERVER_ID: [MessageHandler(filters.TEXT, get_solus_server_id)],
    },
    fallbacks=[],
    per_chat=True,
    allow_reentry=True,
    conversation_timeout=1500,
)


# ==================== DELETE VPS HANDLER ====================

@handle_error
async def delete_vps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete VPS account from database (removes API credentials)"""
    chat_id = update.effective_chat.id
    data = update.callback_query.data
    await update.callback_query.answer()
    
    if data.startswith('delete_virt_'):
        vps_id = data.replace('delete_virt_', '')
        try:
            # Get the API details for this VPS
            api_details = sqlite_manager.select(table='API_DETAIL', where=f'chat_id = {chat_id}')
            
            if api_details:
                # Delete the entire API credential entry (removes ALL VPS from that provider)
                for api in api_details:
                    sqlite_manager.delete({'API_DETAIL': ['api_key', api[3]]})
                
                # Delete all notifications associated with this chat
                sqlite_manager.custom_multi(
                    f"DELETE FROM VS_NOTIFICATION WHERE chat_id = {chat_id}"
                )
                text = f"✅ Virtualizor account and all its VPS deleted from database"
            else:
                text = "❌ No Virtualizor account found"
        except Exception as e:
            text = f"❌ Error: {str(e)}"
    
    elif data.startswith('delete_solus_'):
        vps_id = data.replace('delete_solus_', '')
        try:
            # Get the API details for this VPS
            api_details = sqlite_manager.select(table='SOLUSVM_API_DETAIL', where=f'chat_id = {chat_id}')
            
            if api_details:
                # Delete the entire API credential entry (removes ALL VPS from that provider)
                for api in api_details:
                    sqlite_manager.delete({'SOLUSVM_API_DETAIL': ['api_key', api[3]]})
                
                # Delete all notifications associated with this chat
                sqlite_manager.custom_multi(
                    f"DELETE FROM SOLUSVM_VS_NOTIFICATION WHERE chat_id = {chat_id}"
                )
                text = f"✅ SolusVM account and all its VPS deleted from database"
            else:
                text = "❌ No SolusVM account found"
        except Exception as e:
            text = f"❌ Error: {str(e)}"
    
    keyboard = [[InlineKeyboardButton('Main Menu', callback_data='main_menu')]]
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html',
                                   reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== MAIN MENU ====================

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    query = update.callback_query
    data = query.data
    await query.answer()

    platform = None
    special_vps = None
    get_detail = False
    
    if data.startswith('virt_'):
        platform = 'virtualizor'
        special_vps = data.replace('virt_', '')
        get_detail = True
    elif data.startswith('solus_'):
        platform = 'solusvm'
        special_vps = data.replace('solus_', '')
        get_detail = True

    text = "• "
    keyboard = [[InlineKeyboardButton('Refresh ↻', callback_data='main_menu')]]

    virt_data = sqlite_manager.select(table='API_DETAIL', where=f'chat_id = {chat_id}')
    solus_data = sqlite_manager.select(table='SOLUSVM_API_DETAIL', where=f'chat_id = {chat_id}')

    if not virt_data and not solus_data:
        text += '\nNo server found!'
        keyboard.extend([
            [InlineKeyboardButton('Add Virtualizor Account ➕', callback_data='add_virtualizor')],
            [InlineKeyboardButton('Add SolusVM Account ➕', callback_data='add_solusvm')]
        ])
    else:
        if platform != 'solusvm' and virt_data:
            text += "\n<b>[Virtualizor]</b>\n"
            for data_row in virt_data:
                end_point, api_key, api_pass = data_row[2], data_row[3], data_row[4]
                
                if platform == 'virtualizor' and special_vps:
                    get_result = await virtualizor_run([end_point], api_key, api_pass, special_vps=special_vps, get_detail=True)
                else:
                    get_result = await virtualizor_run([end_point], api_key, api_pass)

                if get_result and get_result[0][0]:
                    text += f"{get_result[0][0]}\n"
                    if not special_vps:
                        keyboard.extend([[InlineKeyboardButton(f'[V] server {vs}', callback_data=f'virt_{vs}')] for vs in get_result[0][1]])

        if platform != 'virtualizor' and solus_data:
            if not special_vps:
                text += "\n<b>[SolusVM]</b>\n"
            
            for data_row in solus_data:
                base_url, api_key, server_id = data_row[2], data_row[3], data_row[4]
                
                if platform == 'solusvm' and special_vps and str(special_vps) == str(server_id):
                    get_result = await solusvm_run(base_url, api_key, server_id, special_vps=special_vps, get_detail=True)
                    if get_result and get_result[0][0]:
                        text += f"{get_result[0][0]}\n"
                elif not special_vps:
                    get_result = await solusvm_run(base_url, api_key, server_id)
                    if get_result and get_result[0][0]:
                        text += f"{get_result[0][0]}\n"
                        keyboard.extend([[InlineKeyboardButton(f'[S] server {vs}', callback_data=f'solus_{vs}')] for vs in get_result[0][1]])

    if special_vps:
        if data.startswith('virt_'):
            keyboard = [
                [InlineKeyboardButton('Delete VPS ❌', callback_data=f'delete_virt_{special_vps}')],
                [InlineKeyboardButton('Main Menu', callback_data='main_menu')]
            ]
        elif data.startswith('solus_'):
            keyboard = [
                [InlineKeyboardButton('Delete VPS ❌', callback_data=f'delete_solus_{special_vps}')],
                [InlineKeyboardButton('Main Menu', callback_data='main_menu')]
            ]

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html',
                                   reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== NOTIFICATION JOB ====================

async def notification_job(context: ContextTypes.DEFAULT_TYPE):
    get_all_virt_api = sqlite_manager.select(table='API_DETAIL')
    get_all_solus_api = sqlite_manager.select(table='SOLUSVM_API_DETAIL')
    
    get_all_virt_notification = sqlite_manager.select(table='VS_NOTIFICATION')
    get_all_solus_notification = sqlite_manager.select(table='SOLUSVM_VS_NOTIFICATION')
    
    get_notification_setting = sqlite_manager.select(column='chat_id,notification_band,notification_day,notification_traffic', table='User')

    virt_api_data = [(data[1], data[2], data[3], data[4]) for data in get_all_virt_api]

    for chat_id, end_point, api_key, api_pass in virt_api_data:
        get_user_notif_setting = [(search[1], search[2], search[3]) for search in get_notification_setting if search[0] == chat_id]
        
        if not get_user_notif_setting:
            continue

        bandwidth_notification_precent = get_user_notif_setting[0][0]
        period_notification_day = get_user_notif_setting[0][1]
        left_traffic_gb = get_user_notif_setting[0][2]

        get_result = await virtualizor_run([end_point], api_key, api_pass, get_vs_usage_detail=True)
        
        if get_result:
            for vs_id, details in get_result[0][2].items():
                check_notif = [(search[3], search[4], search[5]) for search in get_all_virt_notification 
                              if search[2] == chat_id and search[1] == int(vs_id)]

                if not check_notif:
                    sqlite_manager.insert('VS_NOTIFICATION', {'vps_id': int(vs_id), 'chat_id': chat_id, 
                                         'notification_band': 0, 'notification_day': 0, 'date': datetime.now()})
                    check_notif = [(0, 0, 0)]

                bandwidth_precent = details.get('bandwidth_left')
                registare_to_now = details.get('register_to_now')
                left_band = details.get('left_band')

                if bandwidth_precent >= bandwidth_notification_precent and not check_notif[0][0]:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 1}}, where=f'vps_id = {vs_id}')
                    text = bandwidth_notification_text.format(bandwidth_precent, f'[V]{vs_id}', left_band)
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][0] and bandwidth_precent < bandwidth_notification_precent:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 0}}, where=f'vps_id = {vs_id}')

                if registare_to_now >= period_notification_day and not check_notif[0][1]:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_day': 1}}, where=f'vps_id = {vs_id}')
                    text = period_notification_text.format(registare_to_now, f'[V]{vs_id}')
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][1] and registare_to_now < period_notification_day:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_day': 0}}, where=f'vps_id = {vs_id}')

                if int(left_band) <= left_traffic_gb and not check_notif[0][2]:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_traffic': 1}}, where=f'vps_id = {vs_id}')
                    text = traffic_notification_text.format(left_band, f'[V]{vs_id}')
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][2] and int(left_band) > left_traffic_gb:
                    sqlite_manager.update({'VS_NOTIFICATION': {'notification_traffic': 0}}, where=f'vps_id = {vs_id}')

    solus_api_data = [(data[1], data[2], data[3], data[4]) for data in get_all_solus_api]

    for chat_id, base_url, api_key, server_id in solus_api_data:
        get_user_notif_setting = [(search[1], search[2], search[3]) for search in get_notification_setting if search[0] == chat_id]
        
        if not get_user_notif_setting:
            continue

        bandwidth_notification_precent = get_user_notif_setting[0][0]
        period_notification_day = get_user_notif_setting[0][1]
        left_traffic_gb = get_user_notif_setting[0][2]

        get_result = await solusvm_run(base_url, api_key, server_id, get_vs_usage_detail=True)
        
        if get_result:
            for vs_id, details in get_result[0][2].items():
                check_notif = [(search[3], search[4], search[5]) for search in get_all_solus_notification 
                              if search[2] == chat_id and search[1] == int(vs_id)]

                if not check_notif:
                    sqlite_manager.insert('SOLUSVM_VS_NOTIFICATION', {'vps_id': int(vs_id), 'chat_id': chat_id, 
                                         'notification_band': 0, 'notification_day': 0, 'date': datetime.now()})
                    check_notif = [(0, 0, 0)]

                bandwidth_precent = details.get('bandwidth_left')
                registare_to_now = details.get('register_to_now')
                left_band = details.get('left_band')

                if bandwidth_precent >= bandwidth_notification_precent and not check_notif[0][0]:
                    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_band': 1}}, where=f'vps_id = {vs_id}')
                    text = bandwidth_notification_text.format(bandwidth_precent, f'[S]{vs_id}', left_band)
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][0] and bandwidth_precent < bandwidth_notification_precent:
                    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_band': 0}}, where=f'vps_id = {vs_id}')

                if registare_to_now >= period_notification_day and not check_notif[0][1]:
                    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_day': 1}}, where=f'vps_id = {vs_id}')
                    text = period_notification_text.format(registare_to_now, f'[S]{vs_id}')
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][1] and registare_to_now < period_notification_day:
                    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_day': 0}}, where=f'vps_id = {vs_id}')

                if int(left_band) <= left_traffic_gb and not check_notif[0][2]:
                    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_traffic': 1}}, where=f'vps_id = {vs_id}')
                    text = traffic_notification_text.format(left_band, f'[S]{vs_id}')
                    await context.bot.send_message(text=text, chat_id=chat_id)

                elif check_notif[0][2] and int(left_band) > left_traffic_gb:
                    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_traffic': 0}}, where=f'vps_id = {vs_id}')


# ==================== NOTIFICATION SETTINGS ====================

@handle_error
async def set_bandwith_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_precent = int(context.args[0])
    if get_precent <= 0 or get_precent > 100:
        raise ValueError('precent higher or lighter 0 and 100')
    chat_id = update.effective_chat.id

    sqlite_manager.update({'User': {'notification_band': get_precent}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 0}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_band': 0}}, where=f'chat_id = {chat_id}')

    await context.bot.send_message(text='Notification Setting Changed successfully!', chat_id=chat_id)


@handle_error
async def set_period_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_day = int(context.args[0])
    if get_day <= 0:
        raise ValueError('day lighter than 0')
    chat_id = update.effective_chat.id

    sqlite_manager.update({'User': {'notification_day': get_day}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_day': 0}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_day': 0}}, where=f'chat_id = {chat_id}')

    await context.bot.send_message(text='Notification Setting Changed successfully!', chat_id=chat_id)


@handle_error
async def set_traffic_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_traffic = int(context.args[0])
    if get_traffic <= 0:
        raise ValueError('traffic lighter than 0')
    chat_id = update.effective_chat.id

    sqlite_manager.update({'User': {'notification_traffic': get_traffic}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_traffic': 0}}, where=f'chat_id = {chat_id}')
    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_traffic': 0}}, where=f'chat_id = {chat_id}')

    await context.bot.send_message(text='Notification Setting Changed successfully!', chat_id=chat_id)


@handle_error
async def clear_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sqlite_manager.update({'VS_NOTIFICATION': {'notification_band': 0, 'notification_day': 0, 'notification_traffic': 0}}, 
                         where=f'chat_id = {chat_id}')
    sqlite_manager.update({'SOLUSVM_VS_NOTIFICATION': {'notification_band': 0, 'notification_day': 0, 'notification_traffic': 0}}, 
                         where=f'chat_id = {chat_id}')
    await context.bot.send_message(text='Notification Clear successfully!', chat_id=chat_id)


@handle_error
async def notification_statua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    get_virt_notif_status = sqlite_manager.select(column='vps_id, notification_band, notification_day, notification_traffic',
                                             table='VS_NOTIFICATION', where=f'chat_id = {chat_id}')
    
    get_solus_notif_status = sqlite_manager.select(column='vps_id, notification_band, notification_day, notification_traffic',
                                             table='SOLUSVM_VS_NOTIFICATION', where=f'chat_id = {chat_id}')

    get_notif_value = sqlite_manager.select(column='notification_band,notification_day,notification_traffic',
                                            table='User', where=f'chat_id = {chat_id}')

    virt_band_width_status, virt_period_status, virt_left_traffic = [], [], []
    solus_band_width_status, solus_period_status, solus_left_traffic = [], [], []

    for vps in get_virt_notif_status:
        virt_band_width_status.append((f'V{vps[0]}', vps[1]))
        virt_period_status.append((f'V{vps[0]}', vps[2]))
        virt_left_traffic.append((f'V{vps[0]}', vps[3]))

    for vps in get_solus_notif_status:
        solus_band_width_status.append((f'S{vps[0]}', vps[1]))
        solus_period_status.append((f'S{vps[0]}', vps[2]))
        solus_left_traffic.append((f'S{vps[0]}', vps[3]))

    all_band = virt_band_width_status + solus_band_width_status
    all_period = virt_period_status + solus_period_status
    all_traffic = virt_left_traffic + solus_left_traffic

    text = (f"BandWidth: {get_notif_value[0][0]}% | status: {all_band}"
            f"\n\nPassed Period: {get_notif_value[0][1]} Day | status: {all_period}"
            f"\n\nLeft Traffic: {get_notif_value[0][2]} GB | status: {all_traffic}")

    await context.bot.send_message(text=text, chat_id=chat_id)


# ==================== MAIN ====================

if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_bot_token).build()
    application.add_handler(CommandHandler('start', start))

    application.add_handler(CommandHandler('set_bandwith_notification', set_bandwith_notification))
    application.add_handler(CommandHandler('set_period_notification', set_period_notification))
    application.add_handler(CommandHandler('set_traffic_notification', set_traffic_notification))
    application.add_handler(CommandHandler('notification_status', notification_statua))
    application.add_handler(CommandHandler('clear_notification', clear_notification))

    application.add_handler(virt_conv_handler)
    application.add_handler(solus_conv_handler)
    application.add_handler(CallbackQueryHandler(delete_vps, pattern=r'delete_virt_.*|delete_solus_.*'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='main_menu'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='solus_(.*)'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='virt_(.*)'))
    application.job_queue.run_repeating(notification_job, interval=check_every_min * 60, first=0)
    application.run_polling()
