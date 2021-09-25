import wave
import numpy as np

class wave_file_object:
    def __init__(self):
        self.location = None
    def getnchannels(self):
        if(self.location == "RAM"):
            return len(self.channels)
        elif(self.location == "disk"):
            return self.wav_obj.getnchannels()
        else:
            raise AttributeError("self.location value is corrupted")

    def getsampwidth(self):
        if(self.location == "RAM"):
            return self.sampwidth
        elif(self.location == "disk"):
            return self.wav_obj.getsampwidth()

    def getframerate(self):
        if(self.location == "RAM"):
            return self.framerate
        elif(self.location == "disk"):
            return self.wav_obj.getframerate()

    def getnframes(self):
        if(self.location == "RAM"):
            return len(self.channels[0])
        elif(self.location == "disk"):
            return self.wav_obj.getnframes()

    def get_audio_length(self):
        return self.getnframes()/self.getframerate()

    def get_peak_val(self):
        return 2**(8*self.getsampwidth()-1)

    def __convert_time_to_frames(self,T):
        return int(T*self.getframerate())

    def read_audio_segment(self,start_time,end_time):
        assert start_time >= 0
        if(end_time is not None): assert start_time < end_time
        start_frame = self.__convert_time_to_frames(start_time)
        end_frame = self.__convert_time_to_frames(end_time) if end_time is not None else self.wav_obj.getnframes()
        assert end_frame <= self.getnframes()

        if(self.location == "RAM"):
            return [c[start_frame:end_frame] for c in self.channels]

        self.wav_obj.setpos(start_frame)
        H = self.wav_obj.readframes(end_frame-start_frame)
        H = np.array([H[i] for i in range(len(H))])

        channel_count = self.wav_obj.getnchannels()
        bit_depth = self.wav_obj.getsampwidth()

        channels = [0] * channel_count
        skip = bit_depth * channel_count
        plimit = 2 ** (8*bit_depth - 1)
        comp = 2 * plimit

        for channel in range(channel_count):
            channels[channel] = sum(
                [256**k * H[(k+bit_depth*channel)::skip] for k in range(bit_depth)]
            )
            channels[channel] = (channels[channel] >= plimit)*(channels[channel]-comp) + (channels[channel] < plimit)*channels[channel]

        return channels

    def load_to_RAM(self):
        assert self.location == "disk"
        self.channels = self.read_audio_segment(0,None)
        self.sampwidth = self.wav_obj.getsampwidth()
        self.framerate = self.wav_obj.getframerate()
        self.wav_obj.close
        self.wav_obj = None
        self.location = "RAM"

    def setsampwidth(self,sampwidth):
        if(self.location != "RAM"):
            raise AttributeError("the file must be loaded to ram using .load_to_RAM() before modifications can be made")
        self.sampwidth = sampwidth

    def update_waveform(self,waveform_operand,time_offset=None,operation="add"):
        """
        updates the existing waveform by performing the operation with the
        waveform_operand. time_offset specifies what time in seconds we need to
        start the modifications at (leave it None for no offset).
        """
        if(self.location != "RAM"):
            raise AttributeError("the file must be loaded to ram using .load_to_RAM() before modifications can be made")
        if(time_offset is not None):
            startframe = self.__convert_time_to_frames(time_offset)
        else:
            startframe = 0
        if(operation=='add'):
            assert len(self.channels) == len(waveform_operand)
            endframe = startframe+len(waveform_operand[0])

            if(endframe > len(self.channels[0])):
                new_channels = []
                for i,c in enumerate(self.channels):
                    d = np.array(c)
                    d.resize(endframe)
                    new_channels.append(d)
                self.channels = new_channels
            for i,c in enumerate(self.channels):
                c[startframe:endframe] += waveform_operand[i]
        if(operation=="subtract"):
            assert len(self.channels == len(waveform_operand))
            endframe = startframe+len(waveform_operand[0])
            if(endframe > len(self.channels[0])):
                for i,c in enumerate(self.channels):
                    d = np.array(s)
                    d.resize(endframe)
                    self.channels[i] = d
            for i,c in enumerate(self.channels):
                c[startframe:endframe] -= waveform_operand[i]

    def write_to_file(self,filename,start_time = None, end_time = None):
        assert self.location == "RAM"
        if(start_time is None and end_time is None):
            file = wave.open(filename,'wb')
            file.setframerate(self.getframerate())
            file.setnframes(self.getnframes())
            file.setnchannels(self.getnchannels())
            file.setsampwidth(self.getsampwidth())
            Hs = []
            posmax = 2**(self.sampwidth*8 - 1)
            comp = 2**(self.sampwidth*8)
            zero = 0
            for channel in self.channels:
                clipped_channel = channel.clip(-posmax,posmax-1)
                H = clipped_channel >= 0
                H = clipped_channel*H + (comp+clipped_channel)*np.logical_not(H)
                H = [int(c) for c in H]
                H = [h.to_bytes(self.sampwidth,"little") if h < comp else zero.to_bytes(self.sampwidth, "little") for h in H ]
                Hs.append(H)
            H = bytearray(self.getnframes()*self.getnchannels()*self.getsampwidth())
            pointer = 0
            for frame in range(self.getnframes()):
                for channel in Hs:
                    for byte in channel[frame]:
                        H[pointer] = byte
                        pointer += 1
            file.writeframes(H)
            file.close()
        else:
            print("not implemented yet")
            return

def read(filename):
    ret = wave_file_object()
    ret.wav_obj = wave.open(filename)
    ret.location = "disk"
    return ret

def new_audio_file(num_channels=2,framerate=44100,sampwidth=2):
    ret = wave_file_object()
    ret.location = "RAM"
    ret.channels = np.zeros((num_channels,1))
    ret.framerate = framerate
    ret.setsampwidth(2)
    return ret

