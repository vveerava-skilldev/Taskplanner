import streamlit as st
import json
import os

# --- Data Layer ---
class Task:
    def __init__(self, name, duration, completed=False):
        self.name = name
        self.duration = duration
        self.completed = completed

    def to_dict(self):
        return {"name": self.name, "duration": self.duration, "completed": self.completed}

class Planner:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks = self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                data = json.load(f)
                return [Task(**t) for t in data]
        return []

    def save_tasks(self):
        with open(self.filename, "w") as f:
            json.dump([t.to_dict() for t in self.tasks], f)

    def add_task(self, name, duration):
        self.tasks.append(Task(name, duration))
        self.save_tasks()

    def delete_task(self, index):
        self.tasks.pop(index)
        self.save_tasks()

    def toggle_task(self, index):
        self.tasks[index].completed = not self.tasks[index].completed
        self.save_tasks()

# --- UI Layer (Streamlit) ---
def main():
    st.set_page_config(page_title="Pro Task Planner", layout="centered")
    st.title("🚀 Personal Task Planner")
    
    planner = Planner()

    # --- Sidebar: Add New Task ---
    st.sidebar.header("Add New Task")
    with st.sidebar.form("task_form", clear_on_submit=True):
        new_name = st.text_input("Task Name")
        new_duration = st.number_input("Duration (Hours)", min_value=0.1, step=0.5)
        submit = st.form_submit_button("Add Task")
        
        if submit and new_name:
            planner.add_task(new_name, new_duration)
            st.rerun()

    # --- Progress Calculation ---
    total_duration = sum(t.duration for t in planner.tasks)
    completed_duration = sum(t.duration for t in planner.tasks if t.completed)
    
    if total_duration > 0:
        progress_percentage = (completed_duration / total_duration)
    else:
        progress_percentage = 0.0

    # --- Header Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tasks", len(planner.tasks))
    col2.metric("Total Hours", f"{total_duration}h")
    col3.metric("Progress", f"{progress_percentage*100:.1f}%")

    st.progress(progress_percentage)

    # --- Task List ---
    st.subheader("Your Tasks")
    if not planner.tasks:
        st.info("No tasks added yet. Use the sidebar to start!")
    else:
        for idx, task in enumerate(planner.tasks):
            col_check, col_name, col_dur, col_del = st.columns([1, 4, 2, 1])
            
            # Toggle Completion
            is_done = col_check.checkbox("Done", value=task.completed, key=f"check_{idx}")
            if is_done != task.completed:
                planner.toggle_task(idx)
                st.rerun()

            # Display Details
            status_style = "~~" if task.completed else ""
            col_name.write(f"{status_style}{task.name}{status_style}")
            col_dur.write(f"⏱ {task.duration}h")

            # Delete Button
            if col_del.button("🗑️", key=f"del_{idx}"):
                planner.delete_task(idx)
                st.rerun()

if __name__ == "__main__":
    main()
