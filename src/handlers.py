from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, ParseMode, InlineKeyboardMarkup
from telegram.ext import MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from requests import post
from src import signup, login, Bot, utils, perfil, tips, bad_report, report_status, daily_report
from src.CustomCalendar import CustomCalendar
from datetime import date

#Envia o menu para o usuario
def start(update, context):
    resposta = "Bem vindo ao DoctorS Bot. Selecione a opção desejada.\n\nCaso deseje voltar ao menu, digite /menu ou /start.\n"
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta,
        reply_markup=get_reply_markup(context.user_data)
    )

    link = "https://scontent-gig2-1.xx.fbcdn.net/v/t1.0-9/103274216_112293347182974_7934951402525681679_o.png?_nc_cat=101&ccb=2&_nc_sid=85a577&_nc_ohc=DfmCZ9ndG5cAX-Mq4qP&_nc_ht=scontent-gig2-1.xx&oh=0566da2b649761aa3348d1f8c89c640a&oe=5FBA8F35"
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=link
    )

def menu(update, context):
    resposta = "Selecione a opção desejada!"
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta,
        reply_markup=get_reply_markup(context.user_data)
    )

def get_reply_markup(user_data):
    if utils.is_logged(user_data):
        reply_keyboard = [  ['Minhas informações','Editar perfil'],
                            ['Sobre','Logout'],
						    ['Ajuda','Dicas'],
                            ['Relatório de Saúde']]
    else:
        reply_keyboard = [  ['Login','Registrar'],
                            ['Sobre','Finalizar'],
						    ['Ajuda']   ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    return markup


def get_report_status(update, context):
    if utils.is_logged(context.user_data):
        report_status.start(update, context)

    else:
        unknown(update, context)

#Retorna as informações dos usuarios
def get_user_info(update, context):
    if utils.is_logged(context.user_data):
        resposta = context.user_data
        utils.image(resposta)
        path = 'general/images/robo_save.png'
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(path, 'rb')
        )
    else:
        unknown(update, context)

#Cadastra novo user
def signup_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(Filters.text("Registrar"), signup.start)],
        states={
            signup.CHOOSING: [MessageHandler(Filters.regex(signup.ENTRY_REGEX), signup.regular_choice)],
            signup.TYPING_REPLY: [MessageHandler((Filters.text | Filters.location) & ~(Filters.command | Filters.regex('^Done$')), signup.received_information)],
        },
        fallbacks=[
            MessageHandler(Filters.regex('^Done$'), signup.done),
            MessageHandler(Filters.regex('^Cancelar$'), utils.cancel),
            MessageHandler(Filters.all, utils.bad_entry)
        ]
    )

#Função de callback do calendário
def birthDayCallBack(update, context):
    result, key, step = CustomCalendar(locale='br', max_date=date.today()).process(update.callback_query.data)
    update.callback_query.answer()
    if not result and key:
        update.callback_query.edit_message_text(f"Selecione o {CustomCalendar.LSTEP[step]}", reply_markup=key)
    elif result:
        context.user_data['Nascimento'] = result
        context.user_data.update({'birthdate' : str(result)})
        update.callback_query.edit_message_text(f'Selecionado: {result}')

        if utils.is_logged(context.user_data):
            context.user_data['resp_item'] = str(result)
            perfil.requestEdit(update, context)
            None
        else:
            signup.requestSignup(update, context)

def logout(update, context):
    if utils.is_logged(context.user_data):
        resposta = f"Já vai?\n\nAté a próxima {context.user_data['user_name']}!"
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=resposta
        )

        daily_report.cancel_daily(update, context)
        #Limpa a sessão do usuário
        context.user_data.clear()

        menu(update,context)
    else:
        #Caso não esteja logado, não entra na função de logout
        unknown(update, context)

#Login de usuario
def login_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(Filters.text("Login"), login.start)],
        states={
            login.CHOOSING: [MessageHandler(Filters.regex(login.ENTRY_REGEX), login.regular_choice)],
            login.TYPING_REPLY: [MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), login.received_information)],
        },
        fallbacks=[
            MessageHandler(Filters.regex('^Done$'), login.done),
            MessageHandler(Filters.regex('^Cancelar$'), utils.cancel),
            MessageHandler(Filters.all, utils.bad_entry)
        ]
    )

