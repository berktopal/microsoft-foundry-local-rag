# Offline RAG System with Microsoft Foundry Local

**Microsoft Foundry Local** ve **RAG (Retrieval-Augmented Generation)** mimarisiyle geliştirilmiş, tamamen yerel (çevrimdışı) ve gizlilik odaklı bir Soru-Cevap asistanı. İnternet bağlantısına veya bulut API'lerine ihtiyaç duymadan yerel dokümanları okur, indeksler ve soruları yalnızca bu dokümanlara dayanarak yanıtlar.

*Microsoft Foundry Local Yaz Okulu programı kapsamında geliştirilmiştir.*

<table border="0">
  <tr>
    <!-- ÜST SATIR -->
    <td>
      <p align="center">
        <!-- 1. Resim (Uygulama Boş Arayüz) -->
        <img src="https://github.com/user-attachments/assets/6f9bc5e9-49a4-4922-89e0-b48399eb3c16" alt="Offline RAG Arayüzü 1" width="500px">
      </p>
    </td>
    <td>
      <p align="center">
        <!-- 2. Resim (Soru-Cevap Demo) -->
        <img src="https://github.com/user-attachments/assets/8e209f45-866e-431d-bdfa-7bb185c249a2" alt="Offline RAG Arayüzü 2" width="500px">
      </p>
    </td>
  </tr>
  <tr>
    <!-- ALT SATIR -->
    <td>
      <p align="center">
        <!-- 3. Resim (RAG Bağlam Şeffaflığı) -->
        <img src="https://github.com/user-attachments/assets/69b2263e-2bbe-44df-9f7c-310e8648b7cc" alt="Offline RAG Arayüzü 3" width="500px">
      </p>
    </td>
    <td>
      <p align="center">
        <!-- 4. Resim (Veri Yükleme/İndeksleme) -->
        <img src="https://github.com/user-attachments/assets/bd5a4745-619a-44ab-b67e-df9775d50a54" alt="Offline RAG Arayüzü 4" width="500px">
      </p>
    </td>
  </tr>
</table>

## Projenin Amacı

Bulut tabanlı yapay zeka servisleri, şirket içi gizli dokümanların veya kişisel verilerin işlenmesinde veri gizliliği riski taşır. Bu proje:

* **Veri gizliliği:** Hiçbir veri cihazdan dışarı çıkmaz (on-premise).
* **Çevrimdışı çalışma:** Modeller indirildikten sonra internet bağlantısı gerekmez.
* **Bağlama sadakat:** Model yalnızca getirilen doküman parçasına dayanarak yanıt verir; bağlamda bilgi yoksa uydurmak yerine *"Bilgi bulunamadı."* yanıtı vermesi hedeflenir ve bu davranış testle kontrol edilir.

## Sistem Mimarisi

```
docs/*.txt|*.pdf ──► ingest.py ──► parçalama ──► qwen3-embedding-0.6b ──► SQLite (local_rag_knowledge.db)
                                                                                              │
Soru ──► embedding ──► kosinüs benzerliği (top_k=1) ◄─────────────────────────────────────────┘
                              │
                              ▼
               Phi-3.5-mini (Foundry Local) ──► Yanıt + kullanılan bağlam
```

1. **Veri alma ve parçalama (hibrit chunking)** — `ingest.py`: Dokümanlar (`.txt` / `.pdf`) önce paragraflara (çift satır sonu) bölünür; 70 kelimeyi aşan paragraflar ayrıca parçalanır (`max_words=70`).
2. **Embedding:** Parçalar `qwen3-embedding-0.6b` modeliyle vektöre dönüştürülür.
3. **Vektör deposu** — `database.py`: Vektörler sunucusuz **SQLite** veritabanında tutulur.
4. **Retrieval ve generation** — `app.py`: Soru vektörize edilir, **kosinüs benzerliği** ile en yakın parça (`top_k=1`) bulunur ve sıkı bir sistem komutuyla birlikte Foundry Local üzerinde çalışan `Phi-3.5-mini` modeline verilir.
5. **Arayüz** — `app_ui.py`: Streamlit sohbet arayüzü; her yanıtın altında modelin kullandığı bağlam şeffaf biçimde gösterilir.

