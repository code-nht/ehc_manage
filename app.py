from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from flask import send_from_directory
import os

app = Flask(__name__)

# --- CẤU HÌNH ỨNG DỤNG ---
app.config['SECRET_KEY'] = 'nguyen_huu_thien'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ehc_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Khởi tạo các công cụ
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Nếu chưa đăng nhập mà vào trang cấm, sẽ bị đẩy về trang 'login'
login_manager.login_message = "Vui lòng đăng nhập để truy cập trang này."

# --- ĐỊNH NGHĨA DATABASE ---


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), default='student')

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    file_path = db.Column(db.String(200), nullable=False)

# Hàm tải user cho Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def home():
    return render_template('home.html')
# 1. Chức năng Đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        role = request.form.get('role')
        email = request.form.get('email')
        phone = request.form.get('phone')
        # Kiểm tra xem tài khoản đã tồn tại chưa
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Tên đăng nhập đã tồn tại!")
            return redirect(url_for('register'))

        # Mã hóa mật khẩu trước khi lưu
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(username=username, password=hashed_password, full_name=full_name, role=role, email=email,phone=phone)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Đăng ký thành công! Vui lòng đăng nhập.")
        return redirect(url_for('login'))
        
    return render_template('register.html')

# 2. Chức năng Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Kiểm tra user có tồn tại và mật khẩu có khớp với mã băm không
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f"Chào mừng {user.full_name}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")
            return render_template('login.html')

# 3. Chức năng Đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 4. Trang Dashboard (Chỉ ai đăng nhập mới vào được)
@app.route('/dashboard')
@login_required
def dashboard():
    return f"""
    <h1>Trang quản lý EHC</h1>
    <p>Xin chào {current_user.full_name} - Vai trò: {current_user.role}</p>
    <a href='/users'><b>-> Xem danh sách lớp</b></a> <br><br>
    <a href='/assignments'><b>-> Quản lý Bài tập</b></a> <br><br>
    <a href='/challenge'><b>-> Tham gia Giải đố (Challenge)</b></a> <br><br>
    <a href='/logout'>Đăng xuất</a>
    """

# --- BƯỚC 3: QUẢN LÝ NGƯỜI DÙNG ---

# 1. Xem danh sách người dùng
@app.route('/users')
@login_required
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

# 2. Sửa thông tin
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Tìm user cần sửa trong Database
    user_to_edit = User.query.get_or_404(user_id)

    # KIỂM TRA QUYỀN (RBAC):
    # Nếu không phải giáo viên, VÀ cũng không phải đang sửa chính mình -> Cấm!
    if current_user.role != 'teacher' and current_user.id != user_to_edit.id:
        flash("Lỗi bảo mật: Bạn không có quyền sửa thông tin của người khác!")
        return redirect(url_for('list_users'))

    if request.method == 'POST':
        # Sinh viên được sửa email và sđt
        user_to_edit.email = request.form.get('email')
        user_to_edit.phone = request.form.get('phone')

        # CHỈ CÓ giáo viên mới được sửa username, họ tên và vai trò
        if current_user.role == 'teacher':
            user_to_edit.username = request.form.get('username')
            user_to_edit.full_name = request.form.get('full_name')
            user_to_edit.role = request.form.get('role')

        db.session.commit()
        flash("Cập nhật thông tin thành công!", "success")
        return redirect(url_for('list_users'))

    return render_template('edit_user.html', user=user_to_edit)

# 3. Xóa người dùng (Chỉ Giáo viên)
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'teacher':
        flash("Bạn không có quyền thực hiện hành động này!")
        return redirect(url_for('list_users'))
    
    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash("Đã xóa người dùng thành công!")
    return redirect(url_for('list_users'))

# --- BƯỚC 4: QUẢN LÝ BÀI TẬP (ASSIGNMENTS & SUBMISSIONS) ---

# 1. Trang danh sách bài tập & Giáo viên giao bài mới
@app.route('/assignments', methods=['GET', 'POST'])
@login_required
def manage_assignments():
    if request.method == 'POST':
        if current_user.role != 'teacher':
            flash("Chỉ giáo viên mới được giao bài!", "danger")
            return redirect(url_for('manage_assignments'))
            
        title = request.form.get('title')
        file = request.files.get('file')
        
        if file and file.filename != '':
            # Làm sạch tên file và lưu vào thư mục
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'assignments', filename)
            file.save(save_path)
            
            # Lưu thông tin vào Database
            new_assignment = Assignment(title=title, file_path=filename, teacher_id=current_user.id)
            db.session.add(new_assignment)
            db.session.commit()
            flash("Giao bài tập thành công!", "success")
            
    assignments = Assignment.query.all()
    return render_template('assignments.html', assignments=assignments)

