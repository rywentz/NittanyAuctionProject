# This code is a modified version of the original template code given to us to use.
# Original code credits to Penn State University CMPSC 431W Spring 2026 Semester

import csv
from flask import Flask, render_template, request
import sqlite3 as sql
import hashlib

app = Flask(__name__)
host = 'http://127.0.0.1:5000'

csvPath = 'NittanyAuctionDataset_v1/Users.csv'

@app.route('/')
def homepage():
    return render_template('homepage.html')

# @app.route('/welcome', methods=['POST', 'GET'])
# def welcome():
#     return render_template('welcome.html')

# @app.route('/homepage', methods =["GET", "POST"])
# def gfg():
#     if request.method == "GET":
#        # getting input with name = fname in HTML form
#        email = request.form.get("email")
#        # getting input with name = lname in HTML form
#        pwd = request.form.get("pwd")
#        return "login is "+ email + pwd
#     return render_template("homepage.html")

@app.route('/addpatient', methods=['POST', 'GET'])
def check_name_on_add():
    error = None
    if request.method == 'POST':
        result = add_name(request.form['FirstName'], request.form['LastName'])
        if result:
            return render_template('addpatient.html', error=error, result=result)
        else:
            error = 'invalid input name'
    return render_template('addpatient.html', error=error)


@app.route('/removepatient', methods=['POST', 'GET'])
def check_name_on_removal():
    error = None
    if request.method == 'POST':
        result = remove_name(request.form['FirstName'], request.form['LastName'])
        if result:
            return render_template('removepatient.html', error=error, result=result)
        else:
            error = 'invalid input name'
    else:
        result = ret_data()
    return render_template('removepatient.html', error=error, result=result)



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email_user = request.form["email"]
        password_user = request.form["password"]

        connection = sql.connect('database.db')
        connection.execute('CREATE TABLE IF NOT EXISTS Users(email TEXT PRIMARY KEY, password TEXT);')
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = ?;', (email_user,))
        user = cursor.fetchone()

        if hashing(password_user) == user[1]:
            print("YIPPEEE")




    return render_template('login.html')

@app.route('/welcome', methods=['POST', 'GET'])
def welcome():
    return render_template('welcome.html')



def add_name(first_name, last_name):
    connection = sql.connect('database.db')
    # connect to database.db and create new patients table
    # autoincrement pid of patients, take arguments from function call and put into firstname and lastname of row in patients
    connection.execute('CREATE TABLE IF NOT EXISTS patients(PID INTEGER PRIMARY KEY AUTOINCREMENT, firstname TEXT, lastname TEXT);')
    connection.execute('INSERT INTO patients (firstname, lastname) VALUES (?,?);', (first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM patients;')
    return cursor.fetchall()

#this function serves to remove patient data from the db based on patient first and last name
def remove_name(first_name, last_name):
    #connect to database.db
    connection = sql.connect('database.db')
    #take arguments from function call and remove based on first name and last name
    connection.execute('DELETE FROM patients WHERE firstname = ? AND lastname = ?;', (first_name, last_name))
    connection.commit()
    cursor = connection.execute('SELECT * FROM patients;')
    return cursor.fetchall()

#this function serves to return all the data from the db on an initial GET request to the page
def ret_data():
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM patients;')
    return cursor.fetchall()



#hashing algorithm that takes a word and hashes it to a SHA256 hash.
def hashing(password):
    sha256 = hashlib.sha256()
    sha256.update(password.encode('utf-8'))
    return sha256.hexdigest()

def populate_users(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS Users(email TEXT PRIMARY KEY, password TEXT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            email = row["email"].strip()
            password = row["password"].strip()

            hashed_password = hashing(password)

            cursor.execute('INSERT INTO Users (email, password) VALUES (?,?);', (email, hashed_password))
    connection.commit()

if __name__ == "__main__":
    print("this is hash of 'database' " + hashing("database"))
    populate_users(csvPath)
    connection = sql.connect('database.db')
    app.run(debug=True)


