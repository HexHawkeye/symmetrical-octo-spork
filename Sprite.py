import sys
import os
import random
import time 
import traceback
from PyQt5.QtWidgets import QApplication, QLabel, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QPixmap, QTransform, QIcon
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5 import QtGui

def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        print("[UNCAUGHT EXCEPTION]")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
base_path = resource_path("tiny-hero-sprites")
icon_path = resource_path("icon.ico")


sys.excepthook = handle_exception

class Spirit(QLabel):
    def __init__(self, frame_width, frame_height, animations, start_state="walk", frame_delay=150):
        super().__init__()
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.frame_width = frame_width
        self.frame_height = frame_height
        self.animations = animations
        self.direction = 1
        self.current_frame = 0
        self.frames = []
        self.state = None
        self.walking = True
        self.flipped = False
        self.previous_state = None
        self.locked = False  # locks state switching
        self.mouse_over = False
        self.can_attack = True
        # Timers
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_frame)

        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.move_spirit)

        self.jump_timer = QTimer()
        self.jump_timer.timeout.connect(self.try_jump)
        self.jump_timer.start(1000)

        self.climb_check_timer = QTimer()
        self.climb_check_timer.timeout.connect(self.try_climb_sequence)
        self.climb_check_timer.start(3000)
        self.click_times = []

        self.drag_start_time = None
        self.drag_start_pos = None

        self.health_bar = QLabel(self)
        self.health_bar.setVisible(True)
        self.max_health = 5
        self.health = self.max_health
        self.update_health_bar()

        self.heal_timer = QTimer()
        self.heal_timer.setSingleShot(True)
        self.heal_timer.timeout.connect(self.restore_health)


        # Start state
        self.set_state(start_state)
        self.move_to_start()

    def update_health_bar(self):
        bar_height = 5
        full_width = self.frame_width
        health_ratio = self.health / self.max_health
        bar_width = max(1, int(full_width * health_ratio))  # Never 0

        # Create transparent pixmap
        pixmap = QPixmap(full_width, bar_height)
        pixmap.fill(Qt.transparent)

        # Paint the health bar
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(Qt.red)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, bar_width, bar_height)
        painter.end()

        # Update QLabel
        self.health_bar.setPixmap(pixmap)
        self.health_bar.setFixedSize(full_width, bar_height)
        self.health_bar.move(0, 2)   # Move it *above* the sprite
        self.health_bar.raise_()
        self.health_bar.setVisible(True)
        self.health_bar.raise_()

        
        
    def closeEvent(self, event):
        print("[DEBUG] Spirit closing. Timer active:", self.heal_timer.isActive())
        super().closeEvent(event)

    def enterEvent(self, event):
        if self.locked or self.mouse_over or not self.can_attack or self.state == "hurt":
            return

        self.mouse_over = True
        self.can_attack = False  # disable until reset

        if self.state == "walk":
            self.set_state("walk_attack")
            QTimer.singleShot(700, lambda: self.resume_from_attack("walk"))

        elif self.state == "run":
            self.set_state("walk_attack")
            QTimer.singleShot(700, lambda: self.resume_from_attack("run"))

        else:
            attack_state = random.choice(["attack1", "attack2"])
            previous = self.state if self.state in ("walk", "run") else "walk"
            self.set_state(attack_state)
            QTimer.singleShot(700, lambda: self.resume_from_attack(previous))

    def resume_from_attack(self, next_state):
        if self.locked or self.state in ("hurt", "death"):
            return  # Don't change state during hurt/death
        self.set_state(next_state)
        QTimer.singleShot(1000, lambda: setattr(self, 'can_attack', True))

    def restore_state(self):
        if not self.locked and self.previous_state:
            self.set_state(self.previous_state)

    def leaveEvent(self, event):
        self.mouse_over = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_time = time.time()
            self.drag_start_pos = event.globalPos()
            self.dragging = True
            self.drag_offset = event.pos()
            self.setWindowOpacity(0.7)

            # Stop movement and fall/climb
            self.move_timer.stop()
            if hasattr(self, 'climb_timer') and self.climb_timer.isActive():
                self.climb_timer.stop()
            if hasattr(self, 'climb_down_timer') and self.climb_down_timer.isActive():
                self.climb_down_timer.stop()
            if hasattr(self, 'fall_timer') and self.fall_timer.isActive():
                self.fall_timer.stop()

            self.locked = True


    def mouseMoveEvent(self, event):
        if getattr(self, 'dragging', False):
            self.move(self.mapToGlobal(event.pos() - self.drag_offset))
            self.update_health_bar()  # Update health bar position

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setWindowOpacity(1.0)

            end_time = time.time()
            end_pos = event.globalPos()

            time_diff = end_time - getattr(self, 'drag_start_time', 0)
            dist = (end_pos - getattr(self, 'drag_start_pos', event.globalPos())).manhattanLength()

            if time_diff < 0.3 and dist < 10:
                # Treat as a click: apply damage
                self.health -= 1
                self.update_health_bar()
                self.heal_timer.start(10000)  # 10 seconds

                if self.health <= 0:
                    self.locked = False
                    self.trigger_death_from_clicks()
                    return

                if  self.state not in ("hurt", "death"):
                    self.locked = False
                    saved_previous = self.state if self.state in ("walk", "run") else "walk"
                    self.set_state("hurt")
                    QTimer.singleShot(700, lambda: self.restore_after_hurt(saved_previous))

            else:
                self.set_state("idle")
                self.start_falling()

    def restore_health(self):
        
        
        if self.health < self.max_health:
            self.health = self.max_health
            self.update_health_bar()
            self.set_state("idle")  # or custom "heal" state
            QTimer.singleShot(500, lambda: self.set_state("walk"))
            

    def restore_after_hurt(self, previous):
        
        self.locked = False  # Always unlock!
        if self.state == "hurt":
            self.set_state(previous)

    def trigger_death_from_clicks(self):
        if self.locked:
            return  # Already dying

        self.locked = True

        # Clear any other queued QTimers by reinitializing (soft way)
        self.animation_timer.stop()
        self.move_timer.stop()
        self.jump_timer.stop()
        self.climb_check_timer.stop()

        self.set_state("death")
        QTimer.singleShot(2000, self.reset_spirit)


    def try_climb_sequence(self):
        if self.locked:
            return
        if self.state not in ("walk", "run", "idle", "hurt"):
            return
        screen = self.screen_rect()
        at_left_edge = self.x() <= 0
        at_right_edge = self.x() + self.frame_width >= screen.width()

        if at_left_edge or at_right_edge:
            if random.random() < 1.0:  # 100% chance at edge
                self.set_state("climb")
                self.start_climbing()

    def start_climbing(self):
        self.locked = True
        self.move_timer.stop()
        self.jump_timer.stop()
        self.climb_check_timer.stop()
        
        self.climb_timer = QTimer()
        self.climb_timer.timeout.connect(self.climb_step)
        self.climb_timer.start(50)

    def climb_step(self):
        x = 0 if self.direction == -1 else self.screen_rect().width() - self.frame_width
        y = self.y() - 5

        if y <= 0:
            self.climb_timer.stop()

            if random.random() < 0.5:
                self.set_state("idle")
                self.start_falling()
            else:
                self.set_state("climb")
                self.start_climbing_down()
        else:
            self.move(x, y)
            self.update_health_bar()

    def start_climbing_down(self):
        self.climb_down_timer = QTimer()
        self.climb_down_timer.timeout.connect(self.climb_down_step)
        self.climb_down_timer.start(50)

    def climb_down_step(self):
        x = 0 if self.direction == -1 else self.screen_rect().width() - self.frame_width
        y = self.y() + 5
        screen = self.screen_rect()

        if y >= screen.height() - self.frame_height - 50:
            self.climb_down_timer.stop()
            self.unlock_and_resume()
        else:
            self.move(x, y)
            self.update_health_bar()

    def start_falling(self):
        self.fall_start_y = self.y()  # record where fall started
        self.fall_timer = QTimer()
        self.fall_timer.timeout.connect(self.fall_step)
        self.fall_timer.start(50)

    def fall_step(self):
        screen = self.screen_rect()
        y = self.y() + 6
        x = self.x()
        self.move(x, y)
        self.update_health_bar()

        fall_distance = y - self.fall_start_y
        half_screen = screen.height() // 2
        bottom = screen.bottom() - self.frame_height - 50

        if y >= bottom:
            self.fall_timer.stop()

            if fall_distance > half_screen:
                self.set_state("death")
                QTimer.singleShot(1200, self.reset_spirit)
            else:
                if self.health > 0:
                    self.health -= 1
                    self.health = max(0, self.health)  # Clamp to 0
                    self.update_health_bar()
                    self.heal_timer.start(10000)
                    

                    if self.health == 0:
                        self.locked = False
                        self.trigger_death_from_clicks()
                        return
                    self.locked = False
                    self.set_state("hurt")
                    QTimer.singleShot(700, self.unlock_and_resume)




    def reset_spirit(self):
        self.locked = False
        self.health = self.max_health
        self.update_health_bar()

        screen = self.screen_rect()
        self.direction = random.choice([-1, 1])
        x = screen.left() if self.direction == 1 else screen.right() - self.frame_width
        y = screen.bottom() - self.frame_height - 50
        self.move(x, y)
        try:
            self.set_state("walk")
        except Exception as e:
            print(f"[ERROR] Failed to reset state: {e}")
            self.set_state("idle")
        self.update_health_bar()

    def unlock_and_resume(self):
        self.locked = False
        self.jump_timer.start(1000)
        self.climb_check_timer.start(3000)
        self.set_state("walk")

    def move_to_start(self):
        screen = self.screen_rect()
        self.move(0, screen.height() - self.frame_height - 50)
        self.update_health_bar() 

    def screen_rect(self):
        pos = self.frameGeometry().center()
        screen = QApplication.screenAt(pos)
        if screen:
            return screen.availableGeometry()
        return QApplication.primaryScreen().availableGeometry()

    def safe_set_state(self, state):
        try:
            self.set_state(state)
        except Exception as e:
            print(f"[ERROR] Failed to set state: {e}")
            QTimer.singleShot(700, lambda: self.safe_set_state("walk"))

    def set_state(self, new_state):
        if new_state not in self.animations:
            print(f"[ERROR] Animation state '{new_state}' not found.")
            return

        if self.locked and new_state != "death":
            return  # Prevent interruptions during death/climb
        
        if new_state not in self.animations:
            print(f"State {new_state} not found!")
            return

        if self.state == "jump":
            self.previous_state = self.previous_state or "walk"
        elif self.state != "jump":
            self.previous_state = self.state

        self.state = new_state
        sprite_path, frame_count = self.animations[new_state]

        try:
            pixmap = QPixmap(sprite_path)
            if pixmap.isNull():
                raise FileNotFoundError(f"Missing sprite: {sprite_path}")
        except Exception as e:
            print(f"[ERROR] Failed to load sprite '{sprite_path}': {e}")
            return

        self.frames = [
            pixmap.copy(QRect(i * self.frame_width, 0, self.frame_width, self.frame_height))
            for i in range(frame_count)
        ]

        if self.direction == -1:
            self.frames = [frame.transformed(QTransform().scale(-1, 1)) for frame in self.frames]

        self.current_frame = 0
        self.setPixmap(self.frames[0])
        self.resize(self.frame_width, self.frame_height)

        # Slow down death animation
        if new_state == "death":
            self.animation_timer.start(300)  # slower frame rate
        else:
            self.animation_timer.start(150)  # default speed

        if new_state in ("walk", "run"):
            self.move_timer.start(50)
        else:
            self.move_timer.stop()


    def update_frame(self):
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.setPixmap(self.frames[self.current_frame])

    def move_spirit(self):
        screen = self.screen_rect()
        x = self.x() + self.direction * (3 if self.state == "walk" else 6)
        y = screen.bottom() - self.frame_height - 50
        self.move(x, y)
        self.update_health_bar()
        
        if self.state in ("walk", "run"):
            mid_screen = (screen.left() + screen.right()) // 2
            if mid_screen - 10 < self.x() < mid_screen + 10 and random.random() < 0.05:
                self.set_state("jump")
                QTimer.singleShot(700, lambda: self.set_state(self.previous_state))
                return

        if (self.direction == 1 and x + self.frame_width >= screen.right()) or \
        (self.direction == -1 and x <= screen.left()):
            self.pause_and_flip()

    def pause_and_flip(self):
        if self.locked:
            return
        self.move_timer.stop()
        if self.state == "walk":
            self.set_state("idle")
            QTimer.singleShot(1000, lambda: self.flip_and_continue("run"))
        elif self.state == "run":
            self.health -= 1
            self.update_health_bar()
            self.heal_timer.start(10000)  # 10 seconds
            if self.health <= 0:
                self.locked = False
                self.trigger_death_from_clicks()
                return
            self.set_state("hurt")
            QTimer.singleShot(1000, lambda: self.flip_and_continue("walk"))

    def flip_and_continue(self, next_state):
        if self.locked:
            return  # Prevent mid-climb flip
        self.direction *= -1
        self.set_state(next_state)

    def try_jump(self):
        if self.locked:
            return
        if self.state in ("walk", "run") and random.random() < 0.05:  # 5% chance
            self.previous_state = self.state
            self.set_state("jump")
            QTimer.singleShot(700, lambda: self.set_state(self.previous_state))
    

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # === Monster selection ===
    monster_list = ["Pink_Monster", "Owlet_Monster", "Dude_Monster"]
    selected_monster = os.environ.get("SPIRIT_CHARACTER", "RANDOM")
    monster = random.choice(monster_list) if selected_monster == "RANDOM" else selected_monster
    print(f"[INFO] Loaded spirit: {monster}")

    # === Asset path setup ===
    base_path = os.path.join(os.path.dirname(__file__), "tiny-hero-sprites")

    def sprite_path(action, frame_count):
        return os.path.join(base_path, f"{monster}/{monster}_{action}_{frame_count}.png")


    # === Animations dictionary ===
    animations = {
        "walk": (sprite_path("Walk", 6), 6),
        "run": (sprite_path("Run", 6), 6),
        "idle": (sprite_path("Idle", 4), 4),
        "jump": (sprite_path("Jump", 8), 8),
        "hurt": (sprite_path("Hurt", 4), 4),
        "climb": (sprite_path("Climb", 4), 4),
        "death": (sprite_path("Death", 8), 8),
        "attack1": (sprite_path("Attack1", 4), 4),
        "attack2": (sprite_path("Attack2", 6), 6),
        "walk_attack": (sprite_path("Walk+Attack", 6), 6),
    }

    # === Create and show spirit ===
    spirit = Spirit(
        frame_width=32,
        frame_height=32,
        animations=animations,
        start_state="walk"
    )
    spirit.show()
    spirit.update_health_bar()
    print("[DEBUG] Sprite pos:", spirit.x(), spirit.y())
    print("[DEBUG] Health bar pos:", spirit.health_bar.x(), spirit.health_bar.y())
    # === Create system tray icon ===
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(icon_path))  # Use resource path here
    tray_icon.setVisible(True)
    tray_icon.showMessage("Desktop Spirit", f"{monster.replace('_', ' ')} is active!", QSystemTrayIcon.Information, 3000)

    # === Tray menu ===
    tray_menu = QMenu()

    # === Character Selection Submenu ===
    character_menu = QMenu("Change Character")
    monster_list = ["Pink_Monster", "Owlet_Monster", "Dude_Monster"]

    def make_switch_character(monster_name):
        def switch():
            os.environ["SPIRIT_CHARACTER"] = monster_name
            os.execl(sys.executable, sys.executable, *sys.argv)
        return switch

    # Add each monster to the character submenu
    for name in monster_list:
        display_name = name.replace("_", " ")
        action = QAction(display_name, tray_menu)
        action.triggered.connect(make_switch_character(name))
        character_menu.addAction(action)

    # Add random option
    random_action = QAction("Random", tray_menu)
    random_action.triggered.connect(make_switch_character("RANDOM"))
    character_menu.addAction(random_action)

    # Add the character menu to the tray
    tray_menu.addMenu(character_menu)

    # === Quit Action ===
    tray_menu.addSeparator()
    quit_action = QAction("Quit", tray_menu)
    quit_action.triggered.connect(QApplication.quit)
    tray_menu.addAction(quit_action)

    # === Assign menu to tray icon ===
    tray_icon.setContextMenu(tray_menu)

    # === Start application ===
    sys.exit(app.exec_())

