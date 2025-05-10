from flask import Flask, request, jsonify, send_from_directory,session
from flask_cors import CORS
# from chat import chatapi, 代码编写api, 写故事api
from chat_test import chatapi, 代码编写api, 写故事api
# from PPT import PPTapi
# from 文本纠错 import 文本纠错api
# from 简历 import 简历api
# from 翻译 import 中译英翻译api,英译中翻译api
import sqlite3
from database import get_db_connection
app = Flask(__name__)

# 配置跨域支持
CORS(app, supportscredentials=True)

# 设置静态文件夹
app.static_folder = 'static'
app.secret_key = 'hard_to_guess_secret_key'
app.config.update(
    SESSION_COOKIE_SECURE=True,      # 仅 HTTPS 下发送 Cookie
    SESSION_COOKIE_HTTPONLY=True,    # 禁止 JavaScript 访问 Cookie
    SESSION_COOKIE_SAMESITE='Lax',   # 或 'Strict'
)

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        # 获取请求中的 JSON 数据
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400

        input_text = data['text']
        input_function = data['function']
        #user_id = data['user_id']  # 从前端获取用户 ID
        print(data)
        # 调用 chatapi 处理文本
        if input_function == None:
            output_text = chatapi(input_text)       

        # if input_function == 1:
        #     output_text = PPTapi(input_text)
        # if input_function == 2:
        #     output_text = PPTapi(input_text)
        # if input_function == 3:
        #     output_text = 简历api(input_text)
        # if input_function == 4:
        #     output_text = 文本纠错api(input_text)
        # if input_function == 5:
        #     output_text = 中译英翻译api(input_text)
        # if input_function == 6:
        #     output_text = 英译中翻译api(input_text)
        if input_function == 7:
            output_text = 代码编写api(input_text)
        if input_function == 8:
            output_text = 写故事api(input_text)
        output_text = str(output_text)
        print(output_text)
        
        # 保存聊天记录到数据库
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
                (session['user_id'], input_text, output_text)
            )
            conn.commit()
        except Exception as e:
            print(f'保存聊天记录失败: {e}')
        finally:
            conn.close()


        
        return jsonify({"result": output_text})

    except Exception as e:
        # 捕获异常并返回 500 错误
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/', methods=['GET'])
def serve_index():
    try:
        return send_from_directory(app.static_folder, 'index_better.html')
    except FileNotFoundError:
        return jsonify({"error": "index_better.html not found"}), 404

@app.route('/admin', methods=['GET'])
def serve_admin():
    try:
        return send_from_directory(app.static_folder, 'login_and_register.html')
    except FileNotFoundError:
        return jsonify({"error": "index_better.html not found"}), 404

# 数据库部分
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and user[2]==password:  # user[2] 是密码字段
        session['user_id'] = user[0]
        return jsonify({"message": "Login successful", "user_id": user[0]}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # 生成聊天响应（这里只是一个简单的回显示例）
    response = f"Echo: {message}"

    # 保存聊天记录到数据库
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
                    (session['user_id'], message, response))
    conn.commit()
    conn.close()

    return jsonify({"response": response})

@app.route('/chat_history', methods=['GET'])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            user_id,  -- 新增字段
            message, 
            response, 
            timestamp 
        FROM chat_history 
        WHERE user_id = ?
    ''', (session['user_id'],))
    chat_history = cursor.fetchall()
    conn.close()

    # 将元组转换为字典列表（确保前端可访问字段）
    result = []
    for row in chat_history:
        result.append({
            "user_id": row[0], 
            "message": row[1],
            "response": row[2],
            "timestamp": row[3]
        })
    
    return jsonify({"chat_history": result})



if __name__ == '__main__':
    app.run(debug=True)

print("系统启动完成") 