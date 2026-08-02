import time
from app import answer_query

TEST_SORULARI = [
    "Berq Bank uygulamasının temel amacı nedir?",
    "Sistemde vektör tabanlı arama süreci nasıl bir akış izliyor?",
    "Berq Bank hangi programlama dilleri ile geliştirildi?",
    "SyllabusAI projesinin özellikleri nelerdir?", 
    "Türkiye'nin başkenti neresidir?" 
]

def run_tests():
    print("Test süreci başlatılıyor...\n")
    rapor_metni = "RAG Sistemi Test Raporu\n"
    rapor_metni += "="*40 + "\n\n"

    for i, soru in enumerate(TEST_SORULARI, 1):
        print(f"Test {i}/{len(TEST_SORULARI)} çalıştırılıyor: {soru}")
        rapor_metni += f"Soru {i}: {soru}\n"
        
        try:
            # app.py güncellendiği için dönen veriyi unpack (açma) yapıyoruz
            cevap, baglam = answer_query(soru)
            rapor_metni += f"Asistan Yanıtı: {cevap}\n"
            rapor_metni += "Durum: BAŞARILI\n"
        except Exception as e:
            rapor_metni += f"Asistan Yanıtı: HATA - {str(e)}\n"
            rapor_metni += "Durum: BAŞARISIZ\n"
            
        rapor_metni += "-"*40 + "\n"
        
        # Kritik Güncelleme: İşlemcinin timeout yememesi için süre 10 saniyeye çıkarıldı.
        print("İşlemci soğutuluyor ve RAM temizleniyor (10 saniye mola)...")
        time.sleep(10) 

    with open("test_raporu.txt", "w", encoding="utf-8") as f:
        f.write(rapor_metni)
        
    print("\nTest tamamlandı! Sonuçlar 'test_raporu.txt' dosyasına kaydedildi.")

if __name__ == "__main__":
    run_tests()