import streamlit as st
import time
from app import answer_query, initialize_models

# Sayfa Yapılandırması
st.set_page_config(page_title="Local RAG Assistant", page_icon="💻", layout="wide")

# UI Optimizasyonları
st.markdown("""
<style>
    .stChatFloatingInputContainer { padding-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_system():
    initialize_models()
    return True

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.title("⚙️ Local RAG System")
    st.caption("Powered by Microsoft Foundry Local")
    st.divider()
    
    st.markdown("### 📊 Mimari Durum")
    st.success("LLM Runtime: Aktif (Çevrimdışı)")
    st.success("Vektör DB: SQLite Bağlı")
    st.info("Hafıza: Son Mesajlar")
    
    st.divider()
    st.markdown("Bu sistem yerel RAG mimarisi ile donatılmıştır.")
    
    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- ANA EKRAN ---
st.title("💻 Yerel Çevrimdışı Q&A Asistanı")
st.markdown("*İnternet bağlantısı olmadan, yerel bilgi tabanınızdaki belgelere dayanarak sorularınızı yanıtlar.*")

# Yükleme Ekranı
with st.spinner("Foundry Local Engine ve Modeller başlatılıyor..."):
    load_system()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        # Eğer geçmişte context varsa onu da expander ile göster
        if "context" in message and message["context"]:
            with st.expander("🔍 Okunan Kaynak Bağlamı (RAG)"):
                st.text(message["context"])

# Kullanıcı Girdisi
if prompt := st.chat_input("Yerel veritabanındaki belgeler hakkında soru sorun..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Asistan Yanıtı
    with st.chat_message("assistant", avatar="🤖"):
        status_placeholder = st.empty()
        
        # MANTIK HATASI DÜZELTİLDİ: Tek ve dürüst bir durum bildirimi
        with status_placeholder.status("🤖 Asistan çalışıyor...", expanded=True):
            st.write("🔍 Belgeler taranıyor ve yapay zeka (Phi-3.5) yanıtı üretiyor...")
            
            # Fonksiyon çağrılıyor (Hem arama hem LLM üretimi arka planda yapılıyor)
            response, context = answer_query(prompt, chat_history=st.session_state.messages[:-1])
            
        status_placeholder.success("✅ Yanıt başarıyla üretildi!")
        
        st.markdown(response)
        
        with st.expander("🔍 Okunan Kaynak Bağlamı (RAG)"):
            st.text(context)
    
    st.session_state.messages.append({"role": "assistant", "content": response, "context": context})