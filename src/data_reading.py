import os
import pickle
import pandas as pd
import docx

class DataReader(object):
	"""Read the necessary data from various sources related to the Test Automation."""
	def __init__(self, path):
		self.path = path
		self.docs = self.read_docs()
		self.test_steps = self.read_test_steps()
		self.test_blocks = self.read_test_blocks()
		self.implemented_tests = self.read_implemented_tests()
		self.entities = self.read_entities()
		self.aliases = self.read_aliases()

	def read_docs(self):
		implemented_test_scenarios_file_path = os.path.join(self.path, "implemented-test-scenarios/TESTS.xlsx")
		test_scenarios_dir_path = os.path.join(self.path, "test-scenarios-reqs-coverage")
		requirements_dir_path = os.path.join(self.path, "reqs")
		documentation_dir_path = os.path.join(self.path, "documentation")

		# Read data from Implemented test scenarios
		implemented_test_scenarios_files_dict = pd.read_excel(implemented_test_scenarios_file_path, sheet_name=None, usecols=0)
		implemented_test_scenarios_files = list(implemented_test_scenarios_files_dict.keys())
		implemented_test_scenarios_files = [f for f in implemented_test_scenarios_files[4:] if f != "REDUNDANCY_CONCEPT"]
		
		implemented_test_scenarios_data = []
		for file in implemented_test_scenarios_files:
			implemented_test_scenarios_data.extend(self.read_excel(implemented_test_scenarios_file_path, file, 1, None))
			implemented_test_scenarios_data.extend(self.read_excel(implemented_test_scenarios_file_path, file, 2, None))
			implemented_test_scenarios_data.extend(self.read_excel(implemented_test_scenarios_file_path, file, 3, None))

		print("Implemented test scenarios files... Done.")

		# Read data from Test scenarios (Excel files)
		test_scenarios_data = []
		test_scenarios_files = self.get_files(test_scenarios_dir_path, ".xlsx")

		for file in test_scenarios_files:
			test_scenarios_data.extend(self.read_excel(file, "Requirements", "Req Name", 1))
			test_scenarios_data.extend(self.read_excel(file, "Requirements", "Description", 1))
			test_scenarios_data.extend(self.read_excel(file, "Test Design Steps", "Test Design Step Name", 1))
			test_scenarios_data.extend(self.read_excel(file, "Test Design Steps", "Test Name", 1))
			test_scenarios_data.extend(self.read_excel(file, "Test Design Steps", "Test Design Description", 1))
			test_scenarios_data.extend(self.read_excel(file, "Test Design Steps", "Test Design Expected Result", 1))

		print("Test scenarios files... Done.")

		# Read data from Requirements (Excel files)
		requirements_data = []
		requirements_files = self.get_files(requirements_dir_path, ".xlsx")

		for file in requirements_files:
			requirements_data.extend(self.read_excel(file,"Sheet1", "Description"))

		print("Requirements files... Done.")

		# Read data from Documentation (Word files)
		documentation_data = []
		documentation_files = self.get_files(documentation_dir_path, ".docx", include_subdirs=True)
		
		for file in documentation_files:
			documentation_data.extend(self.read_word(file))
		print("Documentation files... Done.")

		# Merge data
		docs = []
		docs.extend(implemented_test_scenarios_data)
		docs.extend(test_scenarios_data)
		docs.extend(requirements_data)
		docs.extend(documentation_data)

		return docs

	def read_test_steps(self):
		scenarios_dir_path = os.path.join(self.path, "evaluation")
		file = scenarios_dir_path + "/TestScenariosWithSteps.xlsx"

		test_steps = []
		test_steps.extend(self.read_excel(file, "Test Design Steps", "Test Design Description", 1))

		return test_steps

	def read_test_blocks(self):
		"""Read extracted descriptions from machine -high level- test blocks (CSV file) """
		test_blocks_file_path = os.path.join(self.path, "parsed/test-blocks/machine_blocks.csv")
		test_blocks_data = pd.read_csv(test_blocks_file_path)
		test_blocks = test_blocks_data["description"].tolist()
		print("Test blocks... Done.")

		return test_blocks

	def read_implemented_tests(self):
		implemented_tests_path = os.path.join(self.path, "parsed/implemented-tests")
		implemented_tests = self.get_files(implemented_tests_path, ".csv")

		return implemented_tests

	def read_entities(self):
		entities_path = os.path.join(self.path, "parsed/entities.csv")
		entities = pd.read_csv(entities_path)
		parameters = entities['Parameters'].tolist()
		applications = entities['Applications'].tolist()
		systems = entities['Systems'].tolist()

		return (parameters, applications, systems)

	def read_aliases(self):
		aliases_path = os.path.join(self.path, "parsed/aliases.csv")
		aliases_data = pd.read_csv(aliases_path)
		aliases = aliases_data['Alias'].tolist()
		names = aliases_data['Name'].tolist()
		
		return (aliases, names)
	
	@staticmethod
	def read_excel(file, sheet, column, header_row=0):	
		excel_dataframe = pd.read_excel(file, sheet_name=sheet, header=header_row).astype(str)
		text_list = excel_dataframe[column].values.tolist()

		return text_list

	@staticmethod
	def read_word(file):
		doc = docx.Document(file)
		text_list = []
		for par in doc.paragraphs:
		    text_list.append(par.text)
		
		return text_list
		    
	@staticmethod
	def get_files(dir_path, file_extension, include_subdirs=False):
		
		if include_subdirs:
			files = [os.path.join(root, name)
		                for root, dirs, files in os.walk(dir_path)
			            for name in files
			            if name.endswith((file_extension))]
		else:
			files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(file_extension)]

		return files