## Kurulum ve Çalıştırma

### Ön koşullar
* Python 3.9+
* [Microsoft Foundry Local](https://github.com/microsoft/Foundry-Local) kurulu olmalı (modeller ilk çalıştırmada indirilir)

```bash
pip install -r requirements.txt
```

### Adımlar
1. **Belgeleri ekleyin:** Sorgulanacak `.txt` / `.pdf` dosyalarını `docs/` klasörüne koyun (örnek: `docs/ornek_bilgi.txt`).
2. **İndeksleyin:**
   ```bash
   python ingest.py
   ```
3. **Arayüzü başlatın:**
   ```bash
   streamlit run app_ui.py
   ```

## Testler

`test_runner.py`, sistemi uçtan uca çalıştırır ve her yanıtı **beklenen anahtar ifadelerle** karşılaştırır. Bir test ancak gerekli ifadelerin tamamı yanıtta geçiyorsa başarılı sayılır; model hatası da başarısızlık sayılır ve betik bu durumda sıfırdan farklı bir çıkış koduyla biter.

```bash
python test_runner.py      # sonuçlar test_raporu.txt dosyasına yazılır
```

| Soru | Beklenen ifade | Kaydedilen yanıt | Durum |
| :--- | :--- | :--- | :--- |
| Berq Bank'ın amacı nedir? | `P2P` | Kullanıcılar arasında hızlı, güvenli ve doğrudan (P2P) para transferi | ✅ |
| Vektör arama akışı nasıldır? | `Embedding`, `Similarity` | Embedding → Similarity Search → Context Retrieval → Generation | ✅ |
| Berq Bank hangi dillerle geliştirildi? | `Java` | Java ve Spring Boot | ✅ |
| SyllabusAI'ın özellikleri nelerdir? | `müfredat` | Ders müfredatlarını dinamik hale getirir… | ✅ |
| Türkiye'nin başkenti neresidir? *(bağlam dışı)* | `Bilgi bulunamadı` | Bilgi bulunamadı | ✅ |

Son soru, sistemin doküman dışı bir bilgiyi kendi genel bilgisinden üretmediğini kontrol etmek için bilerek eklenmiştir. Test seti küçüktür (5 soru); genel bir doğruluk ölçümü değil, temel davranışların regresyon kontrolüdür.

## Mühendislik Kararları (yalnızca CPU ortamı için)

* **Hibrit parçalama:** Sabit kelime sayısıyla kesmek anlamsal bütünlüğü bozduğu için önce paragraf bazlı bölme yapıldı; çok uzun PDF bloklarında işlemciyi kilitlememek için `max_words=70` üst sınırı eklendi.
* **`top_k=1`:** Küçük bir modelin okuması gereken bağlamı en aza indirerek CPU'da yanıt süresini kısaltır. Karşılığında, cevabı birden fazla parçaya dağılmış sorularda isabet düşebilir.
* **Sade ve kesin sistem komutu:** Küçük dil modelleri uzun ve şartlı talimatlarda kararsızlaşabildiği için komut üç kurala indirildi: yalnızca bağlamı kullan, bağlamdaki ifadeleri aktar, bağlamda ipucu yoksa *"Bilgi bulunamadı."* yaz. Önceki sürümdeki kafa karıştırıcı ek şart kaldırıldı.
* **Deterministik ve hızlı üretim:** `temperature=0.0` ile tekrarlanabilir yanıtlar; CPU'da gecikmeyi azaltmak için `max_tokens=80`.
* **Dayanıklılık:** CPU'da uzun süren çağrılar için 120 sn zaman aşımı ve 2 denemeli yeniden deneme (retry) mekanizması.

## Proje Yapısı

```
├── ingest.py        # dokümanları okur, parçalar, embedding üretir, SQLite'a yazar
├── database.py      # SQLite şeması, kosinüs benzerliği, en yakın parçaları getirme
├── app.py           # retrieval + Phi-3.5-mini ile yanıt üretimi
├── app_ui.py        # Streamlit arayüzü
├── test_runner.py   # anahtar ifade tabanlı uçtan uca testler
└── docs/            # indekslenecek dokümanlar
```
