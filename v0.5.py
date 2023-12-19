import psycopg2
import argparse
import conn_password
import os
from Cryptodome.Cipher import AES
from pbkdf2 import PBKDF2
from base64 import b64encode, b64decode


def encrypt_password(plaintext_password, hashed_master_password, salt=b'ez.gg', iterations=6000):
    key = PBKDF2(str(hashed_master_password), salt, iterations=iterations).read(32)

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
    

# Functions
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
                            plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user)
                    
                    if plaintext_password:
                        print("PLAINTEXT PASSWORD: "+plaintext_password)
                    else:
                        print("ERROR: PLAINTEXT PASSWORD WAS UNABLE TO BE FETCHED. Please try again.")
                    print("----------")
        else:
            print("[Database is empty] OR [Item does not exist]")

    else:
        print("Database does not exist.")


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


def getSaltAndMasterPassword(cursor, database_user):
    cursor.execute("SELECT salt, database_pw FROM login_manager WHERE database_user = '"+database_user+"'")
    fetch = cursor.fetchall()[0]

    hex_salt = fetch[0]
    database_pw = fetch[1]

    return hex_salt, database_pw

# Initializes the Parser
parser = argparse.ArgumentParser(
    description="Password Manager"
)


def fullEncrypt(cursor, plaintext_password, current_database_user):
    hex_salt, hashed_master_pw = getSaltAndMasterPassword(cursor, current_database_user)

    salt = bytes(hex_salt)

    encrypted_ciphertext = encrypt_password(plaintext_password, hashed_master_pw, salt)

    return encrypted_ciphertext


def fullDecrypt(cursor, encrypted_password, current_database_user):
    hex_salt, hashed_master_pw = getSaltAndMasterPassword(cursor, current_database_user)

    salt = bytes(hex_salt)

    plaintext_password = decrypt_password(encrypted_password, hashed_master_pw, salt)

    return plaintext_password


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

# Setup the connection and cursor
conn = psycopg2.connect(dbname = "ps", user = "postgres", password = conn_password.getPW())

cursor = conn.cursor()

os.system('clear')

current_database_user = ""

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
        print(salt)

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
            else:
                print("ACCESS DENIED")
                print("Please try again.")
                print("----------")
                ans = ""
        else:
            print("Invalid Username. Please try again.")
            print("----------")
            ans = ""


if args.list:
    print("COMMAND: LIST")
    print("")

    listPlaintextPasswords_RowsThatApply(cursor, 'database_user', current_database_user)
    # listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)


elif args.create:
    print("COMMAND: CREATE")
    print("")
    if tableExists(cursor, 'password_manager'):
        print("Database already exists")
    else:
        cursor.execute('''CREATE TABLE password_manager(
                database_user TEXT,
                url TEXT,
                username TEXT,
                password TEXT
                )''')
        if tableExists(cursor, 'password_manager'):
            cursor.execute("SELECT * FROM password_manager")

            print(cursor.fetchall())
            print("")
            print("SUCCESS. Password Manager Database has been created.")
        else:
            print("There was an error with creating the password manager database. Please Try Again.")

            
elif args.drop_database:
    print("COMMAND: DROP")
    print("")
    if tableExists(cursor, 'password_manager'):
        cursor.execute("DROP TABLE password_manager")

        if tableExists(cursor, 'password_manager'):
            print("There was an error with dropping the password manager database. Please Try Again.")
        else:
            print("SUCCESS. Password Manager Database has been dropped")
    else:
        print("Database does not exist.")


elif args.list_tables:
    print("LOGIN_MANAGER")
    print("----------")
    listTable(cursor, 'login_manager')
    print("")

    print("PASSWORD_MANAGER")
    print("----------")
    listTable(cursor, 'password_manager')


elif args.insert:
    url = args.insert[0]
    username = args.insert[1]
    plaintext_password = args.insert[2]

    # ENCRYPTION
    encrypted_ciphertext = fullEncrypt(cursor, plaintext_password, current_database_user)


    if tableExists(cursor, 'password_manager'):
        cursor.execute("INSERT INTO password_manager(database_user, url, username, password) VALUES ('"+current_database_user+"', '"+url+"', '"+username+"', '"+encrypted_ciphertext+"')  ")

        print("SUCCESS. Entry has been Inserted.")
        
        print("DATABASE:")
        print("----------")
        listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)
        print("PLAINTEXT PASSWORD: "+plaintext_password)
    else:
        print("Unable to insert entry - Database does not exist. Use argument --create to create database.")


elif args.delete_entry:
    url = args.delete_entry[0]
    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("DELETE FROM password_manager WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")

        print("SUCCESS. Entry has been Deleted.")
        print("")

        print("DATABASE:")
        print("----------")
        listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)

elif args.delete_all_entries:
    if tableExists(cursor, 'password_manager'):
        cursor.execute("SELECT * FROM password_manager WHERE database_user = '"+current_database_user+"'")
        rowNum = len(cursor.fetchall())

        if rowNum > 0:
            cursor.execute("DELETE FROM password_manager WHERE database_user = '"+current_database_user+"'")
            print("SUCCESS. Your Database Entries have been deleted.")
            print("")

            print("DATABASE:")
            print("----------")
            listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)
        else:
            print("[Your Database is already empty]")
    else:
        print("Database does not exist.")
        

elif args.update_password:
    url = args.update_password[0]
    new_password = args.update_password[1]

    # ENCRYPTION
    encrypted_ciphertext = fullEncrypt(cursor, new_password, current_database_user)

    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("UPDATE password_manager SET password = '"+encrypted_ciphertext+"' WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")

        print("SUCCESS. Entry has been Updated.")
        print("")

        print("DATABASE:")
        print("----------")
        listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)


elif args.update_username:
    url = args.update_username[0]
    new_username = args.update_username[1]

    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("UPDATE password_manager SET username = '"+new_username+"' WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")

        print("SUCCESS. Entry has been Updated.")
        print("")

        print("DATABASE:")
        print("----------")

        listRowsThatApply(cursor, 'password_manager', 'database_user', current_database_user)


elif args.query:
    url = args.query[0]

    if checkURLexists(cursor, 'password_manager', url):
        # DECRYPTION
        cursor.execute("SELECT password FROM password_manager WHERE (url = '"+url+"' AND database_user = '"+current_database_user+"')")
        encrypted_password = cursor.fetchall()[0][0]

        plaintext_password = fullDecrypt(cursor, encrypted_password, current_database_user)

        if plaintext_password:
            # Prints query
            print("SUCCESS. QUERY:")
            print("----------")
            listRowsThatApply(cursor, 'password_manager', 'url', url, 'database_user', current_database_user)
            print("PLAINTEXT PASSWORD: "+plaintext_password)
            print("----------")
        else:
            print("Error: Message corrupted. Please try again.")



print("") # Readability


# when it takes an entire 4 lines just to shut down...
conn.commit()
cursor.close()
conn.close()
exit()
