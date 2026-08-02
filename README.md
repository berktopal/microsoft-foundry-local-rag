#  Offline RAG System with Microsoft Foundry Local

Bu proje, **Microsoft Foundry Local** ve **RAG (Retrieval-Augmented Generation)** mimarisi kullanılarak geliştirilmiş, tamamen yerel (çevrimdışı) ve gizlilik odaklı bir Soru-Cevap (Q&A) asistanıdır.

İnternet bağlantısına veya bulut API'lerine ihtiyaç duymadan, sağlanan yerel dokümanları okur, indeksler ve kullanıcının sorularına %100 yerel kaynaklara dayalı yanıtlar üretir.

##  Projenin Amacı ve Çözdüğü Problem
Günümüzdeki bulut tabanlı yapay zeka çözümleri (ChatGPT, Claude vb.) şirket içi gizli dokümanların veya kişisel verilerin işlenmesi için güvenlik riskleri taşır. Bu proje;
* **Veri Gizliliği:** Hiçbir verinin dışarı çıkmadığı (On-Premise),
* **Çevrimdışı Çalışma:** İnternet bağımlılığının olmadığı,
* **Halüsinasyon Direnci (Zero-Hallucination):** LLM'in sadece ve sadece okuduğu yerel belgelere (bağlama) sadık kaldığı, bilgi yoksa uydurmak yerine "Bilgi bulunamadı." diyebilen bir çözüm sunar.

##  Sistem Mimarisi ve Kullanılan Teknolojiler
Proje, 4 temel RAG adımını yerel olarak simüle eder:

1. **Veri Alma & Parçalama (Hybrid Semantic Chunking):** Dokümanlar (`.txt` veya `.pdf`), anlam bütünlüğü korunarak paragraf bazlı (çift satır atlama) yöntemle ayrılırken, CPU şişmelerini önlemek için `max_words=70` güvenlik sübabıyla hibrit olarak parçalanır (`ingest.py`).
2. **Embedding (Gömme):** Parçalar, `qwen3-embedding-0.6b` modeli ile sayısal vektörlere dönüştürülür.
3. **Vektör Veritabanı:** Vektörler, hafif ve sunucusuz bir çözüm olan **SQLite** üzerinde depolanır (`database.py`).
4. **Retrieval & Generation (Sentezleme):** Kullanıcı sorusu vektörize edilir, **Kosinüs Benzerliği (Cosine Similarity)** ile en yakın bağlam çekilir (`top_k=1`). Çekilen bağlam, **Microsoft Foundry Local** üzerinde çalışan `Phi-3.5-mini` modeline sıkı bir "Sistem Komutu (System Prompt)" ile verilerek cevap üretilir (`app.py`).

##  Kurulum ve Çalıştırma

### Ön Koşullar
* Python 3.9 veya üzeri
* Microsoft Foundry Local SDK (`pip install foundry-local-sdk`)
* Streamlit (`pip install streamlit`)
* Numpy & PyPDF2

### Adım Adım Çalıştırma
1. **Belgeleri Yükleme:** Sorgulanmasını istediğiniz dokümanları (`.txt` veya `.pdf`) projedeki `docs/` klasörünün içine atın.
2. **Veritabanını Oluşturma (İndeksleme):**
   Terminalde şu komutu çalıştırarak belgelerin hibrit yöntemle parçalanıp vektör veritabanına (SQLite) kaydedilmesini sağlayın:
   ```bash
   python ingest.py
   ```
3. **Kullanıcı Arayüzünü Başlatma:**
   Streamlit arayüzünü ayağa kaldırmak için şu komutu çalıştırın:
   ```bash
   streamlit run app_ui.py
   ```
   *Tarayıcınızda açılan ekranda asistana belgelerle ilgili sorular sorabilirsiniz.*

##  Hata Ayıklama
Streamlit arayüzünde, asistanın verdiği her yanıtın altında **" Okunan Kaynak Bağlamı (RAG)"** adında bir açılır menü bulunur. Bu menüye tıklayarak asistanın o cevabı üretmek için veritabanından hangi metin bloklarını çektiğini (Kosinüs Benzerliği sonuçlarını) şeffaf bir şekilde görebilirsiniz.

##  Öğrenilen Dersler ve Optimizasyonlar

Bu projeyi geliştirirken kısıtlı donanımlarda (yalnızca CPU) RAG sistemlerini optimize etmek için kritik ve yenilikçi mühendislik kararları alınmıştır:

* **Hibrit Parçalama (Hybrid Chunking):** Sadece sabit kelime limitine göre (Fixed-Size) kesmek bağlam kanamasına yol açtığı için önce çift satır atlamaya (paragrafa) göre anlamsal bir bölme yapıldı. Büyük PDF bloklarında işlemcinin kilitlenmesini önlemek için ise `max_words=70` limitiyle çalışan bir güvenlik mekanizması entegre edildi.
* **Ekstrem Hız Modu (CPU Optimizasyonu):** Veritabanı izolasyonu kusursuz hale getirildiği için, modelin okuması gereken parça sayısı `top_k=1` seviyesine düşürüldü. Bu sayede işlemci yükü hafifletilerek yanıt süresi donanımın elverdiği minimum fiziksel sınırlara çekildi.
* **Recency Bias (Son Saniye Eğilimi) Kalkanı:** Küçük dil modellerinin sistem komutlarını unutma eğilimine karşı, "Bilgi uydurma" yasağı `system_prompt` yerine, doğrudan kullanıcı sorusunun bir milisaniye öncesine enjekte edilerek %100 halüsinasyon direnci sağlandı.
* **Truncation (Kesinti) Koruması:** Küçük modellerin iki nokta (`:`) işaretini durma komutu olarak algılaması ve listeleri yarıda kesmesi engellendi. `max_tokens` genişletilerek ve modele "eksiksiz okuma" talimatı verilerek veri kaybının önüne geçildi.

##  Test Raporu
Sistemin verimliliğini ve halüsinasyon direncini ölçmek için hazırlanan otomatik test süreci 5/5 başarı oranıyla tamamlanmıştır.

| Soru | Asistan Yanıtı | Durum |
| :--- | :--- | :--- |
| Berq Bank amacı nedir? | P2P para transferi sağlamaktır. | Başarılı |
| RAG akışı nasıldır? | Embedding -> Similarity -> Retrieval -> Generation | Başarılı |
| Berq Bank dilleri? | Java ve Spring Boot | Başarılı |
| SyllabusAI özellikleri? | Müfredat dinamiği, etkileşimli asistan, optimizasyon | Başarılı |
| Türkiye'nin başkenti? | Bilgi bulunamadı. | Başarılı |

*Not: 5. soru, sistemin dış bilgiye kapalı olduğunu ve bağlam dışı konularda halüsinasyon üretmediğini kanıtlamak için özel olarak eklenmiştir.*

---
*Bu proje, Microsoft Foundry Local Yaz Okulu programı kapsamında geliştirilmiştir.*

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