class waveform:
    def __init__(self,protocol,**kwargs):
        if(protocol == "sine"):
            self.protocol = "sine"
            self.help_text = """
            one cycle of a sine wave with amplitude 1.
            """
        if(protocol == "power"):
            self.protocol = "power"
            self.exponent = kwargs["exponent"]
            self.help_text = """
            1-(4*x)**exponent for x < 0.25
            ((1-4*x)**exponent - 1 for x >= 0.25 and x < 0.5
            (4*x-2)**exponent - 1 for x >= 0.5 and x < 0.75
            1-(4*x-2)**exponent for x >= 0.75
            """
        if(protocol == "compound"):
            self.protocol = "compound"
            self.component_waveforms = kwargs["component_waveforms"]

    def generate_wave(self,framerate,frequency,amplitude,length=None,phase = 0,arrival_delay = 0):
        if(self.protocol == "compound"):
            ret = 0
            for component in self.component_waveforms:
                ret += component['waveform'].generate_wave(framerate,frequency*component['frequency'],amplitude*component['amplitude'],length,phase+component['phase'],arrival_delay)
            return ret
        fT = 0
        if(length is not None):
            fT = frequency*np.arange(framerate*length)/framerate
        else:
            if(np.shape(frequency) == ()):
                fT = frequency*np.arange(len(amplitude))/framerate
            else:
                fT = np.zeros(len(frequency)+1)
                np.cumsum(frequency,out=fT[1:])
                fT /= framerate
                fT = fT[:-1]
        fT += phase
        fT += arrival_delay*frequency
        if(self.protocol == "sine"):
            return amplitude*np.sin(2*np.pi*fT)
        if(self.protocol == "power"):
            fT_1 = fT%1
            phasemultiplier = (fT_1 < 0.25)*(1-(4*fT_1)**self.exponent)
            phasemultiplier += np.logical_and(fT_1 >= 0.25, fT_1 < 0.5)*((2-4*fT_1)**self.exponent - 1)
            phasemultiplier += np.logical_and(fT_1 >=0.5, fT_1 < 0.75)*((4*fT_1-2)**self.exponent - 1)
            phasemultiplier += (fT_1 >= 0.75)*(1-(4-4*fT_1)**self.exponent)
            return amplitude*phasemultiplier

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
        print("python3 wapl.py quick_write")
        print("python3 wapl.py waveform")
        print("python3 wapl.py write")
        print("python3 wapl.py update")
        exit(0)
    if(sys.argv[1] == "read"):
        from matplotlib import pyplot as plt
        polaris = read(sys.argv[2])
        channels = polaris.read_audio_segment(0,1)
        m = (channels[0] - channels[1])/2
        print(np.shape(channels))
        for c in channels:
            plt.plot(c)
        plt.show()
    if(sys.argv[1] == "quick_write"):
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
    if(sys.argv[1] == "load_to_RAM"):
        import time
        from matplotlib import pyplot as plt
        polaris = read(sys.argv[2])
        starttime = time.time()
        polaris.load_to_RAM()
        print(f"time taken to load to RAM: {(time.time()-starttime)}s")
        channels = polaris.read_audio_segment(0,1)
        for c in channels:
            plt.plot(c)
        plt.show()
    if(sys.argv[1] == "write"):
        import time
        binaural = new_audio_file(2,44100,2)
        wf = waveform("sine")
        starttime = time.time()
        print(binaural.get_peak_val())
        ampmod1 = np.linspace(binaural.get_peak_val()/10,binaural.get_peak_val(),44100*5)
        print(time.time()-starttime)
        channel1 = wf.generate_wave(44100,440,ampmod1)
        print(time.time()-starttime)
        channel2 = wf.generate_wave(44100,440,ampmod1[::-1])
        print(time.time()-starttime)
        binaural.channels = [channel1,channel2]
        binaural.write_to_file("sampleaudio/binaural.wav")
        print(time.time()-starttime)
    if(sys.argv[1] == "update"):
        wf = waveform("sine")
        naf = new_audio_file(2,44100,2)
        waveform_operand = [wf.generate_wave(44100,440,2**13,5)]*2
        naf.update_waveform(waveform_operand,operation="add")
        waveform_operand = [wf.generate_wave(44100,220,2**13,2)]*2
        naf.update_waveform(waveform_operand,operation="add")
        naf.update_waveform(waveform_operand,time_offset=6,operation="add")
        naf.write_to_file("sampleaudio/update.wav")
    if(sys.argv[1] == "alternate-waveforms"):
        from matplotlib import pyplot as plt
        for i in range(1,7):
            wf = waveform("power",exponent=i)
            gw = wf.generate_wave(44100,440,2**15,5)
            naf = new_audio_file(2,44100,2)
            naf.update_waveform([gw,gw],operation="add")
            naf.write_to_file(f"sampleaudio/power_{i}.wav")
    if(sys.argv[1] == "compound-waveform"):
        from matplotlib import pyplot as plt
        wf0 = waveform("sine")
        wf_c = waveform("compound",component_waveforms=[
        {"waveform":wf0,"frequency":1,"amplitude":0.5,"phase":0},
        {"waveform":wf0,"frequency":2,"amplitude":0.1,"phase":0.5},
        {"waveform":wf0,"frequency":4,"amplitude":0.01,"phase":0},
        {"waveform":wf0,"frequency":8,"amplitude":0.001,"phase":0},
        {"waveform":wf0,"frequency":16,"amplitude":0.0001,"phase":0},
        ])
        gw = wf_c.generate_wave(44100,440,2**15,5)
        naf = new_audio_file(2,44100,2)
        naf.update_waveform([gw,gw],operation="add")
        naf.write_to_file("sampleaudio/tentative-violin.wav")
