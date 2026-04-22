# This code is a modified version of the original template code given to us to use.
# Original code credits to Penn State University CMPSC 431W Spring 2026 Semester

import csv

from flask import Flask, render_template, request, session, sessions, redirect, jsonify
import sqlite3 as sql

import hashlib
from datetime import date
import uuid

app = Flask(__name__)
app.secret_key = 'NITTANYAUCTION'
host = 'http://127.0.0.1:5000'

# Path to all CVS files

Address_csvPath = 'NittanyAuctionDataset_v1/Address.csv'
Auction_Listings_csvPath = 'NittanyAuctionDataset_v1/Auction_Listings.csv'
Bidders_csvPath = 'NittanyAuctionDataset_v1/Bidders.csv'
Bids_csvPath = 'NittanyAuctionDataset_v1/Bids.csv'
Categories_csvPath = 'NittanyAuctionDataset_v1/Categories.csv'
Credit_Cards_csvPath = 'NittanyAuctionDataset_v1/Credit_Cards.csv'
Helpdesk_csvPath = 'NittanyAuctionDataset_v1/Helpdesk.csv'
Local_Vendors_csvPath = 'NittanyAuctionDataset_v1/Local_Vendors.csv'
Ratings_csvPath = 'NittanyAuctionDataset_v1/Ratings.csv'
Requests_csvPath = 'NittanyAuctionDataset_v1/Requests.csv'
Sellers_csvPath = 'NittanyAuctionDataset_v1/Sellers.csv'
Transactions_csvPath = 'NittanyAuctionDataset_v1/Transactions.csv'
Users_csvPath = 'NittanyAuctionDataset_v1/Users.csv'
Zipcode_Info_csvPath = 'NittanyAuctionDataset_v1/Zipcode_Info.csv'
Image_Path_cvsPath = 'NittanyAuctionDataset_v1/Image_Paths.csv'
Watchlist_csvPath = 'NittanyAuctionDataset_v1/Watchlist.csv'
Stop_Time_csvPath = 'NittanyAuctionDataset_v1/stop_times.csv'


