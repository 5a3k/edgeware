import customtkinter as tk
from tkinter import ttk, messagebox
import win32gui
import time
import pyclip
import keyboard
import random
import string
import requests


# Tabs
tk.set_appearance_mode("light")
tk.set_default_color_theme("blue")
root = tk.CTk()
root.title("Edgeware v0.01 Beta")
root.geometry("400x265")
root.wm_attributes("-topmost", True)
root.iconbitmap("logo.ico")

tabs = tk.CTkTabview(root)
cmdline = tabs.add("Console")
roapi = tabs.add("Roblox API")
settings = tabs.add("Settings")
tabs.pack(expand=1, fill="both")


class Roapi:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.session.cookies.set(".ROBLOSECURITY", self.cookie)
        self.canceled = False

        csrf_token = self.session.post("https://auth.roblox.com/v2/logout").headers.get('X-CSRF-TOKEN')
        if not csrf_token:
            self.canceled = True
            return

        self.session.headers.update({
            "x-csrf-token": csrf_token,
            "Content-Type": "application/json"
        })

        self.user_id = self.get_user_id()

    def get_user_id(self):
        response = self.session.get("https://users.roblox.com/v1/users/authenticated")
        if response.status_code == 200:
            return response.json()["id"]
        else:
            self.canceled = True
            raise Exception("Failed to retrieve user ID. Check your .ROBLOSECURITY cookie.")

    def get_friends(self, target_user_id):
        response = self.session.get(f"https://friends.roblox.com/v1/users/{target_user_id}/friends")
        if response.status_code == 200:
            friends_data = response.json()
            return friends_data["data"]
        else:
            print("Failed to retrieve friends. Status Code:", response.status_code)
            print("Response Content:", response.text)
            return []

    def create_conversation(self, target_user_id):
        while True:
            response = self.session.post("https://apis.roblox.com/platform-chat-api/v1/create-conversations", json={
                "conversations": [
                    {
                        "type": "one_to_one",
                        "participant_user_ids": [target_user_id]
                    }
                ],
                "include_user_data": True
            })

            if response.status_code == 200:
                return response.json()["conversations"]
            else:
                print("create_conversation | Failed or rate limited. Retrying in 60 seconds.")
                time.sleep(60)

    def send_message(self, conversation_id, message_content):
        while True:
            response = self.session.post("https://apis.roblox.com/platform-chat-api/v1/send-messages", json={
                "conversation_id": conversation_id,
                "messages": [
                    {"content": message_content}
                ]
            })

            if response.status_code == 200:
                return
            else:
                print("send_message | Failed or rate limited. Retrying in 60 seconds.")
                time.sleep(60)

    def get_badges(self, target_user_id):
        badges = []
        next_page_cursor = ""
        while True:
            response = self.session.get(
                f"https://badges.roblox.com/v1/users/{target_user_id}/badges",
                params={"limit": 100, "sortOrder": "Asc", "cursor": next_page_cursor},
            )

            if response.status_code == 200:
                data = response.json()
                badges.extend(data["data"])
                next_page_cursor = data.get("nextPageCursor", "")
                if not next_page_cursor:
                    break
            else:
                raise Exception("Failed to fetch badges.")
        return badges

    def delete_badge(self, badge_id):
        while True:
            response = self.session.delete(f"https://badges.roblox.com/v1/user/badges/{badge_id}")
            if response.status_code == 200:
                break
            else:
                print(f"delete_badge | Rate limited. Retrying in 30 seconds.")
                time.sleep(30)

    def fetch_all_servers(self, place_id):
        params = {
            "sortOrder": "Desc",
            "excludeFullGames": False,
            "limit": 100
        }
        cursor = ""
        all_servers = []

        while True:
            if cursor:
                params["cursor"] = cursor
            else:
                params.pop("cursor", None)

            try:
                response = self.session.get(
                    f"https://games.roblox.com/v1/games/{place_id}/servers/Public",
                    params=params,
                )
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    print("fetch_all_servers | Rate limited. Retrying in 30 seconds.")
                    time.sleep(30)
                    continue
                else:
                    raise

            data = response.json()

            if "data" in data and isinstance(data["data"], list):
                all_servers.extend(data["data"])

            cursor = data.get("nextPageCursor")
            if not cursor:
                break

        return all_servers


