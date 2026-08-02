import os
import re
import time
from database import get_top_chunks
from foundry_local_sdk import Configuration, FoundryLocalManager

EMBEDDING_MODEL_NAME = "qwen3-embedding-0.6b"
CHAT_MODEL_NAME = "phi-3.5-mini"

_emb_client = None
_chat_client = None
_is_initialized = False

def initialize_models():
    global _emb_client, _chat_client, _is_initialized
    if _is_initialized: return _emb_client, _chat_client
        
    config = Configuration(app_name="local_rag_assistant")
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    emb_model = manager.catalog.get_model(EMBEDDING_MODEL_NAME)
    emb_model.load()
    _emb_client = emb_model.get_embedding_client()

    chat_model = manager.catalog.get_model(CHAT_MODEL_NAME)
    chat_model.download()
    chat_model.load()
    _chat_client = chat_model.get_chat_client() 
    
    _is_initialized = True
    return _emb_client, _chat_client

def answer_query(user_question, chat_history=None):
    emb_client, chat_client = initialize_models()
    
    # 1. Saf Sorgu
    query_response = emb_client.generate_embeddings([user_question])
    query_vector = query_response.data[0].embedding
    
    # 2. Tam Okuma
    retrieved_chunks = get_top_chunks(query_vector, top_k=1)
    context = "\n---\n".join(retrieved_chunks)
    
    # 3. Küçük Modeller (SLM) İçin En Sade ve Net Prompt
    system_prompt = (
        "Sen bir bilgi çıkarma asistanısın. SADECE sana verilen BAĞLAM metnini okuyarak SORU'yu cevapla.\n"
        "Yanıt verirken BAĞLAM'daki ifadeleri doğrudan kopyala, kendi yorumunu katma.\n"
        "Eğer BAĞLAM metninde soruyla ilgili HİÇBİR kelime veya ipucu geçmiyorsa, sadece 'Bilgi bulunamadı.' yaz."
    )
    
    # 💥 PROBLEM ÇÖZÜLDÜ: Sondaki kafa karıştırıcı "Not: tam cevap yoksa" şartı tamamen silindi. 
    # Model artık sadece ve doğrudan soruyu görüp bağlama odaklanacak.
    user_prompt_compiled = f"BAĞLAM:\n{context}\n\nSORU: {user_question}"
    
    messages_payload = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt_compiled}]
    
    # 4. Otomatik Tekrar Deneme (Retry) Mekanizması
    max_retries = 2
    raw_response = ""
    
    for attempt in range(max_retries):
        try:
            if hasattr(chat_client, 'chat') and hasattr(chat_client.chat, 'completions'):
                response = chat_client.chat.completions.create(
                    model=CHAT_MODEL_NAME, 
                    messages=messages_payload, 
                    max_tokens=80,  # İŞLEMCİ HIZI İÇİN 250'DEN 80'E DÜŞÜRÜLDÜ
                    temperature=0.0,
                    timeout=120.0   # ZAMAN AŞIMINI ÖNLEMEK İÇİN SÜRE UZATILDI
                )
                message_obj = response.choices[0].message
                raw_response = getattr(message_obj, 'content', str(message_obj))
            elif hasattr(chat_client, 'complete_chat'):
                response = chat_client.complete_chat(messages=messages_payload)
                raw_response = str(response)
            else:
                response = chat_client.complete(messages=messages_payload)
                raw_response = str(response)
            
            break  # Başarılı olursa döngüden çık
            
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Sistem Hatası (Motor Kilitlendi): {str(e)}", context
            print(f"\n[Sistem] İşlemci zaman aşımına uğradı, {attempt+1}. kez tekrar deneniyor...")
            time.sleep(5) # 5 saniye nefes alıp tekrar dene

    # 5. KESİN TEMİZLEYİCİ
    clean_response = raw_response
    match = re.search(r"content=['\"](.*?)['\"],\s*(?:refusal|role)=", raw_response, re.DOTALL)
    if match:
        clean_response = match.group(1)
    elif "content='" in raw_response:
        clean_response = raw_response.split("content='")[1].split("',")[0]
                    
    # Düşünce bloklarını temizle
    clean_response = re.sub(r'<think>.*?</think>', '', clean_response, flags=re.DOTALL).strip()
    
    # UI DÜZELTMESİ: Metin içindeki harf olan '\n' ifadelerini GERÇEK satır atlamaya çevir.
    clean_response = clean_response.replace('\\n', '\n')
    
    final_answer = clean_response if len(clean_response) > 1 else "Bilgi bulunamadı."
    
    return final_answer, context