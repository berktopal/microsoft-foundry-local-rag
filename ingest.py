import os
import re
import PyPDF2
from database import init_db, insert_chunk, DB_NAME
from foundry_local_sdk import Configuration, FoundryLocalManager

EMBEDDING_MODEL_NAME = "qwen3-embedding-0.6b"

def clean_text(text):
    # KRİTİK DÜZELTME: Sadece yan yana boşlukları sil, satır atlamalarını (\n) KORU!
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def chunk_text(text, max_words=70):
    # 1. Önce senin istediğin gibi paragraflara böl (İzolasyon korundu)
    raw_chunks = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
    final_chunks = []
    for chunk in raw_chunks:
        words = chunk.split()
        
        # 2. GÜVENLİK SÜBABI: Eğer paragraf çok uzunsa (PDF'den gelen dev metinler)
        # Onu CPU'nun rahat okuyabileceği maksimum kelime sınırlarına böl.
        if len(words) > max_words:
            for i in range(0, len(words), max_words):
                safe_chunk = " ".join(words[i:i + max_words])
                if len(safe_chunk.split()) > 3: # 3 kelimeden kısa çöpleri alma
                    final_chunks.append(safe_chunk)
        else:
            if len(words) > 3:
                final_chunks.append(chunk)
                
    return final_chunks

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n\n"
    except Exception as e:
        print(f"[Hata] {pdf_path} okunamadı: {e}")
    return text

def ingest_documents(directory_path="docs/"):
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"\n[Sistem] Eski veritabanı silindi, yenileniyor...")

    init_db()
    
    config = Configuration(app_name="local_rag_assistant")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance
    
    embedding_model = manager.catalog.get_model(EMBEDDING_MODEL_NAME)
    embedding_model.load()
    embedding_client = embedding_model.get_embedding_client()

    print(f"\n[Sistem] Belgeler taranıyor (Hibrit Parçalama aktif)...")
    
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        content = ""
        
        if filename.lower().endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif filename.lower().endswith(".pdf"):
            content = extract_text_from_pdf(file_path)
        else:
            continue

        if not content.strip(): continue

        content = clean_text(content)
        chunks = chunk_text(content)
        
        for chunk in chunks:
            response = embedding_client.generate_embeddings([chunk])
            vector = response.data[0].embedding
            insert_chunk(chunk, vector)
            
    print(f"\n✅ Tüm belgeler izolasyon ve hız kurallarına göre işlendi.")

if __name__ == "__main__":
    ingest_documents()