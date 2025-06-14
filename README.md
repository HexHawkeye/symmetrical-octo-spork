# 🧙‍♂️ Desktop Spirit

A playful animated sprite that walks, jumps, climbs, attacks, and reacts on your desktop! Built using **PyQt5**, this customizable character interacts with your mouse and screen edges — complete with a health system, draggable movement, and system tray integration.

![demo](./preview.gif) <!-- Optional: add a demo GIF or screenshot -->

---

## ✨ Features

- 🎮 Randomly selected sprite from: `Pink_Monster`, `Owlet_Monster`, or `Dude_Monster`
- 🧠 Idle, Walk, Run, Jump, Climb, Fall, Hurt, Death animations
- 🐁 Attacks when mouse hovers over
- 🖱️ Click to damage it — 5 hits triggers a death + respawn
- 🖱️ Click and drag to move across monitors
- 💀 Falls to death if dropped from high enough
- 📌 System tray with **Quit** and **Change Character** options
- ❤️ Health bar above sprite

---
![free-pixel-art-tiny-hero-sprites](https://github.com/user-attachments/assets/0a7ef025-efb1-4d22-b8cf-ed6ad3a32a74)



## 🛠 Requirements

- Python 3.8+
- [PyQt5](https://pypi.org/project/PyQt5/)

```bash
pip install PyQt5

📁 Setup

    Clone this repository:

git clone https://github.com/your-username/desktop-spirit.git
cd desktop-spirit

Place your sprite folders in the tiny-hero-sprites/ directory:

tiny-hero-sprites/
├── Pink_Monster/
├── Owlet_Monster/
└── Dude_Monster/

Run the script:

python spirit.py

⚙️ Sprites Format

Each character folder (e.g. Pink_Monster) should include PNG sprites like:

    Pink_Monster_Walk_6.png

    Pink_Monster_Run_6.png

    Pink_Monster_Idle_4.png

    Pink_Monster_Jump_8.png

    Pink_Monster_Death_8.png

    etc.

Frames are laid out horizontally.

🖼️ System Tray Icon

Place an icon image (icon.png) in the root of the project for tray display. You can use any .png at 32x32 or 64x64.

🧪 Development Notes

    Death triggers if falling from more than half the screen height.

    You can switch characters via tray or by restarting.

    Screen edge detection adapts to multiple monitors.

📃 License

MIT License. Customize and distribute freely.

🙏 Credit

Sprites sourced from:
    craftpix.net{
    Free Pixel Art Tiny Hero Sprites}
