from django.urls import path
from . import views

urlpatterns = [
    
	path('', views.tienda, name="tienda"),
	path('cartera/', views.cartera, name="cartera"),
	path('verificar/', views.verificar, name="verificar"),
    path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
	path('autentificarse/', views.autentificarse, name="autentificarse"),
	path('registrarse/', views.registrarse, name="registrarse"),
	path('desconectarse/', views.desconectarse, name="desconectarse"),

]