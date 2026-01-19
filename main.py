from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mysqldb import MySQL
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
#--------- Main ----------
@app.route('/')
def home():
   return render_template("auth/index.html")


@app.route('/login', methods=['GET','POST'])
def login():
   if request.method == "POST":
      username = request.form['username']
      password = request.form['password']

      cur = mysql.connection.cursor()
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



#-----admin------

@app.route('/admin/')
def admin_dashboard():
   if session['session']['role'] != 'admin':
        return redirect(url_for('home'))
   
   cur = mysql.connection.cursor()
   cur.execute("SELECT COUNT(*) AS total FROM projects")
   total_projects = cur.fetchone()['total']

   cur.execute("SELECT COUNT(*) AS total FROM projects WHERE status = 'ongoing'")
   ongoing_projects = cur.fetchone()['total']

   cur.execute("SELECT IFNULL(SUM(allocated_amount),0) AS total FROM budgets")
   total_budget = cur.fetchone()['total']

   cur.execute("SELECT IFNULL(SUM(utilized_amount),0) AS total FROM budgets")
   budget_utilized = cur.fetchone()['total']

   # Recent projects with budget
   cur.execute("""
      SELECT p.id, p.title, p.status,p.brgy, p.start_date, p.end_date,
            IFNULL(b.allocated_amount,0) AS budget
      FROM projects p
      LEFT JOIN budgets b ON p.id = b.project_id
      ORDER BY p.id DESC
      LIMIT 10
   """)
   projects = cur.fetchall()  # Already list of dicts

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