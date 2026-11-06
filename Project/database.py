# Connects to MySQL, creates tables, all GUI and console operations go through this file.

from __future__ import annotations
import hashlib
from collections.abc import Callable
from contextlib import contextmanager
from tkinter import messagebox
from typing import Any
import mysql.connector
from mysql.connector import Error

# Setings of MySQL server
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "mysql12345",
    "database": "school_management",
}
VALID_EMAIL_DOMAIN = "@coventry.edu.kz"


class DatabaseError(RuntimeError):
    pass

# This class is the one that takes cares of everything that has to do with MySQL. 
# When created it stores DB_CONFIG settings. 
class DatabaseManager:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = dict(config or DB_CONFIG)
        self._schema_ready = False



    # Opens a short-lived MySQL connection for use with the with statement.
    # use_database=false connects without selecting a database
    # Commits on success, rolls back if theres an error.
    @contextmanager
    def connection(self, use_database: bool = True):
        # Drop database key when connecting at server level only
        cfg = dict(self._config)
        if not use_database:
            cfg.pop("database", None)
        conn = cur = None
        try:
            conn = mysql.connector.connect(**cfg)
            cur = conn.cursor(dictionary=True)
            yield cur
            conn.commit()
        except Error as exc:
            if conn:
                conn.rollback()
            raise DatabaseError(str(exc)) from exc
        finally:
            if cur:
                cur.close()
            if conn and conn.is_connected():
                conn.close()
                #And in the end it just closes the connection and ide.

    # Ensures that database is created if it's missing. And schema ready stops it from running again after every button click.
    def ensure_schema(self) -> None:
        if self._schema_ready:
            return
        db = self._config["database"]
        with self.connection(use_database=False) as c:
            c.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        with self.connection() as c:
            self._create_tables(c)
            self._create_indexes(c)
            self._seed_demo_data(c)
        self._schema_ready = True

    # Creates all app tables
    def _create_tables(self, c) -> None:
        stmts = [
            """CREATE TABLE IF NOT EXISTS users (
 user_id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL, password VARCHAR(255) NOT NULL,
 role ENUM('teacher','student') NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT uq_users_username UNIQUE (username))""",
            """CREATE TABLE IF NOT EXISTS teachers (
 teacher_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, first_name VARCHAR(50) NOT NULL,
 last_name VARCHAR(50) NOT NULL, email VARCHAR(120) NOT NULL, phone VARCHAR(20), department VARCHAR(80) DEFAULT 'General',
 hire_date DATE NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT uq_teachers_user UNIQUE (user_id), CONSTRAINT uq_teachers_email UNIQUE (email),
 CONSTRAINT fk_teachers_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE,
 CONSTRAINT chk_teachers_name CHECK (first_name <> '' AND last_name <> ''))""",
            """CREATE TABLE IF NOT EXISTS students (
 student_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, first_name VARCHAR(50) NOT NULL,
 last_name VARCHAR(50) NOT NULL, email VARCHAR(120) NOT NULL, date_of_birth DATE NOT NULL, phone VARCHAR(20),
 group_name VARCHAR(30) NOT NULL, enrollment_date DATE NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT uq_students_user UNIQUE (user_id), CONSTRAINT uq_students_email UNIQUE (email),
 CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE CASCADE,
 CONSTRAINT chk_students_name CHECK (first_name <> '' AND last_name <> ''), CONSTRAINT chk_students_group CHECK (group_name <> ''))""",
            """CREATE TABLE IF NOT EXISTS courses (
 course_id INT AUTO_INCREMENT PRIMARY KEY, course_code VARCHAR(20) NOT NULL, course_name VARCHAR(120) NOT NULL,
 teacher_id INT NOT NULL, credits TINYINT NOT NULL DEFAULT 3, semester VARCHAR(40) NOT NULL, max_students INT NOT NULL DEFAULT 30,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT uq_courses_code UNIQUE (course_code),
 CONSTRAINT fk_courses_teacher FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON UPDATE CASCADE ON DELETE RESTRICT,
 CONSTRAINT chk_courses_credits CHECK (credits BETWEEN 1 AND 6), CONSTRAINT chk_courses_capacity CHECK (max_students > 0))""",
            """CREATE TABLE IF NOT EXISTS registrations (
 registration_id INT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, course_id INT NOT NULL,
 registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT uq_registrations_student_course UNIQUE (student_id, course_id),
 CONSTRAINT fk_registrations_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
 CONSTRAINT fk_registrations_course FOREIGN KEY (course_id) REFERENCES courses(course_id) ON UPDATE CASCADE ON DELETE CASCADE)""",
            """CREATE TABLE IF NOT EXISTS grades (
 grade_id INT AUTO_INCREMENT PRIMARY KEY, registration_id INT NOT NULL, grade DECIMAL(5,2) NOT NULL, letter_grade VARCHAR(2) NOT NULL,
 graded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT uq_grades_registration UNIQUE (registration_id),
 CONSTRAINT fk_grades_registration FOREIGN KEY (registration_id) REFERENCES registrations(registration_id) ON UPDATE CASCADE ON DELETE CASCADE,
 CONSTRAINT chk_grades_range CHECK (grade BETWEEN 0 AND 100))""",
            """CREATE TABLE IF NOT EXISTS attendance (
 attendance_id INT AUTO_INCREMENT PRIMARY KEY, registration_id INT NOT NULL, att_date DATE NOT NULL,
 status ENUM('Present','Absent','Late','Excused') NOT NULL DEFAULT 'Present', created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT uq_attendance_registration_date UNIQUE (registration_id, att_date),
 CONSTRAINT fk_attendance_registration FOREIGN KEY (registration_id) REFERENCES registrations(registration_id) ON UPDATE CASCADE ON DELETE CASCADE)""",
        ]
        for s in stmts:
            c.execute(s)


    # This method adds indexes on columns to speed up searches.
    def _create_indexes(self, c) -> None:
        for s in (
            "CREATE INDEX idx_teachers_last_name ON teachers(last_name)",
            "CREATE INDEX idx_teachers_department ON teachers(department)",
            "CREATE INDEX idx_students_last_name ON students(last_name)",
            "CREATE INDEX idx_students_group_name ON students(group_name)",
            "CREATE INDEX idx_courses_name ON courses(course_name)",
            "CREATE INDEX idx_courses_teacher ON courses(teacher_id)",
            "CREATE INDEX idx_registrations_student ON registrations(student_id)",
            "CREATE INDEX idx_registrations_course ON registrations(course_id)",
        ):
            try:
                c.execute(s)
            except Error as exc:
                if getattr(exc, "errno", None) != 1061:
                    raise


    #This fills the database with demo info ONLY if it's empty.
    # Otherwise it inserts in order
    # 1. Teacher user
    # 2. Student user
    # 3. One course (Database Systems)
    # 4. One registration linking harry to that course.

    def _seed_demo_data(self, c) -> None:
        th = hashlib.sha256(b"tstark123").hexdigest()
        sh = hashlib.sha256(b"hpotter123").hexdigest()
        c.execute("SELECT COUNT(*) AS total FROM users")
        if c.fetchone()["total"]:
            return
        c.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'teacher')", ("Tony_Stark", th))
        tid_u = c.lastrowid
        c.execute(
            "INSERT INTO teachers (user_id, first_name, last_name, email, phone, department, hire_date) VALUES (%s,'Tony','Stark','tony.stark@coventry.edu.kz','+77010000001','Computer Science','2021-09-01')",
            (tid_u,),
        )
        tid = c.lastrowid
        c.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'student')", ("Harry_Potter", sh))
        sid_u = c.lastrowid
        c.execute(
            "INSERT INTO students (user_id, first_name, last_name, email, date_of_birth, phone, group_name, enrollment_date) VALUES (%s,'Harry','Potter','harry.potter@coventry.edu.kz','2002-07-31','+77010000002','SE-301','2023-09-01')",
            (sid_u,),
        )
        sid = c.lastrowid
        c.execute(
            "INSERT INTO courses (course_code, course_name, teacher_id, credits, semester, max_students) VALUES ('CS301','Database Systems',%s,3,'Spring 2026',30)",
            (tid,),
        )
        cid = c.lastrowid
        c.execute("INSERT INTO registrations (student_id, course_id) VALUES (%s, %s)", (sid, cid))



