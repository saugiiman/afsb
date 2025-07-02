from flask import Flask, request, redirect, render_template_string, session, url_for
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "supersecretkey"
os.makedirs("confessions", exist_ok=True)

# Bootstrap UI wrapper
def render_ui(title, content):
    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>{title}</title>
        <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
        <style>
            body {{
                background: linear-gradient(to right, #000000, #1a1a1a);
                color: #fff;
                font-family: 'Arial', sans-serif;
                padding: 2rem;
            }}
            .container {{
                max-width: 700px;
                margin: auto;
                background-color: #111;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 0 10px #0f0;
            }}
            input, textarea {{ background: #222; color: #0f0; border: 1px solid #0f0; }}
            img.profile-pic {{ border-radius: 50%; width: 100px; height: 100px; object-fit: cover; margin-bottom: 10px; }}
            .nav-tabs .nav-link.active {{ background-color: #0f0; color: #000; }}
            .nav-tabs .nav-link {{ color: #0f0; }}
        </style>
    </head>
    <body>
        <div class='container'>
            {content}
        </div>
    </body>
    </html>
    """)

# Get profile picture and bio
INSTAGRAM_CACHE = {}
def fetch_ig_data(username):
    if username in INSTAGRAM_CACHE:
        return INSTAGRAM_CACHE[username]
    url = f"https://www.instagram.com/{username}/"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        data = r.text.split('"profile_pic_url_hd":"')[1].split('"')[0].replace("\\u0026", "&")
        desc = soup.find("meta", {"name": "description"})["content"]
        bio = desc.split("•")[-1].strip() if "•" in desc else desc
        info = {"pic": data, "bio": bio}
        INSTAGRAM_CACHE[username] = info
        return info
    except:
        return {"pic": "", "bio": ""}

@app.route('/')
def home():
    msg = request.args.get("link")
    return render_ui("NGL Clone | Confess Now", f'''
        <h2 class="text-center">🕵️‍♂️ Anonymous Confession</h2>
        <form action="/u" method="get" class="mt-4">
            <input name="username" class="form-control mb-3" placeholder="Enter username (e.g. insta handle)" required>
            <button type="submit" class="btn btn-success w-100">Get Confession Link</button>
        </form>
        {'<div class="alert alert-info mt-3">🔗 Share your confession link: <code>' + msg + '</code></div>' if msg else ''}
        <div class="text-center mt-4">
            <a href="/user/login" class="btn btn-outline-light">Already have an account? Login</a>
        </div>
    ''')

@app.route('/u')
def redirect_to_user():
    username = request.args.get("username")
    return redirect(f"/?link=/u/{username}") if username else "Username missing", 400

@app.route('/u/<username>', methods=['GET', 'POST'])
def confess(username):
    filepath = f"confessions/{username}.txt"
    if request.method == "POST":
        msg = request.form.get("message")
        if msg:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(msg.strip() + "\n")
            return redirect(f"/u/{username}?sent=1")
    sent = request.args.get("sent")
    info = fetch_ig_data(username)
    return render_ui(f"Confess to {username}", f'''
        <div class='text-center'>
            <img src="{info['pic']}" class="profile-pic"><br>
            <strong>@{username}</strong><br><small>{info['bio']}</small>
        </div>
        <hr>
        <h5>Send an anonymous message</h5>
        {"<div class='alert alert-success'>✅ Message sent!</div>" if sent else ""}
        <form method="post" class="mt-3">
            <textarea name="message" class="form-control mb-3" rows="4" required></textarea>
            <button type="submit" class="btn btn-success w-100">Send</button>
        </form>
    ''')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        session['user'] = username
        return redirect('/dashboard')
    return render_ui("User Login", '''
        <h3 class="text-center">Login with Username</h3>
        <form method="post">
            <input name="username" class="form-control mb-3" placeholder="Your Instagram username" required>
            <button class="btn btn-success w-100">Login</button>
        </form>
    ''')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    username = session.get('user')
    if not username:
        return redirect('/user/login')
    filepath = f"confessions/{username}.txt"
    replypath = f"confessions/{username}_replies.txt"

    # Save reply
    if request.method == "POST":
        idx = int(request.form.get("index"))
        reply = request.form.get("reply")
        if reply:
            with open(replypath, "a", encoding="utf-8") as f:
                f.write(f"{idx}:{reply.strip()}\n")

    messages = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            messages = [msg.strip() for msg in f.readlines()]

    replies = {}
    if os.path.exists(replypath):
        with open(replypath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(":", 1)
                if len(parts) == 2:
                    replies[int(parts[0])] = parts[1]

    info = fetch_ig_data(username)
    msg_html = ""
    for i, msg in enumerate(messages):
        msg_html += f"""
        <div class='card bg-dark text-light mb-3'>
            <div class='card-body'>
                <p>{msg}</p>
                {f'<div class="mt-2"><strong>Reply:</strong> {replies[i]}</div>' if i in replies else f'''
                <form method='post'>
                    <input type='hidden' name='index' value='{i}'>
                    <input name='reply' placeholder='Your reply' class='form-control form-control-sm mb-2'>
                    <button class='btn btn-sm btn-outline-success'>Reply</button>
                </form>'''}
            </div>
        </div>
        """

    return render_ui("Your Confessions", f'''
        <div class='text-center'>
            <img src="{info['pic']}" class="profile-pic"><br>
            <strong>@{username}</strong><br><small>{info['bio']}</small>
        </div>
        <ul class="nav nav-tabs mt-4" id="myTab" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" id="messages-tab" data-bs-toggle="tab" data-bs-target="#messages" type="button" role="tab">📥 Messages</button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" id="share-tab" data-bs-toggle="tab" data-bs-target="#share" type="button" role="tab">🔗 Share</button>
          </li>
        </ul>
        <div class="tab-content mt-3">
          <div class="tab-pane fade show active" id="messages" role="tabpanel">
            {msg_html if messages else '<p>No messages yet.</p>'}
          </div>
          <div class="tab-pane fade" id="share" role="tabpanel">
            <p>🔗 Your confession link:</p>
            <input class="form-control mb-3" value="/u/{username}" readonly onclick="this.select()">
            <a href="https://www.instagram.com/direct/inbox/" target="_blank" class="btn btn-success w-100">Share on Instagram</a>
          </div>
        </div>
        <a href="/logout" class="btn btn-outline-light btn-sm mt-4">Logout</a>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    ''')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
