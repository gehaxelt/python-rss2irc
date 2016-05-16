
class Colours:
	def __init__(self, col, string):
		self.colour = col
		self.string = string
		self.default = '\033[0m'
		self.ret = self.string+self.default

	def get(self):
		if self.colour == '1' or self.colour == 'red':
			return '\033[031m'+self.ret
		elif self.colour == '2' or self.colour == 'green':
			return '\033[032m'+self.ret
		elif self.colour == '3' or self.colour == 'yellow':
			return '\033[033m'+self.ret
		elif self.colour == '4' or self.colour == 'blue':
			return '\033[034m'+self.ret
		elif self.colour == '5' or self.colour == 'purple':
			return '\033[035m'+self.ret
		elif self.colour == '6' or self.colour == 'cyan':
			return '\033[036m'+self.ret
		elif self.colour == '7' or self.colour == 'lightgreen':
			return '\033[1;32m'+self.ret
		elif self.colour == '8' or self.colour == 'grey':
			return '\033[1;30m'+self.ret
		elif self.colour == '9' or self.colour == 'pink':
			return '\033[1;35m'+self.ret
		elif self.colour == '10' or self.colour == 'lightblue':
			return '\033[1;34m'+self.ret
		else:
			return '\033[1;37m'+self.ret

#Testing

if __name__ == "__main__":
	for i in range(0, 11):
		print Colours(str(i), 'Testing').get() + "TESTING "+Colours(str(i), 'wat').get()
