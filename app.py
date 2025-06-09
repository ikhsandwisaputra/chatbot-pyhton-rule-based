# app.py
from dotenv import load_dotenv
load_dotenv()
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, flash, session)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from flask_bcrypt import Bcrypt
import datetime # Untuk tanggal lahir dan timestamp riwayat
import json
from serpapi import GoogleSearch
import os # Seharusnya sudah ada
import requests # <-- TAMBAHKAN INI


app = Flask(__name__)

# KONEKSI KE DATABASE
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kunci_rahasia_yang_sangat_aman_bro_default') # Ganti dengan kunci rahasia yang kuat
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SUPABASE_DB_URL')
# --- AKHIR PERUBAHAN UTAMA ---

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# === MODEL DATABASE ===
# Model database (User, DiagnosaHistory) tetap sama, tidak perlu diubah
# kecuali ada tipe data spesifik SQLite yang tidak kompatibel langsung dengan PostgreSQL,
# tapi untuk modelmu saat ini (Integer, String, Text, Date, DateTime, ForeignKey) seharusnya aman.
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(150), nullable=False)
    nim = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # Bcrypt hash biasanya cukup panjang, String(128) masih ok
    diagnosa_history = db.relationship('DiagnosaHistory', backref='pasien', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class DiagnosaHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nama_lengkap_pasien = db.Column(db.String(150), nullable=False)
    tanggal_lahir_pasien = db.Column(db.Date, nullable=False)
    jenis_kelamin_pasien = db.Column(db.String(20), nullable=False)
    gejala_dialami_json = db.Column(db.Text, nullable=False) # Menyimpan gejala sebagai JSON string (Text cocok untuk PostgreSQL)
    hasil_diagnosa_text = db.Column(db.Text, nullable=False)
    tanggal_diagnosa = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow) # default timezone-aware bisa dipertimbangkan jika perlu

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === DATA FORWARD CHAINING (Sama seperti sebelumnya) ===
gejala_list_fc = [
    {"kode": "SP01", "nama": "Mual dan Muntah"}, {"kode": "SP02", "nama": "Nafsu Makan Berkurang"},
    {"kode": "SP03", "nama": "Perut Sakit"}, {"kode": "SP04", "nama": "Perut kembung"},
    {"kode": "SP05", "nama": "Nyeri Ulu Hati"}, {"kode": "SP06", "nama": "Panas di Dada"},
    {"kode": "SP07", "nama": "Muntah Darah"}, {"kode": "SP08", "nama": "Sendawa"},
    {"kode": "SP09", "nama": "Berat Badan Turun"}, {"kode": "SP10", "nama": "Lemah Letih Lesu"},
    {"kode": "SP11", "nama": "Sakit pada Tukak Lambung"}, {"kode": "SP12", "nama": "Sesak Napas"},
    {"kode": "SP13", "nama": "Kejang Perut"}, {"kode": "SP14", "nama": "Sembelit"},
    {"kode": "SP15", "nama": "Perubahan Suhu Tubuh dan Keringat Dingin"}, {"kode": "SP16", "nama": "Perasaan Kenyang Berlebih"},
    {"kode": "SP17", "nama": "BAB Hitam"}, {"kode": "SP18", "nama": "Sering Cegukan"},
    {"kode": "SP19", "nama": "BAB Berdarah"}, {"kode": "SP20", "nama": "Anemia"},
    {"kode": "SP21", "nama": "Sulit Tidur"}, {"kode": "SP22", "nama": "Sakit Tenggorokan"},
    {"kode": "SP23", "nama": "Kadar Gula Tidak Terkontrol"}, {"kode": "SP24", "nama": "Asam dan Pahit pada Mulut"}
]
gejala_map_fc = {g['kode']: g['nama'] for g in gejala_list_fc}
penyakit_map_fc = {
    "DS01": "Maag", "DS02": "Dyspepsia", "DS03": "Kanker Lambung", "DS04": "Gastroparesis",
    "DS05": "Tukak Lambung", "DS06": "Gastroenteritis", "DS07": "GERD"
}
rules_fc = [
    {"rule_id": "RL1", "if_gejala": ["SP01", "SP02", "SP03", "SP05", "SP08", "SP24"], "then_penyakit": "DS01"},
    {"rule_id": "RL2", "if_gejala": ["SP03", "SP05", "SP14", "SP15", "SP16", "SP17", "SP21"], "then_penyakit": "DS02"},
    {"rule_id": "RL3", "if_gejala": ["SP01", "SP02", "SP04", "SP05", "SP06", "SP07", "SP09", "SP10", "SP13", "SP16", "SP17", "SP19", "SP20"], "then_penyakit": "DS03"},
    {"rule_id": "RL4", "if_gejala": ["SP05", "SP06", "SP07", "SP08", "SP09", "SP23"], "then_penyakit": "DS04"},
    {"rule_id": "RL5", "if_gejala": ["SP02", "SP04", "SP05", "SP08", "SP09", "SP10", "SP11", "SP12", "SP14", "SP16", "SP19", "SP20"], "then_penyakit": "DS05"},
    {"rule_id": "RL6", "if_gejala": ["SP01", "SP02", "SP03", "SP04", "SP05", "SP12", "SP19"], "then_penyakit": "DS06"},
    {"rule_id": "RL7", "if_gejala": ["SP01", "SP02", "SP03", "SP04", "SP05", "SP08", "SP22", "SP24", "SP18"], "then_penyakit": "DS07"}
]