def rng(length):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def new_line(pre, post):
    return pre + (" " * (200 - (len(pre) + len(post)))) + post


class Roblox:
    def __init__(self, delay=0.03):
        self.delay = delay

    def reset(self):
        for i in range(2):
            weird = ""
            for i in range(5):
                weird += rng(8 - i) + "؁؁؁؁؁ ؁؁؁؁؁"
            self.send("/e ؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁؁ " + weird)

    def focus(self):
        handle = win32gui.FindWindow(None, "Roblox")
        if handle == 0:
            messagebox.showerror("Error", "Roblox window not found!")
            return False
        win32gui.SetForegroundWindow(handle)
        time.sleep(self.delay)
        return True

    def send(self, msg):
        keyboard.press_and_release("/")
        time.sleep(self.delay)
        pyclip.copy(msg)
        keyboard.send("ctrl+v")
        time.sleep(self.delay)
        keyboard.press_and_release("enter")
        time.sleep(self.delay)


# Command registry
commands = {}
roblox = Roblox()
isLegacy = True


def command():
    def wrapper(func):
        def wrapped(*args):
            return func(*args)
        commands[func.__name__] = wrapped
        return wrapped
    return wrapper


@command()
def chat(*args):
    message = " ".join(args)
    if roblox.focus():
        log_message(f"Message sent: {message}")
        roblox.send(message)


@command()
def reset():
    if roblox.focus():
        roblox.reset()
        log_message("The filter was reset.")


@command()
def swatsika():
    if roblox.focus():
        if isLegacy:
            roblox.send("⬛⬛⬛⬜⬛⬛⬛⬛⬛⬛⬛ ৌৌ⬛⬛⬛⬜⬛⬛⬛⬛⬛⬛⬛ ৌৌ⬛⬛⬛⬜⬛⬛⬛⬛⬛⬛⬛ ৌৌ⬛⬛⬛⬜⬛⬛⬛⬜⬜⬜⬜ ৌৌ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ ৌৌ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ ৌৌ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ ৌৌ⬜⬜⬜⬜⬛⬛⬛⬜⬛⬛⬛ ৌৌ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛⬛ ৌৌ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛⬛ ৌৌ⬛⬛⬛⬛⬛⬛⬛⬜⬛⬛⬛")
        else:
            roblox.send("⬜⬜⬜🔳⬜🔳🔳🔳⬜⬜⬜")
            roblox.send("⬜⬜⬜🔳⬜🔳⬜⬜⬜⬜⬜")
            roblox.send("⬜⬜⬜🔳🔳🔳🔳🔳⬜⬜⬜")
            roblox.send("⬜⬜⬜⬜⬜🔳⬜🔳⬜⬜⬜")
            roblox.send("⬜⬜⬜🔳🔳🔳⬜🔳⬜⬜⬜")


weird = "\u09CC"


@command()
def fakeadmin():
    if roblox.focus():
        if isLegacy:
            roblox.send(f";admin all {weird * 43}⸻⸻⸻⸻⸻ {weird * 56}► You are now admin! {weird * 57}⸻⸻⸻⸻⸻")
        else:
            roblox.send(";admin all                                                                                                                                                                    ► You are now admin!")


@command()
def fakeadmin2():
    if roblox.focus():
        if isLegacy:
            roblox.send(f";admin all {weird * 44}{{Team}} You are now on the 'Admins' team.")
        else:
            roblox.send(new_line(";admin all", "{Team} You are now on the 'Admins' team."))


@command()
def fakechat(*args):
    message = " ".join(args)
    if roblox.focus():
        if isLegacy:
            roblox.send(f" {weird * 44}{message}")
        else:
            roblox.send(new_line("hi", message))


@command()
def lbc():
    if roblox.focus() and isLegacy:
        roblox.send(f" {weird * 199}")


