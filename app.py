#!/usr/bin/env python3
"""
Streamlit Web App - Upwork AI Assistant Chat Interface
"""

import streamlit as st
import yaml
from pathlib import Path
import chromadb
from chromadb.config import Settings
import sys

try:
    from ollama import Client
    OLLAMA_CLIENT = True
except ImportError:
    try:
        import ollama
        OLLAMA_CLIENT = False
    except ImportError:
        st.error("⚠ Lỗi: Không tìm thấy ollama. Hãy cài: pip install ollama")
        st.stop()

sys.path.insert(0, str(Path(__file__).parent))

from utils.embedding import get_embedding_model

# Load config
@st.cache_resource
def load_config():
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    profile_path = Path(__file__).parent / 'config' / 'profile.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = yaml.safe_load(f)
    
    return config, profile

@st.cache_resource
def init_chromadb():
    """Khởi tạo ChromaDB - tự động tạo collection nếu chưa có"""
    config, _ = load_config()
    chromadb_config = config['chromadb']
    persist_dir = Path(__file__).parent / chromadb_config['persist_directory']
    persist_dir.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    # Dùng get_or_create_collection để tự động tạo nếu chưa có
    collection = client.get_or_create_collection(
        name=chromadb_config['collection_name'],
        metadata={"hnsw:space": "cosine"}
    )
    return collection

@st.cache_resource
def _get_cached_embedding_model():
    """Cache SentenceTransformer model để tăng tốc (Streamlit cache)"""
    return get_embedding_model()

@st.cache_data
def _load_ai_rules():
    """Cache AI rules files để tránh đọc file mỗi lần chat"""
    rules_dir = Path(__file__).parent / 'ai_rules'
    rules = {
        'system_instruction': '',
        'rulebook': '',
        'hardware': '',
        'profile_context': ''
    }
    
    analysis_file = rules_dir / 'analysis.md'
    if analysis_file.exists():
        with open(analysis_file, 'r', encoding='utf-8') as f:
            rules['system_instruction'] = f.read()
    
    rules_file = rules_dir / 'upwork_rules.md'
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules['rulebook'] = f.read()
    
    hardware_file = rules_dir / 'hardware.md'
    if hardware_file.exists():
        with open(hardware_file, 'r', encoding='utf-8') as f:
            rules['hardware'] = f.read()
    
    profile_context_file = rules_dir / 'profile_context.md'
    if profile_context_file.exists():
        with open(profile_context_file, 'r', encoding='utf-8') as f:
            rules['profile_context'] = f.read()
    
    return rules

def search_jobs(collection, query_text, top_k=10):
    """Search jobs trong ChromaDB"""
    try:
        model = _get_cached_embedding_model()
        query_embedding = model.encode([query_text])[0].tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        jobs = []
        # Check if results are valid
        if results and 'ids' in results and results['ids'] and len(results['ids']) > 0:
            if len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    job = {
                        'job_id': results['ids'][0][i],
                        'title': results['metadatas'][0][i].get('title', ''),
                        'description': results['documents'][0][i],
                        'budget': results['metadatas'][0][i].get('budget', ''),
                        'proposals': results['metadatas'][0][i].get('proposals', ''),
                        'client_country': results['metadatas'][0][i].get('client_country', ''),
                        'category': results['metadatas'][0][i].get('category', ''),
                        'link': results['metadatas'][0][i].get('link', ''),
                        'source': results['metadatas'][0][i].get('source', 'Unknown'),
                    }
                    jobs.append(job)
        
        return jobs
    except Exception as e:
        st.error(f"Lỗi khi search jobs: {e}")
        st.info("💡 Tip: Có thể cần reinstall ChromaDB: pip install --upgrade chromadb>=1.3.5")
        return []

