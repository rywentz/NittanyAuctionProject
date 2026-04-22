Welcome to Nittany Auction!


Created by: Ryan Wentz, Braydon Corey, Khushil Patel, and Tai Nguyen
CMPSC 431W - Spring 2026 - Prof. Wang-Chien Lee

* all rights to images (found in static folder) used in this prototype go to their respective owners.

Nittany Auction is an online auction listing and bidding application geared towards universities to offer.
Nittany Auction aims to bring together local businesses and vendors to encourage a strong local economy close to campuses.
This is a rough prototype for the application which uses data given to us from the instructor.
* This data (in the form of .csv files) can be found in the 'NittanyAuctionDataset_v1' folder.

The data given to us is added to, modified, and removed in some cases to show the application's extent.

We use Python as the programming language for the project, SQLite for the database, and Flask for the back-end operations.

Decisions made as for the functionality of the program stem from our original Phase 1 report of the project.
In Phase 1, we completed a detailed Requirement Analysis, a Conceptual Database Design, a Technology Survey where we explored
other options for our stack, and Schema Normalization.


-----HTML Templates: (templates folder)-----

account.html - Functions as the Account Information page for users, displaying important information of the user that we have on file.

catalog.html - Displays the parent categories of the database and is used to access subcatalog.html.

createaccount.html - Prompts the user to input key information needed to add them to the database. This allows new users to access the application.

helpdesk.html - Provides key management functions for the Help Desk staff of Nittany Auction. Here, category requests are approved,
    user escalation of privileges is approved, etc.

homepage.html - The main hub for users in the application. Users can access their account information, their watchlist, logout,
    view the catalog, and more.

listitem.html - Prompts the user (must be a Seller) to input information needed to list an item.

listitemsuccess.html - After successful listing of an item, the user is directed here and their item is added into the database.

login.html - Serves as a basic login method for Buyers, Sellers, and HelpDesk personnel. User's passwords are never stored in plaintext
    and are instead hashed in the database.

lvaccount.html - Similar to account.html in which the Local Vendor's information is visible to them. Local Vendor's do not have a name
    and instead sign up with their business name and details.

payment.html - Acts as the transaction page and handles the bidding/transaction logic.

RenderItem.html - Renders an item, its image (if applicable), information about the listing, etc.

selleraccount.html - Similar to account.html in which the seller's information is visible to them. Sellers must have a valid bank account
    on file.

subcatalog.html - Renders all items under a parent category so Users can view all items in the database. Uses the selection from catalog.html to
    query the correct items under that parent category.

watchlist.html - Users can add specific listings to their watchlist so they can quickly view details about items they are interested in.

welcome.html - Welcome page which all users are routed to after successful login.

----- app.py -----

app.py serves as the main program to run the application locally. It defines the functions and the queries used while the
application is being run. The application is created in a way in which data which is necessary is pulled from the database
and never hard-coded into the program.