@command()
def bbc():
    if roblox.focus() and isLegacy:
        wtf = f" {weird * 105} {'⸻' * 1} {'⸻' * 22} {'⸻' * 22} {'⸻' * 22} {'⸻' * 22}"
        roblox.send(wtf)


@command()
def error():
    if roblox.focus() and isLegacy:
        for i in range(3):
            roblox.send("　")


alphabet = {
    "a": [
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
    ],
    "b": [
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳🔳⬜",
        "🔳⬜🔳",
        "🔳🔳🔳",
    ],
    "c": [
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳⬜⬜",
        "🔳⬜⬜",
        "🔳🔳🔳",
    ],
    "d": [
        "🔳🔳⬜",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳🔳⬜",
    ],
    "e": [
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳🔳🔳",
    ],
    "f": [
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳⬜⬜",
    ],
    "g": [
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳🔳🔳",
    ],
    "h": [
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
    ],
    "i": [
        "🔳",
        "⬜",
        "🔳",
        "🔳",
        "🔳",
    ],
    "j": [
        "🔳🔳",
        "⬜🔳",
        "⬜🔳",
        "⬜🔳",
        "🔳🔳",
    ],
    "k": [
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳🔳⬜",
        "🔳⬜🔳",
        "🔳⬜🔳",
    ],
    "l": [
        "🔳⬜",
        "🔳⬜",
        "🔳⬜",
        "🔳⬜",
        "🔳🔳",
    ],
    "m": [
        "🔳🔳⬜🔳🔳",
        "🔳⬜🔳⬜🔳",
        "🔳⬜⬜⬜🔳",
        "🔳⬜⬜⬜🔳",
        "🔳⬜⬜⬜🔳",
    ],
    "n": [
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
    ],
    "o": [
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳🔳🔳",
    ],
    "p": [
        "🔳🔳⬜",
        "🔳⬜🔳",
        "🔳🔳⬜",
        "🔳⬜⬜",
        "🔳⬜⬜",
    ],
    "q": [
        "🔳🔳🔳⬜",
        "🔳⬜🔳⬜",
        "🔳⬜🔳⬜",
        "🔳⬜🔳⬜",
        "⬜🔳⬜🔳",
    ],
    "r": [
        "🔳🔳🔳",
        "🔳⬜🔳",
        "🔳🔳⬜",
        "🔳⬜🔳",
        "🔳⬜🔳",
    ],
    "s": [
        "🔳🔳🔳",
        "🔳⬜⬜",
        "🔳🔳🔳",
        "⬜⬜🔳",
        "🔳🔳🔳",
    ],
    "t": [
        "🔳🔳🔳",
        "⬜🔳⬜",
        "⬜🔳⬜",
        "⬜🔳⬜",
        "⬜🔳⬜",
    ],
    "u": [
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳🔳🔳",
    ],
    "v": [
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "🔳⬜🔳",
        "⬜🔳⬜",
    ],
    "w": [
        "🔳⬜⬜⬜🔳",
        "🔳⬜⬜⬜🔳",
        "🔳⬜⬜⬜🔳",
        "🔳⬜🔳⬜🔳",
        "⬜🔳⬜🔳",
    ],
    "x": [
        "🔳⬜🔳",
        "🔳⬜🔳",
        "⬜🔳⬜",
        "🔳⬜🔳",
        "🔳⬜🔳",
    ],
    "y": [
        "🔳⬜🔳",
        "🔳⬜🔳",
        "⬜🔳⬜",
        "⬜🔳⬜",
        "⬜🔳⬜",
    ],
    "z": [
        "🔳🔳🔳",
        "⬜⬜🔳",
        "⬜🔳⬜",
        "🔳⬜⬜",
        "🔳🔳🔳",
    ],
}


