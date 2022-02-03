import numpy as np
import cv2
import rtmidi
import mido
import time
import math

''' entweder Video oder Webcam einlesen '''
#cap = cv2.VideoCapture('demo.mov') # Video einlesen
cap = cv2.VideoCapture('demo_alle_farben.mov')
#cap = cv2.VideoCapture(0) # WebCam-Stream/ externe Kamera einlesen
frame_rate = cap.get(5) #frame_rate


####### MIDI #####################
midi_Output = mido.open_output('IAC-Treiber Bus 1') # MidiOutput 
''' Definition der vier verschiedenen Midi-Nachrichten '''
def sendPlayNote(sample, velocity):
    message = mido.Message('note_on', note=sample, velocity=velocity) # data byte 0 = 144 in Dezimal
    midi_Output.send(message) # Nachricht wird zum Treiber geschickt

def sendStopNote(sample, velocity): 
    message = mido.Message('note_off', note=sample, velocity=velocity) # data byte 0 = 128 in Dezimal
    midi_Output.send(message) 

def sendPanControl(control, value):
    message = mido.Message('control_change', control=control, value=value) # data byte 0 = 176 in Dezimal
    midi_Output.send(message) 

def sendGainControl(sample, value):
    message = mido.Message('polytouch', note=sample, value=value) # data byte 0 = 160 in Dezimal
    midi_Output.send(message) 
##################################

############ VIDEO ALGORITHMEN ##############
''' Farbanteile aus eingehendem Signal filtern'''
def FarbenErkennung(h, s, v, hue_lb, hue_ub, sat_lb, sat_ub):
    hue = cv2.inRange(h, hue_lb, hue_ub) # Fabrwinkel-Range
    sat = cv2.inRange(s, sat_lb, sat_ub) # Saturation-Range
    zwischen_maske = cv2.bitwise_and(hue, sat)
    maske = cv2.bitwise_and(zwischen_maske, v) # Value-Range über alle Werte
    _, maske = cv2.threshold(maske, 70, 255, cv2.THRESH_BINARY) # Binärmaske 

    return maske # Maske zur Formerkennung benutzen
''' Funktionen zur Verbesserung der Farbfilterung'''
# input = Farbmaske oder z.B farbmaske->entrauschen->closeVordergrund
def entrauschen(maske):
    kSize = 5
    maske_median = cv2.medianBlur(maske, kSize)
    return maske_median

def closeVordergrund(maske):
    struct_element = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    closing = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, struct_element)
    return closing