# 2. Sinh viên nộp bài
@app.route('/submit/<int:assignment_id>', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role != 'student':
        flash("Chỉ sinh viên mới có tính năng nộp bài!", "danger")
        return redirect(url_for('manage_assignments'))

    file = request.files.get('file')
    if file and file.filename != '':
        # Tạo tên file có kèm username để giáo viên dễ phân biệt (VD: tri_bai1.docx)
        filename = secure_filename(f"{current_user.username}_{file.filename}")
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'submissions', filename)
        file.save(save_path)
        
        # Lưu vào Database
        new_submission = Submission(assignment_id=assignment_id, student_id=current_user.id, file_path=filename)
        db.session.add(new_submission)
        db.session.commit()
        flash("Nộp bài thành công!", "success")
        
    return redirect(url_for('manage_assignments'))

# 3. Giáo viên xem danh sách bài nộp của 1 đề bài
@app.route('/submissions/<int:assignment_id>')
@login_required
def view_submissions(assignment_id):
    if current_user.role != 'teacher':
        flash("Bạn không có quyền xem danh sách nộp bài!", "danger")
        return redirect(url_for('manage_assignments'))
        
    assignment = Assignment.query.get_or_404(assignment_id)
    # Lấy tất cả bài nộp của đề này
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    return render_template('submissions.html', assignment=assignment, submissions=submissions)

# 4. Route hỗ trợ Tải file về máy (Cho cả đề bài và bài nộp)
@app.route('/download/<folder>/<filename>')
@login_required
def download_file(folder, filename):
    # Chỉ cho phép tải từ 2 thư mục này để tránh Path Traversal
    if folder not in ['assignments', 'submissions']:
        return "Thư mục không hợp lệ!", 400
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], folder), filename, as_attachment=True)

# --- BƯỚC 5: TRÒ CHƠI GIẢI ĐỐ (CHALLENGE) ---

@app.route('/challenge', methods=['GET', 'POST'])
@login_required
def challenge():
    # Khai báo đường dẫn tới thư mục chứa file giải đố
    challenge_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'challenge')
    hint_file = os.path.join(challenge_folder, 'hint.txt') # File này chỉ để lưu câu gợi ý
    
    # 1. NẾU LÀ GIÁO VIÊN: Xử lý việc đăng file và gợi ý
    if current_user.role == 'teacher':
        if request.method == 'POST':
            file = request.files.get('file')
            hint = request.form.get('hint')
            
            if file and file.filename != '':
                # Lấy tên file gốc (Giữ nguyên khoảng trắng, VD: "truyen kieu.txt")
                filename = os.path.basename(file.filename) 
                file.save(os.path.join(challenge_folder, filename))
                
                # Lưu câu gợi ý vào một file tên là hint.txt
                with open(hint_file, 'w', encoding='utf-8') as f:
                    f.write(hint)
                    
                flash("Tạo thử thách thành công!", "success")
                return redirect(url_for('challenge'))
        return render_template('challenge.html')
        
    # 2. NẾU LÀ SINH VIÊN: Xử lý giải đố
    else:
        # Lấy câu gợi ý ra cho sinh viên đọc
        hint = "Giáo viên chưa tạo thử thách nào."
        if os.path.exists(hint_file):
            with open(hint_file, 'r', encoding='utf-8') as f:
                hint = f.read()
                
        content = None
        if request.method == 'POST':
            answer = request.form.get('answer').strip()
            # Lấy đáp án của sinh viên + đuôi .txt
            filename = f"{answer}.txt"
            
            # Chống hacker dùng Path Traversal (VD nhập answer = "../app")
            if '/' in filename or '\\' in filename:
                flash("Đáp án chứa ký tự lạ!", "danger")
            else:
                filepath = os.path.join(challenge_folder, filename)
                # ĐÂY CHÍNH LÀ CHÌA KHÓA: Kiểm tra xem có tồn tại cái tên file này trên ổ cứng không
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    flash("Chính xác! Dưới đây là phần thưởng của bạn.", "success")
                else:
                    flash("Sai rồi! Bạn suy nghĩ thêm nhé.", "danger")
                    
        return render_template('challenge.html', hint=hint, content=content)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            os.makedirs(os.path.join(UPLOAD_FOLDER, 'assignments'))
            os.makedirs(os.path.join(UPLOAD_FOLDER, 'submissions'))
            os.makedirs(os.path.join(UPLOAD_FOLDER, 'challenge'))
    app.run(debug=True)
