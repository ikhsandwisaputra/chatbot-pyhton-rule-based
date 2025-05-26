# app.py
from flask import Flask, render_template, request, jsonify
import json # Untuk debugging atau logging jika diperlukan

app = Flask(__name__)

# ==============================================================================
# DATA BERDASARKAN DOKUMEN PDF
# ==============================================================================

# Tabel 1: Gejala-gejala penyakit maag akut dan kronis beserta Nilai Pakar
gejala_data_list = [
    {"kode": "G01", "nama": "Pusing", "nilai_pakar": 0.2},
    {"kode": "G02", "nama": "Mual", "nilai_pakar": 0.2},
    {"kode": "G03", "nama": "Nyeri perut", "nilai_pakar": 0.4},
    {"kode": "G04", "nama": "Lemas", "nilai_pakar": 0.8},
    {"kode": "G05", "nama": "Demam", "nilai_pakar": 0.6},
    {"kode": "G06", "nama": "Berat badan menurun", "nilai_pakar": 0.8},
    {"kode": "G07", "nama": "Seperti ditusuk", "nilai_pakar": 0.8},
    {"kode": "G08", "nama": "Keluar daging kecil di anus", "nilai_pakar": 0.8},
    {"kode": "G09", "nama": "Nyeri ulu hati", "nilai_pakar": 0.6},
    {"kode": "G10", "nama": "Muntah darah", "nilai_pakar": 0.8},
    {"kode": "G11", "nama": "Batuk", "nilai_pakar": 0.4},
    {"kode": "G12", "nama": "Rasa panas di tenggorokan", "nilai_pakar": 0.6},
    {"kode": "G13", "nama": "Mual ", "nilai_pakar": 0.2},
    {"kode": "G14", "nama": "Stres", "nilai_pakar": 0.4},
    {"kode": "G15", "nama": "Ilusi", "nilai_pakar": 0.6},
    {"kode": "G16", "nama": "Pusing ", "nilai_pakar": 0.2},
    {"kode": "G17", "nama": "Berat badan menurun ", "nilai_pakar": 0.8},
    {"kode": "G18", "nama": "Sesak napas", "nilai_pakar": 0.6},
    {"kode": "G19", "nama": "Pandangan kabur", "nilai_pakar": 0.8},
    {"kode": "G20", "nama": "Batuk ", "nilai_pakar": 0.2},
    {"kode": "G21", "nama": "Perut terasa mengisap", "nilai_pakar": 0.8},
    {"kode": "G22", "nama": "Lemas ", "nilai_pakar": 0.8},
    {"kode": "G23", "nama": "Muntah", "nilai_pakar": 0.6}
]
# Membuat dictionary untuk akses cepat berdasarkan kode gejala
gejala_map = {g['kode']: g for g in gejala_data_list}

# Tabel 2: Analisis gejala pasien penyakit maag akut dan kronis (Kasus Lama)
kasus_data_list = [
    {"kode_pasien": "P001", "gejala_kode": ["G01", "G02", "G03", "G05", "G06", "G09", "G10"], "keterangan": "Maag Kronis"},
    {"kode_pasien": "P002", "gejala_kode": ["G01", "G04", "G05", "G07", "G09", "G10", "G22"], "keterangan": "Maag Kronis"},
    {"kode_pasien": "P003", "gejala_kode": ["G01", "G03", "G05", "G09", "G10", "G23"], "keterangan": "Maag Kronis"},
    {"kode_pasien": "P004", "gejala_kode": ["G01", "G02", "G03", "G09", "G10", "G23"], "keterangan": "Maag Kronis"},
    {"kode_pasien": "P005", "gejala_kode": ["G01", "G03", "G05", "G07", "G11", "G22"], "keterangan": "Maag Kronis"},
    {"kode_pasien": "P006", "gejala_kode": ["G11", "G13", "G15", "G18", "G21", "G22"], "keterangan": "Maag Akut"},
    {"kode_pasien": "P007", "gejala_kode": ["G11", "G12", "G13", "G16", "G19", "G22"], "keterangan": "Maag Akut"},
    {"kode_pasien": "P008", "gejala_kode": ["G11", "G12", "G14", "G15", "G18", "G20", "G23"], "keterangan": "Maag Akut"},
    {"kode_pasien": "P009", "gejala_kode": ["G04", "G09", "G11", "G14", "G17", "G18", "G20"], "keterangan": "Maag Akut"},
    {"kode_pasien": "P010", "gejala_kode": ["G11", "G15", "G17", "G18", "G20", "G21", "G22"], "keterangan": "Maag Akut"}
]

