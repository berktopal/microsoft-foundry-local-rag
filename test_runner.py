"""
RAG sistemi için uçtan uca değerlendirme.

Her soru için yanıtta bulunması GEREKEN anahtar ifadeler tanımlıdır; bir test
ancak bu ifadelerin tamamı yanıtta geçiyorsa BAŞARILI sayılır. Son soru
bilerek dokümanlarda olmayan bir bilgiyi sorar ve sistemin bilgi uydurmak
yerine "Bilgi bulunamadı" demesini doğrular.

Çalıştırma:  python test_runner.py   (önce: python ingest.py)
"""
import sys
import time

COOLDOWN_SECONDS = 10  # CPU'da ardışık çağrılarda zaman aşımını önlemek için

# (soru, yanıtta geçmesi gereken ifadeler)
TEST_CASES = [
    ("Berq Bank uygulamasının temel amacı nedir?", ["P2P"]),
    ("Sistemde vektör tabanlı arama süreci nasıl bir akış izliyor?", ["Embedding", "Similarity"]),
    ("Berq Bank hangi programlama dilleri ile geliştirildi?", ["Java"]),
    ("SyllabusAI projesinin özellikleri nelerdir?", ["müfredat"]),
    # Bağlam dışı soru: halüsinasyon kontrolü
    ("Türkiye'nin başkenti neresidir?", ["Bilgi bulunamadı"]),
]


def evaluate(answer, expected_phrases):
    """Yanıtta beklenen tüm ifadeler geçiyorsa (büyük/küçük harf duyarsız) True döner."""
    normalized = (answer or "").casefold()
    missing = [p for p in expected_phrases if p.casefold() not in normalized]
    return not missing, missing


def run_tests(answer_fn=None, cooldown=COOLDOWN_SECONDS, report_path="test_raporu.txt"):
    if answer_fn is None:
        from app import answer_query  # Foundry Local yalnızca gerçek çalıştırmada gerekir
        answer_fn = answer_query

    print("Test süreci başlatılıyor...\n")
    report = ["RAG Sistemi Test Raporu", "=" * 40, ""]
    passed = 0

    for i, (question, expected) in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: {question}")
        try:
            answer, _context = answer_fn(question)
            ok, missing = evaluate(answer, expected)
        except Exception as e:  # model/çalışma zamanı hatası testi başarısız sayar
            answer, ok, missing = f"HATA - {e}", False, expected

        passed += ok
        report += [
            f"Soru {i}: {question}",
            f"Beklenen ifadeler: {', '.join(expected)}",
            f"Asistan Yanıtı: {answer}",
            "Durum: BAŞARILI" if ok else f"Durum: BAŞARISIZ (eksik: {', '.join(missing)})",
            "-" * 40,
        ]

        if cooldown and i < len(TEST_CASES):
            time.sleep(cooldown)

    summary = f"Sonuç: {passed}/{len(TEST_CASES)} test başarılı"
    report.append(summary)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")

    print(f"\n{summary}. Ayrıntılar '{report_path}' dosyasında.")
    return passed == len(TEST_CASES)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
