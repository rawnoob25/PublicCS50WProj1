import os
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import re
from flask import abort
from flask import jsonify
from werkzeug.exceptions import BadRequest
from werkzeug.security import check_password_hash, generate_password_hash

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
	session["login"] = ''

	return render_template("index.html", error = error)

#update later
def isOKLogin(uname,pw):
	records = db.execute("SELECT * FROM users WHERE username = :username", {"username" : uname}).fetchall()
	print(records)
	val = records[0]["password"]
	print(val)
	print(check_password_hash(val, pw))
	if check_password_hash(val, pw):
		return "ok"
	elif db.execute("SELECT * FROM users WHERE username = :username", {"username": uname}).rowcount > 0:
		return "pwWrong"
	else:
		return "unameDNE" #user doesn't exist

@app.route("/validateLogin", methods=["POST"])
def validateLogin():
	uname = request.form.get("username")
	pw = request.form.get("pw")
	if isOKLogin(uname,pw) == "ok":
		session["login"] = uname
		user = session["login"]
		return render_template("loginSuccess.html", user=user)
	elif isOKLogin(uname,pw) =="pwWrong":
		return render_template("index.html", error="Incorrect Password")
	else: #isOKLogin(uname,pw)=="unameDNE"
		return render_template("index.html", error="Username does not exist.")

@app.route("/showReviews4User", methods=["GET","POST"])
def showReviews4User():
	un = session['login']
	if db.execute("SELECT isbn FROM reviews WHERE username = :username", {"username":un}).rowcount == 0:
		return render_template("reviews4User.html", reviews="", user=un)
	else:
		reviews = db.execute("SELECT title, author, username, review, rating FROM reviews JOIN books ON reviews.isbn=books.isbn WHERE username = :username", {"username":un})
		return render_template("reviews4User.html", reviews=reviews, user=un)

@app.route("/search", methods=["POST","GET"])
def search():
	user = session["login"]
	if user == '':
		raise BadRequest("User is seeing invalid view of application")

	return render_template("search.html", error='', user=user)

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

@app.route("/validateRegistration", methods=["POST"])
def validateRegistration():
	uname = request.form.get("uname_candidate")
	pw = request.form.get("pw_candidate")
	#check if already in users table
	status = ""
	if db.execute("SELECT * FROM users WHERE username = :username", {"username": uname}).rowcount > 0:
		status = "nameTaken"
		return render_template("register.html", status = status)

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
	hashPW = generate_password_hash(pw)
	db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":uname, "password":hashPW})
	db.commit()
	return render_template("registrationSuccess.html", uname = uname)
	
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
		db.execute("DELETE FROM reviews WHERE username = :username", {"username": un})
		db.commit()
		return render_template("accountDeleted.html")
	else:
		status = "error"
		return render_template("deleteAcct.html", status = status)

@app.route("/basicSearch", methods=["POST"])
def basicSearch():
	by = request.form['searchUsing']
	val = request.form.get("value")
	user = session['login']
	if by == "Title":
		if db.execute("SELECT title FROM books WHERE title = :title", {"title": val}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)
		else:
			books = db.execute("SELECT * FROM books WHERE title = :title", {"title": val}).fetchall()
			return render_template("searchResults.html", books = books, user=user)
	elif by == "Author":
		if db.execute("SELECT title FROM books WHERE author = :author", {"author": val}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)		
		else: 
			books = db.execute("SELECT * FROM books WHERE author = :author", {"author": val}).fetchall()
			return render_template("searchResults.html", books = books, user=user)
	else: #by == "IBSN"
		if db.execute("SELECT title FROM books WHERE isbn = :isbn", {"isbn": val}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)	
		else: 
			books = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": val}).fetchall()
			return render_template("searchResults.html", books = books, user=user)

@app.route("/basicSearchPartial", methods=["POST"])
def basicSearchPartial():
	by = request.form['searchUsing']
	val = request.form.get("value")
	valPatt = '%'+val+'%'
	user=session['login']
	if valPatt == '%%':
		valPatt = ''	
	if by == "Title":
		if db.execute("SELECT title FROM books WHERE title LIKE :title", {"title": valPatt}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)
		else:
			books = db.execute("SELECT * FROM books WHERE title LIKE :title", {"title": valPatt}).fetchall()
			return render_template("searchResults.html", books = books, user=user)
	elif by == "Author":
		if db.execute("SELECT title FROM books WHERE author LIKE :author", {"author": valPatt}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)		
		else: 
			books = db.execute("SELECT * FROM books WHERE author LIKE :author", {"author": valPatt}).fetchall()
			return render_template("searchResults.html", books = books, user=user)
	else: #by == "IBSN"
		if db.execute("SELECT title FROM books WHERE isbn LIKE :isbn", {"isbn": valPatt}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)	
		else: 
			books = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn": valPatt}).fetchall()
			return render_template("searchResults.html", books = books, user=user)