# === ROUTES AUTENTIKASI (Tidak ada perubahan, tetap sama) ===
@app.route('/')
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('landing.html', title="Selamat Datang")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        nama = request.form.get('nama')
        nim = request.form.get('nim')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([nama, nim, email, password]):
            flash('Semua field registrasi wajib diisi!', 'danger')
            return redirect(url_for('register'))

        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Email sudah terdaftar. Silakan gunakan email lain atau login.', 'warning')
            return redirect(url_for('register'))

        user_by_nim = User.query.filter_by(nim=nim).first()
        if user_by_nim:
            flash('NIM sudah terdaftar. Silakan gunakan NIM lain atau login.', 'warning')
            return redirect(url_for('register'))

        try:
            new_user = User(nama=nama, nim=nim, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback() 
            flash(f'Terjadi kesalahan saat membuat akun: {str(e)}', 'danger')
            print(f"Error during registration: {e}") 
            return render_template('register.html', title="Daftar Akun") 
    return render_template('register.html', title="Daftar Akun")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        identifier = request.form.get('identifier') 
        password = request.form.get('password')
        
        user = User.query.filter((User.nama == identifier) | (User.email == identifier) | (User.nim == identifier)).first()
        
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            flash('Login berhasil!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login gagal. Periksa kembali username/email/NIM dan password Anda.', 'danger')
    return render_template('login.html', title="Login")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('landing_page'))

# === ROUTES UTAMA SETELAH LOGIN (Tidak ada perubahan, tetap sama) ===
@app.route('/home')
@login_required
def home():
    return render_template('home.html', title="Beranda VCare")

