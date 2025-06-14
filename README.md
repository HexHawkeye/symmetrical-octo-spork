# 🧙‍♂️ Desktop Spirit

A playful animated sprite that walks, jumps, climbs, attacks, and reacts on your desktop!  
Built using **PyQt5**, this customizable character interacts with your mouse and screen edges — complete with a health system, draggable movement, and system tray integration.

---

## ✨ Features

- 🎮 Randomly selected sprite from: `Pink_Monster`, `Owlet_Monster`, or `Dude_Monster`
- 🧠 Animated states: Idle, Walk, Run, Jump, Climb, Fall, Hurt, Death
- 🐁 Attacks when mouse hovers over it
- 🖱️ Click to damage the sprite — 5 hits trigger death + respawn
- 🖱️ Click and drag to move across monitors
- 💀 Falls to death if dropped from high enough
- 📌 System tray with **Quit** and **Change Character** options
- ❤️ Health bar above the sprite that auto-restores after 10 seconds of no damage

---

![free-pixel-art-tiny-hero-sprites](https://github.com/user-attachments/assets/0a7ef025-efb1-4d22-b8cf-ed6ad3a32a74)

---

## 🛠 Requirements

Install dependencies using pip:

bash
pip install PyQt5 Pillow

 📁 Setup

    Clone the repository

git clone https://github.com/your-username/desktop-spirit.git
cd desktop-spirit

    Add sprite folders

Place your character folders inside the tiny-hero-sprites/ directory:

tiny-hero-sprites/
├── Pink_Monster/
├── Owlet_Monster/
└── Dude_Monster/

    Run the script

python Sprite.py

⚙️ Sprite Format

Each character folder must include PNG sprite sheets like:

Pink_Monster_Walk_6.png
Pink_Monster_Run_6.png
Pink_Monster_Idle_4.png
Pink_Monster_Jump_8.png
Pink_Monster_Death_8.png
...

    Sprite sheets should contain horizontal frame sequences.

    Filenames must follow the format: Character_Action_FrameCount.png

🖼️ System Tray Icon

    Include an icon.png or icon.ico in the root directory for the system tray.

    PNG should be 32x32 or 64x64 if not converting to ICO for .exe.

🧪 Development Notes

    Character dies if dropped from a height greater than half the screen.

    Health auto-restores after 10 seconds of no damage.

    Edge detection and multi-monitor support included.

    Tray menu allows character switching without restarting.

📦 Building to EXE (Optional)
Use PyInstaller to create a Windows executable:

pyinstaller Sprite.py --name SpriteApp --windowed --icon=icon.ico \
--add-data "tiny-hero-sprites;tiny-hero-sprites" --add-data "icon.ico;."

    Be sure to convert icon.png to icon.ico using Pillow or an image editor.

📃 License
MIT License. Free to modify, share, and use in personal projects.

🙏 Credit
Sprites from:
🎨 craftpix.net — Free Pixel Art Tiny Hero Sprites

