import serial
import sys
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
import pi_servo_hat
import time

ypos = -40
xpos = -10
baud_rate = 115200

def face_track(words,servos):
	global ypos,xpos,baud_rate
	if words[0] == "Face":

                x = (int(words[2][2:-1]))
                y = (int(words[3][2:-1]))
                if y > 120 or y < 110:
                        ypos -= 5 if y > 130 else +5				
                        if x > 140 or x < 110:
                                if x > 130:
                                        xpos = xpos + 1
                        else:
                                xpos = xpos - 1

                        servos.move_servo_position(0,ypos)
                        servos.move_servo_position(1,xpos)
                        print("x coord is"+str(x))
                        print("y coord is" +str(y))
                        print(xpos)
                        print(ypos)
                if ypos > 80 or ypos < -180:
                        ypos = -40
                if xpos > 160 or xpos < -160:
                        xpos = 0


def main():
	servos = pi_servo_hat.PiServoHat()
	servos.restart()
	serial_port = "/dev/ttyACM0"
#	baud_rate = 115200
#	ypos = -40
#	xpos = -10
	print(servos.get_servo_position(1))
	print(servos.get_servo_position(0))
	servos.move_servo_position(0,ypos)
	servos.move_servo_position(1,xpos)
	#exit()
	
	with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
		print("listening")

		while True:
			line = ser.readline().decode('utf-8').strip()
			if line:
                                words = line.split()
                                face_track(words,servos)
                                time.sleep(.5)
                                servos.restart() 
					
main()
