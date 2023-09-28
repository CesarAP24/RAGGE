# funcion para generar contraseña de 6 digitos de letras y numeros
import random
import string

def generate_password():
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(6))