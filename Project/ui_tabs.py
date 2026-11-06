# GUI tabs: login, teacher lists, grades, attendance, student view
from __future__ import annotations
import hashlib
from collections.abc import Callable
from tkinter import messagebox
import customtkinter as ctk
from database import call_proc
from ui_core import (
    ERROR, GREY_D, GREY_L, PINK, PINK_L, ROSE, TEXT, WHITE,
    AttendanceForm, CourseForm, GradeForm, StudentForm, TeacherForm,
    create_table, make_entry, make_label, set_msg_error, styled_button,
)
from utils import bubble_sort, linear_search

# same style for combo boxes and search boxes
COMBO_STYLE = dict(fg_color=WHITE, border_color=PINK, text_color=TEXT)
SEARCH_ENTRY_STYLE = dict(
    width=200,
    fg_color=WHITE,
    border_color=PINK,
    text_color=TEXT,
    font=("Segoe UI", 11),
    corner_radius=6,
)
TABVIEW_STYLE = dict(
    fg_color=WHITE,
    segmented_button_fg_color=PINK_L,
    segmented_button_selected_color=PINK,
    segmented_button_selected_hover_color=ROSE,
    segmented_button_unselected_color=PINK_L,
    text_color=TEXT,
    text_color_disabled=GREY_D,
)


# This function sets the column headings and widths on the table
def set_column_widths(tv, cols, widths):
    for c, w in zip(cols, widths):
        tv.heading(c, text=c)
        tv.column(c, width=w, anchor="center")


def _fill_tv(tv, rows, values_fn: Callable):
    tv.delete(*tv.get_children())
    for r in rows:
        tv.insert("", "end", values=values_fn(r))


def _sort_str(key: str, rev: bool = False):
    return (lambda r, k=key: (r[k] or "").lower() if isinstance(r.get(k), str) else str(r[k] or ""), rev)


def _sort_id(key: str, rev: bool = False):
    return (lambda r, k=key: r[k], rev)


def _sort_date(key: str, rev: bool = False):
    return (lambda r, k=key: str(r.get(k, "")), rev)


def _name_part_sort(part: int, rev: bool = False):
    def key(r):
        parts = r["student_name"].split()
        return (parts[part] if part < len(parts) else "").lower()

    return (key, rev)


def _add_search(parent, callback) -> ctk.StringVar:
    var = ctk.StringVar()
    se = ctk.CTkEntry(parent, textvariable=var, placeholder_text="🔍 Search…", **SEARCH_ENTRY_STYLE)
    se.pack(side="left", padx=4)
    se.bind("<KeyRelease>", lambda _: callback())
    return var


def _grade_display(r) -> tuple:
    g = r["grade"]
    return (
        r["student_name"],
        r["group_name"],
        r["course_name"],
        r["course_code"],
        f"{g}%" if g is not None else "—",
        r["letter_grade"] or "—",
        str(r["graded_at"])[:10] if r["graded_at"] else "—",
    )


