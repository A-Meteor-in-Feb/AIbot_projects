#!/usr/bin/env python3
# pip install evdev
from evdev import InputDevice, categorize, ecodes, list_devices, KeyEvent

# 1) 找到 Newland 设备对应的 event 节点
def find_newland_event():
    for path in list_devices():
        dev = InputDevice(path)
        name = (dev.name or "").lower()
        phys = (dev.phys or "").lower()
        if "newland" in name or "newland" in phys:
            return path
    raise RuntimeError("未找到 Newland 扫码器的 /dev/input/eventX 节点。")

path = find_newland_event()
dev = InputDevice(path)
print(f"Using {path} ({dev.name})")

# 2) 可选：抓取设备，避免把按键送到终端
dev.grab()  # 没权限会抛错；root 或合适的 udev 规则即可

# 3) 把按键事件转成字符串；遇到 Enter 视为一条扫码完成
keymap = {
    'KEY_0':'0','KEY_1':'1','KEY_2':'2','KEY_3':'3','KEY_4':'4',
    'KEY_5':'5','KEY_6':'6','KEY_7':'7','KEY_8':'8','KEY_9':'9',
    'KEY_A':'a','KEY_B':'b','KEY_C':'c','KEY_D':'d','KEY_E':'e','KEY_F':'f',
    # 如需更多字符，按需补：KEY_MINUS -> '-', KEY_SLASH -> '/', 等等
}

buf = []
print("Ready. Scan a code...")

for event in dev.read_loop():
    if event.type != ecodes.EV_KEY:
        continue
    ke = categorize(event)
    if ke.keystate != KeyEvent.key_down:
        continue

    code = ke.keycode
    if isinstance(code, list):  # 某些系统返回 ['KEY_1'] 这种
        code = code[0]

    if code in ('KEY_ENTER', 'KEY_KPENTER'):
        barcode = ''.join(buf)
        if barcode:
            print(f"SCAN: {barcode}, type:", type(barcode))
        buf = []
    else:
        ch = keymap.get(code)
        if ch:
            buf.append(ch)
