import os
import base64
from mimetypes import guess_type
from tqdm import tqdm
import openai
from evaluators.evaluator import Evaluator
from time import sleep
import re

class GPT_4o_Evaluator(Evaluator):
	def __init__(self, model_name, k=-1):
		super(GPT_4o_Evaluator, self).__init__(model_name, k)
		self.client = openai.OpenAI(
			api_key = "YOUR_API_KEY",
			base_url = "YOUR_BASE_URL"
		)
		
	def split_markdown(self, md):
		# use regex to extract image property
		items = re.split('(<img_\d+>)', md) # 对输入的数据按照<img_数字>拆分为列表

		# 从分割后的字符串列表中去除空的元素（完全由空白符、换行符或制表符构成的字符串）
		items = [item for item in items if item and not item.isspace()]
		message_items = [] # 对md解析后的，输入给模型的message列表
		for item in items:
			if item[:5] == '<img_': # 图片
				image_path = os.path.join(self.image_parent_dir, item[1:-1]+'.jpg')
				if not os.path.exists(image_path):
					print('Image file not found!')
				mime_type, _ = guess_type(image_path)
				assert mime_type == 'image/jpeg'
				with open(image_path, 'rb') as image_file:
					base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
				message_items.append({
					'type': 'image_url',
					'image_url': {
						'url': f"data:{mime_type};base64,{base64_encoded_data}"
					}
				})
			else:
				message_items.append({ # 模型的文本接口格式
					'type': 'text',
					'text': item.strip()
				})
		return message_items

	def make_input(self, prompt, question_content): # 按照学科，组装最终给模型的输入
		if self.is_chinese:
			question_message = self.split_markdown(prompt + '\n' + question_content)
			messages = [
				{
					'role': 'system',
					'content': f'你是一个中文人工智能助手。请根据要求，完成下面的竞赛题目。'
				},
				{
					'role': 'user',
					'content': question_message
				}
			]
		else:
			question_message = self.split_markdown(prompt + '\n' + question_content)
			messages = [
				{
					'role': 'system',
					'content': f'You are an AI assistant. Please answer the following competition problems as required.'
				},
				{
					'role': 'user',
					'content': question_message
				}
			]
		return messages

	def get_answer(self, input): # 让模型推理出答案
		response=None
		timeout_counter=0
		while response is None and timeout_counter<=30:
			try:
				response = self.client.chat.completions.create(
					model= "gpt-4o-2024-05-13",
					messages=input,
					temperature=0.,
					max_tokens=1024
				)
			except Exception as msg:
				if "timeout=600" in str(msg):
					timeout_counter+=1
				print(msg)
				sleep(5)
				continue
		if response==None:
			answer = ''
		else:
			answer = response.choices[0].message.content
		return answer
