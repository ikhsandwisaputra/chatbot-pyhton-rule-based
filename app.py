# app.py
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==============================================================================
# DATA BERDASARKAN DOKUMEN PDF (Forward Chaining)
# ==============================================================================

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

@app.route('/')
def index():
    return render_template('index.html', title="Selamat Datang di VCare")

@app.route('/chat')
def chat_page():
    mode = request.args.get('mode', 'diagnosa_maag_fc')
    initial_message = "Hallo! Selamat datang di Chatbot VCare."
    if mode == 'diagnosa_maag_fc':
        title = "Diagnosa Penyakit Lambung (Forward Chaining)"
        initial_bot_message = ("Saya akan membantu Anda melakukan diagnosa awal penyakit lambung "
                               "berdasarkan metode Forward Chaining. Saya akan menanyakan beberapa gejala. "
                               "Silakan jawab 'Ya' atau 'Tidak'.")
    elif mode == 'chat_vcare':
        title = "Chat VCare"
        initial_bot_message = "Ada yang bisa saya bantu hari ini? (Fitur chat umum sedang dalam pengembangan)"
    else:
        return "Mode tidak valid", 400
    return render_template('chat_fc.html',
                           title=title, mode=mode, initial_message=initial_message,
                           initial_bot_message=initial_bot_message,
                           total_gejala=len(gejala_list_fc) if mode == 'diagnosa_maag_fc' else 0)

@app.route('/proses_diagnosa_fc', methods=['POST'])
def proses_diagnosa_fc():
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
        user_confirmed_symptoms = set()
        for kode_gejala, dialami in user_answers.items():
            if dialami:
                user_confirmed_symptoms.add(kode_gejala)
        
        # --- DEBUGGING START ---
        print("=======================================")
        print(f"DEBUG: Jawaban lengkap pengguna (user_answers): {user_answers}")
        print(f"DEBUG: Gejala yang dikonfirmasi 'Ya' (user_confirmed_symptoms): {user_confirmed_symptoms}")
        print("---------------------------------------")
        # --- DEBUGGING END ---
        
        diagnosed_diseases_codes = set()
        for rule in rules_fc:
            # --- DEBUGGING START ---
            print(f"DEBUG: Mengecek Aturan: {rule['rule_id']} untuk penyakit {rule['then_penyakit']}")
            print(f"DEBUG:   Membutuhkan gejala: {rule['if_gejala']}")
            # --- DEBUGGING END ---
            conditions_met = True
            for gejala_in_rule in rule['if_gejala']:
                if gejala_in_rule not in user_confirmed_symptoms:
                    # --- DEBUGGING START ---
                    print(f"DEBUG:   Gejala WAJIB {gejala_in_rule} TIDAK DITEMUKAN di gejala pengguna. Aturan {rule['rule_id']} GAGAL.")
                    # --- DEBUGGING END ---
                    conditions_met = False
                    break 
            
            if conditions_met:
                # --- DEBUGGING START ---
                print(f"DEBUG:   SEMUA gejala untuk aturan {rule['rule_id']} TERPENUHI. Menambahkan penyakit {rule['then_penyakit']}.")
                # --- DEBUGGING END ---
                diagnosed_diseases_codes.add(rule['then_penyakit'])
            # --- DEBUGGING START ---
            # else:
            #     print(f"DEBUG:   Kondisi untuk aturan {rule['rule_id']} TIDAK TERPENUHI.")
            print("---------------------------------------")
            # --- DEBUGGING END ---

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
        return jsonify({'is_finished': True, 'final_diagnosis': hasil_diagnosa_text})

@app.route('/proses_chat_umum', methods=['POST'])
def proses_chat_umum():
    return jsonify({
        'bot_reply': "Terima kasih atas pesan Anda. Fitur chat umum VCare saat ini sedang dalam tahap pengembangan.",
        'is_finished': True 
    })

if __name__ == '__main__':
    app.run(debug=True)