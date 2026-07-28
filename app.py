import sqlite3
from fastapi import FastAPI,HTTPException

app=FastAPI()


def init_db():
    connection=sqlite3.connect("tasks.db") #create a db
    cursor=connection.cursor()
    # create a table
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,done BOOL DEFAULT 0)"
    )

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count= cursor.fetchone()[0]
    #insert seed data if table is empty
    if count == 0:
        example_tasks=[
            ("Buy groceries",True),
            ("Finish the assignment",False),
            ("Clean the room",False)
        ]
        cursor.executemany("INSERT INTO tasks (title,done) VALUES (?,?)",example_tasks)
        print("Initial data seeded")

    connection.commit()
    connection.close()

#execute everytime app starts
@app.on_event("startup")
def on_startup():
    init_db()

def connect_database():
    connection=sqlite3.connect("tasks.db")
    connection.row_factory=sqlite3.Row
    return connection

@app.get("/tasks")
def read_task():
    connection=connect_database()
    cursor=connection.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows=cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]

@app.get("/tasks/{task_id}")
def read_one_task(task_id:int):
    connection=connect_database()
    cursor=connection.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id=?",(task_id,))
    row=cursor.fetchone()
    connection.close()

    if row is None:
        raise HTTPException(status_code=404,detail="Task not found")
    
    return dict(row)