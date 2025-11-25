# ...existing code...
from flask import Blueprint, request, jsonify, current_app, render_template
from functools import lru_cache
from src.models.ChatBot import ChatBot
from src.models.user import db

chatbot_bp = Blueprint('chatbot', __name__)
bot = ChatBot()  # Create single instance

# إضافة راوت صفحة الـ ChatBot (GET) لكي يعمل url_for('chatbot.page')
@chatbot_bp.route('/', methods=['GET'])
def page():
    return render_template('chatbot.html')

# راوت الـ API (POST) موجود - تأكد اسمه لا يتغير
@chatbot_bp.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json(silent=True) or {}
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
    
    response = bot.get_response(data['question'])  # Remove db parameter
    return jsonify({'response': response})
# ...existing code...