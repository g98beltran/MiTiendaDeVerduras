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
from django.conf import settings
from django.core.mail import send_mail

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

@csrf_protect
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

@csrf_protect
def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		email = customer.email
	else:
		customer, order = guestOrder(request, data)
		email = customer.email
	aux = data['form']['total']
	aux=aux.replace(",",".")
	total = float(aux)
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()
	if order.shipping == True:
		envio =ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)
	else:
		envio = "No hay Envio se trata de un producto digital"

	direccion = 'Dirección -> '+str(data['shipping']['address'])+'\nCiudad -> '+str(data['shipping']['city'])+'\nPaís -> '+str(data['shipping']['state'])+'\nCódigo Postal -> '+str(data['shipping']['zipcode'])
	mensaje = "Hola, "+ customer.name +".\nHa realizado usted un pedido en MiTiendadeVerduras.com \n\n"
	mensaje += "Productos:"+str(order.get_elementos)
	mensaje += "La dirección introducida es: \n"+direccion+ "\n\n"
	mensaje += "Revisaremos si el pedido está pagado y le enviaremos el paquete.\n\n"
	mensaje += "Muchas gracias por comprar en nuestra tienda.\n\n\n\n\n"
	
	para = [settings.EMAIL_HOST_USER,email]

	send_mail(
		'Pedido MiTiendaDeVerduras',
		mensaje,
		settings.EMAIL_HOST_USER,
		para
	)
	# send_mail('hola','Correo enviado desde Django','xxxxx@gmail.com',a)
	return JsonResponse('Payment submitted..', safe=False)

