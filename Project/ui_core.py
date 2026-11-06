# UI imports: colors, buttons, tables, edit forms

from __future__ import annotations
import hashlib
from datetime import date, datetime
from tkinter import ttk
import customtkinter as ctk
from database import call_proc
from utils import grade_to_letter, validate_dob, validate_email, validate_grade, validate_name

# Values for themes
PINK, PINK_D, PINK_L, ROSE = "#FF61A6", "#D80479", "#2a1622", "#FF94C2"
WHITE, GREY_L, GREY_D, TEXT, PURE_WHITE = "#1E2024", "#141517", "#A0A0A0", "#F2F3F5", "#FFFFFF"
SUCCESS, ERROR, WARN = "#4CAF50", "#F44336", "#FF9800"


# These functions help keeping widgets look consistent.
def styled_button(parent, text, command, width=140, fg=PURE_WHITE, bg=PINK, hover=PINK_D):
    return ctk.CTkButton(parent, text=text, command=command, fg_color=bg, hover_color=hover, text_color=fg, font=("Segoe UI", 12, "bold"), corner_radius=8, width=width, height=32)


def make_make_label(parent, text, bold=False, size=12, color=TEXT):
    return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"), text_color=color)


def make_make_entry(parent, placeholder="", width=240, show=""):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width, fg_color=WHITE, border_color=PINK, text_color=TEXT, font=("Segoe UI", 12), corner_radius=6, show=show)


make_label = make_make_label
make_entry = make_make_entry


def set_msg_error(w, m): w.configure(text=m, text_color=ERROR)
def set_msg_ok(w, m): w.configure(text=m, text_color=SUCCESS)


def create_table(parent, columns, height=300):
# Using this I built a styled data grid
    sep_char = "\u2503"
    sep_width = 10

    st = ttk.Style()
    st.theme_use("default")
    st.configure(
        "Pink.Treeview",
        background=WHITE,
        foreground=PURE_WHITE,
        rowheight=26,
        fieldbackground=WHITE,
        bordercolor=PINK,
        font=("Segoe UI", 11),
    )
    st.configure(
        "Pink.Treeview.Heading",
        background=PINK,
        foreground=PURE_WHITE,
        font=("Segoe UI", 11, "bold"),
        relief="flat",
    )
    st.map("Pink.Treeview", background=[("selected", PINK_D)], foreground=[("selected", PURE_WHITE)])
    frame = ctk.CTkFrame(parent, fg_color=WHITE, corner_radius=8, border_color=PINK, border_width=1)
    actual = [x for i, c in enumerate(columns) for x in ([c, f"sep_{i}"] if i < len(columns) - 1 else [c])]
    tv = ttk.Treeview(frame, columns=actual, show="headings", style="Pink.Treeview", height=height)
    for i in range(len(columns) - 1):
        tv.column(f"sep_{i}", width=sep_width, stretch=False, anchor="center", minwidth=sep_width)
        tv.heading(f"sep_{i}", text=sep_char)
    tv.tag_configure("even", background=WHITE)
    tv.tag_configure("odd", background="#2b1b24")
    tv.row_count = 0
    _ins, _del = tv.insert, tv.delete

    def _insert(p, index, iid=None, **kw):
        # This function inserts a new row into the table.
        kw.setdefault("tags", ("even" if tv.row_count % 2 == 0 else "odd",))
        tv.row_count += 1
        if "values" in kw:
            v = list(kw["values"])
            kw["values"] = sum(([x, sep_char] for x in v[:-1]), start=[]) + [v[-1]]
        return _ins(p, index, iid=iid, **kw)

    def _delete(*items):
        # This function deletes the selected row from the table.
        _del(*items)
        if not tv.get_children():
            tv.row_count = 0

    tv.insert, tv.delete = _insert, _delete
    vsb, hsb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview), ttk.Scrollbar(frame, orient="horizontal", command=tv.xview)
    tv.configure(yscroll=vsb.set, xscroll=hsb.set)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tv.pack(fill="both", expand=True)
    return frame, tv


