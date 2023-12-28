# Pygame
import pygame
from pygame import display

# Argument Parsing
import argparse

# Python files
import secretFunctions

# Protection - Hashing and Encrpytion Modules
from Cryptodome.Cipher import AES
from pbkdf2 import PBKDF2
from base64 import b64encode, b64decode

# SQL
import psycopg2

# Text-to-speech
import pyttsx3
import syllapy

# Speech Recognition
from speech_recognition import Microphone, Recognizer, AudioFile, UnknownValueError, RequestError

# Large Language Model
import openai

# Generic Random Libraries
import threading
import time
import math
import os

# VARIABLES
# Initializing and Setup
pygame.init()

engine = pyttsx3.init()

foobar = 0

mic = Microphone()
recog = Recognizer()

# Initializes the Parser
parser = argparse.ArgumentParser(
    description="Password Manager"
)

# Setup the connection and cursor
conn = psycopg2.connect(dbname = "ps", user = "postgres", password = secretFunctions.getPW())

cursor = conn.cursor()

# Setups OpenAI
client = openai.OpenAI(api_key=secretFunctions.getAPIKey())
chatMessages = [{"role": "system", "content": "You are a friendly, understanding, and supportive bot who enjoys creating positive connections and bonds with elderly users. You also help elderly to manage their passwords securely and easily online."}]

# "Normal" variables
string = ""

current_database_user = "bob"
plaintext_master_pw = "bob"

blit_text_list = []
speak_queue = []
bot_speaking = False

current_dialogue_memory = 1

insertEntryData = {
    "url": "",
    "username": "",
    "password": ""
}

updateEntryData = {
    "url": "",
    "new_data": ""
}

# Pygame Variables
screenWidth = 1200
screenHeight = 600

screen = display.set_mode([screenWidth, screenHeight])

font = pygame.font.SysFont("Arial", 32)


# FUNCTIONS
def encrypt_password(plaintext_password, master_password, salt=b'ez.gg', iterations=6000):
    key = PBKDF2(str(master_password), salt, iterations=iterations).read(32)

    cipher = AES.new(key, AES.MODE_GCM)

    nonce = cipher.nonce

    ciphertext, tag = cipher.encrypt_and_digest(bytes(plaintext_password, 'ascii'))

    encrypted_ciphertext = b64encode(ciphertext + nonce).decode()

    return encrypted_ciphertext


def decrypt_password(encrypted_password, key, salt=b'ez.gg', iterations=6000):
    encryption_key = PBKDF2(str(key), salt, iterations=iterations).read(32)

    nonce = (b64decode(encrypted_password))[-16:]

    ciphertext = (b64decode(encrypted_password))[:-16]

    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=nonce)
    
    try:
        # Even if the master password is wrong, it will only occasionally give an error at 'except'.
        # Mostly, the user will just recieve an inaccurate password if they inserted the incorrect master password
        pw = cipher.decrypt(ciphertext).decode()
        return pw
    except ValueError:
        return False
    

def tableExists(cursor, tablename):
    cursor.execute("SELECT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = '"+tablename+"') AS table_existence")

    if cursor.fetchall()[0][0]:
        return True
    else:
        return False
    

def listTable(cursor, tablename):
    if tableExists(cursor, tablename):
        cursor.execute("SELECT * FROM "+tablename)
        tableReference = cursor.fetchall()
        if len(tableReference) > 0:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '"+tablename+"' ORDER BY ordinal_position")
            columnReference = cursor.fetchall()

            for x in range(len(tableReference)):
                for y in range(len(tableReference[x])):
                    print(columnReference[y][0].upper()+": "+str(tableReference[x][y]))

                print("----------")
        else:
            print("[Database is empty]")
    else:
        print("Database does not exist.")


def listRowsThatApply(cursor, tablename, rowIdentifier1=False, condition1=False, rowIdentifier2=False, condition2=False, columnSpecifier='*'):
    if tableExists(cursor, tablename):
        if rowIdentifier2:
            cursor.execute("SELECT "+columnSpecifier+" FROM "+tablename+" WHERE ("+rowIdentifier1+" = '"+condition1+"' AND "+rowIdentifier2+" = '"+condition2+"')")
            rows = cursor.fetchall()
        elif rowIdentifier1:
            cursor.execute("SELECT "+columnSpecifier+" FROM "+tablename+" WHERE "+rowIdentifier1+" = '"+condition1+"'")
            rows = cursor.fetchall()
        else:
            cursor.execute("SELECT "+columnSpecifier+" FROM "+tablename)
            rows = cursor.fetchall()

        if len(rows) > 0:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '"+tablename+"' ORDER BY ordinal_position")
            columnReference = cursor.fetchall()

            for x in range(len(rows)):
                    for y in range(len(rows[x])):
                        print(columnReference[y][0].upper()+": "+str(rows[x][y]))

                    print("----------")
        else:
            print("[Database is empty] OR [Item does not exist]")

    else:
        print("Database does not exist.")