@app.route("/advancedSearch", methods=["POST"])
def advancedSearch():
	any_all = request.form['any_all']
	tit = request.form.get("title")
	aut = request.form.get("author")
	isb = request.form.get("isbn")
	user = session['login']
	if any_all == "Any":
		if db.execute("SELECT title FROM books WHERE title = :title OR author = :author  OR isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)
		else:
			books = db.execute("SELECT * FROM books WHERE title = :title OR author = :author  OR isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).fetchall()
			return render_template("searchResults.html", books = books, user=user)

	else: # any_all == "All"
		if db.execute("SELECT title FROM books WHERE title = :title AND author = :author  AND isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)
		else:
			books = db.execute("SELECT * FROM books WHERE title = :title AND author = :author  AND isbn = :isbn", {"title": tit, "author": aut, "isbn":isb}).fetchall()
			return render_template("searchResults.html", books = books, user=user)

@app.route("/advancedSearchPartial", methods=["POST"])
def advancedSearchPartial():
	user = session['login']
	any_all = request.form['any_all']
	tit = request.form.get("title")
	aut = request.form.get("author")
	isb = request.form.get("isbn")
	titPatt = '%'+tit+'%'
	autPatt = '%'+aut+'%'
	isbPatt = '%'+isb+'%'
	if titPatt == '%%':
		titPatt = ''
	if autPatt == '%%':
		autPatt = ''
	if isbPatt == '%%':
		isbPatt = ''

	if any_all == "Any":
		if db.execute("SELECT title FROM books WHERE title LIKE :title OR author LIKE :author  OR isbn LIKE :isbn", {"title": titPatt, "author": autPatt, "isbn": isbPatt}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)
		else:
			books = db.execute("SELECT * FROM books WHERE title LIKE :title OR author LIKE :author  OR isbn LIKE :isbn", {"title": titPatt, "author": autPatt, "isbn": isbPatt}).fetchall()
			print(books)
			return render_template("searchResults.html", books = books, user=user)

	else: # any_all == "All"
		if db.execute("SELECT title FROM books WHERE title LIKE :title AND author LIKE :author  AND isbn LIKE :isbn", {"title": titPatt, "author": autPatt, "isbn": isbPatt}).rowcount == 0:
			return render_template("search.html", error="noMatch", user=user)
		else:
			books = db.execute("SELECT * FROM books WHERE title LIKE :title AND author LIKE :author  AND isbn LIKE :isbn", {"title": titPatt, "author": autPatt, "isbn": isbPatt}).fetchall()
			return render_template("searchResults.html", books = books, user=user)

@app.route("/search/<isbn>", methods=["GET"])
def bookInfo(isbn):
	user = session['login']
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	if book is None:
		return render_template("search.html", error="noMatch", user=user)
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "0HyXLM8Pi1U9HWe7774AIQ", "isbns": isbn})
	ratingsCt = -1
	avgRating = -1
	try:
		obj = res.json()
		if obj is not None:
			ratingsCt = ((obj['books'])[0])['ratings_count']
			avgRating = ((obj['books'])[0])['average_rating']
	except:
		pass

	
	reviews = db.execute("SELECT review, username FROM reviews WHERE isbn = :isbn", {"isbn" : isbn}).fetchall()
	print(reviews)
	print(type(reviews))
	if reviews != None and reviews!=[]:
		ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn", {"isbn" : isbn}).fetchall()
		ratings = [x[0] for x in ratings]
		print("reviews: "+str(reviews))
		print("type(reviews): "+str(type(reviews)))
		print("ratings: "+str(ratings))
		print("type(ratings): "+str(type(ratings)))
		avgUserRating = round(sum(ratings)/len(ratings), 2)
	else:
		ratings = ""
		reviews=""
		avgUserRating = -1

	userLeftReview = False
	if db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND username = :username", {"isbn" : isbn, "username":session["login"]}).rowcount > 0:
		userLeftReview = True

	user = session["login"]
	return render_template("bookInfo.html", book=book, ratingsCt=ratingsCt, avgRating=avgRating, reviews=reviews, avgUserRating=avgUserRating, userLeftReview=userLeftReview, user = user)

@app.route("/reviewAdded/<isbn>/<username>", methods=["POST"])
def leaveReview(isbn, username):
	theRating = int(request.form['rating'])
	theReview = request.form['review']
	db.execute("INSERT INTO reviews (isbn, username, rating, review) VALUES (:isbn, :username, :rating, :review)", {"isbn":isbn, "username":username, "rating":theRating, "review":theReview})
	db.commit()
	user = session["login"]
	return render_template("reviewAdded.html", user=user)

@app.route("/api/<isbn>", methods=["GET"])
def displayJSON(isbn):
	if db.execute("SELECT title FROM books WHERE isbn = :isbn", {"isbn": isbn}).rowcount == 0:
		abort(404)
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "0HyXLM8Pi1U9HWe7774AIQ", "isbns": isbn})
	obj = res.json()
	item = (obj['books'])[0]
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone() #type(book) is class 'sqlalchemy.engine.result.RowProxy', which functions as a tuple that can be indexed by columns in the table
	title = book['title']
	author = book['author']
	year = book['year']
	isbn = book['isbn']
	ratings_count = item['ratings_count']
	average_score = item['average_rating']
	d = {"title": title, 
		"author": author, 
		"year": year, 
		"isbn": isbn, 
		"ratings_count": ratings_count,
		"average_score": average_score}
	resp = jsonify(d)
	resp.status_code = 200
	return resp