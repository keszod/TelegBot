# -*- coding: utf-8 -*-
import requests
import json
import traceback
import urllib.parse
import os
from sql import SQLighter
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from time import sleep

def get_products(chat_id):
	with open(f'products/products {chat_id}.json','r',encoding='utf-8-sig') as file:
		products = json.loads(file.read())

	return products

def save_products(products,chat_id):
	print('saving')
	with open(f'products/products {chat_id}.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(products))

def start_loop():
	print('Петля запущена')
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	db_path = os.path.join(BASE_DIR, "db.db")

	db = SQLighter(db_path)
	
	while  True:
		sended_message = False
		while True:
			hour,minute = datetime.now().strftime("%H:%M").split(':')
			print(hour,'hour')
			if hour == '10' and not sended_message:
				users = db.get_users()

				for user in users:		
					start_parse(user[0])
				sended_message = True
			if hour == '11':
				break
			
			sleep(20)

#@dp.message_handler()
def start_parse(chat_id):
	products = get_products(chat_id)
	send_message(chat_id,'Отчёт готовится,ожидайте')
	for product in products:
		name = product['name'].split('/')[0]
		url = product['url']
		text = f'<b>{name}</b>:\n\n'
		count = 0		
		for search in product['search']:
			count += 1
			name_search = search[0].strip()
			print(name_search)
			try:
				number = check_position(name_search,url)
				
				if number is None:
					answer_message = name_search+' - товар в выдаче, на 25+ странице🔴'
				elif 'реклама' in number:
					number = number.split()[1]
					if not 'реклама' in search[1]:
						answer_message = name_search+' - товар рекламный©,место '+number+' 🟢'
					else:
						diff = str(int(search[1].split()[1])-int(number))
						end = '🟢' if int(diff) >= 0 else '🔴'
						diff = '+'+diff if int(diff) >= 0 else diff

						answer_message = name_search+' - товар рекламный©,место '+number+'('+diff+') '+end
				
				elif 'нет' in number:
					answer_message = '<del>'+name_search+'</del>'+' - товар отсутствует в выдаче 🔴'
				
				else:
					if not search[1] or not search[1].isnumeric():
						answer_message = name_search+' - место '+number+' 🟢'
					else:
						diff = str(int(search[1])-int(number))
						end = '🟢' if int(diff) >= 0 else '🔴'
						diff = '+'+diff if int(diff) >= 0 else diff

						answer_message = name_search+' - место '+number+'('+diff+') '+end
				
				
				search[1] = number
				save_products(products,chat_id)
			except:
				traceback.print_exc()
				answer_message = name_search+' - произошла ошибка⚠️'

			text += str(count)+'. '+answer_message+'\n'
		
		text += '\n'
		send_message(text,chat_id)
	
	return number

def send_message(message,chat_id):
	telegram_api = 'https://api.telegram.org/bot5551309951:AAG3V_8u2GzIszbet40XhgZlkVd4FJ1IT6o/'
	chat_id = chat_id
	message = urllib.parse.quote_plus(message)
	url = telegram_api + 'sendMessage?chat_id='+chat_id+'&text='+message+'&parse_mode=html'
	requests.get(url)

def get_page(url):
	headers = get_headers()
	r = requests.get(url,headers=headers)
	test(r.text,'test.html')
	json_ = json.loads(r.text)
	sleep(1)
	return json_

def test(content,name):
	with open(name,'w',encoding='utf-8') as f:
		f.write(content)

def get_headers():
	with open('headers.txt','r',encoding='utf-8') as file:
		headers = file.read()
		headers = headers.splitlines()
		py_headers = {}
		for header in headers:
			key,value = header.split(': ')
			py_headers[key] = value

		return py_headers

def check_adv(query,id_):
	search_url = f'https://catalog-ads.wildberries.ru/api/v5/search?keyword={query}'
	print(search_url)
	data = get_page(search_url)['adverts']
	number = 1
	if data is None:
		return None
	
	for adv in data:
		print(int(adv['id']))
		if int(adv['id']) == int(id_):
			return number
		number += 1
	return None

def get_name(id_):
	print(id_)
	search_url = f'https://wbx-content-v2.wbstatic.net/ru/{id_}.json'
	result = get_page(search_url)
	if 'imt_name'  in result:
		return result['imt_name']
	else:
		return result['subj_name']

def check_product(query,id_,last_page=26,extra_params=''):
	number = 1
	for page in range(1,last_page):
		print('page is ',page)
		search_url = f'https://search.wb.ru/exactmatch/ru/common/v4/search?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-162903,-446078&emp=0&lang=ru&locale=ru&page={page}&pricemarginCoeff=1.0&query={query}&reg=0&regions=68,64,83,4,38,80,33,70,82,86,30,69,22,66,31,40,1,48&resultset=catalog&sort=popular&spp=0'+extra_params
		data = get_page(search_url)['data']

		for product in data['products']:
			if int(product['id']) == int(id_):
				print(id_)
				return str(number)

			number += 1
		
		if len(data['products']) < 100:
			return None
	else:
		return None

def check_brand(query,id_):
	search_url = f'https://wbx-content-v2.wbstatic.net/ru/{id_}.json'
	brand_id = get_page(search_url)['data']['brand_id']
	extra = f'&fbrand={brand_id}'

	return check_product(query,id_,10000,extra)
	
def check_position(query,url):
	id_ = int(url.split('/')[4].split('/')[0])
	adv = check_adv(query,id_)
	if  adv:
		print('Товар найден среди рекламы')
		return 'реклама '+str(adv)
	
	print('Товар не рекламный')
	
	if not check_brand(query,id_):
		print('Товар отсутствует')
		return 'нет'

	print('Товар найден в сортировки по бренду')

	return check_product(query,id_)

if __name__ == '__main__':
	#start_parse('618939593')
	#start_loop()
	send_message('~Товар~','618939593')