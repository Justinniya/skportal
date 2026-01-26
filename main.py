from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from config import Config

pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

def get_db():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=3306,
        cursorclass=Config.DB_CURSORCLASS
    )
#--------- Main ----------
@app.route('/')
def home():
   return render_template("auth/index.html")


@app.route('/login', methods=['GET','POST'])
def login():
   if request.method == "POST":
      username = request.form['username']
      password = request.form['password']

      conn = get_db()
      cur = conn.cursor()
      cur.execute(
         'SELECT * FROM users WHERE username=%s AND status=1',
         (username,)
      )
      user = cur.fetchone()
      cur.close()
      if user and user['password'] == password:
         session['session'] = user

         print(session['session'])

         return redirect(url_for('dashboard'))

      flash('Invalid username or password')
      return redirect(url_for('home'))
   

@app.route('/logout')
def logout():
   session.pop('session', None)
   # print(session['user_id'] == True)
   return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():
   if 'session' not in session:
      return redirect(url_for('home'))
   
   print(session['session'])

   if session['session']['role'] == 'admin':
      print(session['session'])
      return redirect(url_for('admin_dashboard'))

   if session['session']['role'] == 'skofficial':
      print(session['session'])
      return redirect(url_for('officials_dashboard'))

   return redirect(url_for('viewers_dashboard'))


@app.route('/projects')
def projects():
   if 'session' not in session:
      return redirect(url_for('home'))
   return render_template("admin/projects.html")

@app.route("/projects/add", methods=["GET", "POST"])
def add_project():
   if 'session' not in session:
      return redirect(url_for('home'))
   return render_template("admin/add_project.html")



@app.route('/admin/')
def admin_dashboard():
   if session['session']['role'] != 'admin':
        return redirect(url_for('home'))
   
   conn = get_db()
   cur = conn.cursor()
   cur.execute("SELECT COUNT(*) AS total FROM projects")
   total_projects = cur.fetchone()['total']

   cur.execute("SELECT COUNT(*) AS total FROM projects WHERE status = 'ongoing'")
   ongoing_projects = cur.fetchone()['total']

   cur.execute("SELECT IFNULL(SUM(allocated_amount),0) AS total FROM budgets")
   total_budget = cur.fetchone()['total']

   cur.execute("SELECT IFNULL(SUM(utilized_amount),0) AS total FROM budgets")
   budget_utilized = cur.fetchone()['total']

   cur.execute("""
      SELECT p.id, p.title, p.status,p.brgy, p.start_date, p.end_date,
            IFNULL(b.allocated_amount,0) AS budget
      FROM projects p
      LEFT JOIN budgets b ON p.id = b.project_id
      ORDER BY p.id DESC
      LIMIT 10
   """)
   projects = cur.fetchall()  

   cur.close()

   return render_template(
      'admin/admin_dashboard.html',
      total_projects=total_projects,
      ongoing_projects=ongoing_projects,
      total_budget=total_budget,
      budget_utilized=budget_utilized,
      projects=projects
   )



#-----sk officials------
@app.route('/officials/')
def officials_dashboard():
   if 'session' not in session:
      return redirect(url_for('home'))
   return "Welcome officials"

#-----viewers------
@app.route('/viewers/')
def viewers_dashboard():
   if 'session' not in session:
      return redirect(url_for('home'))
   return "Welcome viewers"


if __name__ == "__main__":
   app.run(debug=True)