# login popup that calls on_success(user) when password is correct
class LoginWindow(ctk.CTkToplevel):

    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("School Management System – Login")
        self.geometry("420x500")
        self.resizable(False, False)
        self.configure(fg_color=PINK_L)
        self.build_ui()
        self.grab_set()

    def build_ui(self):
        ctk.CTkLabel(self, text="🎓 School Management", font=("Segoe UI", 22, "bold"), text_color=ROSE).pack(pady=(40, 4))
        ctk.CTkLabel(self, text="School database by Tomiris Kussanova", font=("Segoe UI", 12), text_color=GREY_D).pack(pady=(0, 30))
        box = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=16)
        box.pack(padx=40, fill="x")
        make_label(box, "Username", bold=True).pack(anchor="w", padx=20, pady=(20, 2))
        self.usr = make_entry(box, "Enter username", width=330)
        self.usr.pack(padx=20, pady=(0, 12))
        make_label(box, "Password", bold=True).pack(anchor="w", padx=20, pady=(0, 2))
        self.pwd = make_entry(box, "Enter password", width=330, show="•")
        self.pwd.pack(padx=20, pady=(0, 12))
        self.msg = make_label(box, "", color=ERROR)
        self.msg.pack(pady=(0, 6))
        styled_button(box, "Login", self.try_login, width=330).pack(padx=20, pady=(0, 20))
        hint = ctk.CTkFrame(self, fg_color="transparent")
        hint.pack(pady=16)
        make_label(hint, "Demo → Teacher: Tony_Stark / tstark123", size=10, color=GREY_D).pack()
        make_label(hint, "Demo → Student: Harry_Potter / hpotter123", size=10, color=GREY_D).pack()

    def try_login(self):
        u, p = self.usr.get().strip(), self.pwd.get()
        if not u or not p:
            return set_msg_error(self.msg, "Please fill in all fields.")
        try:
            # password hashed with SHA256 for database check
            rows = call_proc("sp_authenticate", (u, hashlib.sha256(p.encode()).hexdigest()))
        except Exception:
            return set_msg_error(self.msg, "Login failed. Check database connection.")
        if not rows:
            return set_msg_error(self.msg, "Invalid username or password.")
        self.on_success(rows[0])
        self.destroy()


