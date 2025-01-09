from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import Shop, ArrivalGoods, MobileSalesBill
from django.db import transaction


class ArrivalGoodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArrivalGoods
        fields = '__all__'


@api_view(['POST'])
def login_view(request):
    """
    Authenticate user based on username and password, and return an access token.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)

    if user is not None:
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response(
            {"access_token": access_token},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_arrival_goods(request):
    print(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
    if not request.user.is_authenticated:
        return Response({"message": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        shop_detail_object = Shop.objects.get(shop_owner=request.user.id)
        arrival_detail_object = ArrivalGoods.objects.filter(
            Q(shop=shop_detail_object) & Q(qty__gte=1)
        )
        serializer = ArrivalGoodsSerializer(arrival_detail_object, many=True)

        return Response({"data": serializer.data, "message": "Get arrival"}, status=status.HTTP_200_OK)
    except Shop.DoesNotExist:
        return Response({"message": "Shop not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensures only authenticated users can access the endpoint
def add_sales_data(request):
    """
    Endpoint to add sales data and save it in the database.
    """
    try:
        # Extract the sales data from the request
        shop_owner = request.user  # The authenticated user
        shop = Shop.objects.filter(shop_owner=shop_owner).first()
        if not shop:
            return Response({"error": "Shop not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        name = data.get('name')
        lot_no = data.get('lot_no')
        total_bags = data.get('total_bags')
        net_weight = data.get('net_weight')

        # Validate required fields
        if not all([name, lot_no, total_bags, net_weight]):
            return Response(
                {"error": "All fields (name, lot_no, total_bags, net_weight) are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create and save the MobileSalesBill instance
        with transaction.atomic():  # Ensures atomicity for database operations
            sales_bill = MobileSalesBill.objects.create(
                shop=shop,
                name=name,
                lot_no=lot_no,
                total_bags=int(total_bags),
                net_weight=float(net_weight),
            )

        return Response(
            {"message": f"Sales data added successfully for {sales_bill.name}."},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
