from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
import mysql.connector
from mysql.connector import Error
import os
import cv2
from tensorflow.keras import models
import hashlib
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 플래시 메시지를 위한 비밀키
app.permanent_session_lifetime = timedelta(minutes=10)  # 세션 유효시간: 10분
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 저장된 모델 불러오기
loaded_model = models.load_model("cat_cnn_model.h5")

# 데이터베이스 연결 및 사용자 정보 저장 함수
def save_user_to_mariadb(username, password, name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            # 비밀번호 해시 처리 (SHA256) 후 저장
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            query = """INSERT INTO users (username, password, name) 
                       VALUES (%s, %s, %s)"""
            cursor.execute(query, (username, hashed_password, name))
            connection.commit()
            flash('회원가입이 완료되었습니다!', 'success')
    except Error as e:
        print("Error while connecting to MariaDB", e)
        flash('회원가입 중 오류가 발생했습니다.', 'danger')
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 글작성 함수
def write_boards(title, writer, content):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            query = """INSERT INTO board (title, writer, content) 
                       VALUES (%s, %s, %s)"""
            cursor.execute(query, (title, writer, content))
            connection.commit()
            flash('작성이 완료되었습니다!', 'success')
    except Error as e:
        print("Error while connecting to MariaDB", e)
        flash('작성 중 오류가 발생했습니다.', 'danger')
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 회원가입 처리
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        
        # 사용자 정보를 DB에 저장
        save_user_to_mariadb(username, password, name)
        return '''
            <script>
                alert("회원가입이 완료되었습니다!");
                window.location.href = "/";
            </script>
        '''
    
    return render_template('signup.html')

#아이디 중복체크
@app.route('/check-username', methods=['GET'])
def check_username():
    username = request.args.get('username')
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT COUNT(*) AS count FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            return jsonify({'exists': result['count'] > 0})
    except Error as e:
        print(f"Error while connecting to MariaDB: {e}")
        return jsonify({'error': 'Database error occurred.'}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 글작성
@app.route('/boardwrite', methods=['GET', 'POST'])
def write_board():
    if request.method == 'POST':
        title = request.form['title']
        writer = request.form['writer']
        content = request.form['content']
        
        # 사용자 정보를 DB에 저장
        write_boards(title, writer, content)
        return '''
            <script>
                alert("작성이 완료되었습니다!");
                window.location.href = "/board";
            </script>
        '''

# 데이터베이스에서 게시글 데이터 가져오는 함수
def get_board_data():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = """SELECT board_no, title, writer, DATE_FORMAT(board_time, '%Y/%m/%d') AS board_time FROM board ORDER BY board_no DESC"""
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print("Error while connecting to MariaDB", e)
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 게시판 페이지 경로 설정
@app.route('/board', methods=['GET'])
def board():
    page = int(request.args.get('page', 1))  # 기본 페이지는 1
    posts_per_page = 10  # 페이지당 게시글 수
    offset = (page - 1) * posts_per_page

    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # 게시글 데이터 가져오기
            query = """
                SELECT board_no, title, writer, DATE_FORMAT(board_time, '%Y/%m/%d') AS board_time
                FROM board
                WHERE view_point = 1
                ORDER BY board_no DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (posts_per_page, offset))
            board_data = cursor.fetchall()

            # 전체 게시글 개수 가져오기
            cursor.execute("SELECT COUNT(*) AS total_posts FROM board")
            total_posts = cursor.fetchone()['total_posts']
            total_pages = (total_posts // posts_per_page) + (1 if total_posts % posts_per_page > 0 else 0)

            return render_template('board.html', board_data=board_data, page=page, total_pages=total_pages)
    except Error as e:
        print(f"Error while connecting to MariaDB: {e}")
        return render_template('board.html', board_data=[], page=1, total_pages=1)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 글쓰기 페이지 경로 설정
@app.route('/write', methods=['GET', 'POST'])
def write():
    return render_template('write.html')

# 이미지 업로드 및 예측 처리
@app.route('/', methods=['GET', 'POST'])
def upload_image():
    comments = get_comments()  # 댓글 불러오기
    
    
    if request.method == 'POST':
        # 이미지 파일이 없는 경우
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']

        # 파일명이 비어 있는 경우
        if file.filename == '':
            return redirect(request.url)

        # 파일이 정상적으로 업로드된 경우
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            class_name, confidence_score = predict_image(filename)
            save_to_mariadb(filename, class_name, confidence_score)
            image_url = url_for('static', filename=os.path.join('uploads', file.filename))
            return render_template('result.html', class_name=class_name, confidence_score=confidence_score, image_url=image_url, comments=comments)

    # GET 요청일 때 업로드 페이지와 댓글 목록을 렌더링
    return render_template('upload.html', comments=comments)

# 예측 함수 정의
def predict_image(image_path):
    image = cv2.imread(image_path)
    image = cv2.resize(image, (80, 80))  # 학습과 동일한 크기
    image = image.reshape(1, 80, 80, 3)
    prediction = loaded_model.predict(image)
    class_label = prediction.argmax()
    class_names = ["노르웨이숲","랙돌","러시안 블루","메인쿤","벵갈","브리티시 숏헤어","샴","스핑크스","아메리칸 숏헤어","아비니시안","페르시안"]  # 고양이 클래스
    class_name = class_names[class_label]
    confidence_score = prediction[0][class_label]
    return class_name, confidence_score

# 이미지 예측 결과 저장
def save_to_mariadb(image_path, class_name, confidence_score):
    connection = None
    try:
        confidence_score = round(float(confidence_score), 2)
        print(f"Attempting to save: image_path={image_path}, class_name={class_name}, confidence_score={confidence_score}")
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            query = """INSERT INTO predictions (image_path, class_name, confidence_score) 
                       VALUES (%s, %s, %s)"""
            cursor.execute(query, (image_path, class_name, confidence_score))
            connection.commit()
            print("Data saved successfully!")
    except Error as e:
        print(f"Error while connecting to MariaDB or executing query: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
# 댓글 저장 함수
def save_comment(username, content):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            query = "INSERT INTO comments (username, content) VALUES (%s, %s)"
            cursor.execute(query, (username, content))
            connection.commit()
    except Error as e:
        print("Error while connecting to MariaDB", e)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 댓글 불러오기 함수
def get_comments():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT username, content, DATE_FORMAT(comment_time, '%Y-%m-%d %H:%i') AS comment_time FROM comments WHERE view_point = 1 ORDER BY id DESC"
            
            cursor.execute(query)
            return cursor.fetchall()
    except Error as e:
        print("Error while connecting to MariaDB", e)
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 댓글 작성 처리 (AJAX 지원)
@app.route('/comment', methods=['POST'])
def comment():
    username = request.form['username']
    content = request.form['content']
    save_comment(username, content)
    # 새로운 댓글 정보 JSON으로 반환
    return jsonify({
        "username": username,
        "content": content,
        "comment_time": "방금 전"  # 새로고침 없이 표시할 간단한 시간 표현
    })

# 페이지 단위로 댓글 가져오기
@app.route('/comments', methods=['GET'])
def comments():
    page = int(request.args.get('page', 1))  # 기본 페이지는 1
    comments_per_page = 10  # 페이지당 댓글 수
    offset = (page - 1) * comments_per_page

    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, username, content, DATE_FORMAT(comment_time, '%Y-%m-%d %H:%i') AS comment_time
                FROM comments
                WHERE view_point = 1
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (comments_per_page, offset))
            comments = cursor.fetchall()

            # 전체 댓글 개수를 가져와서 총 페이지 수 계산
            cursor.execute("SELECT COUNT(*) AS total_comments FROM comments")
            total_comments = cursor.fetchone()['total_comments']
            total_pages = (total_comments // comments_per_page) + (1 if total_comments % comments_per_page > 0 else 0)

            return jsonify({
                "comments": comments,
                "total_pages": total_pages
            })
    except Error as e:
        print("Error while connecting to MariaDB", e)
        return jsonify({"error": "Database connection error"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

#글내용 불러오기
@app.route('/read/<int:board_no>', methods=['GET'])
def read(board_no):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            query = "SELECT title, writer, content, DATE_FORMAT(board_time, '%Y/%m/%d') AS board_time FROM board WHERE board_no = %s"
            cursor.execute(query, (board_no,))
            post = cursor.fetchone()
            if post:
                return render_template('read.html', post=post)
            else:
                flash('해당 게시글을 찾을 수 없습니다.', 'danger')
                return redirect('/board')
    except Error as e:
        print(f"Error while connecting to MariaDB: {e}")
        flash('데이터베이스 연결 오류가 발생했습니다.', 'danger')
        return redirect('/board')
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
# 로그인 처리
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 비밀번호 해싱
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        connection = None
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='ongsjongs',
                password='1234',
                database='test'
            )
            if connection.is_connected():
                cursor = connection.cursor(dictionary=True)
                query = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, hashed_password))
                user = cursor.fetchone()

                if user:
                    session.permanent = True  # 세션 지속 시간 설정
                    session['username'] = user['username']
                    
                    return redirect('/')
                else:
                    flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
        except Error as e:
            print(f"Error while connecting to MariaDB: {e}")
            flash('로그인 중 문제가 발생했습니다.', 'danger')
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    return render_template('login.html')

# 로그아웃 처리
@app.route('/logout')
def logout():
    session.pop('username', None)
    
    return redirect('/')

#댓글삭제 처리
@app.route('/delete', methods=['POST'])
def delete_comment():
    comment_id = request.form.get('comment_id')  # 댓글 ID를 POST 요청으로 받음
    print(f"Received comment_id: {comment_id}")  # 로그 추가
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            # view_point를 0으로 변경
            query = "UPDATE comments SET view_point = 0 WHERE id = %s"
            cursor.execute(query, (comment_id,))
            connection.commit()
            return jsonify({'success': True, 'message': '댓글이 비활성화되었습니다.'})
    except Error as e:
        print(f"Error while connecting to MariaDB: {e}")
        return jsonify({'success': False, 'message': '댓글 비활성화에 실패했습니다.'}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# 게시글 삭제 처리 (view_point 변경)
@app.route('/boarddelete', methods=['POST'])
def delete_board():
    board_no = request.form.get('board_no')  # 게시글 번호를 POST 요청으로 받음
    print(f"Received board_no: {board_no}")  # 디버그용 로그
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='ongsjongs',
            password='1234',
            database='test'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            # view_point를 0으로 변경
            query = "UPDATE board SET view_point = 0 WHERE board_no = %s"
            cursor.execute(query, (board_no,))
            connection.commit()
            return jsonify({'success': True, 'message': '게시글이 비활성화되었습니다.'})
    except Error as e:
        print(f"Error while connecting to MariaDB: {e}")
        return jsonify({'success': False, 'message': '게시글 비활성화에 실패했습니다.'}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=4500, debug=True)