def gen(query):
    total = ["", "", "", "", ""]

    for y in range(len(query)):
        char = query[y]
        if char in alphabet:
            emojis = alphabet[char]
            for i in range(len(emojis)):
                total[i] += emojis[i]
                if y < len(query) - 1:
                    total[i] += "⬜"

    if isLegacy:
        text = ""
        for i in range(len(total)):
            line = total[i]
            text += line
            if i < len(total) - 1:
                text += " " + "ৌ" * ((12 - len(line)) * 2)
        roblox.send(text)
    else:
        for line in total:
            roblox.send(line)


@command()
def bigchat(*args):
    message = " ".join(args)
    if roblox.focus():
        gen(message)


@command()
def pp():
    if roblox.focus() and isLegacy:
        roblox.send("⬜⬛⬛⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ ⬛⬜⬜⬜⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ ⬛⬜⬜⬜⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬜ ⬛⬜⬜⬜⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬛ ⬜⬛⬛⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬛ ⬛⬜⬜⬜⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬛ ⬛⬜⬜⬜⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬜ ⬛⬜⬜⬜⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ ⬜⬛⬛⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜")


bypasses = {
    "fag": "ꜰᴀɢ",
    "fucking": "ꜰᴜᴄᴋIɴɢ",
    "fuck": "ꜰᴜᴄᴋ",
    "zoophile": "zoophiIe",
    "kill you": "ᴋɪʟʟ ʏᴏᴜ",
    "kill": "ᴋɪʟʟ",
    "yourself": "ʏᴏᴜʀsᴇIꜰ",
    "dick": "ᴅiᴄᴋ",
    "cock": "ᴄᴏᴄᴋ",
    "suck my": "sᴜᴄᴋ ᴍʏ",
    "suck": "sᴜᴄᴋ",
    "eat my": "ᴇᴀᴛ ᴍʏ",
    "damn": "ᴅᴀᴍɴ",
    "twink": "ᴛᴡɪɴᴋ",
    "slave": "sIᴀᴠᴇ",
    "dyke": "ᴅʏᴋᴇ",
    "pissed": "ᴘissed",
    "sandwich": "saɴdwich",
    "anal": "anaI",
    "pervert": "ᴘᴇʀᴠᴇʀt",
    "white knight": "ᴡhite knight",
    "twerk": "ᴛᴡeʀᴋ",
    "tiktok": "ᴛiᴋᴛᴏᴋ",
    "black": "ʙIᴀᴄᴋ",
    "gf": "ɢꜰ",
    "my girlfriend": "ᴍʏ ɢɪʀʟꜰʀɪᴇɴᴅ",
    "girlfriend": "ɢɪʀʟꜰʀɪᴇɴᴅ",
    "swatsika": "sᴡᴀsᴛɪᴋᴀ",
    "gay": "ɢᴀʏ",
    "naked": "ɴᴀᴋᴇᴅ",
    "rape": "ʀᴀʏᴘᴇ",
    "meat": "ᴍᴇᴀᴛ",
    "cum": "ᴄᴜᴍ",
}


def convert(query):
    for i in bypasses:
        query = query.replace(i, bypasses[i])
    return query


@command()
def by(*args):
    message = " ".join(args)
    if roblox.focus():
        roblox.send(convert(message))


@command()
def cmds():
    log_message(", ".join(commands))


@command()
def clear():
    console_output.configure(state=tk.NORMAL)
    console_output.delete(1.0, tk.END)
    console_output.configure(state=tk.DISABLED)


def log_message(message):
    console_output.configure(state=tk.NORMAL)
    console_output.insert(tk.END, message + "\n")
    console_output.configure(state=tk.DISABLED)
    console_output.yview(tk.END)


def execute_command():
    cmd = entry.get().strip()
    entry.delete(0, tk.END)
    parts = cmd.split(" ")
    cmd_name, args = parts[0], parts[1:]
    if cmd_name in commands:
        commands[cmd_name](*args)
    else:
        log_message(f"Unknown command: {cmd}")


# Console UI


def toggle_legacy(event):
    global isLegacy
    selected_service = chat_service_combo.get()
    if selected_service == "LegacyChatService":
        isLegacy = True
    else:
        isLegacy = False


console_output = tk.CTkTextbox(cmdline, height=10, state=tk.DISABLED)
console_output.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