# Total bobot semua gejala (nilai pakar) untuk perhitungan skor keseluruhan
total_bobot_semua_gejala = sum(g['nilai_pakar'] for g in gejala_data_list)

# ==============================================================================
# ROUTES FLASK
# ==============================================================================

@app.route('/')
def index():
    """Menampilkan halaman utama."""
    return render_template('index.html', title="Selamat Datang di VCare")

@app.route('/chat')
def chat_page():
    """Menampilkan halaman chat berdasarkan mode."""
    mode = request.args.get('mode', 'diagnosa_maag_cbr')
    initial_message = "Hallo! Selamat datang di Chatbot VCare."
    
    if mode == 'diagnosa_maag_cbr':
        title = "Diagnosa Maag (Metode Jurnal)"
        initial_bot_message = ("Saya akan membantu Anda melakukan diagnosa awal penyakit maag "
                               "berdasarkan metode jurnal. Saya akan menanyakan beberapa gejala. "
                               "Silakan jawab 'Ya' atau 'Tidak'.")
    elif mode == 'chat_vcare':
        title = "Chat VCare"
        initial_bot_message = "Ada yang bisa saya bantu hari ini? (Fitur chat umum sedang dalam pengembangan)"
    else:
        return "Mode tidak valid", 400

    return render_template('chat_cbr.html',
                           title=title,
                           mode=mode,
                           initial_message=initial_message,
                           initial_bot_message=initial_bot_message,
                           total_gejala=len(gejala_data_list) if mode == 'diagnosa_maag_cbr' else 0
                           )

