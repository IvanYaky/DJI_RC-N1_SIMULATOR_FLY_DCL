import argparse
import struct
import time
from threading import Thread

try: import serial.tools.list_ports
except ModuleNotFoundError:
    print ("You need to install 'pyserial' to run this program.\nTry this command: pip3 install pyserial")
    quit(1)

parser = argparse.ArgumentParser(description='DJI Mavic 3 RC231 (RC-N1) <-> Gamepad interface.')
parser.add_argument('-p', '--port', help='RC Serial Port - leave empty to scan - example: COM3')
parser.add_argument('--driver', help='Driver Type', default='vgamepad', choices=['vgamepad', 'vjoy'])
parser.add_argument('-d', '--device', help='VJoy Device ID - Only needed when using vjoy driver', type=int, default=1)
parser.add_argument('-i', '--invert', help='Invert lv, lh, rv, rh, or cam axis', nargs='*', default=['lv', 'rv'])

args = parser.parse_args()
invert = frozenset(args.invert)
maxValue = 0x8000 # == 32768

if args.driver == "vgamepad":
    try: import vgamepad as vg
    except ModuleNotFoundError:
        print ("If you want to use vgamepad as driver, you'll need to install 'vgamepad' to run this program.\nTry this command: pip3 install vgamepad")
        quit(1)
    gamepad = vg.VX360Gamepad()
elif args.driver == "vjoy":
    try: import pyvjoy as vg
    except ModuleNotFoundError:
        print ("If you want to use vjoy as driver, you'll need to install 'pyvjoy' to run this program.\nTry this command: pip3 install pyvjoy")
        quit(1)
    class vGamepad(vg.VJoyDevice):
        def left_joystick(self, h, v): self.data.wAxisX, self.data.wAxisY = h, v
        def right_joystick(self, h, v): self.data.wAxisXRot, self.data.wAxisYRot = h, v
        def press_button(self, button): self.data.lButtons |= button
        def release_button(self, button): self.data.lButtons &= ~button
        def left_trigger(self): return
        def reset(self): super().reset();self.data.lButtons=0;self.left_joystick(0x4000, 0x4000),self.right_joystick(0x4000, 0x4000)
        def shutdown(self): self.reset(),self.update(),self.__del__()
    class XUSB_BUTTON:XUSB_GAMEPAD_A=1<<0;XUSB_GAMEPAD_B=1<<1;XUSB_GAMEPAD_X=1<<2;XUSB_GAMEPAD_Y=1<<3
    vg.XUSB_BUTTON=XUSB_BUTTON()
    gamepad = vGamepad(args.device)

events = (
    gamepad.left_trigger,
    gamepad.left_joystick(-16384, 16384),
    gamepad.right_joystick(-16384, 16384),
    )

gamepad.reset()
time.sleep(1)

def calc_checksum(packet, plength):

    crc = [0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
    0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
    0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
    0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
    0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
    0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
    0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
    0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
    0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
    0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
    0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
    0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
    0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
    0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
    0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
    0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
    0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
    0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
    0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
    0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
    0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
    0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
    0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
    0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
    0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
    0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
    0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
    0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
    0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
    0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
    0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
    0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78]

    # Seeds
    # v = 0x1012 #Naza M
    # v = 0x1013 #Phantom 2
    # v = 0x7000 #Naza M V2
    v = 0x3692  #P3/P4/Mavic 

    for i in range(0, plength):
        vv = v >> 8
        v = vv ^ crc[((packet[i] ^ v) & 0xFF)]
    return v