def speakRowsThatApply(cursor, tablename, rowIdentifier1=False, condition1=False, rowIdentifier2=False, condition2=False, columnSpecifier='*'):
    if tableExists(cursor, tablename):
        if rowIdentifier2:
            cursor.execute("SELECT "+columnSpecifier+" FROM "+tablename+" WHERE ("+rowIdentifier1+" = '"+condition1+"' AND "+rowIdentifier2+" = '"+condition2+"')")
            rows = cursor.fetchall()
        elif rowIdentifier1:
            cursor.execute("SELECT "+columnSpecifier+" FROM "+tablename+" WHERE "+rowIdentifier1+" = '"+condition1+"'")
            rows = cursor.fetchall()
        else:
            cursor.execute("SELECT "+columnSpecifier+" FROM "+tablename)
            rows = cursor.fetchall()

        if len(rows) > 0:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '"+tablename+"' ORDER BY ordinal_position")
            columnReference = cursor.fetchall()

            for x in range(len(rows)):
                    for y in range(len(rows[x])):
                        text = columnReference[y][0].upper()+": "+str(rows[x][y])
                        defaultBotSpeak(text)

                    print("----------")
        else:
            text = "Database is empty OR Item does not exist."
            defaultBotSpeak(text)

    else:
        text = "Database does not exist."
        defaultBotSpeak(text)



def listPlaintextPasswords_RowsThatApply(cursor, rowIdentifier1=False, condition1=False, rowIdentifier2=False, condition2=False, columnSpecifier='*'):
    if tableExists(cursor, 'password_manager'):
        if rowIdentifier2:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager WHERE ("+rowIdentifier1+" = '"+condition1+"' AND "+rowIdentifier2+" = '"+condition2+"')")
            rows = cursor.fetchall()
        elif rowIdentifier1:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager WHERE "+rowIdentifier1+" = '"+condition1+"'")
            rows = cursor.fetchall()
        else:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager")
            rows = cursor.fetchall()

        if len(rows) > 0:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'password_manager' ORDER BY ordinal_position")
            columnReference = cursor.fetchall()

            for x in range(len(rows)):
                    for y in range(len(rows[x])):
                        print(columnReference[y][0].upper()+": "+str(rows[x][y]))

                        if columnReference[y][0] == "password":
                            # Decrypts Encrypted Password To Get Plaintext Password
                            encrypted_password = rows[x][y]
                            plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user, plaintext_master_pw)
                    
                    if plaintext_password:
                        print("PLAINTEXT PASSWORD: "+plaintext_password)
                    else:
                        print("ERROR: PLAINTEXT PASSWORD WAS UNABLE TO BE FETCHED. Please try again.")
                    print("----------")
        else:
            print("[Database is empty] OR [Item does not exist]")

    else:
        print("Database does not exist.")


def speakPlaintextPasswords_RowsThatApply(cursor, rowIdentifier1=False, condition1=False, rowIdentifier2=False, condition2=False, columnSpecifier='*'):
    if tableExists(cursor, 'password_manager'):
        if rowIdentifier2:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager WHERE ("+rowIdentifier1+" = '"+condition1+"' AND "+rowIdentifier2+" = '"+condition2+"')")
            rows = cursor.fetchall()
        elif rowIdentifier1:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager WHERE "+rowIdentifier1+" = '"+condition1+"'")
            rows = cursor.fetchall()
        else:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager")
            rows = cursor.fetchall()

        if len(rows) > 0:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'password_manager' ORDER BY ordinal_position")
            columnReference = cursor.fetchall()

            for x in range(len(rows)):
                    for y in range(len(rows[x])):
                        text = columnReference[y][0].upper()+": "+str(rows[x][y])

                        defaultBotSpeak(text)

                        if columnReference[y][0] == "password":
                            # Decrypts Encrypted Password To Get Plaintext Password
                            encrypted_password = rows[x][y]
                            plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user, plaintext_master_pw)
                    
                    if plaintext_password:
                        text = "PLAINTEXT PASSWORD: "+plaintext_password
                        defaultBotSpeak(text)

                    else:
                        text = "ERROR: PLAINTEXT PASSWORD WAS UNABLE TO BE FETCHED. Please try again."
                        defaultBotSpeak(text)

                    text = "----------"

                    print(text)
                    defaultBotAppendToBlitTextList(text)
        else:
            text = "Database is empty OR Item does not exist."

            defaultBotSpeak(text)

    else:
        text = "Database does not exist."
        defaultBotSpeak(text)