@app.route('/mulai_diagnosa', methods=['GET', 'POST'])
@login_required
def mulai_diagnosa():
    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap')
        tanggal_lahir_str = request.form.get('tanggal_lahir')
        jenis_kelamin = request.form.get('jenis_kelamin')

        if not all([nama_lengkap, tanggal_lahir_str, jenis_kelamin]):
            flash('Semua data diri wajib diisi!', 'danger')
            return redirect(url_for('mulai_diagnosa'))
        
        try:
            # Validasi format tanggal tetap penting
            datetime.datetime.strptime(tanggal_lahir_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Format tanggal lahir tidak valid. Gunakan YYYY-MM-DD.', 'danger')
            return redirect(url_for('mulai_diagnosa'))

        session['data_pasien_diagnosa'] = {
            'nama_lengkap': nama_lengkap,
            'tanggal_lahir': tanggal_lahir_str, 
            'jenis_kelamin': jenis_kelamin
        }
        return redirect(url_for('chat_diagnosa_fc'))

    return render_template('form_data_diri.html', title="Data Diri Pasien")


@app.route('/chat_diagnosa_fc')
@login_required
def chat_diagnosa_fc():
    if 'data_pasien_diagnosa' not in session:
        flash('Silakan isi data diri pasien terlebih dahulu.', 'warning')
        return redirect(url_for('mulai_diagnosa'))

    mode = 'diagnosa_maag_fc'
    title = "Diagnosa Penyakit Lambung (Forward Chaining)"
    initial_bot_message = ("Saya akan membantu Anda melakukan diagnosa awal penyakit lambung. "
                           "Jawablah pertanyaan berikut dengan 'Ya' atau 'Tidak'.")
    
    return render_template('chat_fc.html', 
                           title=title,
                           mode=mode,
                           initial_message="Memulai sesi diagnosa...",
                           initial_bot_message=initial_bot_message,
                           total_gejala=len(gejala_list_fc)
                           )

@app.route('/proses_diagnosa_fc', methods=['POST'])
@login_required
def proses_diagnosa_fc_endpoint(): 
    if 'data_pasien_diagnosa' not in session:
        return jsonify({'error': 'Data pasien tidak ditemukan di sesi. Harap isi form data diri.'}), 400

    data = request.get_json()
    index_symptom_dijawab = data.get('current_symptom_index', 0) 
    user_answers = data.get('user_answers', {})
    answered_symptom_code = data.get('answered_symptom_code')
    answer_value = data.get('answer_value')
    index_untuk_pertanyaan_selanjutnya = 0

    if answered_symptom_code and answer_value is not None:
        user_answers[answered_symptom_code] = answer_value
        index_untuk_pertanyaan_selanjutnya = index_symptom_dijawab + 1
    else:
        index_untuk_pertanyaan_selanjutnya = 0

    if index_untuk_pertanyaan_selanjutnya < len(gejala_list_fc):
        data_pertanyaan_selanjutnya = gejala_list_fc[index_untuk_pertanyaan_selanjutnya]
        return jsonify({
            'is_finished': False,
            'next_question_text': f"Apakah Anda mengalami: {data_pertanyaan_selanjutnya['nama']}?",
            'next_symptom_code': data_pertanyaan_selanjutnya['kode'],
            'current_symptom_index': index_untuk_pertanyaan_selanjutnya, 
            'user_answers': user_answers,
            'progress': f"Pertanyaan {index_untuk_pertanyaan_selanjutnya + 1} dari {len(gejala_list_fc)}"
        })
    else:
        user_confirmed_symptoms_dict = {k:v for k,v in user_answers.items() if v}
        user_confirmed_symptoms = set(user_confirmed_symptoms_dict.keys())

        diagnosed_diseases_codes = set()
        for rule in rules_fc:
            conditions_met = True
            for gejala_in_rule in rule['if_gejala']:
                if gejala_in_rule not in user_confirmed_symptoms:
                    conditions_met = False
                    break
            if conditions_met:
                diagnosed_diseases_codes.add(rule['then_penyakit'])
        
        hasil_diagnosa_text = "--- Hasil Diagnosa (Forward Chaining) ---\n\n"
        if diagnosed_diseases_codes:
            hasil_diagnosa_text += "Berdasarkan gejala yang Anda alami, kemungkinan penyakit yang Anda derita adalah:\n"
            for i, kode_penyakit in enumerate(diagnosed_diseases_codes):
                nama_penyakit = penyakit_map_fc.get(kode_penyakit, "Nama Penyakit Tidak Diketahui")
                hasil_diagnosa_text += f"- {nama_penyakit}\n"
            hasil_diagnosa_text += "\n"
        else:
            hasil_diagnosa_text += "Berdasarkan gejala yang Anda berikan, tidak ditemukan penyakit yang cocok dalam basis pengetahuan kami.\n\n"
            
        hasil_diagnosa_text += (
            "**Penting:** Ini adalah diagnosa awal dan bukan pengganti konsultasi medis profesional. "
            "Untuk diagnosa yang akurat dan penanganan yang tepat, silakan kunjungi dokter."
        )

        data_pasien = session['data_pasien_diagnosa']
        try:
            tgl_lahir = datetime.datetime.strptime(data_pasien['tanggal_lahir'], '%Y-%m-%d').date()
            
            gejala_dialami_untuk_db = {
                gejala_map_fc[kode]: "Ya" for kode, dialami in user_answers.items() if dialami
            }

            riwayat = DiagnosaHistory(
                user_id=current_user.id,
                nama_lengkap_pasien=data_pasien['nama_lengkap'],
                tanggal_lahir_pasien=tgl_lahir,
                jenis_kelamin_pasien=data_pasien['jenis_kelamin'],
                gejala_dialami_json=json.dumps(gejala_dialami_untuk_db), 
                hasil_diagnosa_text=hasil_diagnosa_text
            )
            db.session.add(riwayat)
            db.session.commit()
            session.pop('data_pasien_diagnosa', None) 
            flash('Diagnosa berhasil disimpan ke riwayat Anda.', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error saat menyimpan riwayat: {e}") 
            flash('Gagal menyimpan diagnosa ke riwayat. Silakan coba lagi.', 'danger')

        return jsonify({'is_finished': True, 'final_diagnosis': hasil_diagnosa_text})

@app.route('/riwayat_diagnosa')
@login_required
def riwayat_diagnosa():
    histories = DiagnosaHistory.query.filter_by(user_id=current_user.id).order_by(DiagnosaHistory.tanggal_diagnosa.desc()).all()
    
    for history in histories:
        try:
            history.gejala_parsed = json.loads(history.gejala_dialami_json)
        except json.JSONDecodeError:
            history.gejala_parsed = {} 

    return render_template('riwayat_diagnosa.html', title="Riwayat Diagnosa", histories=histories)

@app.route('/chat_vcare_umum')
@login_required
def chat_vcare_umum():
    return render_template('chat_fc.html',
                           title="Chat VCare Umum",
                           mode="chat_vcare_umum", 
                           initial_message="Hallo! Ada yang bisa saya bantu?",
                           initial_bot_message="Silakan ketik pertanyaan Anda.",
                           total_gejala=0 
                           )

@app.route('/proses_chat_umum', methods=['POST'])
@login_required
def proses_chat_umum_endpoint():
    return jsonify({
        'bot_reply': "Fitur chat umum VCare sedang dalam tahap pengembangan lebih lanjut. Terima kasih atas pesan Anda!",
    })


# app.py

@app.route('/cari-faskes')
@login_required
def cari_faskes():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        flash('Koordinat lokasi tidak ditemukan.', 'danger')
        return redirect(url_for('dashboard')) 

    serpapi_key = os.getenv('SERPAPI_API_KEY')
    if not serpapi_key:
        flash('Kunci API SerpApi tidak dikonfigurasi.', 'danger')
        return redirect(url_for('dashboard'))

    params = {
        "engine": "google_maps",
        "q": "rumah sakit | puskesmas | klinik | apotek | dokter | praktek umum",
        # "ll": f"@{-0.1286759},{102.1567432},17z",
        "ll": f"@{lat},{lon},15z",
        "hl": "id",
        "api_key": serpapi_key
    }

    # --- MULAI BLOK DEBUGGING ---
    print("\n--- DEBUGGING PENCARIAN SERPAPI ---")
    print(f"Parameter yang dikirim: {params}")
    # --------------------------------

    places = []
    try:
        search = GoogleSearch(params)
        results_dict = search.get_dict()

        # --- BLOK DEBUGGING PALING PENTING ---
        print("\n--- HASIL MENTAH DARI SERPAPI ---")
        import json
        print(json.dumps(results_dict, indent=2)) # Mencetak JSON dengan format rapi
        print("------------------------------------")
        # --------------------------------------

        # Cek jika ada error di dalam respons SerpApi
        if 'error' in results_dict:
            print(f"Error dari SerpApi: {results_dict['error']}")
            raise Exception(results_dict['error'])

        local_results = results_dict.get('local_results', [])
        
        for result in local_results:
            place_id = result.get('place_id')
            place_name = result.get('title')
            maps_url = f"https://www.google.com/maps/search/?api=1&query={place_name}&query_place_id={place_id}"

            places.append({
                'name': place_name,
                'address': result.get('address'),
                'rating': result.get('rating'),
                'reviews': result.get('reviews'),
                'type': result.get('type'),
                'thumbnail': result.get('thumbnail'),
                'maps_url': maps_url
            })

    except Exception as e:
        print(f"ERROR: Terjadi kesalahan saat memproses permintaan SerpApi: {e}")
        # Jangan tampilkan flash message di sini agar kita bisa lihat halaman kosong
        # flash('Terjadi kesalahan saat mencoba mengambil data.', 'danger')
    
    # Render template seperti biasa
    return render_template('hasil_faskes.html', 
                           places=places, 
                           user_lat=lat, 
                           user_lon=lon)


if __name__ == '__main__':
    # with app.app_context():
        # PERHATIAN: Perintah db.create_all() akan membuat tabel berdasarkan modelmu
        # JIKA tabel tersebut belum ada di database Supabase.
        # Jika kamu sudah punya tabel di Supabase dengan struktur yang berbeda,
        # ini bisa error atau tidak sesuai harapan.
        # Pastikan skema di Supabase (jika sudah ada) cocok dengan model Flask-SQLAlchemy mu.
        # Jika ini adalah setup baru, db.create_all() akan membuatkan tabelnya untukmu.
        # db.create_all() 
    app.run(host='0.0.0.0', port=5000, debug=True)