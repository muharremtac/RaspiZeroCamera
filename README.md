**Raspberry Pi Camera app for Adafruit PiTFT 2.2" HAT Mini Kit - 320x240 2.2" TFT - No Touch**

This documents includes Raspberry Pi SD image URL (Jessie or Jessie Lite):
https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi/easy-install

If does not work Raspberry Pi Zero camera, please update your firmware:

`sudo rpi-update`

This code is based on Adafruit PiCam
https://github.com/adafruit/adafruit-pi-cam

If you want to add startup this code, one method can be work:

Add to ~/.config/lxsession/LXDE-pi/autostart this command:

`@python camerastart.py`