def showPlaintextPasswords_RowsThatApply(cursor, rowIdentifier1=False, condition1=False, rowIdentifier2=False, condition2=False, columnSpecifier='*'):
    if tableExists(cursor, 'password_manager'):
        if rowIdentifier2:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager WHERE ("+rowIdentifier1+" = '"+condition1+"' AND "+rowIdentifier2+" = '"+condition2+"')")
            rows = cursor.fetchall()
        elif rowIdentifier1:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager WHERE "+rowIdentifier1+" = '"+condition1+"'")
            rows = cursor.fetchall()
        else:
            cursor.execute("SELECT "+columnSpecifier+" FROM password_manager")
            rows = cursor.fetchall()

        if len(rows) > 0:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'password_manager' ORDER BY ordinal_position")
            columnReference = cursor.fetchall()

            for x in range(len(rows)):
                    for y in range(len(rows[x])):
                        text = columnReference[y][0].upper()+": "+str(rows[x][y])

                        print(text)

                        defaultTimeDelayBotAppendToBlitTextList(text)

                        if columnReference[y][0] == "password":
                            # Decrypts Encrypted Password To Get Plaintext Password
                            encrypted_password = rows[x][y]
                            plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user, plaintext_master_pw)
                    
                    if plaintext_password:
                        text = "PLAINTEXT PASSWORD: "+plaintext_password
                        print(text)

                        defaultTimeDelayBotAppendToBlitTextList(text)
                    else:
                        text = "ERROR: PLAINTEXT PASSWORD WAS UNABLE TO BE FETCHED. Please try again."

                        defaultBotSpeak(text)

                    text = "----------"

                    print(text)
                    defaultBotAppendToBlitTextList(text)
        else:
            text = "Database is empty OR Item does not exist."

            defaultBotSpeak(text)
    else:
        text = "Database does not exist."
        
        defaultBotSpeak(text)


def defaultBotAppendToBlitTextList(text):
    start_time = time.time()
    
    chatMessages.append({"role": "system", "content": text})

    multi_lined_text = get_multi_lined_text(text, font, extraWords="Bot:")

    for line in multi_lined_text:
        blit_text_list.append([start_time, "bot", line, (255, 255, 255), font, (0, 0)])


def defaultUserAppendToBlitTextList(text):
    start_time = time.time()

    chatMessages.append({"role": "user", "content": text})

    multi_lined_text = get_multi_lined_text(text, font, extraWords="You:")

    for line in multi_lined_text:
        blit_text_list.append([start_time, "user", line, (255, 0, 0), font, (0, 0)])


def defaultTimeDelayBotAppendToBlitTextList(text):
    # This puts it under user to trick the computer to go by delay for bot text (check game loop code)
    start_time = time.time()

    chatMessages.append({"role": "system", "content": text})

    multi_lined_text = get_multi_lined_text(text, font, extraWords="Bot:")

    for line in multi_lined_text:
        blit_text_list.append([start_time, "user", line, (255, 255, 255), font, (0, 0)])


def checkURLexists(cursor, tablename, url, filter=True):
    if tableExists(cursor, tablename):
        cursor.execute("SELECT * FROM "+tablename)
        tableReference = cursor.fetchall()
        if len(tableReference) > 0:
            cursor.execute("SELECT EXISTS(SELECT 1 FROM "+tablename+" WHERE url ='"+url+"')")
            urlCheck = cursor.fetchall()[0][0]
            if urlCheck:
                return True
            else:
                print("No entry identified with the URL provided. Please try again.")
                print("")

                print("URL Provided for reference.")
                print("----------")
                print(url)
                print("")

                print("----------")
                print("DATABASE:")
                print("----------")

                # we can't just always do filter setting bc the function might not always be used for password manager
                # - that's the whole point of the 'tablename' parameter anyways.
                if filter:
                    listRowsThatApply(cursor, tablename, 'database_user', current_database_user)
                else:
                    listTable(cursor, tablename)
        else:
            print("Database is empty")
    else:
        print("Database does not Exist")

    return False