# This is a small base class other repositories inherit from so we don't repeat over and over again.
class BaseRepository:

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def fetch_all_rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._db.connection() as c:
            c.execute(sql, params)
            return c.fetchall()

    def fetch_one_row(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._db.connection() as c:
            c.execute(sql, params)
            return c.fetchone()

    def execute_statement(self, sql: str, params: tuple[Any, ...] = ()) -> bool:
        with self._db.connection() as c:
            c.execute(sql, params)
        return True


class AuthRepository(BaseRepository):
    # Handles login. It takes username and hashed password, runs one query on users (with teacher/student joins),
    # and returns one user row or an empty list.
    def authenticate(self, username: str, password_hash: str) -> list[dict[str, Any]]:
        row = self.fetch_one_row(
            "SELECT u.user_id,u.username,u.role,t.teacher_id,t.first_name AS t_first,t.last_name AS t_last,"
            "s.student_id,s.first_name AS s_first,s.last_name AS s_last,s.group_name FROM users u "
            "LEFT JOIN teachers t ON t.user_id=u.user_id LEFT JOIN students s ON s.user_id=u.user_id "
            "WHERE u.username=%s AND u.password=%s",
            (username, password_hash),
        )
        return [row] if row else []


class StudentRepository(BaseRepository):
    # This is a database layer for student records. Each student also has a users row for login.

    # Loads every student sorted by ID (ascending).
    def read_all(self) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT student_id,first_name,last_name,email,date_of_birth,phone,group_name,enrollment_date FROM students ORDER BY student_id"
        )

    # Creates a new student record.
    def create(self, args: tuple[Any, ...]) -> bool:
        username, password_hash, first, last, email, dob, phone, group, enrolled = args
        with self._db.connection() as c:
            c.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'student')", (username, password_hash))
            uid = c.lastrowid
            c.execute(
                "INSERT INTO students (user_id,first_name,last_name,email,date_of_birth,phone,group_name,enrollment_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (uid, first, last, email, dob, phone or None, group, enrolled),
            )
        return True

    # Updates an existing student record.
    def update(self, args: tuple[Any, ...]) -> bool:
        sid, first, last, email, dob, phone, group, enrolled = args
        return self.execute_statement(
            "UPDATE students SET first_name=%s,last_name=%s,email=%s,date_of_birth=%s,phone=%s,group_name=%s,enrollment_date=%s WHERE student_id=%s",
            (first, last, email, dob, phone or None, group, enrolled, sid),
        )

    # Deletes a student record.
    def delete(self, student_id: int) -> bool:
        return self.execute_statement("DELETE FROM students WHERE student_id=%s", (student_id,))


