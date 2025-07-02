from flask import Flask, render_template, request, redirect, url_for, session ,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,date
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=False, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bg_color = db.Column(db.String(50), default='#0d1b2a')

class Expense(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=datetime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
   
@app.route("/")
def index():
         
    return render_template("welcome.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    flash("Successfully login")
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            session["user_id"] = user.id
            flash("Login successful")
            return redirect(url_for("home"))
        return redirect(url_for("register"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    flash("Registered successfully")
    if request.method == "POST":
        new_user = User(username=request.form["username"], password=request.form["password"])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session.get("user_id")) 
    today = date.today()
    expenses_today= Expense.query.filter_by(user_id=user.id).filter(Expense.date == today).all()
    total_today = sum(exp.amount for exp in expenses_today)
    current_month = today.month
    current_year = today.year

    expenses_month = Expense.query.filter_by(user_id=user.id).filter(
        db.extract('month', Expense.date)== current_month,
        db.extract('year', Expense.date)== current_year,
    ).all()

    total_month = sum(exp.amount for exp in expenses_month)

    return render_template("home.html", username=user.username, bg_color = user.bg_color, total_today = total_today,total_month = total_month)

@app.route("/about")
def about():
    user = User.query.get(session.get("user_id")) 

    return render_template("about.html", username=user.username, bg_color=user.bg_color)

@app.route("/add", methods=["GET", "POST"])
def add_expense():
     if "user_id" not in session:
        return redirect(url_for("login"))
     
     user = User.query.get(session.get("user_id")) 
   
     if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        amount = float(request.form["amount"])
        date_str = request.form["date"]
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        user_id = session["user_id"]
        new_expense = Expense(title=title, category=category,date=date, amount=amount, user_id=user_id)
        db.session.add(new_expense)
        db.session.commit()
        flash("Expenses successfully added")
        return redirect(url_for("view_expenses"))
     return render_template("add.html", username = user.username, bg_color=user.bg_color)

@app.route("/expenses", methods=["GET", "POST"])
def view_expenses():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    query = Expense.query.filter_by(user_id=user.id)

    selected_month = request.args.get("month")
    selected_year = request.args.get("year")
    selected_category = request.args.get("category")

    if selected_month and selected_year:
        query = query.filter(
            db.extract('month', Expense.date) == int(selected_month),
            db.extract('year', Expense.date) == int(selected_year)
        )

    if selected_category and selected_category != "All":
        query = query.filter(Expense.category == selected_category)

    expenses = query.order_by(Expense.date.desc()).all()
    total_amount = sum(e.amount for e in expenses)

    return render_template(
        "expenses.html",
        expenses=expenses,
        request=request,
        total_amount=total_amount,
        selected_month=selected_month,
        selected_year=selected_year,
        selected_category=selected_category,
        username=user.username,
        bg_color=user.bg_color
)

@app.route("/modify")
def modify_expenses():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session.get("user_id")) 
    expenses = Expense.query.filter_by(user_id=user.id).all()
    return render_template("modify.html", expenses=expenses, username=user.username, bg_color=user.bg_color)
    
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    expenses = Expense.query.get_or_404(id)
    user = User.query.get(session.get("user_id")) 
   
    if request.method == "POST":
        expenses.title = request.form["title"]
        expenses.amount = float(request.form["amount"])
        flash("Expenses modified successfully")
        db.session.commit()
        return redirect(url_for("modify_expenses"))
    return render_template("edit.html", expenses=expenses, username=user.username, bg_color=user.bg_color)
@app.route("/delete/<int:id>")
def delete_expenses(id):
     if "user_id" not in session:
        return redirect(url_for("login"))
     
     expenses = Expense.query.get_or_404(id)
     db.session.delete(expenses)
     db.session.commit()
     flash("Expenses deleted successfully")

     return redirect(url_for("modify_expenses"))
   
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        user.bg_color = request.form["bg_color"]
        db.session.commit()
        flash("background chaNGED")
        return redirect("/home")
    
    return render_template("settings.html", username=user.username, bg_color=user.bg_color)

@app.route("/graph")
def graph():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session.get("user_id")) 
   
    expenses = Expense.query.all()
    return render_template("graph.html", expenses=expenses, username=user.username, bg_color=user.bg_color)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect (url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