def speakQuery(url):
    if checkURLexists(cursor, 'password_manager', url):
        # DECRYPTION
        cursor.execute("SELECT password FROM password_manager WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")
        encrypted_password = cursor.fetchall()[0][0]

        plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user, plaintext_master_pw)

        if plaintext_password:
            # Prints query
            print("SUCCESS. QUERY:")
            print("----------")
            listRowsThatApply(cursor, 'password_manager', 'url', url, 'database_user', current_database_user)
            print("PLAINTEXT PASSWORD: "+plaintext_password)
            print("----------")

            speakRowsThatApply(cursor, 'password_manager', 'url', url, 'database_user', current_database_user)

            text = "PLAINTEXT PASSWORD: "+plaintext_password
            
            defaultBotSpeak(text)
        else:
            text = "Error: Message corrupted. Please try again."

            defaultBotSpeak(text)
    else:
        speak_queue.append("URL is unrecognized. The URL you inputted is displayed in text.")
        defaultBotAppendToBlitTextList(url)


def speakDeleteAllEntries():
    if tableExists(cursor, 'password_manager'):
        cursor.execute("SELECT * FROM password_manager WHERE database_user = '"+current_database_user+"'")
        rowNum = len(cursor.fetchall())

        if rowNum > 0:
            cursor.execute("DELETE FROM password_manager WHERE database_user = '"+current_database_user+"'")

            text = "SUCCESS. Your Database Entries have been deleted."
            
            defaultBotSpeak(text)

            print("")

            print("DATABASE:")
            print("----------")
            listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)
        else:
            text = "Your Database is already empty."
            
            defaultBotSpeak(text)
            
    else:
        text = "Database does not exist."
        
        defaultBotSpeak(text)


def speakDeleteEntry(url):
    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("DELETE FROM password_manager WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")

        text = "SUCCESS. Entry has been Deleted."
        
        defaultBotSpeak(text)

        print("")

        text = "DATABASE:"
        
        defaultBotSpeak(text)

        text = "----------"
        defaultBotAppendToBlitTextList(text)
        print(text)
        
        showPlaintextPasswords_RowsThatApply(cursor, 'database_user', current_database_user)

    else:
        speak_queue.append("URL is unrecognized. The URL you inputted is displayed in text.")
        defaultBotAppendToBlitTextList(url)


def speakInsertEntry():
    url = insertEntryData["url"]
    username = insertEntryData["username"]
    plaintext_password = insertEntryData["password"]

    # ENCRYPTION
    encrypted_ciphertext = fullEncrypt(cursor, plaintext_password, current_database_user, plaintext_master_pw)

    if tableExists(cursor, 'password_manager'):
        cursor.execute("INSERT INTO password_manager(database_user, url, username, password) VALUES ('"+current_database_user+"', '"+url+"', '"+username+"', '"+encrypted_ciphertext+"')  ")

        print("SUCCESS. Entry has been Inserted.")
        
        print("DATABASE:")
        print("----------")
        listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)
        print("PLAINTEXT PASSWORD: "+plaintext_password)

        text = "DATABASE:"
        
        defaultBotSpeak(text)

        defaultBotAppendToBlitTextList("----------")

        showPlaintextPasswords_RowsThatApply(cursor, 'database_user', current_database_user)
    else:
        text = "Unable to insert entry - Database does not exist."

        defaultBotSpeak(text)


def speakUpdatePassword():
    url = updateEntryData["url"]
    new_password = updateEntryData["new_data"]

    # ENCRYPTION
    encrypted_ciphertext = fullEncrypt(cursor, new_password, current_database_user, plaintext_master_pw)

    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("UPDATE password_manager SET password = '"+encrypted_ciphertext+"' WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")

        text = "SUCCESS. Entry has been Updated."
        
        defaultBotSpeak(text)

        print("")

        text = "DATABASE:"
        
        defaultBotSpeak(text)

        text = "----------"

        defaultBotAppendToBlitTextList(text)

        speakPlaintextPasswords_RowsThatApply(cursor, 'database_user', current_database_user)


def getSalt(cursor, database_user):
    cursor.execute("SELECT salt FROM login_manager WHERE database_user = '"+database_user+"'")
    fetch = cursor.fetchall()[0]
    if len(fetch) != 0:
        hex_salt = fetch[0]
    else:
        # Something random idk - in the case of error
        hex_salt = hex(1)
        print("Salt fetch error. Please try again.")

    return hex_salt


def fullEncrypt(cursor, plaintext_password, current_database_user, plaintext_master_pw):
    hex_salt = getSalt(cursor, current_database_user)

    salt = bytes(hex_salt)

    encrypted_ciphertext = encrypt_password(plaintext_password, plaintext_master_pw, salt)

    return encrypted_ciphertext


