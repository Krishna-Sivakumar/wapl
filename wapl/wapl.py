import wave
import numpy as np

class wave_file_object:
    def __init__(self):
        self.location = None
    def getnchannels(self):
        assert self.location == "disk"
        return self.wav_obj.getnchannels()

    def getsampwidth(self):
        assert self.location == "disk"
        return self.wav_obj.getsampwidth()

    def getframerate(self):
        assert self.location == "disk"
        return self.wav_obj.getframerate()

    def getnframes(self):
        assert self.location == "disk"
        return self.wav_obj.getnframes()

    def get_audio_length(self):
        assert self.location == "disk"
        return self.wav_obj.getnframes()/self.wav_obj.getframerate()

    def __convert_time_to_frames(self,T):
        assert self.location == "disk"
        return int(T*self.wav_obj.getframerate())

    def read_audio_segment(self,start_time,end_time):
        assert self.location == "disk"
        assert start_time >= 0
        assert start_time < end_time
        start_frame = self.__convert_time_to_frames(start_time)
        end_frame = self.__convert_time_to_frames(end_time)
        assert end_frame <= self.wav_obj.getnframes()
        self.wav_obj.setpos(start_frame)
        H = self.wav_obj.readframes(end_frame-start_frame)
        H = np.array([H[i] for i in range(len(H))])
        channels = [0]*self.wav_obj.getnchannels()
        skip = self.wav_obj.getsampwidth()*self.wav_obj.getnchannels()
        plimit = 2**(8*self.wav_obj.getsampwidth()-1)
        comp = 2*plimit
        for ch in range(self.wav_obj.getnchannels()):
            channels[ch] = sum([256**k*H[(k+self.wav_obj.getsampwidth()*ch)::skip] for k in range(self.wav_obj.getsampwidth())])
            channels[ch] = (channels[ch] >= plimit)*(channels[ch]-comp) + (channels[ch] < plimit)*channels[ch]
        return channels

def read(filename):
    ret = wave_file_object()
    ret.wav_obj = wave.open(filename)
    ret.location = "disk"
    return ret

#boiler plate
def new_audio_file(num_channels):
    ret = wave_file_object()
    ret.location = "RAM"
    ret.channels = [0]*num_channels
    return ret

class waveform:
    def __init__(self,protocol,**kwargs):
        if(protocol == "sine"):
            self.protocol = "sine"
            self.help_text = """
            one cycle of a sine wave with amplitude 1.
            """
    def generate_wave(self,framerate,frequency,amplitude,length=None,initial_phase = 0):
        fT = 0
        if(length is not None):
            fT = frequency*np.arange(framerate*length)/framerate + initial_phase
        else:
            if(np.shape(frequency) == ()):
                length = len(amplitude)
                fT = frequency*np.arange(framerate*length)/framerate + initial_phase
            else:
                fT = np.zeros(len(frequency)+1)
                np.cumsum(frequency,out=fT[1:])
                fT /= framerate
                fT = fT[:-1]
        if(self.protocol == "sine"):
            return amplitude*np.sin(2*np.pi*fT)

def quick_write(filename,channel):
    file = wave.open(filename,'wb')
    file.setframerate(44100)
    file.setnframes(len(channel))
    file.setsampwidth(2)
    file.setnchannels(1)
    pow16 = 2**16
    H = [int(c) for c in channel]
    H = [pow16+h if h<0 else h for h in H]
    H = b''.join([h.to_bytes(2,"little") for h in H])
    file.writeframes(H)
    file.close()

if(__name__ == "__main__"):
    import sys
    if len(sys.argv) == 1:
        print("provide some arguments if you wanna run tests. Following are possible arguments:")
        print("python3 wapl.py read <input filename>")
        print("python3 wapl.py write")
        exit(0)
    if(sys.argv[1] == "read"):
        from matplotlib import pyplot as plt
        polaris = wapl(sys.argv[2])
        channels = polaris.read_audio_segment(0,1)
        m = (channels[0] - channels[1])/2
        print(np.shape(channels))
        for c in channels:
            plt.plot(c)
        plt.show()
    if(sys.argv[1] == "write"):
        from matplotlib import pyplot as plt
        fr = 44100
        T = 220
        data = (2**15)*np.sin(T*2*np.pi*np.arange(fr)/fr)
        #plt.plot(data)
        quick_write("sampleaudio/sine220.wav",data)
        plt.show()
    if(sys.argv[1] == "waveform"):
        wf = waveform("sine")
        generated_wave = wf.generate_wave(44100,440,2**15,1)
        quick_write("sampleaudio/sine440.wav",generated_wave)
        frequency_modulation = wf.generate_wave(44100,1,20,5)+440
        amp_modulation = np.linspace(2**14,2**15,len(frequency_modulation))
        modulated_wave = wf.generate_wave(44100,frequency_modulation,amp_modulation)
        quick_write("sampleaudio/mod.wav",modulated_wave)
