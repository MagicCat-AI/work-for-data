from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from chat import chatapi
app = Flask(__name__)
CORS(app)  # 启用跨域支持

app.static_folder = 'static'

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        data = request.get_json()
        input_text = data.get('text')
        if input_text:
            # 这里可以对输入文本进行处理，这里简单返回输入文本加上一个后缀
            output_text = chatapi(input_text)
            return jsonify({"result": output_text})
        else:
            return jsonify({"error": "No text provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(app.static_folder, 'index_better.html')

if __name__ == '__main__':
    app.run(debug=True)
