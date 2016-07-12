import RPi.GPIO as GPIO
import atexit
import errno
import fnmatch
import io
import os
import os.path
import picamera
import pygame
import stat
import threading
import time
import yuv2rgb
from pygame.locals import *
from subprocess import call

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

rgb = bytearray(320 * 240 * 3)
yuv = bytearray(320 * 240 * 3 / 2)

screenMode = 3
screenModePrior = -1
settingMode = 4
storeMode = 0
storeModePrior = -1
sizeMode = 0
fxMode = 0
isoMode = 0
iconPath = 'icons'
saveIdx = -1
loadIdx = -1
scaled = None

pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

sizeMode = 0


def spinner():
    global busy, screenMode, screenModePrior

    pygame.display.update()

    busy = True
    n = 0
    while busy is True:
        pygame.display.update()
        n = (n + 1) % 5
        time.sleep(0.15)


pathData = [
    '/home/pi/Photos',
    '/boot/DCIM/CANON999',
    '/home/pi/Photos']

sizeData = [
    [(2592, 1944), (320, 240), (0.0, 0.0, 1.0, 1.0)],
    [(1920, 1080), (320, 180), (0.1296, 0.2222, 0.7408, 0.5556)],
    [(1440, 1080), (320, 240), (0.2222, 0.2222, 0.5556, 0.5556)]]

t = threading.Thread(target=spinner)
t.start()

camera = picamera.PiCamera()
atexit.register(camera.close)

camera.resolution = sizeData[sizeMode][1]
camera.crop = (0.0, 0.0, 1.0, 1.0)


def imgRange(path):
    min = 9999
    max = 0
    try:
        for file in os.listdir(path):
            if fnmatch.fnmatch(file, 'IMG_[0-9][0-9][0-9][0-9].JPG'):
                i = int(file[4:8])
                if (i < min): min = i
                if (i > max): max = i
    finally:
        return None if min > max else (min, max)


def takePicture():
    global busy, gid, loadIdx, saveIdx, scaled, sizeMode, storeMode, storeModePrior, uid

    if not os.path.isdir(pathData[storeMode]):
        try:
            os.makedirs(pathData[storeMode])
            os.chown(pathData[storeMode], uid, gid)
            os.chmod(pathData[storeMode],
                     stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                     stat.S_IRGRP | stat.S_IXGRP |
                     stat.S_IROTH | stat.S_IXOTH)
        except OSError as e:
            print errno.errorcode[e.errno]
            return

    if storeMode != storeModePrior:
        r = imgRange(pathData[storeMode])
        if r is None:
            saveIdx = 1
        else:
            saveIdx = r[1] + 1
            if saveIdx > 9999: saveIdx = 0
        storeModePrior = storeMode

    while True:
        filename = pathData[storeMode] + '/IMG_' + '%04d' % saveIdx + '.JPG'
        if not os.path.isfile(filename): break
        saveIdx += 1
        if saveIdx > 9999: saveIdx = 0

    t = threading.Thread(target=spinner)
    t.start()

    scaled = None
    camera.resolution = sizeData[sizeMode][0]
    camera.crop = sizeData[sizeMode][2]
    try:
        camera.capture(filename, use_video_port=False, format='jpeg',
                       thumbnail=None)
        os.chmod(filename,
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        img = pygame.image.load(filename)
        scaled = pygame.transform.scale(img, sizeData[sizeMode][1])
        if storeMode == 2:
            if upconfig:
                cmd = uploader + ' -f ' + upconfig + ' upload ' + filename + ' Photos/' + os.path.basename(filename)
            else:
                cmd = uploader + ' upload ' + filename + ' Photos/' + os.path.basename(filename)
            call([cmd], shell=True)

    finally:
        camera.resolution = sizeData[sizeMode][1]
        camera.crop = (0.0, 0.0, 1.0, 1.0)

    busy = False
    t.join()

    if scaled:
        if scaled.get_height() < 240:
            screen.fill(0)
        screen.blit(scaled,
                    ((320 - scaled.get_width()) / 2,
                     (240 - scaled.get_height()) / 2))
        pygame.display.update()
        time.sleep(2.5)
        loadIdx = saveIdx


while (True):

    input_state = GPIO.input(17)
    if input_state == False:
        takePicture()

    stream = io.BytesIO()
    camera.capture(stream, use_video_port=True, format='raw')
    stream.seek(0)
    stream.readinto(yuv)
    stream.close()

    yuv2rgb.convert(yuv, rgb, sizeData[sizeMode][1][0], sizeData[sizeMode][1][1])

    img = pygame.image.frombuffer(rgb[0:(sizeData[sizeMode][1][0] * sizeData[sizeMode][1][1] * 3)],
                                  sizeData[sizeMode][1], 'RGB')

    if img is None or img.get_height() < 240:
        screen.fill(0)

    if img:
        screen.blit(img,
                    ((320 - img.get_width()) / 2,
                     (240 - img.get_height()) / 2))

    pygame.display.update()
