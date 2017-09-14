import os, re, xlsxwriter, sys, argparse
controllers = []

def checkIfFileIsController(path):
	lines = [line.rstrip('\n') for line in open(path)]
	for line in lines:
		if line == "@Controller":
			return True

def fetchControllerName(text):
	return re.search(r"(?<=class\s)([a-z-A-Z0-9]+)",text,re.DOTALL).group()

def fetchApi(text):
	res = re.search(r"(?<=@RequestMapping\(Array\(\")[a-zA-Z0-9/{}\-,]+", text)
	if res:
		return res.group()
	else:
		res = re.search(r"(?<=@RequestMapping\(value = Array\(\")[a-zA-Z0-9/{}\-,]+",text)
		if res:
			return res.group()
		return ""

def fetchEndpoints(fullPath):
	f = open(fullPath, "r")
	text = f.read()
	startClassIndex = re.search(r"(class\s.*?)\{",text,re.DOTALL).end()
	text = text[startClassIndex:]
	return re.findall(r"(@RequestMapping.*?[\s\t]def.*?)}",text, re.DOTALL)

def fetchMethod(funcText):
	res = re.search(r"(?<=method\s=\sArray\()([A-Za-z\.]+)",funcText)
	if res:
		return res.group()
	else:
		return ""

def checkIfLoginIsRequired(funcText):
	if "@RequireLogin" in funcText:
		return "True"
	else:
		return "False"

def fetchFunctionName(funcText):
	res = re.search(r"(?<=def\s)([a-zA-Z0-9]+)", funcText,re.DOTALL)
	if res:
		return res.group()
	else:
		return ""

def fetchParameters(funcText):
	res = re.search(r"def\s[A-Za-z0-9]+\((.*?)\):|.*\)\s*=", funcText,re.DOTALL)
	if res:
		return str(res.group(1)).replace("  ", "").replace("\n","").replace(",", ",\n")
	else:
		return ""

def createControllerObject(path):
	f = open(path,"r")
	text = f.read()
	controllerStartIndex = re.search(r"@Controller",text).start()
	RequestMappingStartIndex = re.search(r"@RequestMapping",text).start()
	if RequestMappingStartIndex < controllerStartIndex:
		text = text[RequestMappingStartIndex:]
	else:
		text = text[controllerStartIndex:]
	controllerEndIndex = re.search(r"(class\s.*?)\{",text,re.DOTALL).end()
	controllerData = text[:controllerEndIndex]
	return {"className": fetchControllerName(controllerData), "apiPrefix": fetchApi(controllerData), "path": path, "apiEndpoints": []}

def searchControllers(start_path):
	for path,dirs,files in os.walk(start_path):
		for filename in files:
			fullPath = os.path.join(path,filename)
			if checkIfFileIsController(fullPath):
				controllers.append(createControllerObject(fullPath))

	for controller in controllers:
		for funcText in fetchEndpoints(controller['path']):
			controller["apiEndpoints"].append({"funcName": fetchFunctionName(funcText), "api": controller["apiPrefix"]+fetchApi(funcText), "method": fetchMethod(funcText), "login": checkIfLoginIsRequired(funcText), "parameters": fetchParameters(funcText)})

def createFile(name):
	workbook = xlsxwriter.Workbook(name)
	worksheet = workbook.add_worksheet()

	worksheet.set_column('A:A', 20)
	bold = workbook.add_format({'bold': True})
	worksheet.write('A1', 'Class Name', bold)
	worksheet.write('B1', 'Endpoint Path', bold)
	worksheet.write('C1', 'Method Allowed', bold)
	worksheet.write('D1', 'Function Name', bold)
	worksheet.write('E1', 'Login is required?', bold)
	worksheet.write('F1', 'Parameters', bold)
	worksheet.write('G1', 'Path', bold)

	counter = 1

	for controller in controllers:
		counter+=1
		worksheet.write('G'+str(counter), controller["path"])
		worksheet.write('B'+str(counter), controller["apiPrefix"])
		worksheet.write('A'+str(counter), controller["className"])

		for endpoint in controller["apiEndpoints"]:
			counter+=1
			worksheet.write('B'+str(counter), endpoint["api"])
			worksheet.write('C'+str(counter), endpoint["method"])
			worksheet.write('D'+str(counter), endpoint["funcName"])
			worksheet.write('E'+str(counter), endpoint["login"])
			worksheet.write('F'+str(counter), endpoint["parameters"])

		counter+=1

	workbook.close()

#TODO: extract add endpoints parameters from methods.

def main(argv):
	parser = argparse.ArgumentParser(description='Maps scala code spring controller\'s endpoints to xlsx file.')
	parser.add_argument('-p','--path', help='Source code directory path (Current directory is the default)')
	parser.add_argument('-o', help='Output file name <name>.xlsx (Defualt: mapped.xlsx')
	args = parser.parse_args()
	
	start_path = "."
	fileName = "mapped.xlsx"
	if args.path:
		start_path = args.path

	if args.o:
		fileName = args.o + ".xlsx"
		
	searchControllers(start_path)
	createFile(fileName)

if __name__ == "__main__":
   main(sys.argv[1:])