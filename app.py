from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import ImageUploadField
from werkzeug.utils import secure_filename
import os
import re
from flask_admin import AdminIndexView
from flask_admin.form import SecureForm
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '222333444'
app.config['UPLOAD_FOLDER'] = 'static/img/gal'



smtp_server = "smtp.mail.ru"
smtp_port = 587
smtp_username = "dimazzz1975@mail.ru"
smtp_password = "zGY201mmGdccqrBmAVmU"
smtp_sender_email = "dimazzz1975@mail.ru"
smtp_receiver_email = "dimazzz1975@mail.ru"

mail = Mail(app)
db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    method_1 = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    sizes = db.Column(db.String(100), nullable=False)
    in_1_m = db.Column(db.Integer, nullable=False)
    marka = db.Column(db.String(100), nullable=False)
    vlaga = db.Column(db.String(100), nullable=False)
    istiraem = db.Column(db.Integer, nullable=False)


    image = db.Column(db.String(255), nullable=False) 

    def __repr__(self):
        return self.title, self.method_1



class ProductView(ModelView):
    form_extra_fields = {
        'image': ImageUploadField('Image', base_path=app.config['UPLOAD_FOLDER'], url_relative_path='static/img/gal/', endpoint='upload')
    }



class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False) 
    alt = db.Column(db.String(100), nullable=True)



class ImageView(ModelView):
    form_extra_fields = {
        'image': ImageUploadField('Image', base_path=app.config['UPLOAD_FOLDER'], url_relative_path='static/img/gal/', endpoint='upload')
    }



class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('admin_authenticated')

    def inaccessible_callback(self, name, **kwargs):
        flash('Please log in to access the admin panel.', 'warning')
        return redirect(url_for('admin_login'))



class MyModelView(ModelView):
    form_base_class = SecureForm



admin = Admin(app, name='Admin Panel', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_view(ProductView(Product, db.session))
admin.add_view(ImageView(Image, db.session))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['admin_authenticated'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session['admin_authenticated'] = False
    flash('Logout successful.', 'info')
    return redirect(url_for('admin.index'))


with app.app_context():
    admin_user = User(username='admin')
    admin_user.set_password('admin_password')
    db.session.add(admin_user)
    try:
        db.session.commit()
    except Exception as e:
        print(f"An error occurred while committing admin user creation: {e}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}


def is_valid_phone(phone):
    pattern = re.compile(r'^\+7\d{10}$')
    return bool(re.match(pattern, phone))


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        product_title = request.form.get('productTitle')


        if not is_valid_phone(phone):
            return "Некорректный номер телефона. Пожалуйста, введите номер в правильном формате."

        
        message = MIMEMultipart()
        
        
        subject = f"Заказ товара: {product_title}"
        message["Subject"] = Header(subject, "utf-8")

        
        message_body = f"Название товара: {product_title}\nИмя:{name}\nНомер телефона: {phone}"
        message.attach(MIMEText(message_body, "plain", "utf-8"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(
                smtp_sender_email, 
                smtp_receiver_email, 
                message.as_bytes().decode('utf-8', 'ignore').encode('utf-8')
            )

        return "Данные успешно отправлены на почту!"
    else:
        return "Метод не разрешен"


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_image = Image(image=filename, alt="Картинка")
        db.session.add(new_image)
        db.session.commit()

        return "File uploaded successfully"

    return "Error uploading file"


@app.route('/send_email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        input_name = request.form['inputname']
        input_email = request.form['inputemail']
        input_phone = request.form['inputphone']
        input_message = request.form['floatingtextarea']

        
        if not (input_name and input_email and input_phone and input_message):
            return jsonify({"error": "Пожалуйста, заполните все поля формы."})

        
        if not is_valid_phone(input_phone):
            return jsonify({"error": "Пожалуйста, введите номер в правильном формате."})
        
        message_body = f"Имя: {input_name}\n Email: {input_email}\n Номер телефона: {input_phone}\n Сообщение: {input_message}"
        
        message = MIMEMultipart()
        message.attach(MIMEText(message_body, "plain", "utf-8"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(
                smtp_sender_email, 
                smtp_receiver_email, 
                message.as_bytes().decode('utf-8', 'ignore').encode('utf-8')
            )

        return jsonify({"success": "Данные успешно отправлены на почту!"})
    else:
        return jsonify({"error": "Метод не разрешен"})


@app.route('/')
def index():
    categories = db.session.query(Product.category).distinct().all()
    category_filter = request.args.get('category', None)

    if category_filter:
        items = Product.query.filter_by(category=category_filter).all()
    else:
        items = Product.query.all()

    return render_template('index.html', categories=categories, items=items, category_filter=category_filter)


@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    if request.method == 'POST':
        file = request.files.get('file')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            new_image = Image(path=filename, alt="Картинка")
            db.session.add(new_image)
            db.session.commit()

    images = Image.query.all()
    return render_template('gallery.html', images=images)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/work')
def work():
    return render_template('work.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/work-single')
def work_single():
    return render_template('work-single.html')


@app.route('/work-single-2')
def work_single_2():
    return render_template('work-single_2.html')


@app.route('/work-single-3')
def work_single_3():
    return render_template('work-single_3.html')


@app.route('/work-single-4')
def work_single_4():
    return render_template('work-single_4.html')


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"An error occurred while creating database tables: {e}")
    app.run(debug=True)