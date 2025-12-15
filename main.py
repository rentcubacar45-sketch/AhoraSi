import asyncio
from pyrogram import Client, filters
from g import UnifiedUploader
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.threads import ObigramThread as SimpleThread

from SQLiteDatabase import SQLiteDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import megacli

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import threading
from flask import Flask

app_web = Flask(__name__)

threads = {}

@app_web.route('/')
def health():
    return 'OK'

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app_web.run(host='0.0.0.0', port=port)

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        asyncio.create_task(message.edit_text(downloadingInfo))
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        asyncio.create_task(message.edit_text(downloadingInfo))
    except Exception as ex: print(str(ex))
    pass

async def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        await message.edit_text('🤜Preparando Para Subir☁...')
        user_info = jdb.get_user(message.from_user.username if message.from_user else str(message.from_user.id))
        cloudtype = user_info['cloudtype']
        proxy_str = user_info['proxy']
        proxy = ProxyCloud.parse(proxy_str) if proxy_str else None
        tokenize = False
        if user_info['tokenize'] != 0:
            tokenize = True
        originalfile = ''
        if len(files) > 1:
            originalfile = filename
        if cloudtype == 'moodle':
            client = UnifiedUploader("Moodle", user_info['moodle_user'], user_info['moodle_password'], user_info['moodle_host'], user_info['moodle_repo_id'], proxy=proxy)
        elif cloudtype == 'cloud':
            client = UnifiedUploader("Next", user_info['moodle_user'], user_info['moodle_password'], user_info['moodle_host'], None, proxy=proxy)
        else:
            return None
        loged = client.login()
        if loged:
            draftlist = []
            for f in files:
                error, data = client.upload_file(f, progressfunc=uploadFile, args=(bot,message,originalfile,thread), tokenize=tokenize)
                if error:
                    await message.edit_text('❌Error: ' + error)
                    return None
                draftlist.append(data)
                os.unlink(f)
            client.logout()
            return draftlist
        else:
            await message.edit_text('❌Error En La Pagina❌')
            return None
    except Exception as ex:
        await message.edit_text('❌Error❌\n' + str(ex))
        return None


async def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(message.from_user.username if message.from_user else str(message.from_user.id))
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        await message.edit_text(compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = await processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = await processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    await message.edit_text('🤜Preparando Archivo📄...')
    files = []
    if client:
        for data in client:
            files.append({'name':data['name'],'directurl':data['url']})
    await message.delete()
    finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
    filesInfo = infos.createFileMsg(file,files)
    await bot.send_message(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
    if len(files)>0:
        txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
        await sendTxt(txtname,files,update,bot)

async def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            await processFile(update,bot,message,file,jdb=jdb)
        else:
            await message.edit_text('❌Error al descargar el enlace❌')

async def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
    megadl = megacli.mega.Mega({'verbose': True})
    megadl.login()
    try:
        info = megadl.get_public_url_info(megaurl)
        file_name = info['name']
        megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
        if not megadl.stoping:
            await processFile(update,bot,message,file_name,thread=thread)
    except:
        files = megaf.get_files_from_folder(megaurl)
        for f in files:
            file_name = f['name']
            megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
            if not megadl.stoping:
                await processFile(update,bot,message,file_name,thread=thread)
        pass
    pass

async def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                await bot.send_document(update.message.chat.id,name)
                os.unlink(name)

async def onmessage(message, bot):
    try:
        thread = SimpleThread()
        threads[thread.id] = thread
        username = message.from_user.username if message.from_user else str(message.from_user.id)
        tl_admin_user = os.environ.get('tl_admin_user','*')

        #Descomentar debajo solo si se ba a poner el usuario admin de telegram manual
        #tl_admin_user = '*'

        jdb = SQLiteDatabase('database')
        jdb.migrate_from_json('database.jdb')

        user_info = jdb.get_user(username)

        if username == tl_admin_user or tl_admin_user=='*' or user_info :  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:return


        msgText = ''
        try: msgText = message.text
        except:pass

        # comandos de admin
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '😃Genial @'+user+' ahora tiene acceso al bot👍'
                    await bot.send_message(message.chat.id,msg)
                except:
                    await bot.send_message(message.chat.id,'❌Error en el comando /adduser username❌')
            else:
                await bot.send_message(message.chat.id,'❌No Tiene Permiso❌')
            return
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        await bot.send_message(message.chat.id,'❌No Se Puede Banear Usted❌')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '🦶Fuera @'+user+' Baneado❌'
                    await bot.send_message(message.chat.id,msg)
                except:
                    await bot.send_message(message.chat.id,'❌Error en el comando /banuser username❌')
            else:
                await bot.send_message(message.chat.id,'❌No Tiene Permiso❌')
            return
        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                await bot.send_message(message.chat.id,'Base De Datos👇')
                await bot.send_document(message.chat.id,'database.db')
            else:
                await bot.send_message(message.chat.id,'❌No Tiene Permiso❌')
            return
        # end

        # comandos de usuario
        if '/tutorial' in msgText:
            tuto = open('tuto.txt','r')
            await bot.send_message(message.chat.id,tuto.read())
            tuto.close()
            return
        if '/myuser' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                await bot.send_message(message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '😃Genial los zips seran de '+ sizeof_fmt(size*1024*1024)+' las partes👍'
                   await bot.send_message(message.chat.id,msg)
                except:
                   await bot.send_message(message.chat.id,'❌Error en el comando /zips size❌')
                return
        if '/account' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /account user,password❌')
            return
        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /host moodlehost❌')
            return
        if '/repoid' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /repo id❌')
            return
        if '/tokenize_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /tokenize state❌')
            return
        if '/tokenize_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /tokenize state❌')
            return
        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /cloud (moodle or cloud)❌')
            return
        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                await bot.send_message(message.chat.id,'❌Error en el comando /uptype (typo de subida (evidence,draft,blog))❌')
            return
        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    await bot.send_message(message.chat.id,statInfo)
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = threads[int(tid)]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                await msg.edit_text('❌Tarea Cancelada❌')
            except Exception as ex:
                print(str(ex))
            return
        #end

        progress_message = await bot.send_message(message.chat.id,'🕰Procesando🕰...')

        thread.store('msg',progress_message)

        if '/start' in msgText:
            start_msg = 'Bot          : CarlosBOtfix\n'
            start_msg+= 'Desarrollador: @Nanatsu2370\n'
            start_msg+= '\n'
            start_msg+= 'Uso          :Envia Enlaces De Descar(Configure Antes De Empezar , Vea El /tutorial)\n'
            await progress_message.edit_text(start_msg)
        elif 'http' in msgText:
            url = msgText
            try:
                await ddl(message,bot,progress_message,url,file_name='',thread=thread,jdb=jdb)
            except Exception as ex:
                await progress_message.edit_text('❌Error interno❌')
        else:
            await message.edit_text('😵No se pudo procesar😵')
    except Exception as ex:
           print(str(ex))


def main():
    bot_token = os.environ.get('BOT_TOKEN') or '8476706727:AAEVlArs-XKY6elCYe9XRbNyhoyFvNdNI5I'
    api_id = os.environ.get('API_ID') or '20534584'
    api_hash = os.environ.get('API_HASH') or '6d5b13261d2c92a9a00afc1fd613b9df'

    # Start web server in a thread
    threading.Thread(target=run_web).start()

    app = Client("tguploaderpro", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
    @app.on_message(filters.text)
    async def handler(client, message):
        await onmessage(message, client)
    app.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
