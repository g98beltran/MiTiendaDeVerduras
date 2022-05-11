from multiprocessing import context
from venv import create
from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from .forms import CrearUsuarioForm

def autentificarse(request):
	if request.method == 'POST' :
		username= request.POST.get('username')
		password= request.POST.get('password')
		user= authenticate(request,username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('tienda')
		else:
			messages.info(request,'nombre o contraseña incorrectos')
	context={}
	return render(request,'tienda/autentificarse.html',context)

def desconectarse(request):
	logout(request)
	return redirect('autentificarse')

@csrf_exempt
def registrarse(request):
	form=CrearUsuarioForm()
	
	if request.method == 'POST':
		form = CrearUsuarioForm(request.POST)
		if form.is_valid():
			form.save()
			user = form.cleaned_data.get('username')
			messages.success(request,'Cuenta creada '+user)
			return redirect('autentificarse')

	
	context={'form':form}
	return render(request,'tienda/registrarse.html',context)

def tienda(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'tienda/tienda.html', context)


def cartera(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'tienda/cartera.html', context)

def verificar(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'tienda/verificar.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

@csrf_exempt
def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)


	
	return JsonResponse('Payment submitted..', safe=False)