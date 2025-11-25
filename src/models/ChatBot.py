from src.models.client import Client
from src.models.task import Task
from src.models.employee import Employee
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class ChatBot:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        
    def get_response(self, question):  # Remove db parameter from here
        try:
            # Clean and prepare question
            question = self._clean_text(question)
            
            # Get data from database
            corpus = self._collect_data()
            
            if not corpus:
                return "عذراً، لا توجد بيانات كافية للإجابة على سؤالك"
            
            # Add question to corpus temporarily for comparison
            texts = [item['text'] for item in corpus]
            texts.append(question)
            
            # Calculate similarities
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
            
            # Find best match
            best_idx = similarities.argmax()
            if similarities[best_idx] < 0.15:
                return "عذراً، لم أفهم سؤالك. هل يمكنك إعادة صياغته؟"
                
            return corpus[best_idx]['response']
            
        except Exception as e:
            return f"حدث خطأ: {str(e)}"

    def _clean_text(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
        
    def _collect_data(self):
        corpus = []
        
        # جمع بيانات العملاء مع التحقق من وجود الخصائص
        clients = Client.query.all()
        for client in clients:
            response = f"العميل: {client.name}"
            if hasattr(client, 'phone'):
                response += f", رقم الهاتف: {client.phone}"
            if hasattr(client, 'email'):
                response += f", البريد: {client.email}"
                
            corpus.append({
                'text': f"معلومات عن العميل {client.name}",
                'response': response
            })
        
       # جمع بيانات المهام
        tasks = Task.query.all()
        for task in tasks:
            response = f"المهمة"
            if hasattr(task, 'name'):  # بعض النماذج تستخدم name بدل title
                response += f": {task.name}"
            elif hasattr(task, 'title'):
                response += f": {task.title}"
            if hasattr(task, 'status'):
                response += f", الحالة: {task.status}"
            if hasattr(task, 'description'):
                response += f", التفاصيل: {task.description}"
                
            task_name = getattr(task, 'name', '') or getattr(task, 'title', '')
            corpus.append({
                'text': f"مهمة {task_name}",
                'response': response
            })
            
        return corpus