def fullDecrypt(cursor, encrypted_password, current_database_user, plaintext_master_pw):
    hex_salt = getSalt(cursor, current_database_user)

    salt = bytes(hex_salt)

    plaintext_password = decrypt_password(encrypted_password, plaintext_master_pw, salt)

    return plaintext_password


# Functions for Listening in Background
def callback(recog, audio):
    if len(speak_queue) == 0: # Only detect whether the user is speaking if the bot is NOT speaking
        global string

        try:
            recognized = recog.recognize_google(audio)

            string = string + " " + recognized

            defaultUserAppendToBlitTextList(recognized)

            print(string)
        except UnknownValueError:
            print("Please say that again.")

        except RequestError as err_msg:
            print("Request Error:")
            print(err_msg)
            print("Please check your internet connection and try again.")
        
        except Exception as e:
            print("Error:")
            print(e)


def start_listening_in_background():
    listening_stopper = recog.listen_in_background(mic, callback, 5)

    return listening_stopper


# Functions for Graphics and UI Display
def getTextWidth(string, font):
    text_image = font.render(string, True, (255,255,255))
    return text_image.get_width()


def get_multi_lined_text(string, font, extraWords="", startX=0, max_width=screenWidth-64):
    multi_lined_text = []
    current_line = extraWords
    x = startX
    space_size = font.size(' ')
    for word in string.split():
        word_image = font.render(word, True, (255,255,255))

        if word_image.get_width() + x >= max_width:

            multi_lined_text.append(current_line)
            current_line = extraWords

            x = startX
        
        current_line = current_line + " " + word
        
        x += word_image.get_width() + space_size[0]

    multi_lined_text.append(current_line)

    return multi_lined_text


def blit_text(string, color, font, position):
    text_image = font.render(string, True, color)
    screen.blit(text_image, position)


def blit_text_with_rect(string, text_color, rect_color, font, position):
    text_image = font.render(string, True, text_color)

    rect_dimensions = (text_image.get_width(), text_image.get_height())
    rect = pygame.Rect(position[0], position[1], rect_dimensions[0], rect_dimensions[1])
    pygame.draw.rect(screen, rect_color, rect)

    screen.blit(text_image, position)


def blit_image(fileName, position):
    image = pygame.image.load(fileName)
    # image = pygame.transform.scale(pygame.image.load(fileName), (32*math.sin(10*time.time())+320, 32*math.sin(10*time.time())+320))
    screen.blit(image, position)


def runAndWaitThread (engine, text):
    global bot_speaking

    bot_speaking = True

    # CURRENT: 14, 52? a bit weird still, sad: 60, canto 131

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[14].id)

    engine.startLoop(False)

    print("Thread")
    engine.say(text)

    while engine.isBusy():
        engine.iterate()
        time.sleep(.01)

    engine.stop()
    engine.endLoop()

    if text in speak_queue:
        speak_queue.remove(text)

    bot_speaking = False
    print("Thread end")
    return


def speak(text):
    thread = threading.Thread(target=runAndWaitThread, daemon=True, args=(engine, text))
    thread.start()

    # start_time = time.time()
    # blit_text_list.append([start_time, "Bot: "+text, (255, 255, 255), font, (0, 0)])


def defaultBotSpeak(text):
    print(text)
    speak_queue.append(text)
    defaultBotAppendToBlitTextList(text)


