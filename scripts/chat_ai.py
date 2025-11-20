#!/usr/bin/env python3
"""
Script chat tương tác với Upwork AI Assistant
Cho phép hỏi đáp, phân tích jobs, viết proposal trực tiếp
"""

import sys
import yaml
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
try:
    from ollama import Client
    OLLAMA_CLIENT = True
except ImportError:
    try:
        import ollama
        OLLAMA_CLIENT = False
    except ImportError:
        print("⚠ Lỗi: Không tìm thấy ollama. Hãy cài: pip install ollama")
        sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load config
config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
profile_path = Path(__file__).parent.parent / 'config' / 'profile.yaml'

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

with open(profile_path, 'r', encoding='utf-8') as f:
    profile = yaml.safe_load(f)

chromadb_config = config['chromadb']
ollama_config = config['ollama']

def init_chromadb():
    """Khởi tạo ChromaDB"""
    persist_dir = Path(__file__).parent.parent / chromadb_config['persist_directory']
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.get_collection(chromadb_config['collection_name'])
    return collection

def search_jobs(collection, query_text, top_k=10):
    """Search jobs trong ChromaDB"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query_text])[0].tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    jobs = []
    if results['ids'] and len(results['ids'][0]) > 0:
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

def chat_with_ai(user_input, collection, conversation_history=[]):
    """Chat với AI"""
    base_url = ollama_config.get('base_url', 'http://localhost:11434')
    
    # Build context
    context = f"""
Profile CEO:
- Skills: {', '.join(profile.get('skills', []))}
- Experience: {profile.get('experience', 0)} năm
- Rate: {profile.get('rate', '')}
"""
    
    # Nếu user hỏi về jobs, search trước
    if any(keyword in user_input.lower() for keyword in ['job', 'việc', 'tìm', 'search', 'phân tích']):
        jobs = search_jobs(collection, user_input, top_k=5)
        if jobs:
            context += f"\n\nJobs tìm được:\n"
            for i, job in enumerate(jobs, 1):
                context += f"{i}. {job['title']}\n   Budget: {job.get('budget', 'N/A')}\n   Link: {job.get('link', 'N/A')}\n\n"
    
    # Build messages
    system_prompt = """Em là Upwork Assistant của CEO Hùng, một freelancer Việt Nam với nhiều năm kinh nghiệm.

QUY TẮC:
- Em LUÔN bắt đầu: "Dạ anh,"
- Em LUÔN kết thúc: "Anh xem sao, quyết định cuối cùng thuộc về anh."
- KHÔNG dùng: "nên", "phải", "tốt nhất", "đề xuất"
- Ngôi xưng: luôn "em"
- Giọng điệu: thực tế, hơi bựa, freelancer VN 8-10 năm
- Em KHÔNG có quyền quyết định, chỉ phân tích và tư vấn"""
    
    messages = [
        {'role': 'system', 'content': system_prompt + '\n\n' + context}
    ]
    
    # Add conversation history
    messages.extend(conversation_history[-4:])  # Chỉ giữ 4 tin nhắn gần nhất
    
    # Add user input
    messages.append({'role': 'user', 'content': user_input})
    
    try:
        if OLLAMA_CLIENT:
            client = Client(host=base_url)
            response = client.chat(
                model=ollama_config['model'],
                messages=messages
            )
            return response['message']['content']
        else:
            response = ollama.chat(
                model=ollama_config['model'],
                messages=messages
            )
            return response['message']['content']
    except Exception as e:
        return f"Lỗi: {e}. Đảm bảo Ollama đang chạy: ollama serve"

def main():
    """Main chat loop"""
    print("=" * 60)
    print("💬 Upwork AI Assistant - Chat Mode")
    print("=" * 60)
    print("Gõ 'quit' hoặc 'exit' để thoát")
    print("Gõ 'help' để xem các lệnh")
    print("=" * 60)
    print()
    
    collection = init_chromadb()
    conversation_history = []
    
    while True:
        try:
            user_input = input("\n🤔 Bạn: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Tạm biệt anh!")
                break
            
            if user_input.lower() == 'help':
                print("""
📋 Các lệnh:
- Hỏi về jobs: "Tìm jobs WordPress", "Phân tích jobs Laravel"
- Hỏi về proposal: "Viết proposal cho job X"
- Hỏi chung: "Tư vấn về job này", "Job này có scam không?"
- Thoát: 'quit', 'exit', 'q'
                """)
                continue
            
            print("\n🤖 AI: ", end='', flush=True)
            response = chat_with_ai(user_input, collection, conversation_history)
            print(response)
            
            # Lưu vào history
            conversation_history.append({'role': 'user', 'content': user_input})
            conversation_history.append({'role': 'assistant', 'content': response})
            
        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt anh!")
            break
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")

if __name__ == '__main__':
    main()

