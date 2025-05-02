import tkinter as tk
from tkinter import messagebox, ttk
import pymysql as mys
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

DATE_FILE = "current_date.txt"

def get_current_date():
    if not os.path.exists(DATE_FILE):
        with open(DATE_FILE, 'w') as f:
            f.write("2025-04-17")

    with open(DATE_FILE, 'r') as f:
        current_date = datetime.strptime(f.read().strip(), "%Y-%m-%d").date()

    new_date = current_date + timedelta(days=1)

    with open(DATE_FILE, 'w') as f:
        f.write(str(new_date))

    return new_date

myconn = mys.connect(
    host='localhost', user='root', passwd='12345', database='library_management'
)
cursor = myconn.cursor()

def create_tables():
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll_no INT PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                email VARCHAR(100),
                class VARCHAR(20),
                contact VARCHAR(15)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS publishers (
                publisher_id INT PRIMARY KEY,
                contact VARCHAR(15),
                author_first_name VARCHAR(50),
                author_last_name VARCHAR(50),
                city VARCHAR(50),
                state VARCHAR(50)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INT PRIMARY KEY,
                book_name VARCHAR(100),
                author_first_name VARCHAR(50),
                author_last_name VARCHAR(50),
                category VARCHAR(50),
                availability BOOLEAN,
                publisher_id INT,
                FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id)
            )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lib (
            issue_id INT PRIMARY KEY,
            roll_no INT,
            book_id INT,
            doi DATE,
            dor DATE,
            status BOOLEAN,
            FOREIGN KEY (roll_no) REFERENCES students(roll_no),
            FOREIGN KEY (book_id) REFERENCES books(book_id)
        )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fine (
                fine_id INT AUTO_INCREMENT PRIMARY KEY,
                issue_id INT,
                roll_no INT,
                days_late INT,
                per_day_fine DECIMAL(5,2),
                fine_amount DECIMAL(10,2) GENERATED ALWAYS AS (days_late * per_day_fine) STORED,
                paid_status BOOLEAN,
                FOREIGN KEY (issue_id) REFERENCES lib(issue_id),
                FOREIGN KEY (roll_no) REFERENCES students(roll_no)
            )
        """)

        myconn.commit()
    except mys.MySQLError as err:
        myconn.rollback()

def create_procedures():
    try:
        cursor.execute("""
            CREATE PROCEDURE IF NOT EXISTS IssueBook (
                IN p_issue_id INT,
                IN p_roll_no INT,
                IN p_book_id INT,
                IN p_doi DATE,
                IN p_dor DATE
            )
            BEGIN
                DECLARE book_available BOOLEAN;
                SELECT availability INTO book_available FROM books WHERE book_id = p_book_id;
                IF book_available THEN
                    INSERT INTO lib (issue_id, roll_no, book_id, doi, dor, status)
                    VALUES (p_issue_id, p_roll_no, p_book_id, p_doi, p_dor, FALSE);
                    UPDATE books SET availability = FALSE WHERE book_id = p_book_id;
                ELSE
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Book is not available';
                END IF;
            END
        """)

        cursor.execute("""
            CREATE PROCEDURE IF NOT EXISTS ReturnBook (
                IN p_issue_id INT
            )
            BEGIN
                DECLARE v_roll_no INT;
                DECLARE v_book_id INT;
                DECLARE v_dor DATE;
                SELECT roll_no, book_id, dor INTO v_roll_no, v_book_id, v_dor
                FROM lib WHERE issue_id = p_issue_id AND status = FALSE;

                UPDATE lib SET status = TRUE WHERE issue_id = p_issue_id;
                UPDATE books SET availability = TRUE WHERE book_id = v_book_id;

                IF CURDATE() > v_dor THEN
                    INSERT INTO fine (issue_id, roll_no, days_late, per_day_fine, paid_status)
                    VALUES (p_issue_id, v_roll_no, DATEDIFF(CURDATE(), v_dor), 5.00, FALSE);
                END IF;
            END
        """)

        myconn.commit()
    except mys.MySQLError as err:
        myconn.rollback()

# Yahoo email configuration
EMAIL_ADDRESS = "college.library@myyahoo.com"  
EMAIL_PASSWORD = "Collegelib@1234"  

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email

        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

        print(f"Email successfully sent to {to_email}")  # Debugging message
    except smtplib.SMTPAuthenticationError:
        print("SMTP Authentication error. Check email credentials.")
    except smtplib.SMTPConnectError:
        print("Failed to connect to the SMTP server. Check your network or server settings.")
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def send_reminder_emails():
    today = get_current_date()

    cursor.execute("""
        SELECT s.email, l.issue_id, b.book_name
        FROM lib l
        JOIN students s ON l.roll_no = s.roll_no
        JOIN books b ON l.book_id = b.book_id
        WHERE l.dor = %s AND l.status = FALSE
    """, (today,))

    for email, issue_id, book_name in cursor.fetchall():
        subject = "Library Book Return Reminder"
        body = f"Dear Student,\n\nThis is a reminder to return the book '{book_name}' (Issue ID: {issue_id}) by tomorrow.\n\nThank you,\nLibrary Management"
        send_email(email, subject, body)

def update_fine():
    today = get_current_date()

    cursor.execute("""
        SELECT issue_id, roll_no, dor FROM lib WHERE status = FALSE AND dor < %s
    """, (today,))

    for issue_id, roll_no, dor in cursor.fetchall():
        days_late = (today - dor).days
        per_day_fine = 5.00

        cursor.execute("SELECT fine_id FROM fine WHERE issue_id = %s", (issue_id,))

        if cursor.fetchone():
            cursor.execute("""
                UPDATE fine SET days_late = %s WHERE issue_id = %s
            """, (days_late, issue_id))
        else:
            cursor.execute("""
                INSERT INTO fine (issue_id, roll_no, days_late, per_day_fine, paid_status)
                VALUES (%s, %s, %s, %s, %s)
            """, (issue_id, roll_no, days_late, per_day_fine, False))

    myconn.commit()

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f4f8")

        style = ttk.Style()
        style.theme_use('default')

        style.configure("TNotebook", background="#ffffff", padding=10)
        style.configure("TNotebook.Tab", font=('Segoe UI', 12), padding=10)
        style.configure("TButton", font=('Segoe UI', 11), padding=6)
        style.configure("TLabel", font=('Segoe UI', 11), background="#f0f4f8")
        style.configure("Treeview.Heading", font=('Segoe UI', 11, 'bold'))
        style.configure("Treeview", font=('Segoe UI', 10))

        self.tabs = ttk.Notebook(self.root)

        self.student_tab = ttk.Frame(self.tabs)
        self.issue_tab = ttk.Frame(self.tabs)
        self.fine_tab = ttk.Frame(self.tabs)
        self.return_tab = ttk.Frame(self.tabs)
        self.search_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.student_tab, text='Register Student')
        self.tabs.add(self.issue_tab, text='Issue Book')
        self.tabs.add(self.fine_tab, text='View Fine')
        self.tabs.add(self.return_tab, text='Return Book')
        self.tabs.add(self.search_tab, text='Search Borrowed')

        self.tabs.pack(expand=1, fill='both')

        self.register_student_ui()
        self.issue_book_ui()
        self.view_fine_ui()
        self.return_book_ui()
        self.search_borrowed_ui()

    def register_student_ui(self):
        fields = ["Roll No", "First Name", "Last Name", "Email", "Class", "Contact"]
        self.student_entries = {}

        frame = tk.Frame(self.student_tab, bg="#f0f4f8")
        frame.pack(pady=40)

        for idx, field in enumerate(fields):
            tk.Label(frame, text=field + ":", anchor="e", width=20, bg="#f0f4f8").grid(row=idx, column=0, padx=10, pady=8, sticky='e')
            entry = tk.Entry(frame, font=('Segoe UI', 10), width=30)
            entry.grid(row=idx, column=1, padx=10, pady=8)
            self.student_entries[field] = entry

        tk.Button(frame, text="Register", command=self.register_student).grid(row=len(fields), columnspan=2, pady=20)

    def register_student(self):
        try:
            values = [self.student_entries[f].get() for f in self.student_entries]
            cursor.execute("""
                INSERT INTO students (roll_no, first_name, last_name, email, class, contact)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, values)
            myconn.commit()
            messagebox.showinfo("Success", "Student registered successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def issue_book_ui(self):
        fields = ["Issue ID", "Roll No", "Book ID", "Date of Issue (YYYY-MM-DD)", "Date of Return (YYYY-MM-DD)"]
        self.issue_entries = {}

        frame = tk.Frame(self.issue_tab, bg="#f0f4f8")
        frame.pack(pady=40)

        for idx, field in enumerate(fields):
            tk.Label(frame, text=field + ":", anchor="e", width=30, bg="#f0f4f8").grid(row=idx, column=0, padx=10, pady=8, sticky='e')
            entry = tk.Entry(frame, font=('Segoe UI', 10), width=30)
            entry.grid(row=idx, column=1, padx=10, pady=8)
            self.issue_entries[field] = entry

        tk.Button(frame, text="Issue Book", command=self.issue_book).grid(row=len(fields), columnspan=2, pady=20)

    def issue_book(self):
        try:
            values = [self.issue_entries[f].get() for f in self.issue_entries]
            cursor.callproc('IssueBook', values)
            myconn.commit()
            messagebox.showinfo("Success", "Book issued successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def return_book_ui(self):
        self.return_entries = {}

        frame = tk.Frame(self.return_tab, bg="#f0f4f8")
        frame.pack(pady=40)

        tk.Label(frame, text="Issue ID:", anchor="e", width=20, bg="#f0f4f8").grid(row=0, column=0, padx=10, pady=8, sticky='e')
        issue_entry = tk.Entry(frame, font=('Segoe UI', 10), width=30)
        issue_entry.grid(row=0, column=1, padx=10, pady=8)
        self.return_entries["Issue ID"] = issue_entry

        tk.Button(frame, text="Return Book", command=self.return_book).grid(row=1, columnspan=2, pady=20)

    def return_book(self):
        try:
            issue_id = self.return_entries["Issue ID"].get()
            cursor.callproc('ReturnBook', (issue_id,))
            myconn.commit()
            messagebox.showinfo("Success", "Book returned successfully!")
            self.load_fine()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def view_fine_ui(self):
        frame = tk.Frame(self.fine_tab, bg="#f0f4f8")
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.tree = ttk.Treeview(frame, columns=("issue_id", "roll_no", "amount", "status"), show="headings", height=15)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(fill='both', expand=True)

        button_frame = tk.Frame(frame, bg="#f0f4f8")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Load Fine", command=self.load_fine).pack(side="left", padx=10)
        tk.Button(button_frame, text="Send Reminder Emails", command=self.send_reminders_ui).pack(side="left", padx=10)

    def send_reminders_ui(self):
        try:
            send_reminder_emails()
            messagebox.showinfo("Success", "Reminder emails sent successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send emails: {str(e)}")

    def load_fine(self):
        try:
            self.tree.delete(*self.tree.get_children())
            cursor.execute("SELECT issue_id, roll_no, fine_amount, paid_status FROM fine WHERE paid_status = FALSE")
            for row in cursor.fetchall():
                self.tree.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def search_borrowed_ui(self):
        frame = tk.Frame(self.search_tab, bg="#f0f4f8")
        frame.pack(pady=40, padx=20, fill='both', expand=True)

        tk.Label(frame, text="Enter Roll No:", bg="#f0f4f8").pack(pady=10)
        self.search_entry = tk.Entry(frame, font=('Segoe UI', 10), width=30)
        self.search_entry.pack(pady=5)

        tk.Button(frame, text="Search", command=self.search_borrowed).pack(pady=10)

        columns = ("Book ID", "Book Name", "DOI", "DOR", "Fine")
        self.search_tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, anchor="center", width=150)

        self.search_tree.pack(fill='both', expand=True, pady=20)

    def search_borrowed(self):
        roll_no = self.search_entry.get()
        try:
            self.search_tree.delete(*self.search_tree.get_children())
            query = """
                SELECT 
                    b.book_id, b.book_name, l.doi, l.dor,
                    IFNULL(f.fine_amount, 0)
                FROM lib l
                JOIN books b ON l.book_id = b.book_id
                LEFT JOIN fine f ON l.issue_id = f.issue_id
                WHERE l.roll_no = %s AND l.status = FALSE
            """
            cursor.execute(query, (roll_no,))
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    self.search_tree.insert('', 'end', values=row)
            else:
                messagebox.showinfo("Info", "No active borrowed books found for this Roll No.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    create_tables()
    create_procedures()
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()