def calc_pkt55_hdr_checksum(seed, packet, plength):
    arr_2A103 = [0x00,0x5E,0xBC,0xE2,0x61,0x3F,0xDD,0x83,0xC2,0x9C,0x7E,0x20,0xA3,0xFD,0x1F,0x41,
        0x9D,0xC3,0x21,0x7F,0xFC,0xA2,0x40,0x1E,0x5F,0x01,0xE3,0xBD,0x3E,0x60,0x82,0xDC,
        0x23,0x7D,0x9F,0xC1,0x42,0x1C,0xFE,0xA0,0xE1,0xBF,0x5D,0x03,0x80,0xDE,0x3C,0x62,
        0xBE,0xE0,0x02,0x5C,0xDF,0x81,0x63,0x3D,0x7C,0x22,0xC0,0x9E,0x1D,0x43,0xA1,0xFF,
        0x46,0x18,0xFA,0xA4,0x27,0x79,0x9B,0xC5,0x84,0xDA,0x38,0x66,0xE5,0xBB,0x59,0x07,
        0xDB,0x85,0x67,0x39,0xBA,0xE4,0x06,0x58,0x19,0x47,0xA5,0xFB,0x78,0x26,0xC4,0x9A,
        0x65,0x3B,0xD9,0x87,0x04,0x5A,0xB8,0xE6,0xA7,0xF9,0x1B,0x45,0xC6,0x98,0x7A,0x24,
        0xF8,0xA6,0x44,0x1A,0x99,0xC7,0x25,0x7B,0x3A,0x64,0x86,0xD8,0x5B,0x05,0xE7,0xB9,
        0x8C,0xD2,0x30,0x6E,0xED,0xB3,0x51,0x0F,0x4E,0x10,0xF2,0xAC,0x2F,0x71,0x93,0xCD,
        0x11,0x4F,0xAD,0xF3,0x70,0x2E,0xCC,0x92,0xD3,0x8D,0x6F,0x31,0xB2,0xEC,0x0E,0x50,
        0xAF,0xF1,0x13,0x4D,0xCE,0x90,0x72,0x2C,0x6D,0x33,0xD1,0x8F,0x0C,0x52,0xB0,0xEE,
        0x32,0x6C,0x8E,0xD0,0x53,0x0D,0xEF,0xB1,0xF0,0xAE,0x4C,0x12,0x91,0xCF,0x2D,0x73,
        0xCA,0x94,0x76,0x28,0xAB,0xF5,0x17,0x49,0x08,0x56,0xB4,0xEA,0x69,0x37,0xD5,0x8B,
        0x57,0x09,0xEB,0xB5,0x36,0x68,0x8A,0xD4,0x95,0xCB,0x29,0x77,0xF4,0xAA,0x48,0x16,
        0xE9,0xB7,0x55,0x0B,0x88,0xD6,0x34,0x6A,0x2B,0x75,0x97,0xC9,0x4A,0x14,0xF6,0xA8,
        0x74,0x2A,0xC8,0x96,0x15,0x4B,0xA9,0xF7,0xB6,0xE8,0x0A,0x54,0xD7,0x89,0x6B,0x35]

    chksum = seed
    for i in range(0, plength):
        chksum = arr_2A103[((packet[i] ^ chksum) & 0xFF)];
    return chksum

def send_duml(s, source, target, cmd_type, cmd_set, cmd_id, payload = None):
    global sequence_number
    sequence_number = 0x34eb
    packet = bytearray.fromhex(u'55')
    length = 13
    if payload is not None:
        length = length + len(payload)

    if length > 0x3ff:
        print("Packet too large")
        exit(1)

    packet += struct.pack('B', length & 0xff)
    packet += struct.pack('B', (length >> 8) | 0x4) # MSB of length and protocol version
    hdr_crc = calc_pkt55_hdr_checksum(0x77, packet, 3)
    packet += struct.pack('B', hdr_crc)
    packet += struct.pack('B', source)
    packet += struct.pack('B', target)
    packet += struct.pack('<H', sequence_number)
    packet += struct.pack('B', cmd_type)
    packet += struct.pack('B', cmd_set)
    packet += struct.pack('B', cmd_id)

    if payload is not None:
        packet += payload

    crc = calc_checksum(packet, len(packet))
    packet += struct.pack('<H',crc)
    s.write(packet)
    #print(' '.join(format(x, '02x') for x in packet))

    sequence_number += 1

print('app version: 3.1.0\n')
# Open serial.
try:
    if args.port:
        s = serial.Serial(port=args.port, baudrate=115200)
        print('Opened serial port:', s.name)
    else:
        result = []
        ports = serial.tools.list_ports.comports(True)

        for port in ports:
            try:
                print(port.description)
                if port.description.find("For Protocol") != -1:
                    print("found DJI USB VCOM For Protocol")
                    s = serial.Serial(port=port.name, baudrate=115200)
                    print('Opened serial port:', s.name)
                    break
                else:
                    print("skip")
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        
        try: s
        except NameError: raise serial.SerialException("Unable to find the correct COM port.\nPerhaps try to supply the portname to the command by adding '-p <COM_PORT>'")