# This is the teacher view for attendance. It can list existing marks, filter, search, whatever and sort them.
class AttendanceTab(ctk.CTkFrame):
    _COLS = ("ID", "Student", "Group", "Course", "Code", "Date", "Status")
    _WIDTHS = (50, 160, 70, 200, 70, 110, 90)
    _SORT_MAP = {
        "ID ↑": _sort_id("attendance_id"),
        "ID ↓": _sort_id("attendance_id", True),
        "Date ↓": _sort_date("att_date", True),
        "Date ↑": _sort_date("att_date"),
        "Student ↑": _sort_str("student_name"),
        "Student ↓": _sort_str("student_name", True),
        "Course ↑": _sort_str("course_name"),
        "Status ↑": _sort_str("status"),
    }
    _NAME_SORT = {
        "First Name ↑": _name_part_sort(0),
        "First Name ↓": _name_part_sort(0, True),
        "Last Name ↑": _name_part_sort(-1),
        "Last Name ↓": _name_part_sort(-1, True),
    }

    def __init__(self, parent):
        super().__init__(parent, fg_color=GREY_L)
        self._data, self._reg_data = [], []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        tb = ctk.CTkFrame(self, fg_color=PINK_L, corner_radius=0)
        tb.pack(fill="x", pady=(0, 8))
        make_label(tb, "Attendance", bold=True, size=14, color=ROSE).pack(side="left", padx=16, pady=10)
        styled_button(tb, "Mark Attendance", self.mark_attendance).pack(side="left", padx=4, pady=8)
        styled_button(tb, "Delete", self.delete_row, bg=ERROR, hover="#C62828").pack(side="left", padx=4)
        sf = ctk.CTkFrame(tb, fg_color="transparent")
        sf.pack(side="right", padx=12)
        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkComboBox(sf, values=["All", "Present", "Absent", "Late"], variable=self.filter_var, width=120, command=lambda _: self.filter_rows(), **COMBO_STYLE).pack(side="left", padx=4)
        self.search_var = _add_search(sf, self.filter_rows)
        self.sort_var = ctk.StringVar(value="ID ↑")
        ctk.CTkComboBox(sf, values=list(self._SORT_MAP), variable=self.sort_var, width=150, command=lambda _: self.sort_rows(), **COMBO_STYLE).pack(side="left", padx=4)
        f, self.tv = create_table(self, self._COLS, height=20)
        set_column_widths(self.tv, self._COLS, self._WIDTHS)
        f.pack(fill="both", expand=True, padx=12, pady=6)

    def refresh(self):
        self._data = call_proc("sp_read_attendance") or []
        self._reg_data = call_proc("sp_read_registrations") or []
        self.filter_rows()

    def show_rows(self, data):
        _fill_tv(self.tv, data, lambda r: (
            r["attendance_id"], r["student_name"], r.get("group_name", ""), r["course_name"],
            r["course_code"], str(r["att_date"]) if r["att_date"] else "", r.get("status", ""),
        ))

    def filter_rows(self):
        st, term = self.filter_var.get(), self.search_var.get().strip()
        data = self._data if st == "All" else [r for r in self._data if r.get("status") == st]
        if term:
            data = linear_search(data, term, ["student_name", "group_name", "course_name", "course_code"])
        fn, rev = self._SORT_MAP.get(self.sort_var.get(), _sort_id("attendance_id"))
        self.show_rows(bubble_sort(data, fn, rev))

    def sort_rows(self):
        self.filter_rows()

    def mark_attendance(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Mark Attendance")
        dlg.geometry("660x520")
        dlg.configure(fg_color=PINK_L)
        dlg.grab_set()
        make_label(dlg, "Mark Attendance", bold=True, size=15, color=ROSE).pack(pady=(18, 4))
        step1 = ctk.CTkFrame(dlg, fg_color=WHITE, corner_radius=10)
        step1.pack(fill="x", padx=20, pady=(0, 8))
        make_label(step1, "Step 1 — Select Course", bold=True, size=12, color=PINK).pack(anchor="w", padx=14, pady=(10, 4))
        seen = {r.get("course_id") or r["course_name"]: r["course_name"] for r in self._reg_data}
        all_c = ["— All Courses —"] + sorted(seen.values())
        course_var = ctk.StringVar(value=all_c[0])
        course_cb = ctk.CTkComboBox(step1, values=all_c, variable=course_var, width=600, font=("Segoe UI", 12), **COMBO_STYLE)
        course_cb.pack(padx=14, pady=(0, 12))
        step2 = ctk.CTkFrame(dlg, fg_color=WHITE, corner_radius=10)
        step2.pack(fill="x", padx=20, pady=(0, 6))
        hdr2 = ctk.CTkFrame(step2, fg_color="transparent")
        hdr2.pack(fill="x", padx=14, pady=(10, 4))
        make_label(hdr2, "Step 2 — Select Student", bold=True, size=12, color=PINK).pack(side="left")
        sort_var = ctk.StringVar(value="First Name ↑")
        cols = ("ID", "First Name", "Last Name", "Group", "Course")
        tbl_f, tv = create_table(step2, cols, height=8)
        set_column_widths(tv, cols, (50, 140, 140, 80, 200))
        tbl_f.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        sort_cb = ctk.CTkComboBox(hdr2, values=list(self._NAME_SORT), variable=sort_var, width=180, font=("Segoe UI", 11), **COMBO_STYLE)
        sort_cb.pack(side="right")

        def _refresh(_=None):
            sel = course_var.get()
            flt = self._reg_data if sel == "— All Courses —" else [r for r in self._reg_data if r["course_name"] == sel]
            fn, rev = self._NAME_SORT.get(sort_var.get(), _name_part_sort(0))
            _fill_tv(tv, bubble_sort(flt, fn, rev), lambda r: (
                (lambda p: (r["registration_id"], p[0], p[1] if len(p) > 1 else "", r.get("group_name", ""), r["course_name"]))(r["student_name"].split(" ", 1))
            ))

        course_cb.configure(command=lambda _: _refresh())
        sort_cb.configure(command=lambda _: _refresh())
        _refresh()

        def pick():
            sel = tv.selection()
            if not sel:
                return messagebox.showwarning("No Selection", "Please select a student row.")
            rid = tv.item(sel[0])["values"][0]
            reg = next((r for r in self._reg_data if r["registration_id"] == rid), None)
            if reg:
                dlg.destroy()
                self._att_form = AttendanceForm(self, self.refresh, reg)

        styled_button(dlg, "✅  Mark Attendance for Selected Student", pick, width=400).pack(pady=10)

    def delete_row(self):
        sel = self.tv.selection()
        if not sel:
            return messagebox.showwarning("No Selection", "Select a row.")
        aid = self.tv.item(sel[0])["values"][0]
        if messagebox.askyesno("Delete", "Remove this attendance record?"):
            call_proc("sp_delete_attendance", (aid,), fetch=False)
            self.refresh()

# Those tables mostly follow the same list pattern. Search with pink toolbar that also allows sorting. Table is fed by call_proc.
# refresh() loads up sp_read_* into self._data.
# show_rows() fills the table with self.row_values(r).
# filter_rows() filters the table based on the search_var.
# sort_rows() sorts the table based on the sort_var.
# get_selected_row() returns the selected row.
# _open_form() opens the form for the selected row.
# open_add() opens the add form.
# open_edit() opens the edit form.
# remove_record() removes the selected row.
# Students, Teachers and Courses only are different in column config, row values and which form/proc they use.
# Registrations drop sort and uses a custom register dialog.
# Attendance and grades are read only.
# MyGradesTab is the student view. It has 3 sub tabs, and each of them are refreshed froim different sp_read_student* calls.

class CRUDTab(ctk.CTkFrame):
    TITLE, COLS, SEARCH_FIELDS, PROC_READ = "", [], [], ""
    SORT_OPTIONS, DEFAULT_SORT, PK_COL_INDEX, PK_FIELD = {}, "", 0, ""
    FORM_CLS = None
    PROC_DELETE = ""
    ADD_LABEL = ""

    def __init__(self, parent, role=""):
        super().__init__(parent, fg_color=GREY_L)
        self.role, self._data = role, []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        tb = ctk.CTkFrame(self, fg_color=PINK_L, corner_radius=0)
        tb.pack(fill="x", pady=(0, 8))
        make_label(tb, self.TITLE, bold=True, size=14, color=ROSE).pack(side="left", padx=16, pady=10)
        if self.role == "teacher":
            self.add_toolbar_buttons(tb)
        sf = ctk.CTkFrame(tb, fg_color="transparent")
        sf.pack(side="right", padx=12)
        self.search_var = _add_search(sf, self.filter_rows)
        if self.SORT_OPTIONS:
            self.sort_var = ctk.StringVar(value=self.DEFAULT_SORT)
            ctk.CTkComboBox(sf, values=list(self.SORT_OPTIONS), variable=self.sort_var, width=180, command=lambda _: self.sort_rows(), **COMBO_STYLE).pack(side="left", padx=4)
        names, widths = [c[0] for c in self.COLS], [c[1] for c in self.COLS]
        f, self.tv = create_table(self, names, height=20)
        set_column_widths(self.tv, names, widths)
        f.pack(fill="both", expand=True, padx=12, pady=6)

    def add_toolbar_buttons(self, tb):
        if not self.FORM_CLS:
            return
        styled_button(tb, self.ADD_LABEL, self.open_add).pack(side="left", padx=4, pady=8)
        styled_button(tb, "Edit", self.open_edit, bg="#7B1FA2", hover="#6A1B9A").pack(side="left", padx=4)
        styled_button(tb, "Delete", self.remove_record, bg=ERROR, hover="#C62828").pack(side="left", padx=4)

    def row_values(self, r):
        raise NotImplementedError

    def refresh(self):
        self._data = call_proc(self.PROC_READ) or []
        self._display_rows(self._data)

    def show_rows(self, data):
        _fill_tv(self.tv, data, self.row_values)

    def _display_rows(self, data):
        if self.SORT_OPTIONS:
            fn, rev = self.SORT_OPTIONS.get(self.sort_var.get(), next(iter(self.SORT_OPTIONS.values())))
            self.show_rows(bubble_sort(data, fn, rev))
        else:
            self.show_rows(data)

    def filter_rows(self):
        term = self.search_var.get().strip()
        data = linear_search(self._data, term, self.SEARCH_FIELDS) if term else self._data
        self._display_rows(data)

    def sort_rows(self):
        self.filter_rows()

    def get_selected_row(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a row.")
            return None
        pk = self.tv.item(sel[0])["values"][self.PK_COL_INDEX]
        return next((r for r in self._data if r[self.PK_FIELD] == pk), None)

    def _open_form(self, data=None):
        if getattr(self, "FORM_NEEDS_TEACHERS", False):
            teachers = call_proc("sp_read_teachers") or []
            return self.FORM_CLS(self, self.refresh, teachers, data=data) if data else self.FORM_CLS(self, self.refresh, teachers)
        return self.FORM_CLS(self, self.refresh, data=data) if data else self.FORM_CLS(self, self.refresh)

    def open_add(self):
        self._form = self._open_form()

    def open_edit(self):
        if d := self.get_selected_row():
            self._form = self._open_form(d)

    def remove_record(self):
        if not (d := self.get_selected_row()) or not messagebox.askyesno("Delete", self.delete_prompt(d)):
            return
        call_proc(self.PROC_DELETE, (d[self.PK_FIELD],), fetch=False)
        self.refresh()

    def delete_prompt(self, d):
        return f"Delete {d['first_name']} {d['last_name']}?"


class StudentsTab(CRUDTab):
    # student CRUD (each student has a user login row)
    TITLE = "Students"
    COLS = [("ID", 40), ("First Name", 110), ("Last Name", 130), ("Email", 240), ("Date of Birth", 110), ("Phone", 120), ("Group", 80), ("Enrolled", 100)]
    SEARCH_FIELDS = ["student_id", "first_name", "last_name", "email", "group_name"]
    PROC_READ = "sp_read_students"
    PK_COL_INDEX, PK_FIELD = 0, "student_id"
    DEFAULT_SORT = "ID ↑"
    SORT_OPTIONS = {"ID ↑": _sort_id("student_id"), "ID ↓": _sort_id("student_id", True), "Last Name ↑": _sort_str("last_name"), "Last Name ↓": _sort_str("last_name", True), "Group ↑": _sort_str("group_name"), "Enrollment ↓": _sort_date("enrollment_date", True)}
    FORM_CLS = StudentForm
    PROC_DELETE = "sp_delete_student"
    ADD_LABEL = "+ Add Student"

    def row_values(self, r):
        return (r["student_id"], r["first_name"], r["last_name"], r["email"], r["date_of_birth"], r["phone"] or "", r["group_name"], r["enrollment_date"])


class TeachersTab(CRUDTab):
    # teacher CRUD
    TITLE = "Teachers"
    COLS = [("ID", 40), ("First Name", 110), ("Last Name", 130), ("Email", 240), ("Phone", 120), ("Department", 160), ("Hired", 100)]
    SEARCH_FIELDS = ["teacher_id", "first_name", "last_name", "email", "department"]
    PROC_READ = "sp_read_teachers"
    PK_COL_INDEX, PK_FIELD = 0, "teacher_id"
    DEFAULT_SORT = "ID ↑"
    SORT_OPTIONS = {"ID ↑": _sort_id("teacher_id"), "ID ↓": _sort_id("teacher_id", True), "Last Name ↑": _sort_str("last_name"), "Last Name ↓": _sort_str("last_name", True), "Department ↑": (lambda r: (r["department"] or "").lower(), False), "Hire Date ↓": _sort_date("hire_date", True)}
    FORM_CLS = TeacherForm
    PROC_DELETE = "sp_delete_teacher"
    ADD_LABEL = "+ Add Teacher"

    def row_values(self, r):
        return (r["teacher_id"], r["first_name"], r["last_name"], r["email"], r["phone"] or "", r["department"] or "", r["hire_date"])


class CoursesTab(CRUDTab):
    # courses linked to one teacher
    TITLE = "Courses"
    COLS = [("ID", 40), ("Code", 70), ("Course Name", 220), ("Teacher", 180), ("Credits", 60), ("Semester", 120), ("Max", 50)]
    SEARCH_FIELDS = ["course_id", "course_code", "course_name", "teacher_name", "semester"]
    PROC_READ = "sp_read_courses"
    PK_COL_INDEX, PK_FIELD = 0, "course_id"
    DEFAULT_SORT = "ID ↑"
    SORT_OPTIONS = {"ID ↑": _sort_id("course_id"), "ID ↓": _sort_id("course_id", True), "Course Name ↑": _sort_str("course_name"), "Course Name ↓": _sort_str("course_name", True), "Code ↑": _sort_str("course_code"), "Credits ↓": (lambda r: r["credits"], True), "Semester ↑": _sort_str("semester")}
    FORM_CLS = CourseForm
    FORM_NEEDS_TEACHERS = True
    PROC_DELETE = "sp_delete_course"
    ADD_LABEL = "+ Add Course"

    def row_values(self, r):
        return (r["course_id"], r["course_code"], r["course_name"], r["teacher_name"], r["credits"], r["semester"], r["max_students"])

    def delete_prompt(self, d):
        return f"Delete course {d['course_name']}?"


class RegistrationsTab(CRUDTab):
    # Manages enrollments, basically linking a student to a course.
    TITLE = "Registrations"
    COLS = [("ID", 40), ("Student", 160), ("Group", 70), ("Course", 200), ("Code", 70), ("Teacher", 160), ("Registered At", 140)]
    SEARCH_FIELDS = ["registration_id", "student_name", "group_name", "course_name", "course_code", "teacher_name"]
    PROC_READ = "sp_read_registrations"
    PK_COL_INDEX, PK_FIELD = 0, "registration_id"
    DEFAULT_SORT = "ID ↑"
    SORT_OPTIONS = {"ID ↑": _sort_id("registration_id"), "ID ↓": _sort_id("registration_id", True), "Student ↑": _sort_str("student_name"), "Course ↑": _sort_str("course_name"), "Registered ↓": _sort_date("registered_at", True)}

    def add_toolbar_buttons(self, tb):
        styled_button(tb, "+ Register Student", self.open_add).pack(side="left", padx=4, pady=8)
        styled_button(tb, "Remove", self.remove_record, bg=ERROR, hover="#C62828").pack(side="left", padx=4)

    def row_values(self, r):
        return (r["registration_id"], r["student_name"], r["group_name"], r["course_name"], r["course_code"], r["teacher_name"], str(r["registered_at"])[:16] if r["registered_at"] else "")

    def open_add(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Register Student to Course")
        dlg.geometry("420x280")
        dlg.configure(fg_color=PINK_L)
        dlg.grab_set()
        students, courses = call_proc("sp_read_students") or [], call_proc("sp_read_courses") or []
        s_map = {f"{s['first_name']} {s['last_name']} ({s['group_name']})": s["student_id"] for s in students}
        c_map = {f"{c['course_code']} – {c['course_name']}": c["course_id"] for c in courses}
        make_label(dlg, "Register Student to Course", bold=True, size=14, color=ROSE).pack(pady=(20, 10))
        box = ctk.CTkFrame(dlg, fg_color=WHITE, corner_radius=12)
        box.pack(padx=30, fill="x")
        make_label(box, "Student *", bold=True, size=11).pack(anchor="w", padx=16, pady=(12, 1))
        sv = ctk.StringVar()
        ctk.CTkComboBox(box, values=list(s_map), variable=sv, width=360, **COMBO_STYLE).pack(padx=16)
        make_label(box, "Course *", bold=True, size=11).pack(anchor="w", padx=16, pady=(10, 1))
        cv = ctk.StringVar()
        ctk.CTkComboBox(box, values=list(c_map), variable=cv, width=360, **COMBO_STYLE).pack(padx=16)
        msg = make_label(box, "", color=ERROR, size=11)
        msg.pack(pady=4)

        def save():
            sn, cn = sv.get(), cv.get()
            if not sn or not cn:
                return set_msg_error(msg, "Please select both student and course.")
            if (sid := s_map.get(sn)) and (cid := c_map.get(cn)):
                call_proc("sp_create_registration", (sid, cid))
                self.refresh()
                dlg.destroy()

        styled_button(box, "Register", save, width=360).pack(padx=16, pady=(0, 16))

    def remove_record(self):
        if (d := self.get_selected_row()) and messagebox.askyesno("Delete", "Remove this registration?"):
            call_proc("sp_delete_registration", (d["registration_id"],), fetch=False)
            self.refresh()


# teacher's grades tab
class GradesTab(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color=GREY_L)
        self._data, self._reg_data = [], []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        tb = ctk.CTkFrame(self, fg_color=PINK_L, corner_radius=0)
        tb.pack(fill="x", pady=(0, 8))
        make_label(tb, "Grades", bold=True, size=14, color=ROSE).pack(side="left", padx=16, pady=10)
        styled_button(tb, "Assign Grade", self.assign_grade).pack(side="left", padx=4, pady=8)
        sf = ctk.CTkFrame(tb, fg_color="transparent")
        sf.pack(side="right", padx=12)
        self.search_var = _add_search(sf, self.filter_rows)
        cols = ("Student", "Group", "Course", "Code", "Grade %", "Letter", "Date")
        f, self.tv = create_table(self, cols, height=20)
        set_column_widths(self.tv, cols, (160, 70, 200, 70, 80, 70, 110))
        f.pack(fill="both", expand=True, padx=12, pady=6)

    def refresh(self):
        self._data = bubble_sort(call_proc("sp_read_grades") or [], lambda r: r["registration_id"], False)
        self._reg_data = bubble_sort(call_proc("sp_read_registrations") or [], lambda r: r["registration_id"], False)
        self.show_rows(self._data)

    def show_rows(self, data):
        _fill_tv(self.tv, data, _grade_display)

    def filter_rows(self):
        term = self.search_var.get().strip()
        data = linear_search(self._data, term, ["student_name", "group_name", "course_name"]) if term else self._data
        self.show_rows(bubble_sort(data, lambda r: r["registration_id"], False))

    def assign_grade(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Select Registration")
        dlg.geometry("640x520")
        dlg.configure(fg_color=PINK_L)
        dlg.grab_set()
        make_label(dlg, "Select a registration to grade", bold=True, size=15, color=ROSE).pack(pady=(16, 4))
        nb = ctk.CTkTabview(dlg, **TABVIEW_STYLE)
        nb.pack(fill="both", expand=True, padx=20, pady=8)
        tvs = {}

        def _add_picker_tab(tab_name, label, names, filter_key, cols, widths, sort_key, row_fn):
            tab = nb.add(tab_name)
            hdr = ctk.CTkFrame(tab, fg_color="transparent")
            hdr.pack(fill="x", padx=10, pady=(10, 8))
            make_label(hdr, label, bold=True, size=12).pack(side="left", padx=(0, 10))
            var = ctk.StringVar(value=names[0] if names else "")
            fc, tv = create_table(tab, cols, height=10)
            set_column_widths(tv, cols, widths)
            fc.pack(fill="both", expand=True, padx=10, pady=4)
            tvs[tab_name] = tv

            def refresh(_=None):
                sel = var.get()
                rows = sorted([x for x in self._reg_data if x[filter_key] == sel], key=sort_key)
                _fill_tv(tv, rows, row_fn)

            ctk.CTkComboBox(hdr, values=names or [""], variable=var, width=300, command=refresh, **COMBO_STYLE).pack(side="left")
            if names:
                refresh()

        courses = sorted({r["course_name"] for r in self._reg_data})
        students = sorted({r["student_name"] for r in self._reg_data})
        _add_picker_tab("Courses", "Select Course:", courses, "course_name", ("Reg ID", "Student", "Group"), (60, 240, 120), lambda x: x["registration_id"], lambda r: (r["registration_id"], r["student_name"], r.get("group_name", "")))
        _add_picker_tab("Students", "Select Student:", students, "student_name", ("Reg ID", "Course", "Code"), (60, 240, 120), lambda x: x["registration_id"], lambda r: (r["registration_id"], r["course_name"], r["course_code"]))

        def pick():
            tv = tvs[nb.get()]
            sel = tv.selection()
            if not sel:
                return messagebox.showwarning("No Selection", "Please pick a row from the table.")
            rid = tv.item(sel[0])["values"][0]
            if reg := next((r for r in self._reg_data if r["registration_id"] == rid), None):
                dlg.destroy()
                self._grade_form = GradeForm(self, self.refresh, reg)

        styled_button(dlg, "Select Registration", pick, width=250).pack(pady=12)


# student view: my grades, attendance, group mates
class MyGradesTab(ctk.CTkFrame):

    def __init__(self, parent, student_id, group_name):
        super().__init__(parent, fg_color=GREY_L)
        self.student_id, self.group_name = student_id, group_name
        self.build_ui()
        self.refresh()

    def build_ui(self):
        nb = ctk.CTkTabview(self, fg_color=GREY_L, **{k: v for k, v in TABVIEW_STYLE.items() if k != "fg_color"})
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        nb.add("My Grades")
        nb.add("My Attendance")
        nb.add("My group")
        cols = ("Course", "Code", "Semester", "Teacher", "Grade %", "Letter", "Date")
        f, self.tv_my = create_table(nb.tab("My Grades"), cols, height=18)
        set_column_widths(self.tv_my, cols, (200, 70, 110, 160, 80, 70, 100))
        f.pack(fill="both", expand=True, padx=8, pady=8)
        cols_a = ("Course", "Code", "Date", "Status")
        f2, self.tv_att = create_table(nb.tab("My Attendance"), cols_a, height=18)
        set_column_widths(self.tv_att, cols_a, (220, 80, 120, 100))
        f2.pack(fill="both", expand=True, padx=8, pady=8)
        gd = nb.tab("My group")
        make_label(gd, f"Group: {self.group_name}", bold=True, size=13, color=ROSE).pack(anchor="w", padx=12, pady=8)
        cols3 = ("Student", "Group", "Course", "Code")
        f3, self.tv_grp = create_table(gd, cols3, height=18)
        set_column_widths(self.tv_grp, cols3, (180, 80, 220, 80))
        f3.pack(fill="both", expand=True, padx=8, pady=4)

    def refresh(self):
        _fill_tv(self.tv_my, call_proc("sp_read_student_grades", (self.student_id,)) or [], lambda r: (
            r["course_name"], r["course_code"], r["semester"], r["teacher_name"],
            f"{r['grade']}%" if r["grade"] is not None else "—", r["letter_grade"] or "—",
            str(r["graded_at"])[:10] if r["graded_at"] else "—",
        ))
        _fill_tv(self.tv_att, call_proc("sp_read_student_attendance", (self.student_id,)) or [], lambda r: (
            r["course_name"], r["course_code"], str(r["att_date"]) if r["att_date"] else "—", r.get("status", "—"),
        ))
        _fill_tv(self.tv_grp, call_proc("sp_read_group_data", (self.group_name,)) or [], lambda r: (
            r["student_name"], r["group_name"], r["course_name"], r["course_code"],
        ))