entry = tk.CTkEntry(cmdline)
entry.pack(fill=tk.X, padx=5, pady=0)
entry.bind("<Return>", lambda event: execute_command())

button_frame = tk.CTkFrame(cmdline)
button_frame.pack(pady=5, side=tk.TOP, anchor="w")

send_btn = tk.CTkButton(button_frame, text="Send", command=execute_command)
send_btn.pack(side=tk.LEFT, padx=5)

chat_service_combo = tk.CTkComboBox(button_frame, values=["LegacyChatService", "TextChatService"], command=toggle_legacy)
chat_service_combo.set("LegacyChatService")
chat_service_combo.pack(pady=5, side=tk.LEFT)

# Authentication Frame
robloxapi = None


def authenticate():
    cookie = cookie_entry.get()
    try:
        global robloxapi
        robloxapi = Roapi(cookie)
        if robloxapi.canceled:
            messagebox.showerror("Error", "Failed to authenticate cookie.")
        else:
            auth_frame.pack_forget()
            api_frame.pack(expand=1, fill="both")
            messagebox.showinfo("Success", "Authenticated successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))


auth_frame = tk.CTkFrame(roapi)
auth_frame.pack(expand=1, fill="both")

cookie_label = tk.CTkLabel(auth_frame, text="Enter .ROBLOSECURITY Cookie:")
cookie_label.pack(pady=5)

cookie_entry = tk.CTkEntry(auth_frame, width=50)
cookie_entry.pack(pady=5)

auth_button = tk.CTkButton(auth_frame, text="Authenticate", command=authenticate)
auth_button.pack(pady=5)

# API Frame (Hidden until authentication)


def mass_message():
    try:
        content = message_entry.get()
        if not content:
            messagebox.showerror("Error", "Message content cannot be empty.")
            return

        friends = robloxapi.get_friends(robloxapi.user_id)
        for i, friend in enumerate(friends, start=1):
            conv_id = robloxapi.create_conversation(friend["id"])[0]["id"]
            robloxapi.send_message(conv_id, content)
        messagebox.showinfo("Edgeware", f"Sent all friends msg: {content}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send messages: {e}")


def delete_badges():
    try:
        badges = robloxapi.get_badges(robloxapi.user_id)
        for i, badge in enumerate(badges, start=1):
            robloxapi.delete_badge(badge["id"])
        messagebox.showinfo("Edgeware", "Deleted all badges!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete badges: {e}")


def find_server():
    try:
        place_id = place_entry.get()
        if not place_id.isdigit():
            messagebox.showerror("Error", "Place ID must be a number.")
            return
        place_id = int(place_id)

        servers = robloxapi.fetch_all_servers(place_id)
        if not servers:
            return

        best_server = min(servers, key=lambda server: server.get("ping", float("inf")))
        job_id = best_server["id"]
        join_url = f"https://www.roblox.com/games/start?placeId={place_id}&launchData={place_id}/{job_id}"

        pyclip.copy(join_url)
        messagebox.showinfo("Edgeware", "Copied join URL!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to find fastest server: {e}")


api_frame = tk.CTkFrame(roapi)

message_entry = tk.CTkEntry(api_frame, width=50)
message_entry.pack(pady=5)

message_button = tk.CTkButton(api_frame, text="Mass Message", command=mass_message)
message_button.pack(pady=5)

delete_button = tk.CTkButton(api_frame, text="Delete All Badges", command=delete_badges)
delete_button.pack(pady=5)

place_entry = tk.CTkEntry(api_frame, width=50)
place_entry.pack(pady=5)

server_button = tk.CTkButton(api_frame, text="Find Fastest Server", command=find_server)
server_button.pack(pady=5)


# Settings UI


def theme_method(event):
    new = theme_combo.get()
    tk.set_appearance_mode(new)


theme_combo = tk.CTkComboBox(settings, values=["system", "light", "dark"], command=theme_method)
theme_combo.set("light")
theme_combo.pack(pady=5)

root.mainloop()
