from evdev import InputDevice, categorize, ecodes, list_devices, KeyEvent
import time

class QrCode:
    def __init__(self, timeout):
        """
        找到 Newland 设备对应的 event 节点
        参数:
            timeout: 时间限制 (s)
        """
        self.path = ""
        for path in list_devices():
            dev = InputDevice(path)
            name = (dev.name or "").lower()
            phys = (dev.phys or "").lower()
            if "newland" in name or "newland" in phys:
                self.path = path

        self.dev = InputDevice(self.path)
        self.keymap = {
            'KEY_0':'0','KEY_1':'1','KEY_2':'2','KEY_3':'3','KEY_4':'4',
            'KEY_5':'5','KEY_6':'6','KEY_7':'7','KEY_8':'8','KEY_9':'9',
            'KEY_A':'a','KEY_B':'b','KEY_C':'c','KEY_D':'d','KEY_E':'e','KEY_F':'f',
            'KEY_G':'g','KEY_H':'h','KEY_I':'i','KEY_J':'j','KEY_K':'k','KEY_L':'l',
            'KEY_M':'m','KEY_N':'n','KEY_O':'o','KEY_P':'p','KEY_Q':'q','KEY_R':'r',
            'KEY_S':'s','KEY_T':'t','KEY_U':'u','KEY_V':'v','KEY_W':'w','KEY_X':'x',
            'KEY_Y':'y','KEY_Z':'z'
        }
        
        self.dev.grab()
        self.timeout = timeout

    def scan(self, code):
        """
        核对二维码是否一致
        参数:
            code: 后台给某个订单分配的二维码字符串
        """
        buf = []
        print("Ready. Scan a code...")
        deadline = time.monotonic() + self.timeout

        while True:
            
            if time.monotonic() > deadline:
                print("QR code timeout")
                return False
            
            event = self.dev.read_one()
            if not event:
                time.sleep(0.005)
                continue

            if event.type != ecodes.EV_KEY:
                continue
            
            ke = categorize(event)
            if ke.keystate != KeyEvent.key_down:
                continue

            key = ke.keycode
            if isinstance(key, list):  # 某些系统返回 ['KEY_1'] 这种
                key = key[0]

            if key in ('KEY_ENTER', 'KEY_KPENTER'):
                barcode = ''.join(buf)
                buf = []

                if barcode == code:
                    print("QR code match")
                    return True
                else:
                    print("not match, keep trying")
            else:
                ch = self.keymap.get(key)
                if ch:
                    buf.append(ch)


    def close(self):
        try:
            self.dev.ungrab()
        except Exception:
            pass
        try:
            self.dev.close()
        except Exception:
            pass
"""
if __name__ == "__main__":
    qr_scanner = QrCode(timeout=60)
    print(qr_scanner.scan(code))     
"""