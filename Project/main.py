#School Management System's Main.py file 
#Run by writing python main.py in terminal

# Adds readability labels for the values
from __future__ import annotations

# I use it to make the gui look more appealing
import customtkinter as ctk

# Importing other python files
from ui_tabs import (
    LoginWindow, AttendanceTab, CoursesTab, RegistrationsTab,
    StudentsTab, TeachersTab, GradesTab, MyGradesTab,
)

# Shared colors so the theme is consistent
from ui_core import GREY_L, PINK, PINK_D, PINK_L, PURE_WHITE, ROSE, TEXT


# Main window class. After login, header and tabs go inside it.
class SchoolApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Dark mode, resolution and title.
        ctk.set_appearance_mode("dark")

        self.title("School Management System")
        self.geometry("1200x750")
        self.configure(fg_color=GREY_L)

        # Filled after login and holds user's data like username, role, ids, etc.
        self.user_data = None

        # Hides the window until the login is successful
        self.withdraw()
        self.open_login()

        # Open_login creates the login popup and passes when_logged_in if the login is successful.
        # User logs in inside the LoginWindow and if it's valid, it called when_logged_in
        # When_logged_in saves the data to self.user_data and shows the main window again after what it called setup_main_screen

    
    def open_login(self):
        self.login_window = LoginWindow(self.when_logged_in)

    def when_logged_in(self, user):
        self.user_data = user
        self.deiconify()
        self.setup_main_screen()

    def setup_main_screen(self):
        #Using self.user_data to build the header and the right tabs.
        user = self.user_data
        role = user["role"]  # "teacher" and "student" control which tabs appear


        # Creating pink frame, a label, etc
        header = ctk.CTkFrame(self, fg_color=PINK, height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="School Management System",
            font=("Segoe UI", 18, "bold"),
            text_color=PURE_WHITE,
        ).pack(side="left", padx=20)

        # Getting the name from the database
        first = user.get("t_first") or user.get("s_first") or user["username"]
        last = user.get("t_last") or user.get("s_last") or ""

        # Determining the badge color based on role
        badge_color = ROSE if role == "teacher" else "#7B1FA2"

        #These lines addd the role badge, name and a logout button on the header.
        ctk.CTkLabel(
            header, text=f"  {role.title()}  ",
            font=("Segoe UI", 10, "bold"),
            text_color=PURE_WHITE, fg_color=badge_color, corner_radius=6,
        ).pack(side="right", padx=6)
        ctk.CTkLabel(
            header, text=f"{first} {last}",
            font=("Segoe UI", 13), text_color=PURE_WHITE,
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            header, text="Logout", command=self.sign_out,
            fg_color="transparent", hover_color=PINK_D,
            text_color=PURE_WHITE, font=("Segoe UI", 11), width=70,
        ).pack(side="right", padx=16)

        # It creates the tab lines and content area under the header.
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=GREY_L,
            segmented_button_fg_color=PINK_L,
            segmented_button_selected_color=PINK,
            segmented_button_selected_hover_color=ROSE,
            segmented_button_unselected_color=PINK_L,
            text_color=TEXT,
        )
        #Makes it take all the remaining space.
        self.tabs.pack(fill="both", expand=True, padx=8, pady=8)

        # Authorization is based on role: teachers get all six management tabs; students get three.
        if role == "teacher":
            for name in ("Students", "Teachers", "Courses", "Registrations", "Grades", "Attendance"):
                self.tabs.add(name)

            StudentsTab(self.tabs.tab("Students"), role).pack(fill="both", expand=True)
            TeachersTab(self.tabs.tab("Teachers"), role).pack(fill="both", expand=True)
            CoursesTab(self.tabs.tab("Courses"), role).pack(fill="both", expand=True)
            RegistrationsTab(self.tabs.tab("Registrations"), role).pack(fill="both", expand=True)
            GradesTab(self.tabs.tab("Grades")).pack(fill="both", expand=True)
            AttendanceTab(self.tabs.tab("Attendance")).pack(fill="both", expand=True)

        elif role == "student":
            for name in ("My Grades & Group", "Students", "Courses"):
                self.tabs.add(name)

            MyGradesTab(
                self.tabs.tab("My Grades & Group"),
                user["student_id"],
                user["group_name"],
            ).pack(fill="both", expand=True)
            StudentsTab(self.tabs.tab("Students"), "student").pack(fill="both", expand=True)
            CoursesTab(self.tabs.tab("Courses"), "student").pack(fill="both", expand=True)

    #Sign out
    def sign_out(self):
        self.user_data = None
        for widget in self.winfo_children():
            widget.destroy()
        self.open_login()



# Part that starts the program
if __name__ == "__main__":

    while True:
        print("\n1 = GUI (desktop)   2 = Console menu   0 = Quit")
        mode = input("Choose mode: ").strip()

        if mode == "0":
            break

        if mode == "1":
            SchoolApp().mainloop()

        elif mode == "2":
            from cli import run_console
            run_console()

        else:
            print("Invalid choice. Enter 0, 1, or 2.")