def chat_with_ai(user_input, collection, conversation_history):
    """Chat với AI"""
    config, profile = load_config()
    ollama_config = config['ollama']
    base_url = ollama_config.get('base_url', 'http://localhost:11434')
    
    # Build context
    context = f"""
Profile Tuấn Anh (freelancer):
- Name: {profile.get('name', 'Tuấn Anh')}
- Title: {profile.get('title', 'Python Developer')}
- Skills: {', '.join(profile.get('skills', []))}
- Experience: {profile.get('experience', 0)} năm
- Rate: {profile.get('rate', '')}
- Work Style: {profile.get('work_style', 'Demo-first')}
"""
    
    # Nếu user hỏi về jobs, search trước (chỉ khi cần)
    if any(keyword in user_input.lower() for keyword in ['job', 'việc', 'tìm', 'search', 'phân tích']):
        jobs = search_jobs(collection, user_input, top_k=5)
        if jobs:
            context += f"\n\nJobs tìm được:\n"
            for i, job in enumerate(jobs, 1):
                context += f"{i}. {job['title']}\n   Budget: {job.get('budget', 'N/A')}\n   Link: {job.get('link', 'N/A')}\n\n"
    
    # Load AI rules từ cache (nhanh hơn)
    ai_rules = _load_ai_rules()
    system_instruction = ai_rules['system_instruction']
    rulebook = ai_rules['rulebook']
    hardware = ai_rules['hardware']
    profile_context = ai_rules['profile_context']
    
    # Build system prompt ngắn gọn hơn (chỉ load rules khi cần)
    # Rút gọn personality để prompt ngắn hơn, nhanh hơn
    system_prompt = f"""Bạn là Lysa - AI assistant thông minh, nói chuyện tự nhiên, có tư duy logic. Hỗ trợ Tuấn Anh (freelancer) tìm jobs, phân tích, viết proposal.

Tone: Tự nhiên như bạn bè, không formal, thực tế, không vòng vo.

{profile_context[:500] if profile_context else ''}"""
    
    # Chỉ thêm rules khi user hỏi về phân tích hoặc proposal
    if any(kw in user_input.lower() for kw in ['phân tích', 'analyze', 'proposal', 'viết']):
        system_prompt += f"\n\n{system_instruction[:300] if system_instruction else ''}"
        system_prompt += f"\n{rulebook[:300] if rulebook else ''}"
    
    messages = [
        {'role': 'system', 'content': system_prompt + '\n\n' + context}
    ]
    
    # Add conversation history
    messages.extend(conversation_history[-4:])
    
    # Add user input
    messages.append({'role': 'user', 'content': user_input})
    
    try:
        if OLLAMA_CLIENT:
            client = Client(host=base_url, timeout=30.0)  # Timeout ngắn hơn
            response = client.chat(
                model=ollama_config['model'],
                messages=messages,
                options={
                    'temperature': 0.5,  # Giảm xuống 0.5 để nhanh hơn nhưng vẫn tự nhiên
                    'num_predict': 500,  # Giảm xuống để nhanh hơn
                    'top_p': 0.85,
                    'top_k': 40,  # Thêm top_k để nhanh hơn
                }
            )
            return response['message']['content']
        else:
            response = ollama.chat(
                model=ollama_config['model'],
                messages=messages,
                options={
                    'temperature': 0.5,
                    'num_predict': 500,
                    'top_p': 0.85,
                    'top_k': 40,
                }
            )
            return response['message']['content']
    except Exception as e:
        return f"Lỗi: {e}. Đảm bảo Ollama đang chạy: ollama serve"

# Streamlit UI
st.set_page_config(
    page_title="Upwork AI Assistant",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Upwork AI Assistant")
st.caption("Chat với AI để phân tích jobs, tư vấn, và viết proposal")

# Sidebar
with st.sidebar:
    st.header("📊 Thông tin")
    config, profile = load_config()
    st.write(f"**Skills:** {', '.join(profile.get('skills', []))}")
    st.write(f"**Experience:** {profile.get('experience', 0)} năm")
    st.write(f"**Rate:** {profile.get('rate', '')}")
    
    st.divider()
    
    st.header("🔧 Actions")
    if st.button("🔄 Refresh Jobs"):
        st.cache_resource.clear()
        st.rerun()
    
    if st.button("📥 Sync Data"):
        import subprocess
        with st.spinner("Đang sync..."):
            result = subprocess.run(
                ["python", "scripts/local_sync_and_rag.py"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                st.success("Sync thành công!")
            else:
                st.error(f"Lỗi: {result.stderr}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Load ChromaDB
try:
    collection = init_chromadb()
    # Check if collection is empty
    try:
        count = collection.count()
        if count == 0:
            st.warning("⚠ ChromaDB collection trống. Hãy chạy `update.bat` để sync jobs vào database.")
    except:
        pass
except Exception as e:
    st.error(f"Lỗi khởi tạo ChromaDB: {e}")
    st.info("💡 **Giải pháp:** Chạy `update.bat` để tạo collection và sync jobs vào ChromaDB.")
    st.stop()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Hỏi gì đó về jobs, proposal, hoặc tư vấn..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Đang suy nghĩ..."):
            response = chat_with_ai(
                prompt, 
                collection, 
                st.session_state.conversation_history
            )
            st.markdown(response)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Update conversation history
    st.session_state.conversation_history.append({'role': 'user', 'content': prompt})
    st.session_state.conversation_history.append({'role': 'assistant', 'content': response})

# Quick actions
st.divider()
st.subheader("💡 Gợi ý câu hỏi")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Tìm jobs WordPress"):
        st.session_state.messages.append({"role": "user", "content": "Tìm jobs WordPress cho anh"})
        st.rerun()

with col2:
    if st.button("📝 Phân tích jobs mới"):
        st.session_state.messages.append({"role": "user", "content": "Phân tích jobs mới nhất cho Tuấn anh"})
        st.rerun()

with col3:
    if st.button("✍️ Viết proposal"):
        st.session_state.messages.append({"role": "user", "content": "Hướng dẫn tuấn anh viết proposal"})
        st.rerun()