def speechResponse(string, current_dialogue_memory):
    # This is a bug that suprisingly happens often - it confuses the database during SQL queries
    string = string.replace("'", "")

    reply = " "

    if current_dialogue_memory == 1:
        if string.lower().find("hello") != -1:
            reply = "Hi! How may I help you today?"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("superman") != -1:
            reply = "Did you say superman? I love superman!"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("list") != -1:
            reply = "listing..."

            speakPlaintextPasswords_RowsThatApply(cursor, 'database_user', current_database_user)

        elif string.lower().find("query") != -1:
            current_dialogue_memory = 2
            reply = "Which URL would you like to query?"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("delete all") != -1:
            reply = "deleting..."

            speakDeleteAllEntries()

        elif string.lower().find("delete") != -1: # this includes delete entry - which is probably more command command
            current_dialogue_memory = 3
            reply = "What is the URL of the entry you would like to delete?"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("insert") != -1: # this includes insert entry - which is probably more common command
            current_dialogue_memory = 4
            reply = "What is the URL of the entry?"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("update password") != -1:
            current_dialogue_memory = 10
            reply = "What is the URL of the entry you would like to update?"
            defaultBotAppendToBlitTextList(reply)

        elif string == "":
            return False
        
        else:
            # Conversational Bot is 🔥🔥🔥
            chatMessages.append({"role": "user", "content": string})

            chat_completion = client.chat.completions.create(
                messages=chatMessages,
                model="gpt-3.5-turbo",
                max_tokens=100
            )

            currentBotContent = chat_completion.choices[0].message.content
            chatMessages.append({"role": "system", "content": currentBotContent})

            reply = currentBotContent
            defaultBotAppendToBlitTextList(reply)
            print(chatMessages)
        
    elif current_dialogue_memory == 2:
        if string != "":
            reply = "querying..."
            current_dialogue_memory = 1
            url = string[1:]

            print(url)

            speakQuery(url)
        else:
            return False
        
    elif current_dialogue_memory == 3:
        if string != "":
            reply = "deleting entry..."
            current_dialogue_memory = 1
            url = string[1:]

            speakDeleteEntry(url)
        else:
            return False
        
    elif current_dialogue_memory == 4:
        if string != "":
            current_dialogue_memory = 5
            url = string[1:]

            insertEntryData["url"] = url
            
            reply = "The URL you inputted is "+url+". Please Confirm."
            defaultBotAppendToBlitTextList(reply)
        else:
            return False
        
    elif current_dialogue_memory == 5:
        if string.lower().find("don't confirm") != -1 or string.lower().find("do not confirm") != -1 or string.lower().find("no") != -1 or string.lower().find("cancel") != -1 or string.lower().find("decline") != -1:
            current_dialogue_memory = 4

            insertEntryData["url"] = ""

            reply = "Understood. Please re-enter the URL of your entry"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("yes") != -1 or string.lower().find("confirm") != -1 or string.lower().find("accept") != -1:
            current_dialogue_memory = 6

            reply = "Confirmed. What is the USERNAME of the entry?"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("quit") != -1 or string.lower().find("exit") != -1:
            current_dialogue_memory = 1

            reply = "Understood. Your entry has not been inserted."
            defaultBotAppendToBlitTextList(reply)

        elif string == "":
            return False
        else:
            reply = "Sorry, I don't understand. Please Confirm."
            defaultBotAppendToBlitTextList(reply)

    elif current_dialogue_memory == 6:
        if string != "":
            current_dialogue_memory = 7
            username = string[1:]

            insertEntryData["username"] = username
            
            reply = "The USERNAME you inputted is "+username+". Please Confirm."
            defaultBotAppendToBlitTextList(reply)
        else:
            return False
        
    elif current_dialogue_memory == 7:
        if string.lower().find("don't confirm") != -1 or string.lower().find("do not confirm") != -1 or string.lower().find("no") != -1 or string.lower().find("cancel") != -1 or string.lower().find("decline") != -1:
            current_dialogue_memory = 6

            insertEntryData["username"] = ""

            reply = "Understood. Please re-enter the USERNAME of your entry"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("yes") != -1 or string.lower().find("confirm") != -1 or string.lower().find("accept") != -1:
            current_dialogue_memory = 8

            reply = "Confirmed. What is the PASSWORD of the entry?"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("quit") != -1 or string.lower().find("exit") != -1:
            current_dialogue_memory = 1

            reply = "Understood. Your entry has not been inserted."
            defaultBotAppendToBlitTextList(reply)

        elif string == "":
            return False
        else:
            reply = "Sorry, I don't understand. Please Confirm."
            defaultBotAppendToBlitTextList(reply)

    elif current_dialogue_memory == 8:
        if string != "":
            current_dialogue_memory = 9
            password = string[1:]

            insertEntryData["password"] = password
            
            reply = "The PASSWORD you inputted is "+password+". Please Confirm."
            defaultBotAppendToBlitTextList(reply)
        else:
            return False
        
    elif current_dialogue_memory == 9:
        if string.lower().find("don't confirm") != -1 or string.lower().find("do not confirm") != -1 or string.lower().find("no") != -1 or string.lower().find("cancel") != -1 or string.lower().find("decline") != -1:
            current_dialogue_memory = 8

            insertEntryData["password"] = ""

            reply = "Understood. Please re-enter the PASSWORD of your entry"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("yes") != -1 or string.lower().find("confirm") != -1 or string.lower().find("accept") != -1:
            current_dialogue_memory = 1

            reply = "Confirmed."
            defaultBotAppendToBlitTextList(reply)

            speakInsertEntry()

        elif string.lower().find("quit") != -1 or string.lower().find("exit") != -1:
            current_dialogue_memory = 1

            reply = "Understood. Your entry has not been inserted."
            defaultBotAppendToBlitTextList(reply)
                
        elif string == "":
            return False
        else:
            reply = "Sorry, I don't understand. Please Confirm."
            defaultBotAppendToBlitTextList(reply)

    elif current_dialogue_memory == 10:
        if string != "":
            url = string[1:]

            if checkURLexists(cursor, 'password_manager', url):
                updateEntryData["url"] = url

                current_dialogue_memory = 11

                reply = "What is the password of the entry you would like to update?"
                defaultBotAppendToBlitTextList(reply)
            else:
                current_dialogue_memory = 1

                reply = "URL is unrecognized. The URL you inputted is displayed in text."
                defaultBotAppendToBlitTextList(url)
        else:
            return False
        
    elif current_dialogue_memory == 11:
        if string != "":
            current_dialogue_memory = 12
            new_pw = string[1:]

            updateEntryData["new_data"] = new_pw

            reply = "The new PASSWORD you inputted is "+new_pw+". Please Confirm."
            defaultBotAppendToBlitTextList(reply)
        else:
            return False
        
    elif current_dialogue_memory == 12:
        if string.lower().find("don't confirm") != -1 or string.lower().find("do not confirm") != -1 or string.lower().find("no") != -1 or string.lower().find("cancel") != -1 or string.lower().find("decline") != -1:
            current_dialogue_memory = 11

            updateEntryData["new_data"] = ""

            reply = "Understood. Please re-enter the new PASSWORD of your entry"
            defaultBotAppendToBlitTextList(reply)

        elif string.lower().find("yes") != -1 or string.lower().find("confirm") != -1 or string.lower().find("accept") != -1:
            current_dialogue_memory = 1

            reply = "Confirmed."
            defaultBotAppendToBlitTextList(reply)

            speakUpdatePassword()
                
        elif string == "":
            return False
        else:
            reply = "Sorry, I don't understand. Please Confirm."
            defaultBotAppendToBlitTextList(reply)



    speak_queue.insert(0, reply)

    return current_dialogue_memory


