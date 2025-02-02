
import pymysql as mys
def displayALL():
    try:
        myconn=mys.connect(host='localhost',user="root",\
                           passwd="1234",database="school")
        mycur=myconn.cursor()
        query="select * from empLIBRARY"
        mycur.execute(query)
        rs=mycur.fetchall() 
        count=mycur.rowcount
        print("Rollno\t\t\tBook Name\t\t\tAuthor\t\t\tDate of issue\t\t\tDate of return")
        for row in rs:
            print(row[0],"\t\t\t",row[1],"\t\t\t\t",row[2],"\t\t",row[3],"\t\t\t",row[4])
        print(" the no:of rows is \t",count)
    except Exception as e:
        print(e)


def Insertion():
    try:
        mycon= mys.connect(host="localhost",user="root",passwd="1234", database ="school")
        mycur=mycon.cursor()
        rollno=int(input("enter the Roll Number:"))
        book=input("enter the Book Name:")
        name=input("Enter the Author:")
        doi=input(" enter the date of issue:")
        dor=input("enter the date of return:")
        mycur.execute("insert into empLIBRARY values\
                                   ({},'{}','{}','{}','{}')".format(rollno,book,name,doi,dor))
        mycon.commit()
        displayALL()
    except Exception as e:    
           print(e)
  
  
  
def Updation():
    try:
        myconn=mys.connect(host='localhost',user="root",\
                           passwd="1234",database="school")
        mycur=myconn.cursor()
        eno=int(input(" enter the rollno to be updated..."))
        newname=input(" enter the new Author")
        newdoi=input("enter the new date of issue")
        query="update empLIBRARY set name='{}' ,doi='{}'\
             where rollno={}".format(newname,newdoi,eno)
        mycur.execute(query)
        myconn.commit()
        print(" Record updated")
        displayALL()

    except Exception as e:
        print(e)
        
        
def Deletion():
    try:
        myconn=mys.connect(host='localhost',user="root",\
                         passwd="1234",database="school")
        mycur=myconn.cursor()    
        eno=int(input("Enter the Roll number to be deleted ..."))
        query="Delete from empLIBRARY where rollno={}".format(eno)
        mycur.execute(query)
        myconn.commit()
        print(" Student deleted")
        displayALL()
    except Exception as e:
        print(e)
        
        

def SearchOne():
    try:
        myconn=mys.connect(host='localhost',user="root",\
                         passwd="1234",database="school")
        mycur=myconn.cursor()
        eno=int(input(" enter the rollno to be searched:"))
        query="select * from empLIBRARY where rollno={}".format(eno)
        mycur.execute(query)
        rs=mycur.fetchone()
        for row in rs:
            if row!=None:
                print(row)
            else:
                print(" No such student")
    except Exception as e:
        print(e)
        
def Searchname():
    try:
        myconn=mys.connect(host='localhost',user="root",passwd="1234",database="school")
        mycur=myconn.cursor()
        Book=input(" enter the Book to be searched:")
        query="select * from empLIBRARY where book='{}'".format(Book)
        print(query)
        mycur.execute(query)
        rs=mycur.fetchall()
        nrec=mycur.rowcount
        print()
        print(" Table Name : empLIBRARY")
        print("rollno\tBook\tAuthor\tdate of issue\tdate of return")
        print("*"*30)
        for row in rs:
            if row!=None:
               print(row[0],"\t",row[1],"\t",row[2],"\t",row[3],"\t",row[4])
            else:
                print(" no such book")      
        print(" Total no:of books",nrec)
    except Exception as e:
        print(e)

def Searchdoi():
    try:
        myconn=mys.connect(host='localhost',user="root"\
                           ,passwd="1234",database="school")
        mycur=myconn.cursor()
        doi=input(" enter the Date of Issue to be searched:")
        query="select * from empLIBRARY where doi='{}'".format(doi)
        mycur.execute(query)
        rs=mycur.fetchall()
        nrec=mycur.rowcount
        print()
        print(" Table Name : empLIBRARY")
        print("rollno\tBook\tAuthor\tdate of issue\tdate of returning")
        print("*"*30)
        for row in rs:
            if row!=None:
               print(row[0],"\t",row[1],"\t",row[2],"\t",row[3],"\t",row[4])
            else:
                print(" no such student")
        
        print(" Total no:of Students",nrec)
    except Exception as e:
        print(e)
def Createdatabase():
    try:
        myconn=mys.connect(host='localhost',user="root",\
                         passwd="1234")
        mycur=myconn.cursor()
        query="create database school";
        mycur.execute(query)
        myconn.commit()
        print(" Database successfully created")
    except Exception as e:
        print(e)
        
def Createtable():
    try:
        myconn=mys.connect(host='localhost',user="root",passwd="1234",database="school")
        mycur=myconn.cursor()
        query="create table empLIBRARY(rollno int primary key,\
                book char(20) not null,name char(20),\
                doi date,dor date)"
        mycur.execute(query)
        myconn.commit()
        print(" Table successfully created")      
    except Exception as e:
        print(e)
  
 
def showtables():
    try:
        myconn=mys.connect(host='localhost',user="root",\
                         passwd="1234",database="school")
        mycur=myconn.cursor()
        query="show tables";
        mycur.execute(query)
        for x in mycur:
            print(x)
    except Exception as e:
        print(e)





def menu():
    ans='y'
    while ans=='y':
        print(" EMP  Details")
        print("1. create database")
        print("2. create table")
        print("3. show tables")
        print("4. Insert")
        print("5. Display")
        print("6. Delete")
        print("7. Update")
        print("8. Search by Rollno")
        print("9. Search by Book")
        print("10. Search by Date of Issue")
        print()
        ch=int(input(" enter the choice"))
        if ch==1:
            Createdatabase()
        elif ch==2:
            Createtable()
        elif ch==3:
            showtables()
        elif ch==4:
            Insertion()
        elif ch==5:
            displayALL()
        elif ch==6:
            Deletion()
        elif ch==7:
            Updation()
        elif ch==8:
            SearchOne()
        elif ch==9:
            Searchname()
        elif ch==10:
            Searchdoi()
        
        ans=input(" do you want to continue y/n")
menu()


