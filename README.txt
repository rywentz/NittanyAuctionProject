This code is for getting the user login for our database started. Currently, the code handles user logins, account creation, and a failed attempt at logging in. Along with a hashing function that stores the user’s password as a SHA256 hash instead of plain text.

The data within the database is populated with a function called ‘populate_users()’ which takes a filepath as a parameter. The filepath shows the location of the .csv file used for filling the tables. We strip the emails and passwords from the csv file and enter them into the database after hashing the passwords.

On login, the application takes in a user’s email and password. The application hashes the password and compares it with the hashed password in the Users table in the database. The application also has means to determine the status (buyer, seller, helpdesk) of a user on log in.

Below are the files that are part of this database currently
Addpatient.html		    unused (used for design)
Createaccount.html		page for account creation
homepage.html           Where the website defaults to
Login.html			    page for user login after landing page
Removepatient.html      unused(used for design)
Welcome.html		    welcome page for logged in users
app.                    Main for our functions


The createaccount page serves to insert new users into the database. On account creation, a user enters a valid email and password. The email must not already exist in the database. On successful account creation, the application stores the users data into the database securely.


To execute the code download the zip file and load it into pycharm professional. Run app.py which will create the database and the table if it does not exist and populate with the information. In the console there will be a local host, one can click to open the webpage.


