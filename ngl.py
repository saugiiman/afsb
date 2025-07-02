from flask import Flask, request, redirect, render_template_string, session, url_for
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
USERNAME = "saugiiman"
PASSWORD = "saugiiman04"
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
                max-width: 600px;
                margin: auto;
                background-color: #111;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 0 10px #0f0;
            }}
            input, textarea {{ background: #222; color: #0f0; border: 1px solid #0f0; }}
        </style>
    </head>
    <body>
        <div class='container'>
            {content}
        </div>
    </body>
    </html>
    """)

@app.route('/')
def home():
    return render_ui("Get Confession Link", '''
        <h2 class="text-center">🔐 PyNGL Confessions</h2>
        <form action="/u" method="get" class="mt-4">
            <input name="username" class="form-control mb-3" placeholder="Enter your username" required>
            <button type="submit" class="btn btn-success w-100">Get My Link</button>
        </form>
    ''')

@app.route('/u')
def redirect_to_user():
    username = request.args.get("username")
    return redirect(f"/u/{username}") if username else "Username missing", 400

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
    return render_ui(f"Confess to {username}", f'''
        <h4>Send anonymous message to <span class="text-success">{username}</span></h4>
        {"<div class='alert alert-success'>✅ Message sent!</div>" if sent else ""}
        <form method="post" class="mt-3">
            <textarea name="message" class="form-control mb-3" rows="4" required></textarea>
            <button type="submit" class="btn btn-success w-100">Send</button>
        </form>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        uname = request.form.get("username")
        pwd = request.form.get("password")
        if uname == USERNAME and pwd == PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid credentials"
    return render_ui("Login", f'''
        <h3 class="text-center">Admin Login</h3>
        {f"<div class='alert alert-danger'>{error}</div>" if error else ""}
        <form method="post">
            <input name="username" placeholder="Username" class="form-control mb-2" required>
            <input name="password" type="password" placeholder="Password" class="form-control mb-3" required>
            <button class="btn btn-success w-100">Login</button>
        </form>
    ''')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))

    users = os.listdir("confessions")
    links = "".join(f"<li><a href='/admin/{u.replace('.txt','')}' class='text-success'>{u.replace('.txt','')}</a></li>" for u in users)
    return render_ui("Admin Dashboard", f'''
        <h3>Admin Panel</h3>
        <ul>{links}</ul>
        <a href="/logout" class="btn btn-outline-light btn-sm mt-3">Logout</a>
    ''')

@app.route('/admin/<username>')
def view_user_msgs(username):
    if not session.get('admin'):
        return redirect(url_for('login'))

    path = f"confessions/{username}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            messages = f.readlines()
    else:
        messages = []

    return render_ui(f"Messages for {username}", f'''
        <h4>Messages for {username}</h4>
        {'<ul class="list-group">' + ''.join(f'<li class="list-group-item bg-dark text-success">{msg.strip()}</li>' for msg in messages) + '</ul>' if messages else '<p>No messages yet.</p>'}
        <a href="/admin" class="btn btn-outline-light btn-sm mt-3">Back to Admin</a>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

