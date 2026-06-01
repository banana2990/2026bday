import os
from flask import Flask, send_from_directory

app = Flask(__name__)

# 첫 화면 요청이 들어오면 index.html 파일을 보여줍니다.
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # Render가 지정해 주는 포트번호를 사용하도록 설정합니다.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)