from django.contrib import auth
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response



@api_view(['GET'])
def flutter_login(request):
    user = auth.authenticate(
        username=request.POST['username'], password=request.POST['password'])
    if user is not None:
        return Response({'token': access_token}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