def signupLogin():
    global current_database_user
    global plaintext_master_pw

    # Here we get the user of the database to signup/login, before we do any argument stuff
    print("PASSWORD MANAGER")
    print("----------")
    print("SIGNUP (1) OR LOGIN (2)")
    print("")
    ans = input("")
    os.system('clear')

    while ans != "1" and ans != "2" and ans.lower() != "signup" and ans.lower() != "login":
        print("PLEASE ENTER EITHER SIGNUP (1) OR LOGIN (2)")
        print("")
        ans = input("")
        os.system('clear')


    if ans == "1" or ans.lower() == "signup":
        # SIGNUP
        ans = "2"
        while ans == "2" or ans.lower() == "no":
            # username
            ans = ""
            while ans == "":
                print("Please input your username. This will be your username for the database to help us remember you.")
                print("")
                print("DATABASE USERNAME:")
                ans = input("")
                os.system('clear')

            database_user = ans

            # hint
            ans = ""
            while ans == "":
                print("Please input a question and an answer that is personal to you. This will help us keep your passwords secure.")
                print("")
                print("Some examples of questions and answers are:")
                print("[What is my favourite colour?] Yellow")
                print("[What is my favourite book?] My Dictionary")
                print("[Who is my grandson?] Ben")
                print("[When was I born?] 1990")
                print("")
                print("QUESTION:")
                ans = input("")
                os.system('clear')

            hint = ans

            # password
            ans = ""
            while ans == "":
                print("Please input a question and an answer that is personal to you, and that you will remember. This will help us keep your passwords secure.")
                print("")
                print("Some examples of questions and answers are:")
                print("[What is my favourite colour?] Yellow")
                print("[What is my favourite book?] My Dictionary")
                print("[Who is my grandson?] Ben")
                print("[When was I born?] 1990")
                print("")
                print("ANSWER:")
                ans = input("")
                os.system('clear')

            unhashed_database_pw = ans
            
            # Hashes the Password
            cursor.execute("SELECT sha1('"+unhashed_database_pw+"')")
            hashed_database_pw = cursor.fetchall()[0][0]

            # Generates 16 byte salt
            salt = os.urandom(16)

            # Inserts the data recieved into the database
            cursor.execute("INSERT INTO login_manager(database_user, database_pw, hint, salt) VALUES ('"+database_user+"', '"+hashed_database_pw+"', '"+hint+"', (%s)) RETURNING *", (salt,))
            insert = cursor.fetchall()[0]

            # Confirmation
            print("CONFIRM:")
            print("----------")
            listRowsThatApply(cursor, 'login_manager', 'database_user', database_user, columnSpecifier='database_user, database_pw, hint, salt')
            print("PLAINTEXT PASSWORD: "+unhashed_database_pw)
            print("----------")
            print("YES[1] OR NO[2]")

            while True:
                ans = input("")
                os.system('clear')

                if ans == "2" or ans.lower() == "no":
                    # Deletes entry if user does not confirm
                    cursor.execute("DELETE FROM login_manager WHERE database_user = '"+database_user+"'")

                    print("You will be asked to resubmit everything. Type enter to continue.")
                    input("")
                    os.system('clear')

                    break
                elif ans == "1" or ans.lower() == "yes":
                    print("ACCOUNT ADDED")
                    print("----------")
                    current_database_user = database_user
                    plaintext_master_pw = unhashed_database_pw

                    break
                else:
                    print("Sorry, but you can only type YES[1] OR NO[2]")
    else:
        # LOGIN
        # username
        ans = ""
        while ans == "":
            while ans == "":
                print("DATABASE USERNAME:")
                ans = input("")
                os.system('clear')

            database_user = ans

            # asks hint
            cursor.execute("SELECT EXISTS(SELECT 1 FROM login_manager WHERE database_user = '"+database_user+"')")

            if cursor.fetchall()[0][0]:
                cursor.execute("SELECT * FROM login_manager WHERE database_user = '"+database_user+"'")
                fetch = cursor.fetchall()

                hint = fetch[0][2]
                database_pw = fetch[0][1]
                print("RIDDLE ME THIS:")
                print(hint)
                print("----------")

                # password
                ans = input("")
                cursor.execute("SELECT sha1('"+ans+"')")
                hashed_database_pw = cursor.fetchall()[0][0]
                os.system('clear')

                if hashed_database_pw == database_pw:
                    print("ACCESS GRANTED")

                    current_database_user = database_user
                    plaintext_master_pw = ans
                else:
                    print("ACCESS DENIED")
                    print("Please try again.")
                    print("----------")
                    ans = ""
            else:
                print("Invalid Username. Please try again.")
                print("----------")
                ans = ""