class TeacherRepository(BaseRepository):
        # This is a database layer for teacher records. Each teacher also has a users row for login.

    # Loads every teacher sorted by ID (ascending).
    def read_all(self) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT teacher_id,first_name,last_name,email,phone,department,hire_date FROM teachers ORDER BY teacher_id"
        )

    # Creates a new teacher record.
    def create(self, args: tuple[Any, ...]) -> bool:
        username, password_hash, first, last, email, phone, department, hire_date = args
        with self._db.connection() as c:
            c.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'teacher')", (username, password_hash))
            uid = c.lastrowid
            c.execute(
                "INSERT INTO teachers (user_id,first_name,last_name,email,phone,department,hire_date) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (uid, first, last, email, phone or None, department or None, hire_date),
            )
        return True

    #Updates an existing teacher record.
    def update(self, args: tuple[Any, ...]) -> bool:
        tid, first, last, email, phone, department, hire_date = args
        return self.execute_statement(
            "UPDATE teachers SET first_name=%s,last_name=%s,email=%s,phone=%s,department=%s,hire_date=%s WHERE teacher_id=%s",
            (first, last, email, phone or None, department or None, hire_date, tid),
        )
        
    # Deletes a teacher record.
    def delete(self, teacher_id: int) -> bool:
        return self.execute_statement("DELETE FROM teachers WHERE teacher_id=%s", (teacher_id,))


class CourseRepository(BaseRepository):
    #Database layer for course records. Each course is linked to one teacher.

    # Loads every course sorted by ID (ascending).
    def read_all(self) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT c.course_id,c.course_code,c.course_name,c.teacher_id,CONCAT(t.first_name,' ',t.last_name) AS teacher_name,"
            "c.credits,c.semester,c.max_students FROM courses c JOIN teachers t ON t.teacher_id=c.teacher_id ORDER BY c.course_id"
        )

    #Creates a new course record.
    def create(self, args: tuple[Any, ...]) -> bool:
        code, name, teacher_id, credits, semester, max_students = args
        return self.execute_statement(
            "INSERT INTO courses (course_code,course_name,teacher_id,credits,semester,max_students) VALUES (%s,%s,%s,%s,%s,%s)",
            (code, name, teacher_id, credits, semester, max_students),
        )

    # Updates an existing course record.
    def update(self, args: tuple[Any, ...]) -> bool:
        cid, code, name, teacher_id, credits, semester, max_students = args
        return self.execute_statement(
            "UPDATE courses SET course_code=%s,course_name=%s,teacher_id=%s,credits=%s,semester=%s,max_students=%s WHERE course_id=%s",
            (code, name, teacher_id, credits, semester, max_students, cid),
        )

    # Deletes a course record.
    def delete(self, course_id: int) -> bool:
        return self.execute_statement("DELETE FROM courses WHERE course_id=%s", (course_id,))


