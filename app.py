import mimetypes
import os
import re
import sys

from flask import request, send_file, Response, Flask, render_template

app = Flask(__name__)
app.debug = True

def send_partial_file(path):
    if not os.path.exists(path):
        return "404 Not Found", 404

    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(path)

    size = os.path.getsize(path)

    start, end = get_ranges(range_header)
    
    # 범위를 벗어난 경우
    if end is not None and end > size or start < 0:
        return "416 Requested Range Not Satisfiable", 416
    
    length = 0
    if end is not None:
        length = end - start
    else:
        #range 요청에서 end는 생략될 수 있습니다. 없는 경우 시작 부터 시작 위치에서 파일 전체까지를 전달합니다.
        length = size - start

    data = None
    with open(path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    response = Response(data,
                        206,
                        mimetype=mimetypes.guess_type(path)[0],
                        direct_passthrough=True)

    #size는 1부터 세지만(바이트 단위) 위치는 0부터 시작하므로 1을 빼야 정상 작동
    response.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, start + length - 1, size))
    response.headers.add('Accept-Ranges', 'bytes')
    
    # 일부 요청에서(VLC 등) 'Connection : close'로 요청을 해서 적용해 봄 하지만 확실한 규명이 안됨 
    #response.headers.add('Connection', 'keep-alive')
    print(response.headers)

    return response


def get_ranges(range_header):
    maches = re.search('(\d+)-(\d*)', range_header)
    ranges = maches.groups()

    start, end = 0, None
    if ranges[0]:
        start = int(ranges[0])
    if ranges[1]:
        end = int(ranges[1])

    return start, end

@app.route("/<string:filename>")
def stream(filename):
    print(request.headers)
    return send_partial_file(filename)

@app.route("/")
def index():
    return render_template("stream.html")

try:
    port_number = sys.argv[1]
except IndexError:
    port_number = 5000
HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
try:
    PORT = int(os.environ.get('SERVER_PORT', port_number))
except ValueError:
    PORT = 5000
app.run(HOST, PORT)