# Rose title on the window, scrollable white box for fields. It returns the box.
def form_header(self, title):
    ctk.CTkLabel(self, text=title, font=("Segoe UI", 16, "bold"), text_color=ROSE).pack(pady=(20, 10))
    b = ctk.CTkScrollableFrame(self, fg_color=WHITE, corner_radius=12)
    b.pack(padx=30, fill="both", expand=True, pady=(0, 10))
    return b


# Save and Cancel row
def form_buttons(box, save_cmd, cancel_cmd=None):
    cancel_cmd = cancel_cmd or box.winfo_toplevel().destroy
    bf = ctk.CTkFrame(box, fg_color="transparent")
    bf.pack(pady=12)
    styled_button(bf, "Save", save_cmd).pack(side="left", padx=6)
    styled_button(bf, "Cancel", cancel_cmd, bg=GREY_D, hover="#555").pack(side="left", padx=6)


# Add/edit student popup; data=None means new student.
class StudentForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, data=None):
        super().__init__(parent)
        self.on_save, self.data = on_save, data
        self.title("Add Student" if data is None else "Edit Student")
        self.geometry("520x600")
        self.resizable(False, False)
        self.configure(fg_color=PINK_L)
        self.grab_set()  # We must close this window before using the main app again
        self.build_ui()
        if data:
            self.fill_form()

    def build_ui(self):
        box = form_header(self, "Student Details")
        # Label, entry key and alaceholder. Only adds login fields only when creating a new student
        F = [("First Name *", "first_name", "Name"), ("Last Name *", "last_name", "Surname"), ("Email *", "email", "student's_email@coventry.edu.kz"), ("Date of Birth *", "dob", "YYYY-MM-DD"), ("Phone", "phone", "+7xxxxxxxxxx"), ("Group *", "group_name", "SE-301"), ("Enrollment Date *", "enroll", "YYYY-MM-DD")]
        if self.data is None:
            F += [("Username *", "username", "Name_Surname"), ("Password *", "password", "min 6 chars")]
        self.entries = {}
        for lt, k, ph in F:
            make_label(box, lt, bold=True, size=11).pack(anchor="w", padx=16, pady=(10, 1))
            e = make_entry(box, ph, width=440, show="•" if k == "password" else "")
            e.pack(padx=16)
            self.entries[k] = e
        self.msg = make_label(box, "", color=ERROR, size=11)
        self.msg.pack(pady=(8, 0))
        form_buttons(box, self.save_form)

    # Copies existing row from the table into the entry boxes.
    def fill_form(self):
        d = self.data
        for k, v in [("first_name", d.get("first_name", "")), ("last_name", d.get("last_name", "")), ("email", d.get("email", "")), ("dob", str(d.get("date_of_birth", "") or "")), ("phone", d.get("phone", "") or ""), ("group_name", d.get("group_name", "")), ("enroll", str(d.get("enrollment_date", "") or ""))]:
            self.entries[k].insert(0, v)

    def save_form(self):
        e = self.entries
        fn, ln, em, db, ph, grp, en = e["first_name"].get().strip(), e["last_name"].get().strip(), e["email"].get().strip(), e["dob"].get().strip(), e["phone"].get().strip(), e["group_name"].get().strip(), e["enroll"].get().strip()
        # Validate names, email domain and date of birth before touching the database
        for err in (validate_name(fn), validate_name(ln), validate_email(em), validate_dob(db)):
            if err:
                return set_msg_error(self.msg, err)
        try:
            ed = datetime.strptime(en, "%Y-%m-%d").date()
        except ValueError:
            return set_msg_error(self.msg, "Enrollment date must be YYYY-MM-DD.")
        hp = hashlib.sha256
        if self.data is None:
            usr, pwd = e["username"].get().strip(), e["password"].get().strip()
            if not usr or not pwd:
                return set_msg_error(self.msg, "Username and password required.")
            if len(pwd) < 6:
                return set_msg_error(self.msg, "Password must be at least 6 characters.")
            # Create users row and students row.
            # Password stored as SHA-256 hex
            ok = call_proc("sp_create_student", (usr, hp(pwd.encode()).hexdigest(), fn, ln, em, db, ph, grp, str(ed)))
        else:
            # update profile only (username and password are not changed freom here)
            ok = call_proc("sp_update_student", (self.data["student_id"], fn, ln, em, db, ph, grp, str(ed)), fetch=False)
        if ok is not None:
            self.on_save()  # refresh the students table on the parent tab
            self.destroy()