class RegistrationRepository(BaseRepository):
    # Handles enrollments, basically linking a student to a course.

    # Loads all registrations sorted by ID (ascending).
    def read_all(self) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT r.registration_id,r.student_id,r.course_id,CONCAT(s.first_name,' ',s.last_name) AS student_name,s.group_name,"
            "c.course_name,c.course_code,CONCAT(t.first_name,' ',t.last_name) AS teacher_name,r.registered_at FROM registrations r "
            "JOIN students s ON s.student_id=r.student_id JOIN courses c ON c.course_id=r.course_id JOIN teachers t ON t.teacher_id=c.teacher_id ORDER BY r.registration_id"
        )

    # Creates a new registration record.
    def create(self, student_id: int, course_id: int) -> bool:
        with self._db.connection() as c:
            c.execute(
                "SELECT c.max_students,COUNT(r.registration_id) AS registered FROM courses c LEFT JOIN registrations r ON r.course_id=c.course_id WHERE c.course_id=%s GROUP BY c.course_id,c.max_students",
                (course_id,),
            )
            row = c.fetchone()
            if not row:
                raise DatabaseError("Selected course does not exist.")
            if row["registered"] >= row["max_students"]:
                raise DatabaseError("Course capacity has already been reached.")
            c.execute("INSERT INTO registrations (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        return True

    # Deletes a registration record.
    def delete(self, registration_id: int) -> bool:
        return self.execute_statement("DELETE FROM registrations WHERE registration_id=%s", (registration_id,))


class GradeRepository(BaseRepository):
    # Handles grades for enrollments. Each grade ties to one registration_id.

    # Loads all grades sorted by registration ID (ascending).
    def read_all(self) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT r.registration_id,CONCAT(s.first_name,' ',s.last_name) AS student_name,s.group_name,c.course_name,c.course_code,"
            "g.grade,g.letter_grade,g.graded_at FROM registrations r JOIN students s ON s.student_id=r.student_id JOIN courses c ON c.course_id=r.course_id "
            "LEFT JOIN grades g ON g.registration_id=r.registration_id ORDER BY r.registration_id"
        )

    #Creates or updates a grade record.
    def upsert(self, args: tuple[Any, ...]) -> bool:
        rid, grade, letter_grade, _c = args
        return self.execute_statement(
            "INSERT INTO grades (registration_id,grade,letter_grade) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE grade=VALUES(grade),letter_grade=VALUES(letter_grade),graded_at=CURRENT_TIMESTAMP",
            (rid, grade, letter_grade),
        )

    #Loads all grades for a specific student sorted by course name.
    def read_for_student(self, student_id: int) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT c.course_name,c.course_code,c.semester,CONCAT(t.first_name,' ',t.last_name) AS teacher_name,g.grade,g.letter_grade,g.graded_at "
            "FROM registrations r JOIN courses c ON c.course_id=r.course_id JOIN teachers t ON t.teacher_id=c.teacher_id "
            "LEFT JOIN grades g ON g.registration_id=r.registration_id WHERE r.student_id=%s ORDER BY c.course_name",
            (student_id,),
        )


class AttendanceRepository(BaseRepository):
    # Tracks attendance for enrollment per day. Each row is one student on one course on one date.

    # Loads all attendance records sorted by ID (ascending).
    def read_all(self) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT a.attendance_id,CONCAT(s.first_name,' ',s.last_name) AS student_name,s.group_name,c.course_name,c.course_code,a.att_date,a.status "
            "FROM attendance a JOIN registrations r ON r.registration_id=a.registration_id JOIN students s ON s.student_id=r.student_id "
            "JOIN courses c ON c.course_id=r.course_id ORDER BY a.attendance_id"
        )

    #Creates or updates an attendance record.
    def upsert(self, args: tuple[Any, ...]) -> bool:
        rid, att_date, status = args
        return self.execute_statement(
            "INSERT INTO attendance (registration_id,att_date,status) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE status=VALUES(status)",
            (rid, att_date, status),
        )

    #Deletes an attendance record.
    def delete(self, attendance_id: int) -> bool:
        return self.execute_statement("DELETE FROM attendance WHERE attendance_id=%s", (attendance_id,))

    #Loads all attendance records for a specific student sorted by date.
    def read_for_student(self, student_id: int) -> list[dict[str, Any]]:
        return self.fetch_all_rows(
            "SELECT c.course_name,c.course_code,a.att_date,a.status FROM attendance a JOIN registrations r ON r.registration_id=a.registration_id "
            "JOIN courses c ON c.course_id=r.course_id WHERE r.student_id=%s ORDER BY a.att_date DESC",
            (student_id,),
        )


