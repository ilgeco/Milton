from random import randint

class Pacinco():
    def __init__(self):
        self.blu=":small_blue_diamond:"
        self.orange=":small_orange_diamond:"
        self.number=[":one:",":two:",":three:",":four:",":five:",":six:",":seven:",":eight:",":nine:"]
        self.price=[(":black_circle:",  float(0.2)) \
                    ,(":brown_circle:", float(0.9))\
                    ,(":red_circle:", float(1.1)) \
                    ,(":red_circle:", float(1.1)) \
                    ,(":yellow_circle:", float(1.5))]
    
    def orange_list(self):
        return [self.orange]*9

    def maps(self,x,y):
        tmp = "".join(self.number) +"\n"
        for i in range(8):
            ora = self.orange_list()
            if i == y:               
                ora[x]=self.blu
            tmp += "".join(ora)+"\n"
        name = [x[0] for x in self.price]
        tmp += "".join(name + name[-2::-1]) +"\n"
        return tmp

    def new_pos(self, x):
        if(x==0):
            return 1
        if(x==8):
            return 7
        if(x == -1):
            return randint(0,8)
        prob=randint(0,10000)
        if(prob>=5000):
            return x+1
        else:
            return x-1 

        
            
    #position is a list of number from 0 to 9
    def play(self):    
        out=[]
        x=-1
        for i in range(8):
            x = self.new_pos(x)
            out.append(self.maps(x,i))
        if(x>=5):
            x=8-x
        return (out,self.price[x][1])

