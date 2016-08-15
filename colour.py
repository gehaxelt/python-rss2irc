
class Colours:
	def __init__(self, col, string):
		self.colour = col
		self.string = string
		self.default = '\017'
		self.ret = self.string+self.default

	def get(self):
		if self.colour == '1' or self.colour == 'red':
			return '\00304'+self.ret
		elif self.colour == '2' or self.colour == 'green':
			return '\00303'+self.ret
		elif self.colour == '3' or self.colour == 'yellow':
			return '\00308'+self.ret
		elif self.colour == '4' or self.colour == 'blue':
			return '\00312'+self.ret
		elif self.colour == '5' or self.colour == 'purple':
			return '\00306'+self.ret
		elif self.colour == '6' or self.colour == 'cyan':
			return '\00310'+self.ret
		elif self.colour == '7' or self.colour == 'lightgreen':
			return '\00309'+self.ret
		elif self.colour == '8' or self.colour == 'grey':
			return '\00314'+self.ret
		elif self.colour == '9' or self.colour == 'pink':
			return '\00313'+self.ret
		elif self.colour == '10' or self.colour == 'lightblue':
			return '\00311'+self.ret
		else:
			return '\00316'+self.ret

"""
if __name__ == "__main__":
	for i in range(0, 11):
		print Colours(str(i), 'Testing').get() + "TESTING "+Colours(str(i), 'wat').get()
"""
