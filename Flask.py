from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chat import chatapi

app = Flask(__name__)

# 配置跨域支持
CORS(app, supports_credentials=True)

# 设置静态文件夹
app.static_folder = 'static'

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        # 获取请求中的 JSON 数据
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided"}), 400

        input_text = data['text']

        # 调用 chatapi 处理文本
        output_text = chatapi(input_text)
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


if __name__ == '__main__':
    app.run(debug=True)
