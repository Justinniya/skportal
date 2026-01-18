from flask import Flask,render_template,request,redirect,url_for,flash,session
from flask_mysqldb import MySQL
import csv
from flask import Response
from datetime import datetime

app = Flask(__name__)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sk_portal'
app.config['SECRET_KEY'] = 'sk_portal'

mysql = MySQL(app)

@app.route('/')
def home():
   return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():
   if request.method == "POST":
       cursor = mysql.connection.cursor()

       
       username = request.form.get('username')
       password = request.form.get('password')
       print(username,password)

       cursor.execute("SELECT * FROM users WHERE username=%s and password=%s",(username,password))
       result = cursor.fetchone()
       if result:
         session['user'] = result
         print(session['user'])
         return redirect('/dashboard')
       
       flash('Invalid username or password')
       return redirect('/')
   
@app.route('/dashboard')
def dashboard():
   cursor = mysql.connection.cursor()

   cursor.execute("""
        SELECT
            (SELECT SUM(total_budget) FROM sk_budget),
            (SELECT SUM(utilized) FROM sk_budget),
            (SELECT COUNT(*) FROM sk_projects WHERE status='Ongoing'),
            (SELECT total FROM youth_statistics ORDER BY year DESC LIMIT 1)
    """)
   row = cursor.fetchone()

   summary = {
      'total_budget': row[0] or 0,
      'utilized': row[1] or 0,
      'projects': row[2] or 0,
      'youth_total': row[3] or 0
   }

   # ---------- BUDGETS ----------
   cursor.execute("""
      SELECT year, total_budget, utilized, remaining, report_file
      FROM sk_budget ORDER BY year DESC
   """)
   budgets = []
   for r in cursor.fetchall():
      budgets.append({
         'year': r[0],
         'total_budget': r[1],
         'utilized': r[2],
         'remaining': r[3],
         'report_file': r[4]
      })

   # ---------- PROJECTS ----------
   cursor.execute("""
      SELECT title, cost, status, start_date, end_date
      FROM sk_projects
   """)
   projects = []
   for r in cursor.fetchall():
      projects.append({
         'title': r[0],
         'cost': r[1],
         'status': r[2],
         'start_date': r[3],
         'end_date': r[4]
      })

   # ---------- ORDINANCES ----------
   cursor.execute("""
      SELECT ordinance_no, title, date_approved
      FROM sk_ordinances
   """)
   ordinances = []
   for r in cursor.fetchall():
      ordinances.append({
         'ordinance_no': r[0],
         'title': r[1],
         'date_approved': r[2]
      })

   # ---------- YOUTH PROGRAMS ----------
   cursor.execute("""
      SELECT name, type, status
      FROM youth_programs
      WHERE status='Active'
   """)
   programs = []
   for r in cursor.fetchall():
      programs.append({
         'name': r[0],
         'type': r[1],
         'status': r[2]
      })

   # ---------- SK OFFICIALS ----------
   cursor.execute("""
      SELECT name, position, committee, contact
      FROM sk_officials
   """)
   officials = []
   for r in cursor.fetchall():
      officials.append({
         'name': r[0],
         'position': r[1],
         'committee': r[2],
         'contact': r[3]
      })

   # ---------- ANNOUNCEMENTS ----------
   cursor.execute("""
      SELECT title, message, event_date
      FROM announcements
   """)
   announcements = []
   for r in cursor.fetchall():
      announcements.append({
         'title': r[0],
         'message': r[1],
         'event_date': r[2]
      })

   # print("summary",summary)
   # print("budgets",budgets)
   # print("projects",projects)
   # print('ordinances',ordinances)
   # print('programs',programs)
   # print('officials',officials)
   # print('announcements',announcements)

   return render_template(
    'dashboard.html',
    summary=summary,
    budgets=budgets,
    projects=projects,
    ordinances=ordinances,
    programs=programs,
    officials=officials,
    announcements=announcements
)

@app.route('/coa/export')
def coa_export():
    if 'user' not in session:
        return redirect('/login')

    cursor = mysql.connection.cursor()

    # --- COA DATA QUERY ---
    cursor.execute("""
        SELECT
            b.year,
            b.total_budget,
            b.utilized,
            b.remaining,
            e.description,
            e.amount,
            e.expense_date,
            e.receipt
        FROM sk_budget b
        LEFT JOIN sk_expenses e ON b.id = e.budget_id
        ORDER BY b.year DESC
    """)

    rows = cursor.fetchall()

   
    def generate():
        yield 'Year,Total Budget,Utilized,Remaining,Expense Description,Expense Amount,Expense Date,Receipt\n'
        for r in rows:
            yield f'{r[0] or ""},{r[1] or 0},{r[2] or 0},{r[3] or 0},{r[4] or ""},{r[5] or 0},{r[6] or ""},{r[7] or ""}\n'


    # --- LOG EXPORT FOR AUDIT ---
    print(session['user'])
    cursor.execute(
        'INSERT INTO coa_exports (exported_by, file_path) VALUES (%s, %s)',
        (session['user'][0], 'COA_EXPORT_CSV')
    )
    mysql.connection.commit()

    filename = f'COA_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return Response(
        generate(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


if __name__ == "__main__":
   app.run(debug=True)