@app.route('/')
def homepage():
    return render_template('homepage.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        email_user = request.form["email"]
        password_user = request.form["password"]

        connection = sql.connect('database.db')
        connection.execute('CREATE TABLE IF NOT EXISTS Users(email TEXT PRIMARY KEY, password TEXT);')
        if not check_in_system(email_user):
            error = 'We do not have sufficient information to complete your request. Please contact the help desk or create a new account.'
            connection.close()
            return render_template('login.html', error=error)

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = ?;', (email_user,))
        user = cursor.fetchone()

        if user and hashing(password_user) == user[1]:
            session['email'] = email_user
            try:
                cursor.execute('SELECT * FROM Helpdesk WHERE email = ?;', (email_user,))
                if cursor.fetchone():
                    session['role'] = 'HelpDesk'
                    connection.close()
                    return render_template('welcome.html', role='HelpDesk', email=email_user)
            except sql.OperationalError:
                pass
            try:
                cursor.execute('SELECT * FROM Sellers WHERE email = ?;', (email_user,))
                if cursor.fetchone():
                    session['role'] = 'Seller'
                    connection.close()
                    return render_template('welcome.html', role='Seller', email=email_user)
            except sql.OperationalError:
                pass
            session['role'] = 'Buyer'
            connection.close()
            return render_template('welcome.html', role='Buyer', email=email_user)
        else:
            connection.close()
            error = 'Incorrect password or email, try again.'


    return render_template('login.html', error=error)


@app.route('/createaccount', methods=['POST', 'GET'])
def createaccount():
    error = None
    success = None
    if request.method == 'POST':
        email_user = request.form["email"]
        password_user = request.form["password"]
        first_name = request.form["firstname"]
        last_name = request.form["lastname"]
        dob = request.form["dob"]
        major = request.form["major"]
        street_number = request.form["streetnum"]
        street_name = request.form["streetname"]
        city = request.form["city"]
        state = request.form["state"]
        zipcode = request.form["zipcode"]

        try:
            age = calculate_age(dob)
        except ValueError:
            error = "Invalid Date."
            return render_template('createaccount.html', error=error, success=success)

        address_id = uuid.uuid4().hex

        connection = sql.connect('database.db')
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute('SELECT * FROM Users WHERE email = ?;', (email_user,))
        existing = cursor.fetchone()

        if existing:
            error = 'An account with that email already exists.'
        else:
            hashed_password = hashing(password_user)
            cursor.execute('INSERT INTO Users (email, password) VALUES (?, ?);', (email_user, hashed_password))
            cursor.execute('INSERT OR IGNORE INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)', (zipcode, city, state))
            cursor.execute('INSERT INTO Address (address_ID, zipcode, street_num, street_name) VALUES (?, ?, ?, ?)', (address_id, zipcode, street_number, street_name))
            cursor.execute('INSERT INTO Bidders (email, first_name, last_name, age, home_address_id, major) VALUES (?, ?, ?, ?, ?, ?)', (email_user, first_name, last_name, age, address_id, major))
            connection.commit()
            success = 'Account created successfully! You can now log in.'

    return render_template('createaccount.html', error=error, success=success)


@app.route('/welcome/', methods=['POST', 'GET'])  # <email>
def welcome():
    return render_template('welcome.html', email=session.get('email'), role=session.get('role'))


@app.route('/logout')
def logout():
    ##logout logic
    session.clear()
    return render_template('login.html')


@app.route('/account', methods=['POST', 'GET'])
def view_account():
    ##pull account data from db
    #DEBUG:
    print(session.get('role'))

    if session.get('role') == 'Buyer':
        email = session.get('email')
        user = pull_user(email)
        address_info = pull_address(email)
        profile_picture = pull_image("Profile Picture")

        card_info = pull_credit_card(email)
        if card_info:
            expire_date = '{} / {}'.format(card_info[2], card_info[3])
            return render_template('account.html', email=session.get('email'), fname=user[0], lname=user[1],
                                   role=session.get('role'), address=address_info, card_num=card_info[0], card_type=card_info[1],
                                   exp=expire_date, security_code=card_info[4], picture=profile_picture)
        else:
            return render_template('account.html', email=session.get('email'), fname=user[0], lname=user[1],
                                   role=session.get('role'), address=address_info, card_num=None,
                                   card_type=None, exp=None, security_code=None, picture=profile_picture)
    elif session.get('role') == 'Seller':
        email = session.get('email')
        if check_lv_status(email): #true if lv, false if just seller
            #DEBUG
            print(email)
            print('should be local vendor')
            seller = pull_lv(email)
            print(seller)
            role = '{} (as Local Vendor)'.format(session.get('role'))
            address_id = seller[5]
            address = pull_business_address(address_id)
            profile_picture = pull_image("Profile Picture")
            average_rating = get_average_rating(email)
            return render_template('lvaccount.html', email=session.get('email'),
                                   acc_num=seller[1], route_num=seller[2], bal=seller[3],
                                   role=role, business=seller[4], csphone=seller[6],
                                   address=address, picture=profile_picture, rating=average_rating)
        else:   #user is just a seller, no business information needed
            email = session.get('email')
            user = pull_user(email)
            address_info = pull_address(email)
            card_info = pull_credit_card(email)
            expire_date = '{} / {}'.format(card_info[2], card_info[3])
            bank = pull_bank_info(email)
            profile_picture = pull_image("Profile Picture")
            average_rating = get_average_rating(email)
            return render_template('selleraccount.html', email=session.get('email'), fname=user[0], lname=user[1],
                                   role=session.get('role'), address=address_info, card_num=card_info[0],
                                   card_type=card_info[1],
                                   acc_num=bank[0], route_num=bank[1], bal=bank[2],
                                   exp=expire_date, security_code=card_info[4], picture=profile_picture, rating=average_rating)

    return render_template('account.html')


@app.route('/edit_profile', methods=['GET'])
def edit_profile():
    if 'email' not in session:
        return redirect('/login')

    email = session.get('email')
    role = session.get('role')
    message = request.args.get('message')
    message_type = request.args.get('message_type')

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    if role == 'Buyer':
        cursor.execute('SELECT first_name, last_name, major, home_address_id FROM Bidders WHERE email = ?', (email,))
        bidder = cursor.fetchone()

        if bidder is None:
            connection.close()
            return redirect('/account')

        first_name, last_name, major, address_id = bidder

        cursor.execute('SELECT street_num, street_name, zipcode FROM Address WHERE address_ID = ?', (address_id,))
        address_row = cursor.fetchone()

        city = ''
        state = ''
        street_num = ''
        street_name = ''
        zipcode = ''

        if address_row is not None:
            street_num, street_name, zipcode = address_row
            cursor.execute('SELECT city, state FROM Zipcode_Info WHERE zipcode = ?', (zipcode,))
            zip_row = cursor.fetchone()
            if zip_row is not None:
                city, state = zip_row

        connection.close()

        return render_template(
            'editprofile.html',
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            major=major,
            street_num=street_num,
            street_name=street_name,
            zipcode=zipcode,
            city=city,
            state=state,
            message=message,
            message_type=message_type
        )

    elif role == 'Seller':
        cursor.execute('SELECT first_name, last_name, home_address_id FROM Bidders WHERE email = ?', (email,))
        seller_row = cursor.fetchone()

        if seller_row is None:
            connection.close()
            return redirect('/account')

        first_name, last_name, address_id = seller_row

        cursor.execute('SELECT street_num, street_name, zipcode FROM Address WHERE address_ID = ?', (address_id,))
        address_row = cursor.fetchone()

        city = ''
        state = ''
        street_num = ''
        street_name = ''
        zipcode = ''

        if address_row is not None:
            street_num, street_name, zipcode = address_row
            cursor.execute('SELECT city, state FROM Zipcode_Info WHERE zipcode = ?', (zipcode,))
            zip_row = cursor.fetchone()
            if zip_row is not None:
                city, state = zip_row

        connection.close()

        return render_template(
            'editprofile.html',
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            major='',
            street_num=street_num,
            street_name=street_name,
            zipcode=zipcode,
            city=city,
            state=state,
            message=message,
            message_type=message_type
        )

    connection.close()
    return redirect('/account')


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'email' not in session:
        return redirect('/login')

    email = session.get('email')
    role = session.get('role')

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    if role == 'Buyer':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        major = request.form['major']
        street_num = request.form['street_num']
        street_name = request.form['street_name']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        new_password = request.form['new_password']

        cursor.execute('SELECT first_name, last_name, major, home_address_id FROM Bidders WHERE email = ?', (email,))
        bidder_row = cursor.fetchone()

        if bidder_row is None:
            connection.close()
            return redirect('/account')

        current_first_name, current_last_name, current_major, address_id = bidder_row

        cursor.execute('SELECT street_num, street_name, zipcode FROM Address WHERE address_ID = ?', (address_id,))
        address_row = cursor.fetchone()

        current_street_num = ''
        current_street_name = ''
        current_zipcode = ''
        current_city = ''
        current_state = ''

        if address_row is not None:
            current_street_num, current_street_name, current_zipcode = address_row
            cursor.execute('SELECT city, state FROM Zipcode_Info WHERE zipcode = ?', (current_zipcode,))
            zip_row = cursor.fetchone()
            if zip_row is not None:
                current_city, current_state = zip_row

        profile_changed = (
            str(first_name) != str(current_first_name) or
            str(last_name) != str(current_last_name) or
            str(major) != str(current_major) or
            str(street_num) != str(current_street_num) or
            str(street_name) != str(current_street_name) or
            str(zipcode) != str(current_zipcode) or
            str(city) != str(current_city) or
            str(state) != str(current_state)
        )

        password_changed = new_password.strip() != ''

        if not profile_changed and not password_changed:
            connection.close()
            return redirect('/edit_profile?message=No+changes+were+made&message_type=info')

        if profile_changed:
            cursor.execute(
                'UPDATE Bidders SET first_name = ?, last_name = ?, major = ? WHERE email = ?', (first_name, last_name, major, email))

            cursor.execute(
                'UPDATE Address SET street_num = ?, street_name = ?, zipcode = ? WHERE address_ID = ?', (street_num, street_name, zipcode, address_id))

            cursor.execute(
                'INSERT OR REPLACE INTO Zipcode_Info(zipcode, city, state) VALUES (?, ?, ?)',
                (zipcode, city, state)
            )

        if password_changed:
            hashed_password = hashing(new_password)
            cursor.execute('UPDATE Users SET password = ? WHERE email = ?', (hashed_password, email))

        connection.commit()
        connection.close()

        if profile_changed and password_changed:
            return redirect('/edit_profile?message=Your+profile+and+password+have+been+updated&message_type=success')
        elif profile_changed:
            return redirect('/edit_profile?message=Your+profile+has+been+updated&message_type=success')
        else:
            return redirect('/edit_profile?message=Your+password+has+been+updated&message_type=success')


    elif role == 'Seller':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        street_num = request.form['street_num']
        street_name = request.form['street_name']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        new_password = request.form['new_password']

        cursor.execute('SELECT first_name, last_name, home_address_id FROM Bidders WHERE email = ?', (email,))
        seller_row = cursor.fetchone()

        if seller_row is None:
            connection.close()
            return redirect('/account')

        current_first_name, current_last_name, address_id = seller_row

        cursor.execute('SELECT street_num, street_name, zipcode FROM Address WHERE address_ID = ?', (address_id,))
        address_row = cursor.fetchone()

        current_street_num = ''
        current_street_name = ''
        current_zipcode = ''
        current_city = ''
        current_state = ''

        if address_row is not None:
            current_street_num, current_street_name, current_zipcode = address_row
            cursor.execute('SELECT city, state FROM Zipcode_Info WHERE zipcode = ?', (current_zipcode,))
            zip_row = cursor.fetchone()
            if zip_row is not None:
                current_city, current_state = zip_row

        profile_changed = (
            str(first_name) != str(current_first_name) or
            str(last_name) != str(current_last_name) or
            str(street_num) != str(current_street_num) or
            str(street_name) != str(current_street_name) or
            str(zipcode) != str(current_zipcode) or
            str(city) != str(current_city) or
            str(state) != str(current_state)
        )

        password_changed = new_password.strip() != ''

        if not profile_changed and not password_changed:
            connection.close()
            return redirect('/edit_profile?message=No+changes+were+made&message_type=info')

        if profile_changed:
            cursor.execute(
                'UPDATE Bidders SET first_name = ?, last_name = ? WHERE email = ?', (first_name, last_name, email))

            cursor.execute(
                'UPDATE Address SET street_num = ?, street_name = ?, zipcode = ? WHERE address_ID = ?', (street_num, street_name, zipcode, address_id))

            cursor.execute('INSERT OR REPLACE INTO Zipcode_Info(zipcode, city, state) VALUES (?, ?, ?)', (zipcode, city, state))

        if password_changed:
            hashed_password = hashing(new_password)
            cursor.execute('UPDATE Users SET password = ? WHERE email = ?', (hashed_password, email))

        connection.commit()
        connection.close()

        if profile_changed and password_changed:
            return redirect('/edit_profile?message=Your+profile+and+password+have+been+updated&message_type=success')
        elif profile_changed:
            return redirect('/edit_profile?message=Your+profile+has+been+updated&message_type=success')
        else:
            return redirect('/edit_profile?message=Your+password+has+been+updated&message_type=success')

    connection.close()
    return redirect('/account')


@app.route('/watchlist', methods=['GET'])
def watchlist():
    email = session.get('email')
    watchlist = pull_watchlist(email)

    return render_template('watchlist.html', watchlist=watchlist, email=email)

@app.route('/remove_watchlist', methods=['POST'])
def remove_watchlist():
    bidder_email = session.get('email')
    seller_email = request.form['seller_email']
    listing_id = request.form['listing_id']

    delete_from_watchlist(bidder_email, seller_email, listing_id)

    return redirect('/watchlist')

@app.route('/add_watchlist', methods=['POST'])
def add_watchlist():
    bidder_email = session.get('email')
    seller_email = request.form['seller_email']
    listing_id = request.form['listing_id']

    add_to_watchlist(bidder_email, seller_email, listing_id)

    return redirect(request.referrer)

# works only for users with .lsu emails (i think)
def pull_user(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    # cursor.execute('SELECT first_name, last_name FROM Users AS u, Bidders AS b, Sellers AS s, Helpdesk AS h '
    #                'WHERE u.email = ? AND (u.email = b.email OR u.email = s.email OR u.email = h.email)', (email,))
    cursor.execute('SELECT first_name, last_name FROM Users AS u, Bidders AS b WHERE u.email = ? AND (u.email = b.email)', (email,))
    user = cursor.fetchone()
    connection.close()
    return user


def pull_lv(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT u.email, s.bank_account_number, s.bank_routing_number, s.balance, lv.business_name, lv.business_address_id, lv.customer_service_phone_number '
                       'FROM Users AS u, Sellers AS s, Local_Vendors lv '
                       'WHERE u.email = ? AND (u.email = s.email) AND (u.email = lv.email)', (email,))

    lv=cursor.fetchone()
    # DEBUG:
    print(lv)
    connection.close()
    return lv


def check_lv_status(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Users AS u, Local_Vendors AS lv WHERE u.email = ? AND (u.email = lv.email)', (email,))
    temp = cursor.fetchone()
    if temp == None:
        connection.close()
        return False
    else:
        connection.close()
        return True


def pull_bank_info(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT s.bank_account_number, s.bank_routing_number, s.balance '
                   'FROM Users AS u, Sellers AS s '
                   'WHERE u.email = ? AND (u.email = s.email)', (email,))
    bank_info = cursor.fetchone()
    connection.close()
    return bank_info

def check_in_system(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT email FROM Sellers WHERE email = ? '
                   'UNION '
                   'SELECT email FROM Bidders WHERE email = ? '
                   'UNION '
                   'SELECT email FROM Local_Vendors WHERE email = ? '
                   'UNION '
                   'SELECT email FROM Helpdesk WHERE email = ? ',
                   (email, email, email, email))

    temp = cursor.fetchone()
    connection.close()
    return temp is not None  # True if user email found in any of the three tables

# returns an address string based on the logged in user's email
def pull_address(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT A.street_num, A.street_name, Z.city, Z.state, A.zipcode FROM Bidders AS B, Address AS A, Zipcode_Info AS Z WHERE B.email = ? AND B.home_address_id = A.address_ID AND A.zipcode = Z.zipcode', (email,))

    address_info = cursor.fetchone()
    address = "{} {} {} {} {}".format(address_info[0], address_info[1], address_info[2], address_info[3], address_info[4])
    connection.close()
    return address


def pull_business_address(address_id):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT A.street_num, A.street_name, Z.city, Z.state, A.zipcode '
                   'FROM Address AS A, Zipcode_Info AS Z '
                   'WHERE A.address_ID = ? AND A.zipcode = Z.zipcode', (address_id,))

    address_info = cursor.fetchone()
    address = "{} {} {} {} {}".format(address_info[0], address_info[1], address_info[2], address_info[3], address_info[4])
    connection.close()
    return address



# returns card information array containing card information based on the logged-in user's email
def pull_credit_card(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT C.credit_card_num, C.card_type, C.expire_month, C.expire_year, C.security_code FROM Credit_Cards C, Users U WHERE U.email = ? AND U.email = C.owner_email', (email,))

    card_info = cursor.fetchone()
    connection.close()
    return card_info


# returns the path of the image based on the image name (used when crossing tables)
def pull_image(name):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT path FROM Image_Paths WHERE product_name = ?', (name,))
    path = cursor.fetchone()
    connection.close()
    return path[0]

def pull_watchlist(email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT A.seller_email, A.listing_id, A.category, A.auction_title, A.product_name, A.status, I.path '
                   'FROM Auction_Listings A, Watchlist W, Image_Paths I '
                   'WHERE W.seller_email = A.seller_email AND W.listing_id = A.listing_id AND A.product_name = I.product_name AND W.bidder_email = ?',
                   (email,))

    watchlist = cursor.fetchall()

    connection.close()
    return watchlist


def add_to_watchlist(bidder_email, seller_email, listing_id):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('INSERT OR IGNORE INTO Watchlist (bidder_email, seller_email, listing_id) VALUES (?, ?, ?);',
                   (bidder_email, seller_email, listing_id))

    connection.commit()
    connection.close()

def delete_from_watchlist(bidder_email, seller_email, listing_id):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('DELETE FROM Watchlist WHERE bidder_email = ? AND seller_email = ? AND listing_id = ?',
                   (bidder_email, seller_email, listing_id))

    connection.commit()
    connection.close()

def is_in_watchlist(bidder_email, seller_email, listing_id):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT 1 FROM Watchlist WHERE bidder_email = ? AND seller_email = ? AND listing_id = ?',
                   (bidder_email, seller_email, listing_id))

    result = cursor.fetchone()
    connection.close()

    if result:
        return True
    else:
        return False

def get_average_rating(seller_email):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT R.rating FROM Rating R WHERE seller_email = ?', (seller_email,))

    ratings = cursor.fetchall()

    # If seller has no ratings yet, make them unrated
    if len(ratings) == 0:
        average_rating = "Unrated"
    else:
        sum = 0
        for rating in ratings:
            sum += rating[0]

        average_rating = sum / len(ratings)

    connection.close()
    return average_rating

def calculate_age(dob):
    month, day, year = dob.split('-')
    today = date.today()

    age = today.year - int(year)

    # Adjust age if birthday hasn't occurred yet
    if (today.month, today.day) < (int(month), int(day)):
        age -= 1

    return age

@app.route('/listitem', methods=['POST', 'GET'])
def list_item():
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT category_name FROM Categories WHERE parent_category = "Root" ')
    parentcategories = cursor.fetchall()
    parent_categories = [row[0] for row in parentcategories]

    return render_template('listitem.html', parent_categories=parent_categories)

@app.route('/listitemsuccess', methods=['POST', 'GET'])
def list_item_success():
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    email = session.get('email')
    parent_category = request.form['parent_category']
    sub_category = request.form['subcategory']
    title = request.form['title']
    pname = request.form['pname']
    pdesc = request.form['pdesc']
    quant = request.form['quant']
    reserveprice = f"${request.form['reserveprice']}"
    maxbids = request.form['maxbids']

    cursor.execute('SELECT MAX(listing_id) FROM Auction_Listings')
    id = cursor.fetchone()
    id = int(id[0]) + 1

    duration = request.form['duration']
    duration = int(duration)

    cursor.execute('INSERT INTO Auction_Listings(seller_email, listing_id, category, auction_title, product_name, product_description, quantity, reserve_price, max_bids, status) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ? , ?, ?);', (email, id, sub_category, title, pname, pdesc, quant, reserveprice, maxbids, 1))

    cursor.execute('INSERT OR IGNORE INTO Stop_Times(Listing_ID, Stop_Time) VALUES (?, ?);', (id, duration))

    cursor.execute('INSERT OR IGNORE INTO Image_Paths(product_name, path) VALUES (?, ?);', (pname, 'image-not-found.webp'))

    connection.commit()
    connection.close()
    return render_template('listitemsuccess.html')

@app.route('/get_subcategories')
def get_subcategories():
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    parent = request.args.get('parent', '')

    #Gets ONLY children
    cursor.execute('WITH RECURSIVE combined_categories AS (SELECT category_name, parent_category FROM Categories WHERE parent_category = ? UNION ALL SELECT c.category_name, c.parent_category FROM Categories AS c JOIN combined_categories AS cc ON c.parent_category = cc.category_name) SELECT DISTINCT l.category FROM auction_listings AS l JOIN Image_Paths AS i ON i.product_name = l.product_name WHERE l.status = 1 AND l.category IN (SELECT category_name FROM combined_categories)', (parent,))
    filter_list = cursor.fetchall()
    filtered = [(filter[0]) for filter in filter_list]

    return jsonify({'subcategories': filtered})


@app.route('/catalog/<category>/<name>/<id>', methods=['POST', 'GET'])
def render_item(category, name, id):
    img_src = pull_image(name)
    bidder_email = session.get('email')
    bid_error = request.args.get('bid_error')
    bid_success = request.args.get('bid_success')
    auction_ended = False
    winner_unpaid = False
    auction_message = None

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM Auction_Listings WHERE listing_id = ?', (id,))
    product = cursor.fetchone()
    #DEBUG:
    print(product)

    cursor.execute('SELECT * FROM Stop_Times WHERE Listing_ID = ?', (id, ))
    stoptime = cursor.fetchone()
    #DEBUG:
    print(stoptime)

    in_watchlist = is_in_watchlist(bidder_email, product[0], id)

    rating = get_average_rating(product[0])

    cursor.execute('SELECT MAX(bid_price) FROM Bids WHERE listing_id = ? AND seller_email = ?', (id, product[0]))

    highest_bid_row = cursor.fetchone()

    if highest_bid_row[0] is None:
        highest_bid = 0
    else:
        highest_bid = highest_bid_row[0]

    cursor.execute('SELECT COUNT(*) FROM Bids WHERE listing_id = ? AND seller_email = ?', (id, product[0]))
    bid_count = cursor.fetchone()[0]

    remaining_bids = product[8] - bid_count

    reserve_price = int(product[7].replace('$', '').replace(',', '').strip())

    if remaining_bids <= 0:
        auction_ended = True

        if highest_bid >= reserve_price:
            cursor.execute('SELECT bidder_email FROM Bids WHERE seller_email = ? AND listing_id = ? ORDER BY bid_price DESC, bid_id DESC LIMIT 1', (product[0], id))
            winner_row = cursor.fetchone()

            if winner_row is not None and winner_row[0] == bidder_email and product[9] != 2:
                winner_unpaid = True
                auction_message = 'Auction ended. You are the winning bidder. Proceed to payment.'
            else:
                auction_message = 'Auction ended. Another bidder won this item.'
        else:
            auction_message = 'Auction ended. The reserve price was not met.'

    connection.close()

    return render_template('RenderItem.html', name=name, category=category, id=id, img_src=img_src, product=product, stoptime=stoptime[1], in_watchlist=in_watchlist, rating=rating, highest_bid=highest_bid, bid_count=bid_count, remaining_bids=remaining_bids, bid_error=bid_error, bid_success=bid_success, auction_ended=auction_ended, winner_unpaid=winner_unpaid, auction_message=auction_message)


@app.route('/place_bid', methods=['POST'])
def place_bid():
    if session.get('role') != 'Buyer':
        return redirect('/login')

    bidder_email = session.get('email')
    seller_email = request.form['seller_email']
    listing_id = request.form['listing_id']
    category = request.form['category']
    name = request.form['name']

    try:
        bid_amount = float(request.form['bid_amount'])
    except ValueError:
        return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_error=Invalid+bid+amount')

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM Auction_Listings WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    listing = cursor.fetchone()

    if listing is None:
        connection.close()
        return redirect('/catalog')

    max_bids = listing[8]

    cursor.execute('SELECT COUNT(*) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    bid_count = cursor.fetchone()[0]

    # Auction ends when max_bids is reached
    if bid_count >= max_bids:
        connection.close()
        return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_error=Auction+ended')

    cursor.execute('SELECT MAX(bid_price) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    highest_bid_row = cursor.fetchone()

    if highest_bid_row[0] is None:
        highest_bid = 0
    else:
        highest_bid = highest_bid_row[0]

    # New bid must be at least $1 higher than current highest bid
    if bid_amount < round(highest_bid + 1, 2):
        connection.close()
        return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_error=Bid+too+low')

    cursor.execute('SELECT bidder_email FROM Bids WHERE seller_email = ? AND listing_id = ? ORDER BY bid_id DESC LIMIT 1', (seller_email, listing_id))
    last_bidder = cursor.fetchone()

    # Bidder cannot place consecutive bids
    if last_bidder is not None and last_bidder[0] == bidder_email:
        connection.close()
        return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_error=You+must+wait+for+another+bidder')

    cursor.execute('SELECT MAX(bid_id) FROM Bids')
    max_bid_id = cursor.fetchone()[0]

    if max_bid_id is None:
        new_bid_id = 1
    else:
        new_bid_id = max_bid_id + 1

    cursor.execute('INSERT INTO Bids(bid_id, seller_email, listing_id, bidder_email, bid_price) VALUES (?, ?, ?, ?, ?)', (new_bid_id, seller_email, listing_id, bidder_email, bid_amount))

    cursor.execute('SELECT COUNT(*) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))

    updated_bid_count = cursor.fetchone()[0]

    if updated_bid_count >= max_bids:
        cursor.execute('SELECT MAX(bid_price) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
        final_highest_bid = cursor.fetchone()[0]

        reserve_price_text = listing[7]
        reserve_price = int(reserve_price_text.replace('$', '').strip())

        # Auction is unsuccessful if reserve price is not met
        if final_highest_bid < reserve_price:
            cursor.execute('UPDATE Auction_Listings SET status = 0 WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
            connection.commit()
            connection.close()
            return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_error=Auction+ended.+Reserve+price+not+met')

        # Auction is successful, current bidder is the winner
        connection.commit()
        connection.close()
        return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_success=Auction+ended.+You+are+the+winning+bidder.+Proceed+to+payment.')

    connection.commit()
    connection.close()

    return redirect(f'/catalog/{category}/{name}/{listing_id}?bid_success=Bid+placed+successfully')


@app.route('/payment/<seller_email>/<int:listing_id>', methods=['GET'])
def payment_page(seller_email, listing_id):
    if session.get('role') != 'Buyer':
        return redirect('/login')

    bidder_email = session.get('email')
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM Auction_Listings WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    listing = cursor.fetchone()

    if listing is None:
        connection.close()
        return redirect('/catalog')

    # Do not allow payment for listings that are already sold or inactive
    if listing[9] != 1:
        connection.close()
        return redirect('/catalog')

    max_bids = listing[8]
    reserve_price = int(listing[7].replace('$', '').strip())

    cursor.execute('SELECT COUNT(*) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    bid_count = cursor.fetchone()[0]

    cursor.execute('SELECT MAX(bid_price) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    highest_bid = cursor.fetchone()[0]

    # Payment allowed only after auction is complete
    if bid_count < max_bids or highest_bid is None:
        connection.close()
        return redirect(f'/catalog/{listing[2]}/{listing[4]}/{listing_id}?bid_error=Auction+is+not+complete')

    # Payment allowed only if reserve price was met
    if highest_bid < reserve_price:
        connection.close()
        return redirect(f'/catalog/{listing[2]}/{listing[4]}/{listing_id}?bid_error=Reserve+price+not+met')

    cursor.execute('SELECT bidder_email FROM Bids WHERE seller_email = ? AND listing_id = ? ORDER BY bid_price DESC, bid_id DESC LIMIT 1', (seller_email, listing_id))
    winner_row = cursor.fetchone()

    if winner_row is None or winner_row[0] != bidder_email:
        connection.close()
        return redirect(f'/catalog/{listing[2]}/{listing[4]}/{listing_id}?bid_error=You+are+not+the+winning+bidder')

    card_info = pull_credit_card(bidder_email)

    connection.close()

    return render_template('payment.html',
                           listing=listing,
                           highest_bid=highest_bid,
                           seller_email=seller_email,
                           listing_id=listing_id,
                           card_info=card_info)


@app.route('/submit_payment', methods=['POST'])
def submit_payment():
    if session.get('role') != 'Buyer':
        return redirect('/login')

    bidder_email = session.get('email')
    seller_email = request.form['seller_email']
    listing_id = int(request.form['listing_id'])
    payment_amount = float(request.form['payment_amount'])

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM Auction_Listings WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    listing = cursor.fetchone()

    if listing is None:
        connection.close()
        return redirect('/catalog')

    # Payment should only happen for an active listing that has not been sold yet
    if listing[9] != 1:
        connection.close()
        return redirect('/catalog')

    max_bids = listing[8]
    reserve_price = int(listing[7].replace('$', '').strip())

    cursor.execute('SELECT COUNT(*) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    bid_count = cursor.fetchone()[0]

    cursor.execute('SELECT MAX(bid_price) FROM Bids WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    highest_bid = cursor.fetchone()[0]

    # Auction must be complete before payment
    if bid_count < max_bids or highest_bid is None:
        connection.close()
        return redirect('/catalog')

    # Reserve price must be met
    if highest_bid < reserve_price:
        connection.close()
        return redirect('/catalog')

    cursor.execute('SELECT bidder_email FROM Bids WHERE seller_email = ? AND listing_id = ? ORDER BY bid_price DESC, bid_id DESC LIMIT 1', (seller_email, listing_id))
    winner_row = cursor.fetchone()

    if winner_row is None or winner_row[0] != bidder_email:
        connection.close()
        return redirect('/catalog')

    # Prevent duplicate payment/transaction for the same listing
    cursor.execute('SELECT 1 FROM Transactions WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))
    existing_transaction = cursor.fetchone()

    if existing_transaction is not None:
        connection.close()
        return redirect('/catalog')

    cursor.execute('SELECT * FROM Credit_Cards WHERE owner_email = ?', (bidder_email,))
    saved_card = cursor.fetchone()

    if saved_card is None:
        credit_card_num = request.form.get('credit_card_num')
        card_type = request.form.get('card_type')
        expire_month = request.form.get('expire_month')
        expire_year = request.form.get('expire_year')
        security_code = request.form.get('security_code')

        if not credit_card_num or not card_type or not expire_month or not expire_year or not security_code:
            connection.close()
            return redirect(f'/payment/{seller_email}/{listing_id}')

        cursor.execute('INSERT INTO Credit_Cards(credit_card_num, card_type, expire_month, expire_year, security_code, owner_email) VALUES (?, ?, ?, ?, ?, ?)', (credit_card_num, card_type, int(expire_month), int(expire_year), int(security_code), bidder_email))

    cursor.execute('SELECT MAX(transaction_id) FROM Transactions')
    max_transaction_id = cursor.fetchone()[0]

    if max_transaction_id is None:
        new_transaction_id = 1
    else:
        new_transaction_id = max_transaction_id + 1

    today = date.today().strftime('%-m/%-d/%y')

    cursor.execute('INSERT INTO Transactions(transaction_id, seller_email, listing_id, bidder_email, date, payment) VALUES (?, ?, ?, ?, ?, ?)', (new_transaction_id, seller_email, listing_id, bidder_email, today, payment_amount))

    cursor.execute('UPDATE Auction_Listings SET status = 2 WHERE seller_email = ? AND listing_id = ?', (seller_email, listing_id))

    connection.commit()
    connection.close()

    return redirect('/welcome/')


@app.route('/catalog/<category>/', methods=['POST', 'GET'])
def subcatalog(category):
    selected_filter = request.args.get('filters')
    search_filter = request.args.get('user_item_lookup')

    connection = sql.connect('database.db')
    cursor = connection.cursor()

    print(selected_filter)

    #Gets the subcategories INCLUDING ROOT
    cursor.execute('WITH RECURSIVE combined_categories AS (SELECT category_name, parent_category FROM Categories WHERE category_name = ? UNION ALL SELECT c.category_name, c.parent_category FROM Categories AS c JOIN combined_categories AS cc ON c.parent_category = cc.category_name) SELECT l.*, i.path FROM auction_listings AS l JOIN Image_Paths AS i ON i.product_name = l.product_name WHERE l.status = 1 AND l.category IN (SELECT category_name FROM combined_categories)', (category,))
    rows = cursor.fetchall()
    product_name = [(row[4], row[1], row[10], row[0], row[7]) for row in rows]
    # print(product_name)

    #Gets ONLY children
    cursor.execute('WITH RECURSIVE combined_categories AS (SELECT category_name, parent_category FROM Categories WHERE parent_category = ? UNION ALL SELECT c.category_name, c.parent_category FROM Categories AS c JOIN combined_categories AS cc ON c.parent_category = cc.category_name) SELECT DISTINCT l.category FROM auction_listings AS l JOIN Image_Paths AS i ON i.product_name = l.product_name WHERE l.status = 1 AND l.category IN (SELECT category_name FROM combined_categories)', (category,))
    filter_list = cursor.fetchall()
    filtered = [(filter[0]) for filter in filter_list]
    print(filtered)

    #Gets ONLY children
    cursor.execute('WITH RECURSIVE combined_categories AS (SELECT category_name, parent_category FROM Categories WHERE parent_category = ? UNION ALL SELECT c.category_name, c.parent_category FROM Categories AS c JOIN combined_categories AS cc ON c.parent_category = cc.category_name) SELECT DISTINCT l.category FROM auction_listings AS l JOIN Image_Paths AS i ON i.product_name = l.product_name WHERE l.status = 1 AND l.category IN (SELECT category_name FROM combined_categories)', (category,))
    filter_list = cursor.fetchall()
    filtered = [(filter[0]) for filter in filter_list]

    if selected_filter:
        cursor.execute('WITH RECURSIVE combined_categories AS (SELECT category_name, parent_category FROM Categories WHERE category_name = ? UNION ALL SELECT c.category_name, c.parent_category FROM Categories AS c JOIN combined_categories AS cc ON c.parent_category = cc.category_name) SELECT l.*, i.path FROM auction_listings AS l JOIN Image_Paths AS i ON i.product_name = l.product_name WHERE l.status = 1 AND l.category IN (SELECT category_name FROM combined_categories)',(selected_filter,))
        rows = cursor.fetchall()
        product_name = [(row[4], row[1], row[10], row[0], row[7]) for row in rows]


    if search_filter:
        cursor.execute('WITH RECURSIVE combined_categories AS (SELECT category_name, parent_category FROM Categories WHERE category_name = ? UNION ALL SELECT c.category_name, c.parent_category FROM Categories AS c JOIN combined_categories AS cc ON c.parent_category = cc.category_name) SELECT l.*, i.path FROM auction_listings AS l JOIN Image_Paths AS i ON i.product_name = l.product_name WHERE l.status = 1 AND l.category IN (SELECT category_name FROM combined_categories) AND l.product_name LIKE ?',(category, f'%{search_filter}%',))
        rows = cursor.fetchall()
        product_name = [(row[4], row[1], row[10], row[0], row[7]) for row in rows]
        print("FOR SEARCH BAR " + search_filter)

    connection.close()
    return render_template('subcatalog.html', category=category, product_name=product_name, filters=filtered)

@app.route('/catalog', methods=['POST', 'GET'])
def catalog(): #Only gives categories where its root aka the main categories
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT category_name FROM Categories WHERE parent_category = "Root"')
    categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return render_template('catalog.html', categories=categories)


@app.route('/helpdesk')
def helpdesk_panel():
    if session.get('role') != 'HelpDesk':
        return redirect('/login')

    email = session.get('email')
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    # Requests still sitting in the team inbox
    cursor.execute('SELECT * FROM Requests WHERE helpdesk_staff_email = "helpdeskteam@lsu.edu" AND request_status = 0 ORDER BY request_id')
    unassigned = cursor.fetchall()

    # Requests claimed by this logged-in helpdesk user
    cursor.execute('SELECT * FROM Requests WHERE helpdesk_staff_email = ? AND request_status = 0 ORDER BY request_id', (email,))
    my_requests = cursor.fetchall()

    # Requests completed by this helpdesk user
    cursor.execute('SELECT * FROM Requests WHERE helpdesk_staff_email = ? AND request_status = 1 ORDER BY request_id DESC', (email,))
    completed = cursor.fetchall()

    connection.close()

    return render_template(
        'helpdesk.html',
        email=email,
        unassigned=unassigned,
        my_requests=my_requests,
        completed=completed
    )

@app.route('/claim_request/<int:request_id>', methods=['POST'])
def claim_request(request_id):
    if session.get('role') != 'HelpDesk':
        return redirect('/login')

    email = session.get('email')
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute('UPDATE Requests SET helpdesk_staff_email = ? WHERE request_id = ? AND helpdesk_staff_email = "helpdeskteam@lsu.edu" AND request_status = 0', (email, request_id))

    connection.commit()
    connection.close()

    return redirect('/helpdesk')

# Helper to extract new category and parent category from AddCategory request text
def parse_add_category_desc(request_desc):
    prefix = 'Please ad a new category '
    middle = ' under '

    if not request_desc.startswith(prefix):
        return None, None

    remaining = request_desc[len(prefix):]

    if middle not in remaining:
        return None, None

    parts = remaining.split(middle, 1)
    new_category = parts[0].strip()
    parent_category = parts[1].strip()

    return new_category, parent_category

@app.route('/complete_request/<int:request_id>', methods=['POST'])
def complete_request(request_id):
    if session.get('role') != 'HelpDesk':
        return redirect('/login')

    email = session.get('email')
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    # Mark only this helpdesk user's active request as completed
    cursor.execute('UPDATE Requests SET request_status = 1 WHERE request_id = ? AND helpdesk_staff_email = ? AND request_status = 0', (request_id, email))

    connection.commit()
    connection.close()

    return redirect('/helpdesk')

@app.route('/approve_category_request/<int:request_id>', methods=['POST'])
def approve_category_request(request_id):
    if session.get('role') != 'HelpDesk':
        return redirect('/login')

    email = session.get('email')
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    # Get this assigned AddCategory request
    cursor.execute('SELECT * FROM Requests WHERE request_id = ? AND helpdesk_staff_email = ? AND request_status = 0', (request_id, email))
    req = cursor.fetchone()

    if req is None:
        connection.close()
        return redirect('/helpdesk')

    request_type = req[3]
    request_desc = req[4]

    # Only process AddCategory requests here
    if request_type != 'AddCategory':
        connection.close()
        return redirect('/helpdesk')

    # Read category info from the request description
    new_category, parent_category = parse_add_category_desc(request_desc)

    if new_category is None or parent_category is None:
        connection.close()
        return redirect('/helpdesk')

    # Add the new category if it does not already exist
    cursor.execute('INSERT OR IGNORE INTO Categories(category_name, parent_category) VALUES (?, ?);', (new_category, parent_category))

    # Mark the request as completed after processing
    cursor.execute('UPDATE Requests SET request_status = 1 WHERE request_id = ?', (request_id,))

    connection.commit()
    connection.close()

    return redirect('/helpdesk')

# hashing algorithm that takes a word and hashes it to a SHA256 hash.
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

            cursor.execute('INSERT OR IGNORE INTO Users (email, password) VALUES (?,?);', (email, hashed_password))
    connection.commit()
    connection.close()


def populate_addresses(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Address(address_ID TEXT PRIMARY KEY, zipcode INT, street_num INT, street_name TEXT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            address_ID = row["address_id"].strip()
            zipcode = int(row["zipcode"].strip())
            street_num = int(row["street_num"].strip())
            street_name = row["street_name"].strip()

            cursor.execute(
                'INSERT OR IGNORE INTO Address(address_ID, zipcode, street_num, street_name) VALUES (?, ?, ?, ?);',
                (address_ID, zipcode, street_num, street_name))
    connection.commit()
    connection.close()


def populate_auction_listings(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Auction_Listings(seller_email TEXT, listing_id INT, category TEXT, auction_title TEXT, product_name TEXT, product_description TEXT, quantity INT, reserve_price TEXT, max_bids INT, status INT, PRIMARY KEY(seller_email, listing_id));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            seller_email = row["Seller_Email"].strip()
            listing_id = row["Listing_ID"].strip()
            category = row["Category"].strip()
            auction_title = row["Auction_Title"].strip()
            product_name = row["Product_Name"].strip()
            product_description = row["Product_Description"].strip()
            quantity = int(row["Quantity"].strip())
            reserve_price = row["Reserve_Price"].strip()
            max_bids = int(row["Max_bids"].strip())
            status = int(row["Status"].strip())

            cursor.execute(
                'INSERT OR IGNORE INTO Auction_Listings (seller_email, listing_id, category, auction_title, product_name, product_description, quantity, reserve_price, max_bids, status) VALUES (?,?,?,?,?,?,?,?,?,?);',
                (seller_email, listing_id, category, auction_title, product_name, product_description, quantity,
                 reserve_price, max_bids, status))
    connection.commit()
    connection.close()


def populate_bidders(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Bidders(email TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, age INT, home_address_id TEXT, major TEXT, FOREIGN KEY(home_address_id) REFERENCES Address(address_ID), FOREIGN KEY(email) REFERENCES Users(email));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            email = row["email"].strip()
            first_name = row["first_name"].strip()
            last_name = row["last_name"].strip()
            age = int(row["age"].strip())
            home_address_id = row["home_address_id"].strip()
            major = row["major"].strip()

            cursor.execute(
                'INSERT OR IGNORE INTO Bidders(email, first_name, last_name, age, home_address_id, major) VALUES (?, ?, ?, ?, ?, ?);',
                (email, first_name, last_name, age, home_address_id, major))
    connection.commit()
    connection.close()


def populate_bids(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Bids(bid_id INT PRIMARY KEY, seller_email TEXT, listing_id INT, bidder_email TEXT, bid_price INT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            bid_int = row["Bid_ID"].strip()
            seller_email = row["Seller_Email"].strip()
            listing_id = int(row["Listing_ID"].strip())
            bidder_email = row["Bidder_Email"].strip()
            bid_price = int(row["Bid_Price"].strip())

            cursor.execute(
                'INSERT OR IGNORE INTO Bids(bid_id, seller_email, listing_id, bidder_email, bid_price) VALUES (?, ?, ?, ?, ?);',
                (bid_int, seller_email, listing_id, bidder_email, bid_price))
    connection.commit()
    connection.close()


def populate_categories(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    # cursor.execute("PRAGMA foreign_keys = ON;")
    # might need a foreign key constraint on categories. not sure as of yet
    cursor.execute('CREATE TABLE IF NOT EXISTS Categories(category_name TEXT PRIMARY KEY, parent_category TEXT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            category_name = row["category_name"].strip()
            parent_category = row["parent_category"].strip()

            cursor.execute('INSERT OR IGNORE INTO Categories(category_name, parent_category) VALUES (?, ?);',
                           (category_name, parent_category))
    connection.commit()
    connection.close()


def populate_credit_cards(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Credit_Cards(credit_card_num TEXT PRIMARY KEY, card_type TEXT, expire_month INT, expire_year INT, security_code INT, owner_email TEXT, FOREIGN KEY(owner_email) REFERENCES Bidders(email));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            credit_card_num = row["credit_card_num"].strip()
            card_type = row["card_type"].strip()
            expire_month = int(row["expire_month"].strip())
            expire_year = int(row["expire_year"].strip())
            security_code = int(row["security_code"].strip())
            owner_email = row["Owner_email"].strip()

            cursor.execute('INSERT OR IGNORE INTO Credit_Cards(credit_card_num, card_type, expire_month, expire_year, '
                           'security_code, owner_email) VALUES (?, ?, ?, ?, ?, ?);',
                           (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email))
    connection.commit()
    connection.close()


def populate_helpdesk(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute('CREATE TABLE IF NOT EXISTS Helpdesk(email TEXT PRIMARY KEY, position TEXT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            email = row["email"].strip()
            position = row["Position"].strip()

            cursor.execute(
                'INSERT OR IGNORE INTO Helpdesk(email, position) VALUES (?, ?);', (email, position))
    connection.commit()
    connection.close()


def populate_local_vendors(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Local_Vendors(email TEXT PRIMARY KEY, business_name TEXT, business_address_id TEXT, customer_service_phone_number TEXT, FOREIGN KEY(email) REFERENCES Sellers(email));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            email = row["Email"].strip()
            business_name = row["Business_Name"].strip()
            business_address_id = row["Business_Address_ID"].strip()
            customer_service_phone_number = row["Customer_Service_Phone_Number"].strip()

            cursor.execute(
                'INSERT OR IGNORE INTO Local_Vendors(email, business_name, business_address_id, customer_service_phone_number) VALUES (?, ?, ?, ?);',
                (email, business_name, business_address_id, customer_service_phone_number))
    connection.commit()
    connection.close()


def populate_rating(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Rating(bidder_email TEXT, seller_email TEXT, rating_date TEXT, rating INT CHECK(rating BETWEEN 1 and 5), rating_desc TEXT,'
        'PRIMARY KEY (bidder_email, seller_email, rating_date),'
        'FOREIGN KEY (bidder_email) REFERENCES Bidders(email),'
        'FOREIGN KEY (seller_email) REFERENCES Sellers(email));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            bidder_email = row["Bidder_Email"].strip()
            seller_email = row["Seller_Email"].strip()

            cursor.execute('SELECT email FROM Sellers WHERE email = ?', (seller_email,))
            match = cursor.fetchone()
            if not match:
                print(f"MISSING in Bidders: '{seller_email}'")
                continue  # skip or remove this to still see the error

            rating_date = row["Date"].strip()
            rating = int(row["Rating"].strip())
            rating_desc = row["Rating_Desc"].strip()

            cursor.execute(
                'INSERT OR IGNORE INTO Rating(bidder_email, seller_email, rating_date, rating, rating_desc) VALUES (?, ?, ?, ?, ?);',
                (bidder_email, seller_email, rating_date, rating, rating_desc))
    connection.commit()
    connection.close()


def populate_requests(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Requests(request_id INT PRIMARY KEY, sender_email TEXT, helpdesk_staff_email TEXT, request_type TEXT, request_desc TEXT, request_status INT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            request_id = int(row["request_id"].strip())
            sender_email = row["sender_email"].strip()
            helpdesk_staff_email = row["helpdesk_staff_email"].strip()
            request_type = row["request_type"].strip()
            request_desc = row["request_desc"].strip()
            request_status = int(row["request_status"].strip())

            cursor.execute(
                'INSERT OR IGNORE INTO Requests(request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) VALUES (?, ?, ?, ?, ?, ?);',
                (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status))
    connection.commit()
    connection.close()

def populate_watchlist(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Watchlist(bidder_email TEXT NOT NULL, seller_email TEXT NOT NULL, listing_id INT NOT NULL,'
        'PRIMARY KEY (bidder_email, seller_email, listing_id),'
        'FOREIGN KEY (bidder_email) REFERENCES Bidders(email),'
        'FOREIGN KEY (seller_email, listing_id) REFERENCES Auction_Listings(seller_email, listing_id));'
    )

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            bidder_email = row["bidder_email"].strip()
            seller_email = row["seller_email"].strip()
            listing_id = int(row["listing_id"].strip())

            cursor.execute('INSERT OR IGNORE INTO Watchlist (bidder_email, seller_email, listing_id) VALUES (?, ?, ?);',
                           (bidder_email, seller_email, listing_id))

    connection.commit()
    connection.close()

def populate_sellers(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Sellers(email TEXT PRIMARY KEY, bank_routing_number TEXT, bank_account_number TEXT, balance REAL, FOREIGN KEY (email) REFERENCES Users(email));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            email = row["email"].strip()
            bank_routing_number = row["bank_routing_number"].strip()
            bank_account_number = row["bank_account_number"].strip()
            balance = float(row["balance"].strip())

            cursor.execute(
                'INSERT OR IGNORE INTO Sellers(email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?);',
                (email, bank_routing_number, bank_account_number, balance))
    connection.commit()
    connection.close()


def populate_transactions(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Transactions(transaction_id INT PRIMARY KEY, seller_email TEXT, listing_id INT, bidder_email, date TEXT, payment REAL, FOREIGN KEY (seller_email, listing_id) REFERENCES Auction_Listings(seller_email, listing_id), FOREIGN KEY (bidder_email) REFERENCES Users(email));')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            transaction_id = int(row["Transaction_ID"].strip())
            seller_email = row["Seller_Email"].strip()
            listing_id = int(row["Listing_ID"].strip())
            bidder_email = row["Bidder_Email"].strip()
            date = row["Date"].strip()
            payment = float(row["Payment"].strip())

            cursor.execute(
                'INSERT OR IGNORE INTO Transactions(transaction_id, seller_email, listing_id, bidder_email, date, payment) VALUES (?, ?, ?, ?, ?, ?);',
                (transaction_id, seller_email, listing_id, bidder_email, date, payment))
    connection.commit()
    connection.close()


def populate_zips(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS Zipcode_Info(zipcode INT PRIMARY KEY, city TEXT, state TEXT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            zipcode = row["zipcode"].strip()
            city = row["city"].strip()
            state = row["state"].strip()

            cursor.execute('INSERT OR IGNORE INTO Zipcode_Info(zipcode, city, state) VALUES (?, ?, ?);',
                           (zipcode, city, state))
    connection.commit()
    connection.close()


def populate_image_paths(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS Image_Paths(product_name TEXT PRIMARY KEY, path TEXT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            product_name = row["product_name"].strip()
            path = row["path"].strip()

            cursor.execute('INSERT OR IGNORE INTO Image_Paths(product_name, path) VALUES (?, ?);', (product_name, path))
    connection.commit()
    connection.close()

def populate_stop_times(filePath):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS Stop_Times(Listing_ID INT PRIMARY KEY, Stop_Time INT);')

    with open(filePath, 'r', encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            id = row["Listing_ID"].strip()
            time = row["Stop_Time"].strip()

            cursor.execute('INSERT OR IGNORE INTO Stop_Times(Listing_ID, Stop_Time) VALUES (?, ?);', (id, time))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    # print("this is hash of 'database' " + hashing("database")) -------testing print
    populate_users(Users_csvPath)
    populate_addresses(Address_csvPath)
    populate_auction_listings(Auction_Listings_csvPath)
    populate_bidders(Bidders_csvPath)
    populate_bids(Bids_csvPath)
    populate_categories(Categories_csvPath)
    populate_credit_cards(Credit_Cards_csvPath)
    populate_helpdesk(Helpdesk_csvPath)
    populate_watchlist(Watchlist_csvPath)

    # CALL SELLERS FIRST
    populate_sellers(Sellers_csvPath)

    populate_local_vendors(Local_Vendors_csvPath)
    populate_rating(Ratings_csvPath)
    populate_requests(Requests_csvPath)

    populate_transactions(Transactions_csvPath)
    populate_zips(Zipcode_Info_csvPath)
    populate_image_paths(Image_Path_cvsPath)
    populate_stop_times(Stop_Time_csvPath)

    image = pull_image("Logo")

    print(image)

    connection = sql.connect('database.db')
    app.run(debug=True)


