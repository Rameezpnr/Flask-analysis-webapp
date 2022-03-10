from market import app
from flask import render_template, redirect, url_for, flash, request
from market.models import Item, User
from market.forms import RegisterForm, LoginForm, PurchaseItemForm, SellItemForm
from market import db
from flask_login import login_user, logout_user, login_required, current_user


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/register2')
def register2_page():
    return render_template('register2.html')


@app.route('/amazon', methods=['POST', 'GET'])
def amazon_page():
    final_amount = ''
    profit = ''
    pm = ''
    tf = ''
    if request.method == 'POST' and 'az_price' in request.form:
            az_price = float(request.form.get('az_price'))
            final_amount = calc_final(az_price)
            cost = request.form['cost']
            tf = round((final_amount * 0.006) + 0.65,2)
            if cost != '':
                cost = float(request.form.get('cost'))
                profit = calc_profit(cost, final_amount)
                pm = calc_pm(profit, cost)
    return render_template("amazon.html", profit=profit, final_amount=final_amount, pm=pm, tf=tf,)

def calc_final(az_price):
    return round(((az_price * .874) - 13.65), 2)
def calc_profit(cost, final_amount):
    return round((final_amount - cost), 2)
def calc_pm(profit, cost):
    return round((profit/cost)*100, 2)


@app.route('/market', methods=['GET', 'POST'])
@login_required
def market_page():
    purchase_form = PurchaseItemForm()
    selling_form = SellItemForm()
    # if purchase_form.validate_on_submit():  # replaced with another code to avoid resubmission popup when refreshing
    #     print(request.form.get('purchased_item'))
    if request.method == "POST":
        # purchase item logic
        purchased_item = request.form.get('purchased_item')
        p_item_object = Item.query.filter_by(name=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.buy(current_user)
                flash(f"congratulations! You purchased {p_item_object.name} for {p_item_object.price}.",
                      category='success')
            else:
                flash(f"unfortunately, your budget is too low for the item", category='danger')
        # sell item logic
        sold_item = request.form.get('sold_item')  # from owned_items_models
        s_item_object = Item.query.filter_by(name=sold_item).first()
        if s_item_object:
            if current_user.can_sell(s_item_object):
                s_item_object.sell(current_user)
                flash(f"congratulations! You sold {s_item_object.name} for {s_item_object.price}.", category='success')
            else:
                flash(f"Something went wrong with selling {s_item_object.name}")

        return redirect(url_for('market_page'))

    if request.method == "GET":
        items = Item.query.filter_by(owner=None)
        owned_items = Item.query.filter_by(owner=current_user.id)
        return render_template('market.html', items=items, purchase_form=purchase_form, owned_items=owned_items,
                               selling_form=selling_form)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_create = User(username=form.username.data,
                           email=form.email.data,
                           password=form.password1.data)
        db.session.add(user_create)
        db.session.commit()

        login_user(user_create)
        flash(f'Account created successfully! Logged in as {user_create.username}', category='success')
        return redirect(url_for('market_page'))

        return redirect(url_for('market_page'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'Error: {err_msg}', category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash(f'You have been logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('market_page'))
        else:
            flash(f'Username and password are not match', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash(f'You have been logged out', category='info')
    return redirect(url_for('home_page'))
