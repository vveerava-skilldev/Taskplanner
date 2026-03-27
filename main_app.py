import streamlit as st
import json
import os
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.express as px

# --- Data Layer ---
class Task:
    def __init__(self, id, name, duration_mins, priority="Medium", progress=0, 
                 remarks="", date=None, start_time="09:00", dependencies=None, history=None):
        self.id = id
        self.name = name
        self.duration_mins = duration_mins
        self.priority = priority
        self.progress = progress
        self.remarks = remarks
        self.date = date or str(datetime.now().date())
        self.start_time = start_time
        self.dependencies = dependencies or []
        self.history = history or [f"🚀 Task initialized on {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    def to_dict(self):
        return self.__dict__

class Planner:
    def __init__(self, filename="tasks_v5.json"):
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

# --- Logic Helpers ---
def get_time_range(task):
    start = datetime.strptime(f"{task.date} {task.start_time}", "%Y-%m-%d %H:%M")
    end = start + timedelta(minutes=task.duration_mins)
    return start, end

def detect_conflicts(tasks):
    conflicts = []
    sorted_tasks = sorted(tasks, key=lambda x: get_time_range(x)[0])
    for i in range(len(sorted_tasks)):
        for j in range(i + 1, len(sorted_tasks)):
            s1, e1 = get_time_range(sorted_tasks[i])
            s2, e2 = get_time_range(sorted_tasks[j])
            if s1 < e2 and s2 < e1:  # Overlap logic
                conflicts.append((sorted_tasks[i].name, sorted_tasks[j].name))
    return conflicts

def format_time(mins):
    h, m = divmod(mins, 60)
    return f"{int(h)}h {int(m)}m" if h > 0 else f"{int(m)}m"

# --- Page: Tasks ---
def task_page(planner):
    st.header("📋 Project Command Center")
    
    # Global Conflict Warning
    conflicts = detect_conflicts(planner.tasks)
    if conflicts:
        for c1, c2 in conflicts:
            st.error(f"⚠️ **Schedule Conflict:** '{c1}' overlaps with '{c2}'")

    with st.expander("➕ Create New Mission", expanded=False):
        with st.form("task_form", clear_on_submit=True):
            name = st.text_input("Task Title")
            c1, c2, c3 = st.columns(3)
            date_val = c1.date_input("Date")
            start_val = c2.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            prio = c3.selectbox("Priority", ["🔥 High", "⚡ Medium", "🧊 Low"], index=1)
            
            c4, c5, c6 = st.columns(3)
            h = c4.number_input("Hours", 0, 24, 0)
            m = c5.number_input("Mins", 0, 59, 30)
            deps = c6.multiselect("Dependencies", [t.name for t in planner.tasks])
            
            remarks = st.text_area("Initial Remarks")
            
            if st.form_submit_button("Launch Task"):
                if name:
                    new_id = str(int(time.time()))
                    new_task = Task(new_id, name, (h*60)+m, prio, 
                                    date=str(date_val), 
                                    start_time=start_val.strftime("%H:%M"),
                                    dependencies=deps, remarks=remarks)
                    planner.tasks.append(new_task)
                    planner.save_tasks()
                    st.rerun()

    for idx, task in enumerate(planner.tasks):
        with st.container(border=True):
            head1, head2 = st.columns([3, 1])
            new_title = head1.text_input("Task Name", task.name, key=f"t_{task.id}")
            if new_title != task.name:
                task.history.append(f"✏️ Renamed from '{task.name}' to '{new_title}'")
                task.name = new_title
                planner.save_tasks()

            prog = head2.select_slider("Progress", options=[0, 25, 50, 75, 100], value=task.progress, key=f"p_{task.id}")
            if prog != task.progress:
                task.history.append(f"📈 Progress set to {prog}%")
                task.progress = prog
                planner.save_tasks()
                if prog == 100: st.balloons()

            d1, d2, d3, d4 = st.columns(4)
            d1.caption(f"📅 {task.date}")
            start, end = get_time_range(task)
            d2.caption(f"⏱️ {start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
            d3.caption(f"🎯 {task.priority}")
            d4.caption(f"🔗 {len(task.dependencies)} Dependencies")

            r1, r2 = st.columns([2, 1])
            new_rem = r1.text_input("Remarks", task.remarks, key=f"r_{task.id}")
            if new_rem != task.remarks:
                task.remarks = new_rem
                planner.save_tasks()
            
            with r2.expander("📜 Activity Log"):
                for entry in reversed(task.history):
                    st.caption(entry)

            if st.button("🗑️ Remove", key=f"del_{task.id}"):
                planner.tasks.pop(idx)
                planner.save_tasks()
                st.rerun()

# --- Page: Timeline & Narrative ---
def timeline_page(planner):
    st.header("⏳ Gantt Chart & Analysis")
    if not planner.tasks:
        st.info("No active missions.")
        return

    data = []
    for t in planner.tasks:
        s, e = get_time_range(t)
        data.append(dict(Task=t.name, Start=s, Finish=e, Priority=t.priority, Completion=t.progress))

    df = pd.DataFrame(data)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Priority", 
                      range_x=[df['Start'].min() - timedelta(hours=1), df['Finish'].max() + timedelta(hours=1)])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

    # Smart Narrative
    st.subheader("📝 Workflow Analysis")
    total_m = sum(t.duration_mins for t in planner.tasks)
    eff_m = sum(t.duration_mins * (t.progress/100) for t in planner.tasks)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total Load:** {format_time(total_m)}")
        st.write(f"**Actual Completion:** {format_time(int(eff_m))}")
        st.write(f"**Tasks Remaining:** {len([t for t in planner.tasks if t.progress < 100])}")
    with col2:
        conflicts = detect_conflicts(planner.tasks)
        if conflicts:
            st.error(f"Critical Planning Error: You have {len(conflicts)} overlapping time slots. Reschedule one to maintain quality.")
        else:
            st.success("Your schedule is mathematically sound. No overlaps detected.")

# --- Page: Insights ---
def insights_page(planner):
    st.header("✨ Performance Analytics")
    if not planner.tasks: return
    
    avg = sum(t.progress for t in planner.tasks) / len(planner.tasks)
    st.write(f"### Project Health: {avg:.0f}%")
    st.progress(avg/100)

    if avg >= 50: st.snow()
    
    # Priority breakdown
    df = pd.DataFrame([t.to_dict() for t in planner.tasks])
    st.write("#### Completion by Priority")
    st.bar_chart(df.groupby('priority')['progress'].mean())

# --- Main Navigation ---
def main():
    st.set_page_config(page_title="Ultra Planner Pro", layout="wide")
    planner = Planner()

    st.sidebar.title("💎 Elite Planner")
    page = st.sidebar.selectbox("Navigate To", ["Task Manager", "Visual Timeline", "Insights"])
    
    st.sidebar.divider()
    if planner.tasks:
        done = sum(1 for t in planner.tasks if t.progress == 100)
        st.sidebar.metric("Tasks Completed", f"{done}/{len(planner.tasks)}")

    if page == "Task Manager": task_page(planner)
    elif page == "Visual Timeline": timeline_page(planner)
    else: insights_page(planner)

if __name__ == "__main__":
    main()
