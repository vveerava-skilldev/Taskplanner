import streamlit as st
import json
import os
import pandas as pd
import time

# --- Data Layer ---
class Task:
    def __init__(self, name, duration_mins, priority="Medium", completed=False):
        self.name = name
        self.duration_mins = duration_mins 
        self.priority = priority
        self.completed = completed

    def to_dict(self):
        return {"name": self.name, "duration_mins": self.duration_mins, "priority": self.priority, "completed": self.completed}

class Planner:
    def __init__(self, filename="tasks_v3.json"):
        self.filename = filename
        self.tasks = self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                return [Task(**t) for t in json.load(f)]
        return []

    def save_tasks(self):
        with open(self.filename, "w") as f:
            json.dump([t.to_dict() for t in self.tasks], f)

# --- UI Components ---
def format_time(mins):
    h, m = divmod(mins, 60)
    return f"{int(h)}h {int(m)}m" if h > 0 else f"{int(m)}m"

# --- Page: Tasks ---
def task_page(planner):
    st.header("📋 Task Management")
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("task_form", clear_on_submit=True):
            name = st.text_input("Task Name")
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("Hours", 0, 24, 0)
            m = c2.number_input("Mins", 0, 59, 30)
            prio = c3.selectbox("Priority", ["🔥 High", "⚡ Medium", "🧊 Low"], index=1)
            if st.form_submit_button("Add Task") and name:
                planner.tasks.append(Task(name, (h*60)+m, prio))
                planner.save_tasks()
                st.rerun()

    for idx, task in enumerate(planner.tasks):
        with st.container(border=True):
            cols = st.columns([0.5, 4, 2, 0.5])
            if cols[0].checkbox("", value=task.completed, key=f"chk_{idx}"):
                task.completed = True; planner.save_tasks()
            
            st_text = "~~" if task.completed else ""
            cols[1].markdown(f"**{st_text}{task.name}{st_text}**")
            cols[2].caption(f"{task.priority} | {format_time(task.duration_mins)}")
            if cols[3].button("🗑️", key=f"del_{idx}"):
                planner.tasks.pop(idx); planner.save_tasks(); st.rerun()

# --- Page: Insights ---
def insights_page(planner):
    st.header("📊 Performance Insights")
    if not planner.tasks:
        st.info("Add tasks to see data.")
        return
    
    done = sum(1 for t in planner.tasks if t.completed)
    total = len(planner.tasks)
    
    c1, c2 = st.columns(2)
    c1.metric("Completion Rate", f"{(done/total)*100:.0f}%")
    c2.metric("Pending Tasks", total - done)
    
    df = pd.DataFrame([t.to_dict() for t in planner.tasks])
    st.subheader("Workload by Priority")
    st.bar_chart(df['priority'].value_counts())

# --- Page: Strategy & Pomodoro ---
def strategy_page(planner):
    st.header("💡 Focus & Strategy")
    
    # Pomodoro Section
    st.subheader("⏱️ Pomodoro Timer")
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        if 'timer_running' not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.time_left = 25 * 60

        placeholder = st.empty()
        
        # Display time
        mins, secs = divmod(st.session_state.time_left, 60)
        placeholder.markdown(f"<h1 style='text-align: center; font-size: 70px;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)

        bc1, bc2, bc3 = st.columns(3)
        if bc1.button("▶️ Start"): st.session_state.timer_running = True
        if bc2.button("⏸️ Pause"): st.session_state.timer_running = False
        if bc3.button("🔄 Reset"): 
            st.session_state.timer_running = False
            st.session_state.time_left = 25 * 60
            st.rerun()

    with col_t2:
        st.info("Strategy: Work for 25 mins, then take a 5-min break.")
        high_prio = [t.name for t in planner.tasks if t.priority == "🔥 High" and not t.completed]
        if high_prio:
            st.warning(f"**Target:** {high_prio[0]}")

    # Logic for timer (only runs when 'Start' is clicked)
    if st.session_state.timer_running and st.session_state.time_left > 0:
        time.sleep(1)
        st.session_state.time_left -= 1
        st.rerun()
    elif st.session_state.time_left == 0:
        st.balloons()
        st.success("Session Complete! Take a break.")
        st.session_state.timer_running = False

    st.divider()
    st.markdown("### 🚀 Execution Tips")
    st.write("1. **Batching:** Group small 'Medium' tasks together.")
    st.write("2. **Focus:** Close your browser tabs except for this planner.")

# --- Main ---
def main():
    st.set_page_config(page_title="Elite Planner", layout="wide")
    planner = Planner()

    st.sidebar.title("🎯 Menu")
    page = st.sidebar.radio("Navigate", ["Tasks", "Insights", "Strategy"])
    
    # Progress Bar in Sidebar
    if planner.tasks:
        prog = sum(1 for t in planner.tasks if t.completed) / len(planner.tasks)
        st.sidebar.write(f"Progress: {prog*100:.0f}%")
        st.sidebar.progress(prog)

    if page == "Tasks": task_page(planner)
    elif page == "Insights": insights_page(planner)
    else: strategy_page(planner)

if __name__ == "__main__":
    main()