# Add/edit teacher popup; same pattern as StudentForm.
class TeacherForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, data=None):
        super().__init__(parent)
        self.on_save, self.data = on_save, data
        self.title("Add Teacher" if data is None else "Edit Teacher")
        self.geometry("520x580")
        self.resizable(False, False)
        self.configure(fg_color=PINK_L)
        self.grab_set()
        self.build_ui()
        if data:
            self.fill_form()

    def build_ui(self):
        box = form_header(self, "Teacher Details")
        # Label, entry key, placeholder.
        F = [("First Name *", "first_name", "Sarah"), ("Last Name *", "last_name", "Johnson"), ("Email *", "email", "s.johnson@coventry.edu.kz"), ("Phone", "phone", "+77011234567"), ("Department", "department", "Computer Science"), ("Hire Date *", "hire_date", "YYYY-MM-DD")]
        if self.data is None:
            F += [("Username *", "username", "s.johnson"), ("Password *", "password", "min 6 chars")]
        self.entries = {}
        for lt, k, ph in F:
            make_label(box, lt, bold=True, size=11).pack(anchor="w", padx=16, pady=(10, 1))
            e = make_entry(box, ph, width=440, show="•" if k == "password" else "")
            e.pack(padx=16)
            self.entries[k] = e
        self.msg = make_label(box, "", color=ERROR, size=11)
        self.msg.pack(pady=(8, 0))
        form_buttons(box, self.save_form)

    # Copy existing teacher row into the entry boxes.
    def fill_form(self):
        d = self.data
        for k, v in [("first_name", d.get("first_name", "")), ("last_name", d.get("last_name", "")), ("email", d.get("email", "")), ("phone", d.get("phone", "") or ""), ("department", d.get("department", "") or ""), ("hire_date", str(d.get("hire_date", "") or ""))]:
            self.entries[k].insert(0, v)

    def save_form(self):
        e = self.entries
        fn, ln, em, ph, dep, hd = e["first_name"].get().strip(), e["last_name"].get().strip(), e["email"].get().strip(), e["phone"].get().strip(), e["department"].get().strip(), e["hire_date"].get().strip()
        # validate names and Coventry email, no date of birth check for teachers
        for err in (validate_name(fn), validate_name(ln), validate_email(em)):
            if err:
                return set_msg_error(self.msg, err)
        try:
            hire = datetime.strptime(hd, "%Y-%m-%d").date()
        except ValueError:
            return set_msg_error(self.msg, "Hire date must be YYYY-MM-DD.")
        hp = hashlib.sha256
        if self.data is None:
            usr, pwd = e["username"].get().strip(), e["password"].get().strip()
            if not usr or not pwd:
                return set_msg_error(self.msg, "Username and password required.")
            if len(pwd) < 6:
                return set_msg_error(self.msg, "Password must be at least 6 characters.")
            # create users row + teachers row
            # password stored as SHA-256 hex
            ok = call_proc("sp_create_teacher", (usr, hp(pwd.encode()).hexdigest(), fn, ln, em, ph, dep, str(hire)))
        else:
            # update profile only (username and password are not changed from here)
            ok = call_proc("sp_update_teacher", (self.data["teacher_id"], fn, ln, em, ph, dep, str(hire)), fetch=False)
        if ok is not None:
            self.on_save()  # refresh the teachers table on the parent tab.
            self.destroy()


# CourseForm, GradeForm, and AttendanceForm are modal popups opened from ui_tabs.
# Shared flow: build fields -> user clicks Save -> validate input -> call_proc(sp_*) -> on_save() refreshes the parent table -> destroy().
# Cancel (via form_buttons) closes the window without saving. Errors show on a red msg label; DB errors also pop up from call_proc.
#
# CourseForm — add/edit a course (no login row). Parent passes the teachers list for the Teacher combo box.
#   Create: sp_create_course(code, name, teacher_id, credits, semester, max_students).
#   Edit: sp_update_course(course_id, …). Matches DB checks: credits 1–6, max_students > 0.
#
# GradeForm — grade one enrollment. Parent passes registration (student + course already chosen).
#   Live letter preview from numeric grade (grade_to_letter). Save: sp_upsert_grade(registration_id, grade, letter, …).
#
# AttendanceForm — mark attendance for one enrollment. Parent passes registration; date defaults to today.
#   Status radio: Present / Absent / Late / Excused. Save: sp_upsert_attendance(registration_id, date, status).


class CourseForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, teachers, data=None):
        super().__init__(parent)
        self.on_save, self.teachers, self.data = on_save, teachers, data
        self.title("Add Course" if data is None else "Edit Course")
        self.geometry("520x500")
        self.resizable(False, False)
        self.configure(fg_color=PINK_L)
        self.grab_set()
        self.build_ui()
        if data:
            self.fill_form()

    def build_ui(self):
        box = form_header(self, "Course Details")

        def row(lt, attr, ph):
            make_label(box, lt, bold=True, size=11).pack(anchor="w", padx=16, pady=(10, 1))
            setattr(self, attr, make_entry(box, ph, width=440))
            getattr(self, attr).pack(padx=16)

        row("Course Code *", "code", "CS301")
        row("Course Name *", "name_e", "Database Systems")
        make_label(box, "Teacher *", bold=True, size=11).pack(anchor="w", padx=16, pady=(10, 1))
        self.teacher_var = ctk.StringVar()
        ctk.CTkComboBox(box, width=440, values=[f"{t['first_name']} {t['last_name']}" for t in self.teachers], variable=self.teacher_var, fg_color=WHITE, border_color=PINK, text_color=TEXT).pack(padx=16)
        row("Credits *", "credits", "3")
        row("Semester *", "semester", "Spring 2025")
        row("Max Students", "maxst", "30")
        self.msg = make_label(box, "", color=ERROR, size=11)
        self.msg.pack(pady=(8, 0))
        form_buttons(box, self.save_form)

    def fill_form(self):
        d = self.data
        self.code.insert(0, d.get("course_code", ""))
        self.name_e.insert(0, d.get("course_name", ""))
        self.credits.insert(0, str(d.get("credits", 3)))
        self.semester.insert(0, d.get("semester", ""))
        self.maxst.insert(0, str(d.get("max_students", 30)))
        if d.get("teacher_name"):
            self.teacher_var.set(d["teacher_name"])

    def save_form(self):
        code, cname, tname = self.code.get().strip(), self.name_e.get().strip(), self.teacher_var.get().strip()
        cred, sem, maxst = self.credits.get().strip(), self.semester.get().strip(), self.maxst.get().strip()
        if not all([code, cname, tname, cred, sem]):
            return set_msg_error(self.msg, "Please fill in all required fields.")
        try:
            ci, mi = int(cred), int(maxst) if maxst else 30
        except ValueError:
            return set_msg_error(self.msg, "Credits and Max Students must be integers.")
        if not 1 <= ci <= 6:
            return set_msg_error(self.msg, "Credits must be between 1 and 6.")
        if mi <= 0:
            return set_msg_error(self.msg, "Max Students must be greater than zero.")
        tid = next((t["teacher_id"] for t in self.teachers if f"{t['first_name']} {t['last_name']}" == tname), None)
        if tid is None:
            return set_msg_error(self.msg, "Please select a valid teacher.")
        ok = call_proc("sp_create_course", (code, cname, tid, ci, sem, mi)) if self.data is None else call_proc("sp_update_course", (self.data["course_id"], code, cname, tid, ci, sem, mi), fetch=False)
        if ok is not None:
            self.on_save()
            self.destroy()


class GradeForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, registration):
        super().__init__(parent)
        self.on_save, self.registration = on_save, registration
        self.title("Enter Grade")
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(fg_color=PINK_L)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        r = self.registration
        ctk.CTkLabel(self, text="Grade Entry", font=("Segoe UI", 16, "bold"), text_color=ROSE).pack(pady=(20, 4))
        ctk.CTkLabel(self, text=f"{r['student_name']}  –  {r['course_name']}", font=("Segoe UI", 11), text_color=GREY_D).pack(pady=(0, 12))
        box = ctk.CTkScrollableFrame(self, fg_color=WHITE, corner_radius=12)
        box.pack(padx=30, fill="both", expand=True, pady=(0, 10))
        make_label(box, "Numeric Grade (0–100) *", bold=True, size=11).pack(anchor="w", padx=16, pady=(14, 1))
        self.grade_e = make_entry(box, "85.5", width=360)
        self.grade_e.pack(padx=16, pady=(0, 6))
        self.preview_lbl = make_label(box, "Letter grade: —", size=11, color=GREY_D)
        self.preview_lbl.pack(anchor="w", padx=16, pady=(0, 4))
        self.grade_e.bind("<KeyRelease>", self.update_letter_preview)
        self.msg = make_label(box, "", color=ERROR, size=11)
        self.msg.pack(pady=(4, 0))
        form_buttons(box, self.save_form)

    def update_letter_preview(self, _=None):
        try:
            g = float(self.grade_e.get().strip())
            if 0 <= g <= 100:
                return self.preview_lbl.configure(text=f"Letter grade: {grade_to_letter(g)}", text_color=ROSE)
        except ValueError:
            pass
        self.preview_lbl.configure(text="Letter grade: —", text_color=GREY_D)

    def save_form(self):
        gs = self.grade_e.get().strip()
        if (err := validate_grade(gs)):
            return set_msg_error(self.msg, err)
        g = float(gs)
        if call_proc("sp_upsert_grade", (self.registration["registration_id"], g, grade_to_letter(g), None), fetch=False) is not None:
            self.on_save()
            self.destroy()


class AttendanceForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, registration=None):
        super().__init__(parent)
        self.on_save, self.registration = on_save, registration
        self.title("Mark Attendance")
        self.geometry("440x400")
        self.resizable(False, False)
        self.configure(fg_color=PINK_L)
        self.grab_set()
        self.build_ui()

    # Runs once when the popup opens from init
    def build_ui(self):
        ctk.CTkLabel(self, text="Attendance Record", font=("Segoe UI", 16, "bold"), text_color=ROSE).pack(pady=(20, 4))
        if self.registration:
            r = self.registration
            ctk.CTkLabel(self, text=f"{r['student_name']}  –  {r['course_name']}", font=("Segoe UI", 11), text_color=GREY_D).pack(pady=(0, 8))
        box = ctk.CTkScrollableFrame(self, fg_color=WHITE, corner_radius=12)
        box.pack(padx=30, fill="both", expand=True, pady=(0, 10))
        make_label(box, "Date *", bold=True, size=11).pack(anchor="w", padx=16, pady=(14, 1))
        self.date_e = make_entry(box, "YYYY-MM-DD", width=380)
        self.date_e.pack(padx=16)
        self.date_e.insert(0, date.today().strftime("%Y-%m-%d"))
        make_label(box, "Status *", bold=True, size=11).pack(anchor="w", padx=16, pady=(10, 1))
        self.status_var = ctk.StringVar(value="Present")
        sf = ctk.CTkFrame(box, fg_color="transparent")
        sf.pack(anchor="w", padx=16, pady=(0, 4))
        for s in ("Present", "Absent", "Late", "Excused"):
            ctk.CTkRadioButton(sf, text=s, variable=self.status_var, value=s, fg_color=PINK, hover_color=PINK_D, text_color=TEXT, font=("Segoe UI", 11)).pack(side="left", padx=8)
        self.msg = make_label(box, "", color=ERROR, size=11)
        self.msg.pack(pady=(4, 0))
        form_buttons(box, self.save_form)

    # Runs when the user clicks Save
    def save_form(self):
        ds = self.date_e.get().strip()
        try:
            datetime.strptime(ds, "%Y-%m-%d")
        except ValueError:
            return set_msg_error(self.msg, "Date must be YYYY-MM-DD.")
        if self.registration is None:
            return set_msg_error(self.msg, "No registration selected.")
        if call_proc("sp_upsert_attendance", (self.registration["registration_id"], ds, self.status_var.get()), fetch=False) is not None:
            self.on_save()
            self.destroy()
