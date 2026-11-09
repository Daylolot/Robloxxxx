"""Synthesize a local review track timed to the Blender choreography."""
from pathlib import Path
import sys
import wave

import numpy as np

from paper_motion import DURATION,ONSET,PACKETS,READ_AT,make_sheets

out=Path(sys.argv[1])
rng=np.random.default_rng(281)
rate=44100
audio=np.zeros((round(DURATION*rate),2),dtype=np.float32)


def add(start,signal,pan,gain):
    offset=round(start*rate)
    end=min(len(audio),offset+len(signal))
    signal=signal[:end-offset]*gain
    audio[offset:end,0]+=signal*np.sqrt((1-pan)*.5)
    audio[offset:end,1]+=signal*np.sqrt((1+pan)*.5)


def flutter(start,duration,pan,gain,grain):
    t=np.arange(round(rate*duration))/rate
    n=rng.normal(0,1,len(t)+1)
    texture=np.diff(n)+.42*n[1:]
    env=np.minimum(1,t/.017)*np.maximum(0,1-t/duration)**1.35
    teeth=.46+.54*(.5+.5*np.sin(2*np.pi*grain*t))**3
    add(start,texture*env*teeth,pan,gain)


for i,start in enumerate((.21,.66,1.13)):
    duration=(.31,.36,.39)[i]
    t=np.arange(round(rate*duration))/rate
    env=np.minimum(1,t/.022)*np.minimum(1,(duration-t)/.043)
    motor=np.sin(2*np.pi*(87*t+8*t*t))+.35*np.sin(2*np.pi*174*t)
    add(start,env*motor,.13,.061)
    flutter(start+.035,duration,.16,.038,31+i*2)
flutter(READ_AT,.085,0,.032,24)
for i,(_,_,_,offset) in enumerate(PACKETS):
    flutter(ONSET+offset,.48,(-.05,-.3,.53,.44,.14)[i],.068,21+i*2)
for i,sheet in enumerate(make_sheets()):
    pan=np.clip((sheet.origin[2]-35)/28,-.7,.7)
    flutter(sheet.peel+.04,.26+i%4*.05,pan,.018,17+i%7)
    flutter(sheet.peel+sheet.rise*.95,.35+i%5*.05,-pan*.6,.022,14+i%8)
for start in np.arange(12.3,20.5,.35):
    flutter(start,float(rng.uniform(.24,.53)),float(rng.uniform(-.8,.8)),.017,float(rng.uniform(11,29)))
audio=np.int16(np.clip(audio,-.92,.92)*32767)
with wave.open(str(out),"wb") as stream:
    stream.setnchannels(2)
    stream.setsampwidth(2)
    stream.setframerate(rate)
    stream.writeframes(audio.tobytes())
