from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chat import chatapi, 代码编写api, 写故事api
from PPT import PPTapi

from 文本纠错 import 文本纠错api
from 简历 import 简历api
from 翻译 import 中译英翻译api,英译中翻译api

app = Flask(__name__)

# 配置跨域支持
CORS(app, supportscredentials=True)

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
        input_function = data['function']
        print(data)
        # 调用 chatapi 处理文本
        if input_function == None:
            output_text = chatapi(input_text)

        if input_function == 1:
            output_text = PPTapi(input_text)
        if input_function == 2:
            output_text = PPTapi(input_text)
        if input_function == 3:
            output_text = 简历api(input_text)
        if input_function == 4:
            output_text = 文本纠错api(input_text)
        if input_function == 5:
            output_text = 中译英翻译api(input_text)
        if input_function == 6:
            output_text = 英译中翻译api(input_text)
        if input_function == 7:
            output_text = 代码编写api(input_text)
        if input_function == 8:
            output_text = 写故事api(input_text)
        output_text = str(output_text)
        print(output_text)
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