def bad_report_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(bad_report.start, pattern='^bad_report$')],
        states={
            bad_report.CHOOSING: [MessageHandler(Filters.text & ~(Filters.regex("^Done$")), bad_report.regular_choice)]
        },
        fallbacks=[MessageHandler(Filters.location, bad_report.done)]
    )

#Login de usuario
def perfil_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(Filters.text("Editar perfil"), perfil.start)],
        states={
            perfil.CHOOSING: [MessageHandler(Filters.regex(perfil.ENTRY_REGEX), perfil.regular_choice)],
            perfil.TYPING_REPLY: [MessageHandler(Filters.text & ~Filters.command, perfil.received_information)],
        },
        fallbacks=[
            MessageHandler(Filters.regex('^Voltar$'), utils.cancel),
            MessageHandler(Filters.all, perfil.bad_entry)
        ]
    )

#Envia informaçoes sobre o bot
def sobre(update, context):
    resposta = 'O DoctorS é um Telegram Bot criado para ajudar a população no combate ao novo coronavírus (SARS-CoV-2).'
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta
    )
    
#Informações sobre as funcionalidades
def ajuda(update, context):
	#Lista de funcionalidades
    resposta = ('O <b><i>DoctorS</i></b> possui as seguintes funcionalidades:\n\n' 
		 		'- <b>Cadastro</b>: Crie uma nova conta de usuário e comece a reportar seu estado de saúde.\n\n'
				'- <b><i>Login</i></b>: Entre em sua conta. Caso você ainda não possua uma, use a função de cadastro.\n\n'
				'- <b><i>Logout</i></b>: Saia de sua conta. Você poderá entrar novamente quando quiser.\n\n'
				'- <b>Reportar estado físico</b>: Informe seu estado de saúde (recomendado uso diário).\n\n'
				'- <b>Dicas</b>: Veja diversas dicas e informações para cuidar da saúde, separadas por tópicos.\n\n' 
 				'- <b>Alterar informações pessoais</b>: Altere algumas informações cadastradas na sua conta.\n\n'
                '- <b>Notícias</b>: O bot envia de forma automática uma notícia relacionada à pandemia por dia. A notícia também pode ser acessada enviando ao bot o comando /noticia.'
	)
    context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=resposta,
		parse_mode=ParseMode.HTML
    )

    resposta = ('<b>Informações gerais:</b>\n\n'
                '- Para navegar nos menus clique em algum dos botões de navegação. Se o teclado de sugestões desaparecer clique no ícone de teclado ao lado do campo de digitação.\n\n'
                '- Nos menus de cadastro e <i>login</i>, quando uma informação válida for inserida, aparecerá no botão correspondente uma marca indicando que ela foi validada.\n\n'
                '- Quando todas as informações forem inseridas aparecerá um botão <i>"Done"</i>. Clique nele para prosseguir com o cadastro ou <i>login</i>.\n\n'
                '- Para apagar os dados inseridos e retornar ao menu anterior utilize o botão cancelar caso esteja disponível.\n\n'
                '- Uma vez por dia será enviada uma mensagem perguntando sobre o seu estado de saúde. Você também pode recebê-la enviando o comando /report ao bot.'
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta,
        parse_mode=ParseMode.HTML
    )

	#Mais informações
    resposta = 'Para informações mais detalhadas <a href="https://fga-eps-mds.github.io/2020-1-DoctorS-Bot/#/docs/Ajuda">clique aqui</a>.'
    context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=resposta,
		parse_mode=ParseMode.HTML,
		disable_web_page_preview = True
    )

def tips_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(Filters.text("Dicas"), tips.start)],
        states={
            tips.CHOOSING: [MessageHandler(Filters.regex(tips.ENTRY_REGEX), tips.regular_choice)]
        },
        fallbacks=[
            MessageHandler(Filters.regex('^Voltar$'), utils.back),
            MessageHandler(Filters.all, tips.bad_entry)
        ]
    )
    
def finalizar(update, context):
    if not utils.is_logged(context.user_data):
        resposta = "Já vai? Tudo bem. Sempre que quiser voltar digite /menu ou /start e receberá o menu inicial.\n\nObrigado por usar o DoctorS!"
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=resposta
        )

#Mensagens não reconhecidas
def unknown(update, context):
    resposta = "Não entendi. Tem certeza de que digitou corretamente?\n\nRetornando ao menu."
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resposta
    )
    menu(update, context)
