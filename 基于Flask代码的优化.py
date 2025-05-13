from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import sqlite3
import logging
from functools import wraps
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
CORS(app, supports_credentials=True)

# 应用配置
app.config.update(
    SECRET_KEY='hard_to_guess_secret_key',
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    STATIC_FOLDER='static',
    DATABASE='chat_app.db'
)

# API服务导入
from chat import chatapi, 代码编写api, 写故事api
from PPT import PPTapi
from 文本纠错 import 文本纠错api
from 简历 import 简历api
from 翻译 import 中译英翻译api, 英译中翻译api
from database import get_db_connection


# 数据类型定义
@dataclass
class User:
    id: int
    username: str


@dataclass
class ChatRecord:
    user_id: int
    message: str
    response: str
    timestamp: str


# 装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def validate_json(*required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing JSON data"}), 400
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            return f(*args, **kwargs)

        return wrapper

    return decorator


# API路由
@app.route('/process_text', methods=['POST'])
@login_required
@validate_json('text', 'function')
def process_text() -> Dict[str, Any]:
    """处理文本请求路由"""
    data = request.get_json()
    input_text = data['text']
    function_type = data['function']

    # 定义功能映射
    function_map = {
        None: chatapi,
        1: PPTapi,
        2: PPTapi,  # 假设这是另一种PPT生成
        3: 简历api,
        4: 文本纠错api,
        5: 中译英翻译api,
        6: 英译中翻译api,
        7: 代码编写api,
        8: 写故事api
    }

    try:
        # 获取对应的API函数
        api_function = function_map.get(function_type)
        if not api_function:
            return jsonify({"error": "Invalid function type"}), 400

        # 调用API函数
        output_text = str(api_function(input_text))
        logger.info(f"Processed text: {input_text[:50]}... -> {output_text[:50]}...")

        # 保存聊天记录
        save_chat_history(session['user_id'], input_text, output_text)

        return jsonify({"result": output_text})

    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/', methods=['GET'])
def serve_index():
    """服务首页"""
    return serve_static_file('index_better.html')


@app.route('/admin', methods=['GET'])
def serve_admin():
    """服务管理页面"""
    return serve_static_file('login_and_register.html')


def serve_static_file(filename: str):
    """服务静态文件通用函数"""
    try:
        return send_from_directory(app.config['STATIC_FOLDER'], filename)
    except FileNotFoundError:
        logger.warning(f"Static file not found: {filename}")
        return jsonify({"error": f"{filename} not found"}), 404


# 用户认证路由
@app.route('/register', methods=['POST'])
@validate_json('username', 'password')
def register() -> Dict[str, Any]:
    """用户注册路由"""
    data = request.get_json()
    username = data['username']
    password = data['password']

    try:
        user_id = create_user(username, password)
        return jsonify({"message": "User registered successfully", "user_id": user_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


@app.route('/login', methods=['POST'])
@validate_json('username', 'password')
def login() -> Dict[str, Any]:
    """用户登录路由"""
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user.id
        return jsonify({"message": "Login successful", "user": {"id": user.id, "username": user.username}})
    return jsonify({"error": "Invalid credentials"}), 401


# 聊天历史路由
@app.route('/chat_history', methods=['GET'])
@login_required
def get_chat_history() -> Dict[str, Any]:
    """获取聊天历史路由"""
    try:
        history = fetch_chat_history(session['user_id'])
        return jsonify({"chat_history": [
            {
                "user_id": record.user_id,
                "message": record.message,
                "response": record.response,
                "timestamp": record.timestamp
            } for record in history
        ]})
    except Exception as e:
        logger.error(f"Failed to fetch chat history: {str(e)}")
        return jsonify({"error": "Failed to fetch chat history"}), 500


# 数据库操作函数
def create_user(username: str, password: str) -> int:
    """创建新用户"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists")
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户凭据"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE username = ? AND password = ?',
                       (username, password))
        user = cursor.fetchone()
        return User(user[0], user[1]) if user else None
    finally:
        conn.close()


def save_chat_history(user_id: int, message: str, response: str) -> None:
    """保存聊天记录"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
            (user_id, message, response)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save chat history: {str(e)}")
        raise
    finally:
        conn.close()


def fetch_chat_history(user_id: int) -> List[ChatRecord]:
    """获取用户聊天历史"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, message, response, timestamp 
            FROM chat_history 
            WHERE user_id = ?
            ORDER BY timestamp DESC
        ''', (user_id,))
        return [ChatRecord(*row) for row in cursor.fetchall()]
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)