import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
	# only execute below lines if database doesn't already exist
	db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year VARCHAR)")
	print('created table')
	db.commit()
	
	f = open('books.csv')
	reader = csv.reader(f)
	firstLine = True
	ct = 0
	for isbn, title, author, year in reader:
		if firstLine:
			firstLine = False
			continue
		db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn":isbn, "title":title, "author":author, "year":year})
		# print(f"Added book {title} by {author} published in {year}. Its IBSN-10 is:{isbn}")
		ct = ct +1
	db.commit()
	print("added "+str(ct)+" entries")

    

    # f = open("flights.csv")
    # reader = csv.reader(f)
    # for origin, destination, duration in reader:
    #     db.execute("INSERT INTO flights (origin, destination, duration) VALUES (:origin, :destination, :duration)",
    #                 {"origin": origin, "destination": destination, "duration": duration})
    #     print(f"Added flight from {origin} to {destination} lasting {duration} minutes.")
    # db.commit()

if __name__ == "__main__":
    main()
