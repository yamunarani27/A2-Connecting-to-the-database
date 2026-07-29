import sqlite3
from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
from typing import Optional

app=FastAPI()

class Item(BaseModel):
    title:str
    done:bool = False

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

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

@app.post("/tasks",status_code=status.HTTP_201_CREATED)
def create_task(item:Item):


    if not item.title or not item.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,detail={"error":"Missing title"}
        )
    connection=connect_database()
    cursor=connection.cursor()
    cursor.execute("INSERT INTO tasks (title,done) VALUES (?,?)",(item.title.strip(),False))
    new_id=cursor.lastrowid
    connection.commit()
    connection.close()
      
    return  {"id": new_id,"title": item.title.strip(),"done": False}

@app.put("/tasks/{task_id}")
def update_task(task_id:int,item:ItemUpdate):

    if item.title is None and item.done is None:
            raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,  
             detail={"error":"Empty request body"} 
            )
    
    connection=connect_database()
    cursor=connection.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id=?",(task_id,))
    existing=cursor.fetchone()
    if existing is None:
            connection.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail={"error":f"Task {task_id} not found"})

    if item.title is not None:
        if not item.title.strip():
            connection.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Title cannot be empty"}
            )
        cursor.execute("UPDATE tasks SET title=? WHERE id=?",(item.title.strip(),task_id))

    if item.done is not None:
        cursor.execute("UPDATE tasks SET done=? WHERE id=?",(item.done,task_id))

    connection.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_task = cursor.fetchone()

    connection.close()

    return  dict(updated_task)

@app.delete("/tasks/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id:int):
    connection=connect_database()
    cursor=connection.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id=?",(task_id,))
    existing=cursor.fetchone()
    if existing is None:
        connection.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail={"error":f"Task {task_id} not found."})

    cursor.execute("DELETE FROM tasks WHERE id=?",(task_id,))

    connection.commit()
    connection.close()