''' Detektion der Form einer eingehenden Maske'''
def FormErkennung(maske, frame):
    detected_form = ' '
    xy_coord = [0, 0]
    konturen, _ = cv2.findContours(maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if konturen == []: # Fall keine Form im frame detektiert
        detected_form = ' ' 
        xy_coord = [0, 0] 
    for kontur in konturen: 
        area = cv2.contourArea(kontur)
        if area < 5000: # kleinere Störflächen auszuschließen
            pass
        else:
            arc_len = cv2.arcLength(kontur, True)
            epsilon = 0.02*arc_len
            approx = cv2.approxPolyDP(kontur, epsilon, True)
            ''' x,y Koordinaten der erkannten Form '''
            ######### Moment ####################
            M = cv2.moments(kontur) 
            if M['m00'] != 0.0: 
                x = int(M['m10']/M['m00']) # x-Koordinate
                y = int(M['m01']/M['m00']) # y-Koordinate
            #####################################
        
            if len(approx) == 4: # Fall Viereck wird erkannt
                detected_form = 'Viereck' #schreibt 'Viereck' in die Variable detected_form wenn in dem frame ein Viereck erkannt wurde
                xy_coord = [x, y] # x, y Koordinaten der erkannten Form in Variable schreiben
            elif len(approx) == 3: # Fall Dreieck wird erkannt
                detected_form = 'Dreieck'
                xy_coord = [x, y]

            elif len(approx) > 4: # Fall Kreis wird erkannt
                detected_form = 'Kreis'   
                xy_coord = [x, y]
  
    return detected_form, xy_coord # detektierte Form und zugehörige Koordinaten ausgeben
#############################################

############ MIDI NOTEN ABH VON FORM UND KOORDINATEN SPIELEN ##########

def roteMidiNotenSpielen(erkannte_form, xy_coord, x_size, y_size):
    if erkannte_form == 'Viereck': 
        pan_midi = x_coord2Midi(xy_coord, x_size) #MIDI Note Paning im Bereich 0-127 aus x-Koordinate
        gain_midi = y_coord2Midi(xy_coord, y_size) #MIDI Note für Gain im Bereich 0-127 aus y-Koordinate
        sendPlayNote(9, 127) # Sample Nr 9 spielen wenn rotes Viereck detektiert wird
        sendPanControl(9, pan_midi) #Sample Nr 9 mit pan_midi-Wert gepant werden
        sendGainControl(9, gain_midi) #Sample Nr 9 mit Lautstäerke gain_midi-Wert abspielen
        sendStopNote(5, 0) #Sample mit Nr 5 gleichzeitig pausieren 
        sendStopNote(3, 0) #Sample mit Nr 3 soll gleichzeitig pausieren
        print('rotes Viereck = Klavier', xy_coord)
    elif erkannte_form == 'Kreis':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(5, 127)
        sendPanControl(5, pan_midi)
        sendGainControl(5, gain_midi)
        sendStopNote(9, 0)
        sendStopNote(3, 0)
        print('roter Kreis = Eulen', xy_coord)
    elif erkannte_form == 'Dreieck':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(3, 127)
        sendPanControl(3, pan_midi)
        sendGainControl(3, gain_midi)
        sendStopNote(9, 0)
        sendStopNote(5, 0)
        print('rotes Dreieck = Cafe', xy_coord)
    elif erkannte_form == ' ': # keine rote Form im frame
        sendStopNote(9, 0)
        sendStopNote(3, 0)
        sendStopNote(5, 0)
        print('keine rote Form detektiert')
    else:
        sendStopNote(9, 0)
        sendStopNote(3, 0)
        sendStopNote(5, 0)
        print('keine rote Form detektiert')
    
def blaueMidiNotenSpielen(erkannte_form, xy_coord, x_size, y_size):
    if erkannte_form == 'Viereck':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(2, 127)
        sendPanControl(2, pan_midi)
        sendGainControl(2, gain_midi)
        sendStopNote(8, 0)
        sendStopNote(1, 0)
        print('blaues Viereck = Möwen', xy_coord)
    elif erkannte_form == 'Kreis':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(8, 127)
        sendPanControl(8, pan_midi)
        sendGainControl(8, gain_midi)
        sendStopNote(2, 0)
        sendStopNote(1, 0)
        print('blauer Kreis = Winter', xy_coord)
    elif erkannte_form == 'Dreieck':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(1, 127)
        sendPanControl(1, pan_midi)
        sendGainControl(1, gain_midi)
        sendStopNote(2, 0)
        sendStopNote(8, 0)
        print('blaues Dreieck = Meer', xy_coord)
    elif erkannte_form == ' ':
        sendStopNote(2, 0)
        sendStopNote(8, 0)
        sendStopNote(1, 0)
        print('keine blaue Form detektiert')
    else:
        sendStopNote(2, 0)
        sendStopNote(8, 0)
        sendStopNote(1, 0)
        print('keine blaue Form detektiert')

def grueneMidiNotenSpielen(erkannte_form, xy_coord, x_size, y_size):
    if erkannte_form == 'Viereck':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(7, 127)
        sendPanControl(7, pan_midi)
        sendGainControl(7, gain_midi)
        sendStopNote(6, 0)
        sendStopNote(4, 0)
        print('günes Viereck = Flugzeug', xy_coord)
    elif erkannte_form == 'Kreis':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(6, 127)
        sendPanControl(6, pan_midi)
        sendGainControl(6, gain_midi)
        sendStopNote(7, 0)
        sendStopNote(4, 0)
        print('grüner Kreis = Gewitter', xy_coord)
    elif erkannte_form == 'Dreieck':
        pan_midi = x_coord2Midi(xy_coord, x_size)
        gain_midi = y_coord2Midi(xy_coord, y_size)
        sendPlayNote(4, 127)
        sendPanControl(4, pan_midi)
        sendGainControl(4, gain_midi)
        sendStopNote(7, 0)
        sendStopNote(6, 0)
        print('grünes Dreieck = Gitarre', xy_coord)
    elif erkannte_form == ' ':
        sendStopNote(7, 0)
        sendStopNote(6, 0)
        sendStopNote(4, 0)
        print('keine grüne Form detektiert')
    else:
        sendStopNote(7, 0)
        sendStopNote(6, 0)
        sendStopNote(4, 0)
        print('keine grüne Form detektiert')
#######################################################################
####### Mappen der x, y Koordinaten auf Wertebereich der Midi-Noten #########

def x_coord2Midi(xy_coord, x_size): # Eingabe: Koordinaten in form [x, y], breite des Videos in Pixel
    x_coord = xy_coord[0] # = x-Koordinate
    m = 127/x_size #mappen durch lineare Funktion
    midi = int(m * x_coord) # ganze Zahl
    return midi

def y_coord2Midi(xy_coord, y_size): # Eingabe: Koordinaten in form [x, y], höhe des Videos in Pixel
    y_coord = xy_coord[1] # = y-Koordinate
    m = -(127/y_size) 
    midi = int(m * y_coord + 127) #mappen durch lineare Funktion, ganze Zahl
    return midi
##########################################################################

######## Video Schleife ###############
while cap.isOpened():
    ret, frame = cap.read() # eingelesene frames aus VideoCapture
    frame_id = cap.get(1) # current frame
    x_size = frame.shape[1] # Breite des Videos in Pixel
    y_size = frame.shape[0] # Höhe des videos in Pixel
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # hsv-Farbraum
    h,s,v = cv2.split(hsv) # splitten des Video-Signals in h, s, v Komponenten 
   
    if frame_id % 0.5*math.floor(frame_rate) == 0: # jede halbe Sekunde Farb- und Formdetektion ausführen
        ############## Farb-Masken ############
        # rot
        rote_maske_unten = FarbenErkennung(h, s, v, 0, 15, 160, 215)
        rote_maske_oben = FarbenErkennung(h, s, v, 175, 179, 160, 255)
        rote_maske = cv2.bitwise_or(rote_maske_unten, rote_maske_oben) #rote maske besteht aus zwei teilen
        rote_maske = entrauschen(rote_maske) # Funktion zur Verbesserung des Ergebnis der Farbfilterung
        rote_maske = closeVordergrund(rote_maske) # Funktion zur Verbesserung des Ergebnis der Farbfilterung
        rote_form, xy_coord_rot = FormErkennung(rote_maske, frame) # erkannte rote Form und zugehörige Koordinten
        roteMidiNotenSpielen(rote_form, xy_coord_rot, x_size, y_size) #Midi-Nachrichten für rote Form senden
        # blau
        blaue_maske = FarbenErkennung(h, s, v, 90, 130, 100, 255) 
        blaue_maske = entrauschen(blaue_maske) 
        blaue_maske = closeVordergrund(blaue_maske) 
        blaue_form, xy_coord_blau = FormErkennung(blaue_maske, frame) # erkannte blaue Form und zugehörige Koordinaten
        blaueMidiNotenSpielen(blaue_form, xy_coord_blau, x_size, y_size) # Midi-Nachrichten für blaue Form senden
        # gruen 
        gruene_maske = FarbenErkennung(h, s, v, 50, 75, 100, 255)
        gruene_maske = entrauschen(gruene_maske)
        gruene_maske = closeVordergrund(gruene_maske)
        gruene_form, xy_coord_gruen = FormErkennung(gruene_maske, frame) # erkannte grüne Form und zugehörige Koordinaten
        grueneMidiNotenSpielen(gruene_form, xy_coord_gruen, x_size, y_size) # Midi-Nachrichten für grüne Form senden
    cv2.imshow('Video-Stream', frame)
    '''winname = 'Video-Stream'
    cv2.namedWindow(winname)
    cv2.moveWindow(winname, 200, 120)
    cv2.imshow(winname, frame)'''
    
    if cv2.waitKey(25) != -1:
        for i in range(9): 
            sendStopNote(i+1, 0)
        break

for r in range(9): 
    sendStopNote(r+1, 0)
cap.release()
cv2.destroyAllWindows()

