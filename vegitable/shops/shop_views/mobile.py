from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from ..models import MobileSalesBill,Shop


@api_view(['POST'])
def login_view(request):
    # Validate input data
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        # Generate JWT token for authenticated user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return Response({"message": "Login successful", "access_token": access_token}, status=status.HTTP_200_OK)
    else:
        # Generic error message for security reasons
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_sales_data_view(request):
    try:
        # Extract data from the POST request
        name = request.data.get('name')
        lot_no = request.data.get('lot_no')
        total_bags = request.data.get('total_bags')
        net_weight = request.data.get('net_weight')

        # Validate required fields
        if not all([name, lot_no, total_bags, net_weight]):
            return Response(
                {"error": "All fields (name, lot_no, total_bags, net_weight) are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate numeric fields
        try:
            total_bags = int(total_bags)
            net_weight = float(net_weight)
        except ValueError:
            return Response(
                {"error": "Total bags must be an integer and net weight must be a float."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)

        MobileSalesBill.objects.create(
            name=name,
            lot_no=lot_no,
            total_bags=total_bags,
            net_weight=net_weight,
            shop = shop_detail_object
        )

        return Response({"message": "Data added successfully"}, status=status.HTTP_201_CREATED)

    except Exception as e:
        # Handle unexpected errors
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
