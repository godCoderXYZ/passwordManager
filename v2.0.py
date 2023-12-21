# Pygame
import pygame
from pygame import display

# Argument Parsing
import argparse

# Python files
import conn_password

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

# Generic Random Libraries
import threading
import time
import math
import os

# VARIABLES
# Initializing and Setup
pygame.init()

engine = pyttsx3.init()

mic = Microphone()
recog = Recognizer()

# Initializes the Parser
parser = argparse.ArgumentParser(
    description="Password Manager"
)

# Setup the connection and cursor
conn = psycopg2.connect(dbname = "ps", user = "postgres", password = conn_password.getPW())

cursor = conn.cursor()

# "Normal" variables
string = ""

current_database_user = "bob"
plaintext_master_pw = "bob"

blit_text_list = []
speak_queue = []
bot_speaking = False

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
                        speak_queue.append(text)
                        defaultBotAppendToBlitTextList(text)

                    print("----------")
        else:
            text = "Database is empty OR Item does not exist."
            print("[Database is empty] OR [Item does not exist]")
            speak_queue.append(text)
            defaultBotAppendToBlitTextList(text)

    else:
        text = "Database does not exist."
        print("Database does not exist.")
        speak_queue.append(text)
        defaultBotAppendToBlitTextList(text)



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

                        print(text)

                        # speak(text)
                        speak_queue.append(text)

                        defaultBotAppendToBlitTextList(text)

                        if columnReference[y][0] == "password":
                            # Decrypts Encrypted Password To Get Plaintext Password
                            encrypted_password = rows[x][y]
                            plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user, plaintext_master_pw)
                    
                    if plaintext_password:
                        text = "PLAINTEXT PASSWORD: "+plaintext_password
                        print(text)
                        speak_queue.append(text)
                        # speak(text)

                        defaultBotAppendToBlitTextList(text)
                    else:
                        text = "ERROR: PLAINTEXT PASSWORD WAS UNABLE TO BE FETCHED. Please try again."
                        print(text)
                        speak_queue.append(text)
                        # speak(text)

                        defaultBotAppendToBlitTextList(text)

                    text = "----------"

                    print(text)
                    defaultBotAppendToBlitTextList(text)
        else:
            text = "Database is empty OR Item does not exist."

            print(text)
            speak_queue.append(text)
            # speak("Database is empty OR Item does not exist.")

            defaultBotAppendToBlitTextList(text)
    else:
        text = "Database does not exist."
        print(text)
        speak_queue.append(text)
        # speak(text)

        defaultBotAppendToBlitTextList(text)


def defaultBotAppendToBlitTextList(text):
    start_time = time.time()
    blit_text_list.append([start_time, "Bot: "+text, (255, 255, 255), font, (0, 0)])

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
    global string
    try:
        recognized = recog.recognize_google(audio)

        string = string + " " + recognized

        print(string)
    except UnknownValueError:
        print("Please say that again.")

    except RequestError as err_msg:
        print("Request Error:")
        print(err_msg)
        print("Please check your internet connection and try again.")


def start_listening_in_background():
    listening_stopper = recog.listen_in_background(mic, callback, 3)

    return listening_stopper


# Functions for Graphics and UI Display
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

    syllableCount = syllapy.count(text)
    print(str(syllableCount)+":"+text)

    if syllableCount == 0:
        syllableCount = 10

    engine.startLoop(False)

    print("Thread")
    engine.say(text)

    start = time.time()

    # while time.time() - start < (syllableCount):
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


def speechResponse(string):
    # # Arguments
    # # admin
    # parser.add_argument("-c", "--create", help="(admins only) create password manager database", action="store_true")
    # parser.add_argument("-dd", "--drop_database", help="(admins only) delete the password manager database", action="store_true")
    # parser.add_argument("-lt", "--list_tables", help="(admins only) list tables", action="store_true")

    # # user
    # parser.add_argument("-l", "--list", help="list usernames and passwords", action="store_true")
    # parser.add_argument("-i", "--insert", type=str, nargs=3, help="insert new entry", metavar=("[URL]", "[USERNAME]", "[PASSWORD]"))
    # parser.add_argument("-de", "--delete_entry", type=str, nargs=1, help="delete specific entry by URL", metavar=("[URL]"))
    # parser.add_argument("-da", "--delete_all_entries", help="delete all entries owned by you", action="store_true")
    # parser.add_argument("-up", "--update_password", type=str, nargs=2, help="update password by URL", metavar=("[URL]", "[NEW PASSWORD]"))
    # parser.add_argument("-uu", "--update_username", type=str, nargs=2, help="update username by URL", metavar=("[URL]", "[NEW USERNAME]"))
    # parser.add_argument("-q", "--query", type=str, nargs=1, help="Query entry by URL", metavar=("[URL]"))
    reply = ""
    if string.lower().find("hello") != -1:
        reply = "Hi! How may I help you today?"

        print("hello detected")

    elif string.lower().find("superman") != -1:
        reply = "Did you say superman? I love superman!"

        print("superman detected")
    elif string.lower().find("list") != -1:
        reply = "listing..."

        print("list detected")

        speakPlaintextPasswords_RowsThatApply(cursor, 'database_user', current_database_user)
    elif string.lower().find("query") != -1:
        url = string.split("query")[1][1:]
        print(url)

        # This is a bug that suprisingly happens often - it confuses the database during SQL queries
        if url.find("'") != -1:
            return False

        if checkURLexists(cursor, 'password_manager', url):
            reply = "querying..."

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
                speak_queue.append(text)
                defaultBotAppendToBlitTextList(text)
            else:
                text = "Error: Message corrupted. Please try again."

                print(text)
                speak_queue.append(text)
                defaultBotAppendToBlitTextList(text)
        else:
            reply = "Please Provide a URL or URL does not exist"
    else:
        return False

    speak(reply)

    return True


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

    blit_text_with_rect(currentString, (0, 0, 54), (34,112,34), font, (0, screenHeight/2))
    blit_image("sun.png", (450, 450))
    lines = 0
    for i in blit_text_list:
        # if time.time() - i[0] < 30:
        if len(speak_queue) != 0:
            blit_text(i[1], i[2], i[3], (0, lines*32))

            lines += 1

        else:
            blit_text_list.remove(i)

    # print(blit_text_list)

    if len(speak_queue) > 0 and not bot_speaking:
        speak(speak_queue[0])
        bot_speaking = True

    display.flip()

    if speechResponse(currentString):
        string = ""

    # print(string)

# when it takes an entire 5 lines just to shut down...
pygame.quit()
conn.commit()
cursor.close()
conn.close()
exit()
