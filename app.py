from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'tasks.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due_date TEXT,
            category TEXT DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Sample data
    c.execute('SELECT COUNT(*) FROM tasks')
    if c.fetchone()[0] == 0:
        samples = [
            ('Design landing page', 'Create mockups and finalize color scheme', 'high', 'in-progress', '2026-04-25', 'Design'),
            ('Set up database schema', 'Define tables and relationships for project', 'high', 'completed', '2026-04-20', 'Backend'),
            ('Write unit tests', 'Cover all API endpoints with tests', 'medium', 'pending', '2026-04-28', 'Testing'),
            ('Update documentation', 'Revise README and API docs', 'low', 'pending', '2026-05-01', 'Docs'),
            ('Deploy to production', 'Push latest build to server', 'high', 'pending', '2026-04-30', 'DevOps'),
        ]
        c.executemany(
            'INSERT INTO tasks (title, description, priority, status, due_date, category) VALUES (?,?,?,?,?,?)',
            samples
        )
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db()
    filter_status = request.args.get('status', 'all')
    filter_priority = request.args.get('priority', 'all')

    query = 'SELECT * FROM tasks WHERE 1=1'
    params = []
    if filter_status != 'all':
        query += ' AND status = ?'
        params.append(filter_status)
    if filter_priority != 'all':
        query += ' AND priority = ?'
        params.append(filter_priority)
    query += ' ORDER BY created_at DESC'

    tasks = conn.execute(query, params).fetchall()

    # Stats
    total = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='in-progress'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
    conn.close()

    return render_template('index.html', tasks=tasks, total=total,
                           completed=completed, in_progress=in_progress,
                           pending=pending, filter_status=filter_status,
                           filter_priority=filter_priority)


@app.route('/add', methods=['POST'])
def add_task():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'medium')
    due_date = request.form.get('due_date', '')
    category = request.form.get('category', 'General').strip()

    if title:
        conn = get_db()
        conn.execute(
            'INSERT INTO tasks (title, description, priority, due_date, category) VALUES (?,?,?,?,?)',
            (title, description, priority, due_date, category)
        )
        conn.commit()
        conn.close()
    return redirect(url_for('index'))


@app.route('/update_status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    status = request.form.get('status')
    conn = get_db()
    conn.execute('UPDATE tasks SET status=? WHERE id=?', (status, task_id))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('index'))


@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        due_date = request.form.get('due_date', '')
        category = request.form.get('category', 'General').strip()
        status = request.form.get('status', 'pending')
        conn.execute(
            'UPDATE tasks SET title=?, description=?, priority=?, due_date=?, category=?, status=? WHERE id=?',
            (title, description, priority, due_date, category, status, task_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    task = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
    conn.close()
    return render_template('edit.html', task=task)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
