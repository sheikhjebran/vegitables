from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from ..repositories.arrival_repository import ArrivalRepository
from ..repositories.mobile_sales_repository import MobileSalesRepository
from ..repositories.shop_metadata_repository import ShopMetadataRepository


mobile_sales_repository = MobileSalesRepository()
arrival_repository = ArrivalRepository()
shop_metadata_repository = ShopMetadataRepository()


def _arrival_firebase_required_message():
    return 'Enable USE_FIREBASE_ARRIVAL=True. SQL arrival path has been removed from mobile goods lookup.'


def _load_shop_metadata(user_id):
    return shop_metadata_repository.require_by_owner_user_id(user_id)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
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
        print(f"Access token frrom Django is = {access_token}")
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
        shop_detail_object = _load_shop_metadata(request.user.id)

        if not arrival_repository.using_firebase():
            return Response({"message": _arrival_firebase_required_message()}, status=status.HTTP_400_BAD_REQUEST)

        arrival_detail_object = arrival_repository.list_available_goods_by_shop(shop_detail_object.pk)
        response_data = [
            {
                'id': goods.local_id,
                'shop': shop_detail_object.pk,
                'arrival_entry': entry.id,
                'former_name': goods.former_name,
                'initial_qty': goods.initial_qty,
                'qty': goods.qty,
                'weight': goods.weight,
                'remarks': goods.remarks,
                'item_name': goods.item_name,
                'advance': goods.advance,
                'patti_status': goods.patti_status,
            }
            for entry, goods in arrival_detail_object
        ]

        return Response({"data": response_data, "message": "Get arrival"}, status=status.HTTP_200_OK)
    except ValueError as error:
        return Response({"message": str(error)}, status=status.HTTP_400_BAD_REQUEST)
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
        shop = _load_shop_metadata(request.user.id)

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
        sales_bill = mobile_sales_repository.create(
            shop_id=shop.pk,
            name=name,
            lot_no=lot_no,
            total_bags=total_bags,
            net_weight=net_weight,
        )

        return Response(
            {"message": f"Sales data added successfully for {sales_bill.name}."},
            status=status.HTTP_201_CREATED,
        )

    except ValueError as error:
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