except serial.SerialException as e:
    print('Could not open serial port:', e)
    exit(1)

# Stylistic: Newline for spacing.
print('\nDji RC231 emulation started...\n')
print('\nTo stop, press Ctrl-C or close the terminal\n')

print('*******************************************************\n')
print('* Telegram: https://t.me/DJI_RC_N1_SIMULATOR_FLY_DC   *\n')
print('* Donate: https://www.buymeacoffee.com/ivanyakymenko  *\n')
print('*******************************************************\n')

# Process input (min 364, center 1024, max 1684)
inr = [364, 1684]
if args.driver == 'vgamepad': outr = [-32768, 32767] # min -32768, max 32767
elif args.driver == 'vjoy': outr = [0, 32767] # min 0, max 32768
def parseInput(input, name):
    # Source: https://stackoverflow.com/a/929107
    output = (((int.from_bytes(input, byteorder='little') - inr[0]) * (outr[1] - outr[0])) / (inr[1] - inr[0])) + outr[0]

    if name in invert:
        if args.driver == 'vgamepad': output = -output
        elif args.driver == 'vjoy': output = outr[1] - output

    if args.driver == 'vjoy' and name == 'cam': output = output * 2 - outr[1]
    
    #print(output, "test")

    return output

st = {"rh": 0, "rv": 0, "lh": 0, "lv": 0, "cam": 0}

stopping = False
def threaded_function():
    while(True):
        time.sleep(0.1)
        #print("working ...")
        gamepad.left_joystick(int(st["lh"]), int(st["lv"]))
        gamepad.right_joystick(int(st["rh"]), int(st["rv"]))
        if st["cam"] > 32000:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y) #restart race
        elif st["cam"] < -32000:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B) #recover drone
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        gamepad.update()
        if stopping: break
    if args.driver == 'vjoy': gamepad.shutdown()

thread = Thread(target = threaded_function, args = ())
thread.start()
#thread.join()

try:
    # enable simulator mode for RC (without this stick positions are sent very slow by RC)
    send_duml(s, 0x0a, 0x06, 0x40, 0x06, 0x24, bytearray.fromhex('01'))

    while True:

        #time.sleep(0.1)
        # read channel values
        send_duml(s, 0x0a, 0x06, 0x40, 0x06, 0x01, bytearray.fromhex(''))
        #s.write(bytearray.fromhex('55 0d 04 33 0a 06 eb 34 40 06 01 74 24'))
        # Don't write to a new line every time.
#        print('\rPinged. ', end='')

        # read duml
        buffer = bytearray.fromhex('')
        while True:
            b = s.read(1)
            if b == bytearray.fromhex('55'):
                buffer.extend(b)
                ph = s.read(2)
                buffer.extend(ph)
                ph = struct.unpack('<H', ph)[0]
                pl = 0b0000001111111111 & ph
                pv = 0b1111110000000000 & ph
                pv = pv >> 10
                pc = s.read(1)
                buffer.extend(pc)
                pd = s.read(pl - 4)
                buffer.extend(pd)
                break
            else:
                break
        data = buffer
#        print(' '.join(format(x, '02x') for x in data))
#        time.sleep(0.5)

        # Reverse-engineered. Controller input seems to always be len 38.
        if len(data) == 38:
            # Reverse-engineered
            st["rh"] = parseInput(data[13:15], 'lh')
            st["rv"] = parseInput(data[16:18], 'lv')

            st["lv"] = parseInput(data[19:21], 'rv')
            st["lh"] = parseInput(data[22:24], 'rh')

            st["cam"] = parseInput(data[25:27], 'cam')

            #print(data)
            #with uinput.Device(events) as device:
            #time.sleep(1)
        #else:
            # print(len(data))

            # Log to console.
            #print('L: H{0:06d},V{1:06d}; R: H{2:06d},V{3:06d}, CAM: {4:06d}\n'.format(st["lh"], st["lv"], st["rh"], st["rv"], st["cam"]), end='')
except serial.SerialException as e:
    # Stylistic: Newline to stop data update and spacing.
    print('\n\nCould not read/write:', e)
except KeyboardInterrupt:
    # Stylistic: Newline to stop data update and spacing.
    print('\n\nDetected keyboard interrupt.')

    pass

print('Stopping.')
stopping = True
thread.join()
print('Stopped')