class GroupRepository(BaseRepository):
    #This one is a read-only reporting. 
    def read_group_data(self, group_name: str) -> list[dict[str, Any]]:
        # For one class group returns every student in that group and each course they are attending.
        return self.fetch_all_rows(
            "SELECT CONCAT(s.first_name,' ',s.last_name) AS student_name,s.group_name,c.course_name,c.course_code FROM registrations r "
            "JOIN students s ON s.student_id=r.student_id JOIN courses c ON c.course_id=r.course_id WHERE s.group_name=%s ORDER BY s.last_name,c.course_name",
            (group_name,),
        )


class ProcedureGateway:
    #This is a single entry point the GUI and CLI use for all database work.

    #This init builds one database manager and one instance of each repository.
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self._db = db or DatabaseManager()
        self.auth = AuthRepository(self._db)
        self.students = StudentRepository(self._db)
        self.teachers = TeacherRepository(self._db)
        self.courses = CourseRepository(self._db)
        self.registrations = RegistrationRepository(self._db)
        self.grades = GradeRepository(self._db)
        self.attendance = AttendanceRepository(self._db)
        self.groups = GroupRepository(self._db)
        gw = self
        self._routes: dict[str, Callable[[tuple[Any, ...]], Any]] = {
            "sp_authenticate": lambda a: gw.auth.authenticate(*a),
            "sp_read_students": lambda a: gw.students.read_all(),
            "sp_create_student": gw.students.create,
            "sp_update_student": gw.students.update,
            "sp_delete_student": lambda a: gw.students.delete(a[0]),
            "sp_read_teachers": lambda a: gw.teachers.read_all(),
            "sp_create_teacher": gw.teachers.create,
            "sp_update_teacher": gw.teachers.update,
            "sp_delete_teacher": lambda a: gw.teachers.delete(a[0]),
            "sp_read_courses": lambda a: gw.courses.read_all(),
            "sp_create_course": gw.courses.create,
            "sp_update_course": gw.courses.update,
            "sp_delete_course": lambda a: gw.courses.delete(a[0]),
            "sp_read_registrations": lambda a: gw.registrations.read_all(),
            "sp_create_registration": lambda a: gw.registrations.create(*a),
            "sp_delete_registration": lambda a: gw.registrations.delete(a[0]),
            "sp_read_grades": lambda a: gw.grades.read_all(),
            "sp_upsert_grade": gw.grades.upsert,
            "sp_read_student_grades": lambda a: gw.grades.read_for_student(a[0]),
            "sp_read_attendance": lambda a: gw.attendance.read_all(),
            "sp_upsert_attendance": gw.attendance.upsert,
            "sp_delete_attendance": lambda a: gw.attendance.delete(a[0]),
            "sp_read_student_attendance": lambda a: gw.attendance.read_for_student(a[0]),
            "sp_read_group_data": lambda a: gw.groups.read_group_data(a[0]),
        }

    # This is what callers actually invoke
    def run(self, proc_name: str, args: tuple[Any, ...] = ()) -> Any:
        # So data of databases, tables, etc exist.
        self._db.ensure_schema()
        # Calls that handler with args as a tuple and returns whatever the repository returns
        if proc_name not in self._routes:
            raise DatabaseError(f"Unknown database operation: {proc_name}")
        return self._routes[proc_name](tuple(args))


DB_GATEWAY = ProcedureGateway()
#Creates one shared gateway for when the module loads. Every part of the app that imorts a database uses this instanc.e


def call_proc(proc_name: str, args: tuple = (), fetch: bool = True):
    #This is just what GUI calls to talk to the database.
    del fetch
    try:
        return DB_GATEWAY.run(proc_name, args)
    except DatabaseError as exc:
        messagebox.showerror("Database Error", str(exc))
        return None