# Arguments
# admin
parser.add_argument("-c", "--create", help="(admins only) create password manager database", action="store_true")
parser.add_argument("-dd", "--drop_database", help="(admins only) delete the password manager database", action="store_true")
parser.add_argument("-lt", "--list_tables", help="(admins only) list tables", action="store_true")

# user
parser.add_argument("-l", "--list", help="list usernames and passwords", action="store_true")
parser.add_argument("-i", "--insert", type=str, nargs=3, help="insert new entry", metavar=("[URL]", "[USERNAME]", "[PASSWORD]"))
parser.add_argument("-de", "--delete_entry", type=str, nargs=1, help="delete specific entry by URL", metavar=("[URL]"))
parser.add_argument("-da", "--delete_all_entries", help="delete all entries owned by you", action="store_true")
parser.add_argument("-up", "--update_password", type=str, nargs=2, help="update password by URL", metavar=("[URL]", "[NEW PASSWORD]"))
parser.add_argument("-uu", "--update_username", type=str, nargs=2, help="update username by URL", metavar=("[URL]", "[NEW USERNAME]"))
parser.add_argument("-q", "--query", type=str, nargs=1, help="Query entry by URL", metavar=("[URL]"))

# Parses the Arguments
args = parser.parse_args()


running = True

# Adjusts recognizer for background noise
with mic:
    recog.adjust_for_ambient_noise(mic, 3)

# Begins listening in background
listening_stopper = start_listening_in_background()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0,0,0))

    currentString = string # To prevent the string from changing during the loop process. currentString updates itself once per loop iteration

    blit_image("sun.png", (450, 450))

    lines = 0
    for i in blit_text_list:
        if i[1] == "bot":
            if len(speak_queue) == 0 and not bot_speaking:
                blit_text_list.remove(i)

        elif i[1] == "user":
            if time.time() - i[0] > 10:
                blit_text_list.remove(i)
        
        if i in blit_text_list:
            blit_text(i[2], i[3], i[4], (0, lines*32))

            lines += 1


    if len(speak_queue) > 0 and not bot_speaking:
        speak(speak_queue[0])

    display.flip()

    speechResponseReturnValue = speechResponse(currentString, current_dialogue_memory)
    if speechResponseReturnValue != False:
        current_dialogue_memory = speechResponseReturnValue
        string = ""


# when it takes an entire 5 lines just to shut down...
pygame.quit()
conn.commit()
cursor.close()
conn.close()
exit()
