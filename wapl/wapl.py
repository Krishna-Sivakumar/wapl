import wave
import numpy as np

class wapl:
    def __init__(self,filename):
        self.wav_obj = wave.open(filename)
        #you are a wrapper class, you don't get anything else
    
    def getnchannels(self):
        return self.wav_obj.getnchannels()
    
    def getsampwidth(self):
        return self.wav_obj.getsampwidth()
    
    def getframerate(self):
        return self.wav_obj.getframerate()
    
    def getnframes(self):
        return self.wav_obj.getnframes()
    
    def get_audio_length(self):
        return self.wav_obj.getnframes()/self.wav_obj.getframerate()
    
    def __convert_time_to_frames(self,T):
        return int(T*self.wav_obj.getframerate())
    
    def read_audio_segment(self,start_time,end_time):
        assert start_time >= 0
        assert start_time < end_time
        start_frame = self.__convert_time_to_frames(start_time)
        end_frame = self.__convert_time_to_frames(end_time)
        assert end_frame <= self.wav_obj.getnframes()
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

def reverse_bits_8(num):
    remainder = num
    ret = 0
    for i in range(7,-1,-1):
        digit = remainder // 2**i
        remainder = remainder % 2**i
        ret += 2**(7-i)*digit
    return int(ret)

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
