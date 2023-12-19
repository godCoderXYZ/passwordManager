import psycopg2
import argparse
import conn_password
import os


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
            for i in range(len(tableReference)):
                print("ID: "+str(tableReference[i][0]))
                print("URL: "+tableReference[i][1])
                print("USERNAME: "+tableReference[i][2])
                print("PASSWORD: "+tableReference[i][3])
                print("----------")
        else:
            print("[Database is empty]")
    else:
        print("Password Manager Database does not exist.")


def checkURLexists(cursor, tablename, url):
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
                listTable(cursor, tablename)
        else:
            print("Database is empty")
    else:
        print("Database does not Exist")

    return False


# Initializes the Parser
parser = argparse.ArgumentParser(
    description="Password Manager"
)


# Arguments
parser.add_argument("-l", "--list", help="list usernames and passwords", action="store_true")
parser.add_argument("-c", "--create", help="create password manager database", action="store_true")
parser.add_argument("-dd", "--drop_database", help="delete the password manager database", action="store_true")
parser.add_argument("-i", "--insert", type=str, nargs=3, help="insert new entry", metavar=("[URL]", "[USERNAME]", "[PASSWORD]"))
parser.add_argument("-de", "--delete_entry", type=str, nargs=1, help="delete specific entry by URL", metavar=("[URL]"))
parser.add_argument("-up", "--update_password", type=str, nargs=2, help="update password by URL", metavar=("[URL]", "[NEW PASSWORD]"))
parser.add_argument("-uu", "--update_username", type=str, nargs=2, help="update username by URL", metavar=("[URL]", "[NEW USERNAME]"))
parser.add_argument("-q", "--query", type=str, nargs=1, help="Query entry by URL", metavar=("[URL]"))

# Parses the Arguments
args = parser.parse_args()

# Setup the connection and cursor
conn = psycopg2.connect(dbname = "ps", user = "postgres", password = conn_password.getPW())

cursor = conn.cursor()

os.system('clear')

# # Printing for debug
# print("")
# print(args)
# print("")

if args.list:
    print("COMMAND: LIST")
    print("")

    listTable(cursor, 'password_manager')


elif args.create:
    print("COMMAND: CREATE")
    print("")
    if tableExists(cursor, 'password_manager'):
        print("Database already exists")
    else:
        cursor.execute('''CREATE TABLE password_manager(
                id SERIAL PRIMARY KEY,
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


elif args.insert:
    url = args.insert[0]
    username = args.insert[1]
    password = args.insert[2]

    if tableExists(cursor, 'password_manager'):
        cursor.execute("INSERT INTO password_manager(url, username, password) VALUES ('"+url+"', '"+username+"', '"+password+"')  ")

        print("SUCCESS. Entry has been Inserted.")
        print("")

        print("DATABASE:")
        listTable(cursor, 'password_manager')
    else:
        print("Unable to insert entry - Database does not exist. Use argument --create to create database.")


elif args.delete_entry:
    url = args.delete_entry[0]
    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("DELETE FROM password_manager WHERE url = '"+url+"'")

        print("SUCCESS. Entry has been Deleted.")
        print("")

        print("DATABASE:")
        listTable(cursor, 'password_manager')
        

elif args.update_password:
    url = args.update_password[0]
    new_password = args.update_password[1]

    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("UPDATE password_manager SET password = '"+new_password+"' WHERE url = '"+url+"'")

        print("SUCCESS. Entry has been Updated.")
        print("")

        print("DATABASE:")
        print("----------")
        listTable(cursor, 'password_manager')


elif args.update_username:
    url = args.update_username[0]
    new_username = args.update_username[1]

    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("UPDATE password_manager SET username = '"+new_username+"' WHERE url = '"+url+"'")

        print("SUCCESS. Entry has been Updated.")
        print("")

        print("DATABASE:")
        print("----------")
        listTable(cursor, 'password_manager')


elif args.query:
    url = args.query[0]

    if checkURLexists(cursor, 'password_manager', url):
        cursor.execute("SELECT id, url, username, password FROM password_manager WHERE url = '"+url+"'")
        queryRow = cursor.fetchall()[0]
        print("SUCCESS. QUERY:")
        print("----------")
        print("ID: "+str(queryRow[0]))
        print("URL: "+queryRow[1])
        print("USERNAME: "+queryRow[2])
        print("PASSWORD: "+queryRow[3])


print("") # Readability

conn.commit()
exit()
