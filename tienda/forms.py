from pyexpat import model
from socket import fromshare
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from tienda.models import Customer

class CrearUsuarioForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2']
        