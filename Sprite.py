import sys
import os
import random
import time 
from PyQt5.QtWidgets import QApplication, QLabel, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QPixmap, QTransform, QIcon
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5 import QtGui


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

        self.health_bar = QLabel(self)
        self.health_bar.move(0, self.frame_height + 2)
        self.max_health = 5
        self.health = self.max_health
        self.update_health_bar()

        # Start state
        self.set_state(start_state)
        self.move_to_start()

    def update_health_bar(self):
        bar_height = 5
        full_width = self.frame_width
        health_ratio = self.health / self.max_health
        bar_width = max(1, int(full_width * health_ratio))  # avoid 0 width

        # Create the bar pixmap
        pixmap = QPixmap(full_width, bar_height)
        pixmap.fill(Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setBrush(Qt.red)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, bar_width, bar_height)
        painter.end()

        # Set it on the health bar QLabel
        self.health_bar.setPixmap(pixmap)
        self.health_bar.setFixedSize(full_width, bar_height)
        self.health_bar.move(0, -bar_height - 4)
        self.health_bar.raise_()  # <- bring to front!
        self.health_bar.show()


    def enterEvent(self, event):
        if self.locked or self.mouse_over:
            return

        self.mouse_over = True

        if self.state == "walk":
            self.set_state("walk_attack")
            QTimer.singleShot(700, lambda: self.set_state("walk"))

        elif self.state == "run":
            self.set_state("walk_attack")
            QTimer.singleShot(700, lambda: self.set_state("run"))

        else:
            attack_state = random.choice(["attack1", "attack2"])
            previous = self.state if self.state in ("walk", "run") else "walk"
            self.set_state(attack_state)
            QTimer.singleShot(700, lambda: self.set_state(previous))

    def leaveEvent(self, event):
        self.mouse_over = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()
            self.setWindowOpacity(0.7)

            # Pause movement and climbing/falling logic
            self.move_timer.stop()
            if hasattr(self, 'climb_timer') and self.climb_timer.isActive():
                self.climb_timer.stop()
            if hasattr(self, 'climb_down_timer') and self.climb_down_timer.isActive():
                self.climb_down_timer.stop()
            if hasattr(self, 'fall_timer') and self.fall_timer.isActive():
                self.fall_timer.stop()

            self.locked = True  # lock all state changes while dragging
            return


    def mouseMoveEvent(self, event):
        if getattr(self, 'dragging', False):
            self.move(self.mapToGlobal(event.pos() - self.drag_offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setWindowOpacity(1.0)

            self.locked = True
            self.set_state("idle")
            self.start_falling()  # this now handles the fall correctly

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

        # Calculate fall distance
        fall_distance = y - self.fall_start_y
        half_screen = screen.height() // 2
        bottom = screen.bottom() - self.frame_height - 50

        if y >= bottom:
            self.fall_timer.stop()

            if fall_distance > half_screen:
                self.set_state("death")
                QTimer.singleShot(1200, self.reset_spirit)
            else:
                self.unlock_and_resume()


    def reset_spirit(self):
        self.locked = False
        self.health = self.max_health
        self.update_health_bar()

        screen = self.screen_rect()
        self.direction = random.choice([-1, 1])
        x = screen.left() if self.direction == 1 else screen.right() - self.frame_width
        y = screen.bottom() - self.frame_height - 50
        self.move(x, y)
        self.set_state("walk")

    def unlock_and_resume(self):
        self.locked = False
        self.jump_timer.start(1000)
        self.climb_check_timer.start(3000)
        self.set_state("walk")

    def move_to_start(self):
        screen = self.screen_rect()
        self.move(0, screen.height() - self.frame_height - 50)

    def screen_rect(self):
        pos = self.frameGeometry().center()
        screen = QApplication.screenAt(pos)
        if screen:
            return screen.availableGeometry()
        return QApplication.primaryScreen().availableGeometry()


    def set_state(self, new_state):
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

        pixmap = QPixmap(sprite_path)
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
    monster = random.choice(monster_list)
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

    # === Create system tray icon ===
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icon.png")))
    tray_icon.setVisible(True)
    tray_icon.showMessage("Desktop Spirit", f"{monster.replace('_', ' ')} is active!", QSystemTrayIcon.Information, 3000)

    # === Tray menu ===
    tray_menu = QMenu()

    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)

    change_character_action = QAction("Change Character")
    def change_character():
        os.execl(sys.executable, sys.executable, *sys.argv)

    change_character_action.triggered.connect(change_character)

    tray_menu.addAction(change_character_action)
    tray_menu.addSeparator()
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)

    # === Start application ===
    sys.exit(app.exec_())