@app.route('/proses_diagnosa_cbr', methods=['POST'])
def proses_diagnosa_cbr():
    data = request.get_json()
    
    # 'current_symptom_index' dari frontend adalah index dari gejala YANG BARU SAJA DIJAWAB (atau 0 untuk panggilan awal).
    # Jika ini panggilan awal, answered_symptom_code akan null.
    index_symptom_dijawab = data.get('current_symptom_index', 0) 
    user_answers = data.get('user_answers', {})
    
    answered_symptom_code = data.get('answered_symptom_code')
    answer_value = data.get('answer_value')

    index_untuk_pertanyaan_selanjutnya = 0

    if answered_symptom_code and answer_value is not None:
        # Simpan jawaban untuk gejala yang baru saja dijawab
        user_answers[answered_symptom_code] = answer_value
        # Tentukan index untuk pertanyaan berikutnya
        index_untuk_pertanyaan_selanjutnya = index_symptom_dijawab + 1
    else:
        # Ini adalah panggilan awal (belum ada gejala yang dijawab), jadi kita minta pertanyaan pertama (index 0)
        index_untuk_pertanyaan_selanjutnya = 0 # atau bisa juga dari index_symptom_dijawab yang defaultnya 0

    if index_untuk_pertanyaan_selanjutnya < len(gejala_data_list):
        data_pertanyaan_selanjutnya = gejala_data_list[index_untuk_pertanyaan_selanjutnya]
        return jsonify({
            'is_finished': False,
            'next_question_text': f"Apakah Anda mengalami: {data_pertanyaan_selanjutnya['nama']}?",
            'next_symptom_code': data_pertanyaan_selanjutnya['kode'],
            # 'current_symptom_index' dalam respons adalah index dari pertanyaan yang BARU DIKIRIM SEKARANG.
            'current_symptom_index': index_untuk_pertanyaan_selanjutnya, 
            'user_answers': user_answers, # Kirim kembali koleksi jawaban yang sudah diperbarui
            'progress': f"Pertanyaan {index_untuk_pertanyaan_selanjutnya + 1} dari {len(gejala_data_list)}"
        })
    else:
        # Semua pertanyaan telah dijawab, lanjutkan ke diagnosis
        numerator_overall = 0
        for kode_gejala, dialami in user_answers.items():
            if dialami and kode_gejala in gejala_map: # Pastikan kode gejala valid
                numerator_overall += gejala_map[kode_gejala]['nilai_pakar']
        
        overall_maag_score_percentage = 0
        if total_bobot_semua_gejala > 0:
            overall_maag_score_percentage = (numerator_overall / total_bobot_semua_gejala) * 100
        
        # Interpretasi berdasarkan Tabel 4
        if overall_maag_score_percentage <= 30:
            interpretasi_overall = "Tidak mungkin menderita maag"
        elif overall_maag_score_percentage <= 70:
            interpretasi_overall = "Ada kemungkinan menderita maag"
        else:
            interpretasi_overall = "Kemungkinan besar pasti menderita maag"

        # Case-Based Reasoning (CBR)
        best_match_case_info = None
        max_similarity = -1.0

        for kasus in kasus_data_list:
            sum_bobot_gejala_cocok_cbr = 0
            sum_bobot_gejala_kasus_lama = 0
            
            for kode_gejala_kasus in kasus['gejala_kode']:
                if kode_gejala_kasus not in gejala_map: 
                    continue 
                
                bobot_gejala = gejala_map[kode_gejala_kasus]['nilai_pakar']
                sum_bobot_gejala_kasus_lama += bobot_gejala
                
                if user_answers.get(kode_gejala_kasus, False): 
                    sum_bobot_gejala_cocok_cbr += bobot_gejala
            
            current_similarity_cbr = 0
            if sum_bobot_gejala_kasus_lama > 0:
                current_similarity_cbr = sum_bobot_gejala_cocok_cbr / sum_bobot_gejala_kasus_lama
            
            if current_similarity_cbr > max_similarity:
                max_similarity = current_similarity_cbr
                best_match_case_info = {
                    "keterangan": kasus['keterangan'],
                    "kode_pasien": kasus['kode_pasien'],
                    "similarity_percentage": max_similarity * 100
                }
        
        # Susun hasil diagnosa
        hasil_diagnosa_text = (
            f"--- Hasil Diagnosa Awal (Berdasarkan Jurnal) ---\n\n"
            f"Skor Kemungkinan Maag Keseluruhan: {overall_maag_score_percentage:.2f}%\n"
            f"Interpretasi Umum: {interpretasi_overall}.\n\n"
        )

        if best_match_case_info:
            hasil_diagnosa_text += (
                f"Analisis Berbasis Kasus (CBR):\n"
                f"Kasus paling mirip: {best_match_case_info['keterangan']} "
                f"(mirip dengan kasus referensi {best_match_case_info['kode_pasien']}).\n"
                f"Tingkat Kemiripan: {best_match_case_info['similarity_percentage']:.2f}%.\n\n"
            )
        else:
            hasil_diagnosa_text += "Analisis Berbasis Kasus (CBR): Tidak ditemukan kasus yang cukup mirip.\n\n"
            
        hasil_diagnosa_text += (
            "**Penting:** Ini adalah diagnosa awal berdasarkan metode dari jurnal penelitian dan "
            "bukan pengganti konsultasi medis profesional. Untuk diagnosa yang akurat dan "
            "penanganan yang tepat, silakan kunjungi dokter."
        )

        return jsonify({
            'is_finished': True,
            'final_diagnosis': hasil_diagnosa_text
        })

@app.route('/proses_chat_umum', methods=['POST'])
def proses_chat_umum():
    """Memproses input chat umum dari pengguna."""
    return jsonify({
        'bot_reply': "Terima kasih atas pesan Anda. Fitur chat umum VCare saat ini sedang dalam tahap pengembangan.",
        'is_finished': True 
    })

if __name__ == '__main__':
    app.run(debug=True)