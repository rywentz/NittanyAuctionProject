# This code is a modified version of the original template code given to us to use.
# Original code credits to Penn State University CMPSC 431W Spring 2026 Semester

import csv
from flask import Flask, render_template, request, session, sessions
import sqlite3 as sql

import hashlib

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
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM Users WHERE email = ?;', (email_user,))
        user = cursor.fetchone()

        if user and hashing(password_user) == user[1]:
            session['email'] = email_user
            try:
                cursor.execute('SELECT * FROM Helpdesk WHERE email = ?;', (email_user,))
                if cursor.fetchone():
                    session['role'] = 'HelpDesk'
                    return render_template('welcome.html', role='HelpDesk', email=email_user)
            except sql.OperationalError:
                pass
            try:
                cursor.execute('SELECT * FROM Sellers WHERE email = ?;', (email_user,))
                if cursor.fetchone():
                    session['role'] = 'Seller'
                    return render_template('welcome.html', role='Seller', email=email_user)
            except sql.OperationalError:
                pass
            session['role'] = 'Buyer'
            return render_template('welcome.html', role='Buyer', email=email_user)
        else:
            error = 'Incorrect password or email, try again.'

    return render_template('login.html', error=error)


@app.route('/createaccount', methods=['POST', 'GET'])
def createaccount():
    error = None
    success = None
    if request.method == 'POST':
        email_user = request.form["email"]
        password_user = request.form["password"]

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
        card_info = pull_credit_card(email)
        expire_date = '{} / {}'.format(card_info[2], card_info[3])
        return render_template('account.html', email=session.get('email'), fname=user[0], lname=user[1],
                               role=session.get('role'), address=address_info, card_num=card_info[0], card_type=card_info[1],
                               exp=expire_date, security_code=card_info[4])
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
            return render_template('lvaccount.html', email=session.get('email'),
                                   acc_num=seller[1], route_num=seller[2], bal=seller[3],
                                   role=role, business=seller[4], csphone=seller[6],
                                   address=address)
        else:   #user is just a seller, no business information needed
            email = session.get('email')
            user = pull_user(email)
            address_info = pull_address(email)
            card_info = pull_credit_card(email)
            expire_date = '{} / {}'.format(card_info[2], card_info[3])
            bank = pull_bank_info(email)
            return render_template('selleraccount.html', email=session.get('email'), fname=user[0], lname=user[1],
                                   role=session.get('role'), address=address_info, card_num=card_info[0],
                                   card_type=card_info[1],
                                   acc_num=bank[0], route_num=bank[1], bal=bank[2],
                                   exp=expire_date, security_code=card_info[4])

    return render_template('account.html')

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


@app.route('/catalog', methods=['POST', 'GET'])
def catalog(): #Only gives categories where its root aka the main categories
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    cursor.execute('SELECT category_name FROM Categories WHERE parent_category = "Root"')
    categories = [row[0] for row in cursor.fetchall()]
    connection.close()

    return render_template('catalog.html', categories=categories)

@app.route('/catalog/<category>', methods=['POST', 'GET'])
def subcatalog(category):
    connection = sql.connect('database.db')
    cursor = connection.cursor()
    print(category)
    #Gets the subcategories
    cursor.execute('SELECT c.category_name FROM Categories AS C WHERE c.parent_category = ?', (category,))
    items = [row[0] for row in cursor.fetchall()]
    connection.close()

    return render_template('subcatalog.html', category=category, items=items)

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

    # CALL SELLERS FIRST
    populate_sellers(Sellers_csvPath)

    populate_local_vendors(Local_Vendors_csvPath)
    populate_rating(Ratings_csvPath)
    populate_requests(Requests_csvPath)

    populate_transactions(Transactions_csvPath)
    populate_zips(Zipcode_Info_csvPath)
    populate_image_paths(Image_Path_cvsPath)

    image = pull_image("Logo")

    print(image)

    connection = sql.connect('database.db')
    app.run(debug=True)


