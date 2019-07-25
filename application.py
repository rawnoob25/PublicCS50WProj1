import os
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import re

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET","POST"])
def index():
	error = False
	return render_template("index.html", error = error)

#update later
def isOKLogin(uname,pw):
	# if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": uname, "password": pw}).rowcount > 0:
	# 	return True
	# return False
	if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": uname, "password": pw}).rowcount > 0:
		return "ok"
	elif db.execute("SELECT * FROM users WHERE username = :username", {"username": uname}).rowcount > 0:
		return "pwWrong"
	else:
		return "unameDNE" #user doesn't exist

@app.route("/validateLogin", methods=["POST"])
def validateLogin():
	uname = request.form.get("username")
	pw = request.form.get("pw")
	# if not isOKLogin(uname,pw):
	# 	error = True
	# 	return render_template("index.html", error = error)
	# return render_template("search.html")
	if isOKLogin(uname,pw) == "ok":
		return render_template("search.html",error="")
	elif isOKLogin(uname,pw) =="pwWrong":
		return render_template("index.html", error="Incorrect Password")
	else: #isOKLogin(uname,pw)=="unameDNE"
		return render_template("index.html", error="Username does not exist.")

@app.route("/register", methods=["POST"])
def register():
	status = "empty"
	return render_template("register.html", status = status)

def checkUname(uname):
	if len(uname)<8:
		return False
	elif re.search("\s", uname):
		return False
	elif not re.search("[A-Za-z]", uname):
		return False
	elif not re.search("[0-9]", uname):
		return False
	else:
		return True

def checkPW(pw):
	if len(pw)<8:
		return False
	elif re.search("\s", pw):
		return False
	elif not re.search("[A-Z]", pw):
		return False
	elif not re.search("[a-z]", pw):
		return False
	elif not re.search("[0-9]", pw):
		return False
	elif not re.search("[\!\@\#\$\%\^\&\*_\-]", pw):
		return False
	else:
		return True

def isOKReg(uname,pw):
	unameOK=1
	pwOK=1
	if not checkUname(uname):
		unameOK=0
	if not checkPW(pw):
		pwOK=0
	return (unameOK, pwOK)
	# return True

# while True:   
#     if (len(password)<8): 
#         flag = -1
#         break
#     elif not re.search("[a-z]", password): 
#         flag = -1
#         break
#     elif not re.search("[A-Z]", password): 
#         flag = -1
#         break
#     elif not re.search("[0-9]", password): 
#         flag = -1
#         break
#     elif not re.search("[_@$]", password): 
#         flag = -1
#         break
#     elif re.search("\s", password): 
#         flag = -1
#         break
#     else: 
#         flag = 0
#         print("Valid Password") 
#         break
@app.route("/validateRegistration", methods=["POST"])
def validateRegistration():
	uname = request.form.get("uname_candidate")
	pw = request.form.get("pw_candidate")
	#check if already in users table
	status = ""
	if db.execute("SELECT * FROM users WHERE username = :username", {"username": uname}).rowcount > 0:
		status = "nameTaken"
		return render_template("register.html", status = status)
	# elif not isOKReg(uname,pw):
	# 	status = "invalidReg"
	# 	return render_template("register.html", status = status)
	validity = isOKReg(uname, pw)
	unameIsOK = validity[0]
	pwIsOK = validity[1]
	if (not unameIsOK and not pwIsOK):
		status = "Username and Password are invalid"
		return render_template("register.html", status = status)
	elif (not unameIsOK):
		status = "Username is Invalid"
		return render_template("register.html", status = status)
	elif (not pwIsOK):
		status = "Password is Invalid"
		return render_template("register.html", status = status)
	db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":uname, "password":pw})
	db.commit()
	return render_template("registrationSuccess.html", uname = uname)
	
		# db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn":isbn, "title":title, "author":author, "year":year})
@app.route("/deleteAcct", methods=["POST"])
def deleteAcct():
	status=""
	return render_template("deleteAcct.html", status = status)

@app.route("/tryDelete", methods=["POST"])
def tryDelete():
	status = ""
	un = request.form.get("uname")
	pw = request.form.get("pw")
	if isOKLogin(un,pw) == "ok":
		db.execute("DELETE FROM users WHERE username = :username AND password = :password", {"username": un, "password": pw})
		db.commit()
		return render_template("accountDeleted.html")
	else:
		status = "error"
		return render_template("deleteAcct.html", status = status)

@app.route("/basicSearch", methods=["POST"])
def basicSearch():
	by = request.form['searchUsing']
	val = request.form.get("value")
	# return render_template("searchResults.html", by = by, val = val)
	if by == "Title":
		if db.execute("SELECT title FROM books WHERE title = :title", {"title": val}).rowcount == 0:
			return render_template("search.html", error="noMatch")
		else:
			books = db.execute("SELECT * FROM books WHERE title = :title", {"title": val}).fetchall()
			return render_template("searchResults.html", books = books)
	elif by == "Author":
		if db.execute("SELECT title FROM books WHERE author = :author", {"author": val}).rowcount == 0:
			return render_template("search.html", error="noMatch")		
		else: 
			books = db.execute("SELECT * FROM books WHERE author = :author", {"author": val}).fetchall()
			return render_template("searchResults.html", books = books)
	else: #by == "IBSN"
		if db.execute("SELECT title FROM books WHERE isbn = :isbn", {"isbn": val}).rowcount == 0:
			return render_template("search.html", error="noMatch")	
		else: 
			books = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": val}).fetchall()
			return render_template("searchResults.html", books = books)

@app.route("/advancedSearch", methods=["POST"])
def advancedSearch():
	any_all = request.form['any_all']
	tit = request.form.get("title")
	aut = request.form.get("author")
	isb = request.form.get("isbn")
	if any_all == "Any":
		if db.execute("SELECT title FROM books WHERE title = :title OR author = :author  OR isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).rowcount == 0:
			return render_template("search.html", error="noMatch")
		else:
			books = db.execute("SELECT * FROM books WHERE title = :title OR author = :author  OR isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).fetchall()
			return render_template("searchResults.html", books = books)

	else: # any_all == "All"
		if db.execute("SELECT title FROM books WHERE title = :title AND author = :author  AND isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).rowcount == 0:
			return render_template("search.html", error="noMatch")
		else:
			books = db.execute("SELECT * FROM books WHERE title = :title AND author = :author  AND isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).fetchall()
			return render_template("searchResults.html", books = books)

@app.route("/search/<isbn>")
def bookInfo(isbn):
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	if book is None:
		return render_template("search.html", error="noMatch")
	return render_template("bookInfo.html", book=book)
    # # Make sure flight exists.
    # flight = db.execute("SELECT * FROM flights WHERE id = :id", {"id": flight_id}).fetchone()
    # if flight is None:
    #     return render_template("error.html", message="No such flight.")

    # # Get all passengers.
    # passengers = db.execute("SELECT name FROM passengers WHERE flight_id = :flight_id",
    #                         {"flight_id": flight_id}).fetchall()
    # return render_template("flight.html", flight=flight, passengers=passengers)
