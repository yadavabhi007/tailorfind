from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView
from .serializers import *
from core.models import *
import datetime
import math
import json
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db.models import Sum
from geopy.geocoders import ArcGIS
from django.contrib.gis.measure import D
import functools



@functools.lru_cache(maxsize=128)
def convert_address_to_coordinates(address):
    geolocator = ArcGIS(timeout=10)
    location = geolocator.geocode(address)
    latitude = location.latitude
    longitude = location.longitude
    return latitude, longitude


def calculate_distance(coord1, coord2):
    """
    Calculate the distance between two latitude and longitude coordinates
    using the Haversine formula.
    """
    latitude, longitude = coord1
    customer_latitude, customer_longitude = coord2
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(latitude)
    lon1_rad = math.radians(longitude)
    lat2_rad = math.radians(customer_latitude)
    lon2_rad = math.radians(customer_longitude)
    # Earth radius in kilometers
    radius = 6371
    # Calculate differences in latitude and longitude
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    # Apply the Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Calculate the distance
    distance = radius * c
    return distance


def calculate_route_distance(route):
    """
    Calculate the total distance along a route defined by a list of latitude and longitude coordinates.
    """
    total_distance = 0
    for i in range(len(route) - 1):
        coord1 = route[i]
        coord2 = route[i+1]
        distance = calculate_distance(coord1, coord2)
        total_distance += distance
    return total_distance


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserLoginView(APIView):
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.data.get('phone')
            device_token = serializer.data.get('device_token')
            user = authenticate(request, phone=phone)
            if user is not None:
                if user.is_active:
                    device = User.objects.filter(phone=phone)
                    device.update(device_token=device_token)
                    user_type = User.objects.get(phone=phone).profile_type
                    token = get_tokens_for_user(user)
                    return Response({'status':'True', 'message':f'{user_type} Login Succesful', 'user_type':user_type, 'token':token})
                return Response({'status':'False', 'message':'Account Suspended By Admin. Contact Admin'})
            User.objects.create(phone=phone, profile_type='Customer')
            user = authenticate(request, phone=phone)
            device = User.objects.filter(phone=phone)
            device.update(device_token=device_token)
            user_type = User.objects.get(phone=phone).profile_type
            token = get_tokens_for_user(user)
            return Response({'status':'True', 'message':'Customer Created And Login Succesful', 'user_type':user_type, 'token':token})
        return Response({'status':'False', 'message':'Login Data Is Not Valid', 'error':serializer.errors})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    def get(self, request, format=None):
        serializer = UserProfileSerializer(instance=request.user)
        return Response({'status':'True', 'message':'View Your Profile', "data": serializer.data})    
    def put(self, request, format=None):
        serializer = UserProfileSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':'True', 'message':'User Profile Changed Succesfully'})
        return Response({'status':'False', 'message':'404 Bad Request', 'errors':serializer.errors})
    def delete(self, request, format=None):
        user = self.request.user
        user.delete()
        return Response({'status':'True', 'message':'User Account Deleted Successfully'})
    

class UserLogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':'True', 'message':'User is Logout'})
        return Response({'status':'False', 'message':'404 Bad Request', 'errors':serializer.errors})


class TailorListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        tailors = User.objects.filter(profile_type='Tailor')
        serializer = UserProfileSerializer(tailors, many=True)
        return Response({'status':'True', 'message':'View Tailor List', "data": serializer.data})


class FemaleServiceListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        services = Service.objects.filter(category='Female')
        serializer = ServiceSerializer(services, many=True)
        return Response({'status':'True', 'message':'View Tailor Services', "data": serializer.data})


class MaleServiceListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        services = Service.objects.filter(category='Male')
        serializer = ServiceSerializer(services, many=True)
        return Response({'status':'True', 'message':'View Tailor Services', "data": serializer.data})



class CustomerMeasurementView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        serializer = MeasurementSerializer(instance=request.user)
        return Response({'status':'True', 'message':'See Your Measurements', "data": serializer.data})
    def put(self, request, format=None):
        serializer = MeasurementSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':'True', 'message':'Measurements Updated Succesfully'})
        return Response({'status':'False', 'message':'404 Bad Request', 'errors':serializer.errors})    


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        services = Order.objects.filter(Q(Q(customer=request.user)|Q(tailor=request.user))|Q(delivery_boy=request.user)).order_by('-id').exclude(status='Canceled')
        for data in services:
            data.total_price = data.service.all().aggregate(Sum('price'))['price__sum']
            da=data.service.values('service')
            tservice=[]
            for  di in da:
                servicess=Service.objects.get(id=di['service']) 
                tservice.append(servicess.name)
            data.item_name=tservice
        serializer = OrderSerializer(services, many=True)
        return Response({'status':'True', 'message':'View Your Orders', "data": serializer.data})


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id, format=None):
        service = Order.objects.get(id=id)
        service.total_price = service.service.all().aggregate(Sum('price'))['price__sum']
        da=service.service.values('service')
        tservice=[]
        for  di in da:
            servicess=Service.objects.get(id=di['service'])
            tservice.append(servicess.name)
        service.item_name=tservice
        serializer = OrderSerializer(service)
        return Response({'status':'True', 'message':'View Your Orders', "data": serializer.data})


class CustomerSelectServiceView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        services = Service.objects.filter(id__in=request.data.get('service'))
        select_service_id = []
        for service in services:
            selected_service = SelectedService.objects.create(service=service)
            select_service_id.append(selected_service.id)
        return Response({'status':'True', 'message':'Service Selected Successfully', 'ids':select_service_id})

class CustomerSelectServicedeleted(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        selected_services = SelectedService.objects.filter(id__in=request.data.get('service_ids'))
        selected_services.delete()
        return Response({'status':'True', 'message':'Service Deleted Successfully'})

class CustomerSelectedServiceView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        selected_services = SelectedService.objects.filter(id__in=request.data.get('service_ids'))
        for service in selected_services:
            service.selected_service_id = service.service.id
            service.name = service.service.name
            service.type = service.service.type
            service.price = service.service.price
        serializer = ServiceSerializer(selected_services, many=True)
        return Response({'status':'True', 'message':'Selected Service Lists', 'data':serializer.data})



class CustomerServiceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, id, format=None):
        if SelectedService.objects.filter(id=id):
            service = SelectedService.objects.get(id=id)
            serializer = ServiceUpdateSerializer(service, data=request.data, partial=True)
            if serializer.is_valid():
                quantity = serializer.validated_data['quantity']
                price = float(quantity)*float(service.service.price)
                serializer.save(price=price)
                return Response({'status':'True', 'message':'Detail Updated Succesfully'})
            return Response({'status':'False', 'message':'404 Bad Request', 'errors':serializer.errors})
        return Response({'status':'False', 'message':'Service Does Not Exists'})


class CustomerPlaceOrderPreviewView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        selected_services = SelectedService.objects.filter(id__in=request.data.get('selected_service'))
        for selected_service in selected_services:
            selected_service.name = selected_service.service.name
            selected_service.type = selected_service.service.type
        total_price = selected_services.aggregate(Sum('price'))['price__sum']
        serializer = OrderPreviewSerializer(selected_services, many=True)
        return Response({'status':'True', 'message':'Order Created Successfully', 'total_price':total_price, 'data':serializer.data})
    

class CustomerPlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        selected_service = SelectedService.objects.filter(id__in=json.loads(request.data.get('selected_service')))
        print(selected_service)
        prices = [item['price'] for item in selected_service.values('price')]
        total_price=sum(prices)
        price=DeliveryBoyEarning.objects.all().values('prize')
        result = price[0]['prize']
        tailor=float(total_price)-float(result)
        commition=tailor*20/100
        tailor_earning=total_price-float(result)-commition
        customer_delivery_address = request.data.get('customer_delivery_address')
        tailors=User.objects.filter(profile_type="Tailor")
        context=[]
        for tail in tailors:
            latitude, longitude = convert_address_to_coordinates(tail.location)
            customer_latitude, customer_longitude = convert_address_to_coordinates(customer_delivery_address)
            route = [(latitude, longitude), (customer_latitude, customer_longitude)]
            distance = calculate_route_distance(route)
            d={
                "distance":distance,
                "id":tail.id
            }
            context.append(d)
        min_distance_dict = min(context, key=lambda x: x['distance'])
        smallest_id = min_distance_dict['id']
        tailorr=User.objects.get(id=smallest_id)
        data=Order.objects.create(customer=request.user, tailor=tailorr, customer_delivery_address=customer_delivery_address,tailor_price=tailor_earning)
        data.service.set(selected_service)
        order_id=Order.objects.get(id=data.id)
        Notification.objects.create(title='Order Placed',message='Your order has been processed successfully, we will notify as our delivery boy visit for Pickup.',recipient = request.user,order_id=order_id)
        return Response({'status':'True', 'message':'Order Created Successfully'})
    

class NearByTailors(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        customer_latitude=request.data.get('latitude')
        customer_longitude=request.data.get('longitude')
        if customer_latitude and customer_longitude!=None:
            tailors=User.objects.filter(profile_type="Tailor")
            context=[]
            for tailor in tailors:
                latitude, longitude = convert_address_to_coordinates(tailor.location)
                route = [(latitude, longitude), (float(customer_latitude), float(customer_longitude))]
                distance = calculate_route_distance(route)
                d={
                    "distance":distance,
                    "id":tailor.id
                }
                context.append(d)
            ids_greater_than_5 = [item['id'] for item in context if item['distance'] < 5]
            tailorr=User.objects.filter(id__in=ids_greater_than_5)
            for tail in tailorr:
                final_lat, final_long = convert_address_to_coordinates(tail.location)
                tail.latitude=final_lat
                tail.longitude=final_long
            serializer=NearByTailorSerializer(tailorr, many=True)
            return Response({'status':'True', 'message':'Near By Tailors','data':serializer.data})
        return Response({'status':'False', 'message':'Your Location Is required'})



class CustomerCancelOrderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerCancelOrderSerializer
    def put(self, request, id, format=None):
        if Order.objects.filter(customer=request.user, id=id, status='Pending'):
            order = Order.objects.get(id=id)
            serializer = CustomerCancelOrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(status='Canceled',canceled_date=datetime.datetime.now())
            return Response({'status':'True', 'message':'Order Canceled Successfully'})
        return Response({'status':'False', 'message':'You Can Not Cancel This Order'})


class CustomerDeleteSelectedServiceView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, id, format=None):
        if SelectedService.objects.filter(id=id):
            selected_service = SelectedService.objects.filter(id=id)
            selected_service.delete()
            return Response({'status':'True', 'message':'Selected Service Deleted'})
        return Response({'status':'False', 'message':'Selected Service Does Not Exists'})



class TailorUpcomingOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        orders = Order.objects.filter(tailor=request.user, status='Pending').order_by('-id')
        serializer = TailorOrderSerializer(orders, many=True)
        return Response({'status':'True', 'message':'My Upcoming Orders', 'data':serializer.data})


class TailorAcceptOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, id, format=None):
        if Order.objects.filter(tailor=request.user, id=id, status='Pending'):
            delivery=User.objects.filter(profile_type='Delivery Boy')
            order = Order.objects.filter(id=id)
            order.update(status='Accepted By Tailor')
            order = Order.objects.get(id=id)
            for deliveries in delivery:
                AllDeliveryBoyAddData.objects.create(order_id=order,delivery_boy_id=deliveries)
            return Response({'status':'True', 'message':'Order Is Accepted By Tailor'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})


class TailorRejectOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, id, format=None):
        if Order.objects.filter(tailor=request.user, id=id, status='Pending'):
            order = Order.objects.get(id=id)
            tailors=User.objects.filter(profile_type="Tailor")
            context=[]
            for tail in tailors:
                latitude, longitude = convert_address_to_coordinates(tail.location)
                customer_latitude, customer_longitude = convert_address_to_coordinates(order.customer_delivery_address)
                route = [(latitude, longitude), (customer_latitude, customer_longitude)]
                distance = calculate_route_distance(route)
                d={
                    "distance":distance,
                    "id":tail.id
                }
                context.append(d)
            sorted_data = sorted(context, key=lambda x: x['distance'])
            last_element = sorted_data[-1]
            if last_element['id'] != order.tailor.id:
                index = next((i for i, d in enumerate(sorted_data) if d['id'] == order.tailor.id), None)
                first_id = sorted_data[index+1]['id']
                tailorr=User.objects.get(id=first_id)
                order.tailor=tailorr
                order.save()
            else:
                Notification.objects.create(title='Cancelled',message="Sorry, we are unable to find availability of Tailors, can't process your order for now.",recipient=order.customer,order_id=order)
                order.status="Canceled"
                order.save()
            return Response({'status':'True', 'message':'Order Is Rejected By Tailor'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})
    




class TailorCompleteOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, id, format=None):
        if Order.objects.filter(tailor=request.user, id=id, status='Order In Progress'):
            orderr = Order.objects.filter(id=id)
            orders = Order.objects.get(id=id)
            orderr.update(status='Completed', completed_date=datetime.datetime.now())
            Notification.objects.create(title='Complete',message='Your Order has been completed by our Tailor.',recipient = orders.customer,order_id=orders)
            delivery=User.objects.filter(profile_type='Delivery Boy')
            for deliveries in delivery:
                AllDeliveryBoyAddData.objects.create(order_id=orders,delivery_boy_id=deliveries)
            return Response({'status':'True', 'message':'Order Is Now Completed'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})


class TailorCompleteOrderViewList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,formate=None):
        if Order.objects.filter(tailor=request.user,status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered']).exists():
            order = Order.objects.filter(tailor=request.user,status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered']).order_by('-id')
            serializer = TailorOrderSerializer(order,many=True)
            return Response({'status':'True', 'message':'My Completed order list','data':serializer.data})
        return Response({'status':'False', 'message':'Empty'})


class TailorAcceptedOrdersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        orders = Order.objects.filter(tailor=request.user, status__in=['Accepted By Tailor',"Preparing To Pickup For Service","Picked For Service","Order In Progress"]).order_by("-id")
        for order in orders:
            order.total_price = order.service.all().aggregate(Sum('price'))['price__sum']
            da=order.service.values('service')
            tservice=[]
            for di in da:
                servicess=Service.objects.get(id=di['service'])
                tservice.append(servicess.name)
            order.item_name=tservice
        serializer = OrderSerializer(orders, many=True)
        return Response({'status':'True', 'message':'My Accepted Orders', 'data':serializer.data})


class TailorEaringsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        earnings = Earning.objects.filter(order__tailor__id=request.user.id)
        pen_earnings = Earning.objects.filter(order__tailor__id=request.user.id, status__in=['Pending', 'Requested'])
        requested_earnings = Earning.objects.filter(order__tailor__id=request.user.id, status='Requested')
        pen_earning_list = []
        for pen in pen_earnings:
            pen.pending_price = pen.order.service.all().aggregate(Sum('price'))['price__sum']
            pen_earning_list.append(pen.pending_price)
        total_pending_price = math.fsum(pen_earning_list)
        requested_earning_list = []
        for requested_earning in requested_earnings:
            requested_earning.price = requested_earning.order.service.all().aggregate(Sum('price'))['price__sum']
            requested_earning_list.append(requested_earning.price)
        requested_earning_price = math.fsum(requested_earning_list)
        for earning in earnings:
            earning.order_id = earning.order.id
            earning.price = earning.order.service.all().aggregate(Sum('price'))['price__sum']
        serializer = EarningSerializer(earnings, many=True)
        return Response({'status':'True', 'message':'My Accepted Orders', 'total_pending_price':total_pending_price, 'requested_earning_price':requested_earning_price, 'data':serializer.data})


class Tailor_Earning(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        if Order.objects.filter(tailor=request.user,status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered']).exists():
            data=Order.objects.filter(tailor=request.user,status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered'])
            context = []
            tailor_context=[]
            for data in data:
                price=data.tailor_price
                context.append(price)
                d={
                    "order_id":data.id,
                    "completed_date":data.completed_date,
                    'earning':data.tailor_price,
                    "status":"Completed",
                }
                tailor_context.append(d)
            total_tailor_earning=sum(context)
            context2 = []
            if Earning.objects.filter(order=request.user).exists():
                earn=Earning.objects.filter(order=request.user)
                for ear in earn:
                    price2=ear.requested_amount
                    context2.append(float(price2))
                total_withdrow_amount=sum(context2)
                remain_price=total_tailor_earning-total_withdrow_amount
            else:
                remain_price=context
            return Response({'status':'True', 'message':'Your Earning',"total_amount":total_tailor_earning,"balance_amount":remain_price,"data":tailor_context})
        return Response({'status':'False', 'message':'Empty'})


class TailorEaringRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, format=None):
        if Order.objects.filter(tailor=request.user,status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered']).exists():
            data=Order.objects.filter(tailor=request.user,status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered'])
            request_amount=request.data.get('amount')
            context = []
            for data in data:
                price = data.tailor_price
                context.append(price)
            total_tailor_earning=sum(context)
            context2 = []
            if Earning.objects.filter(order=request.user).exists():
                earn = Earning.objects.filter(order=request.user)
                for ear in earn:
                    price2 = ear.requested_amount
                    context2.append(float(price2))
                total_withdrow_amount = sum(context2)
                remain_price = total_tailor_earning-total_withdrow_amount
            else:
                remain_price = context
            if float(request_amount) <= remain_price:
                Earning.objects.create(requested_amount=request_amount,request_date=datetime.datetime.now(),order=request.user,profile_type=request.user.profile_type)
                return Response({'status':'True', 'message':'You Have Requested Your Earning'})
            return Response({'status':'False', 'message':'You have no efficent balance'})
        return Response({'status':'False', 'message':'You have no completed order'})


class EarningWithdrowlist(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        earn=Earning.objects.filter(order=request.user).order_by('-id')
        serializer=EarningSerializer(earn,many=True)
        return Response({'status':'True', 'message':'Withdrewal List',"data":serializer.data})


class DeliveryBoyUpcomingOrder(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user).exists():
            data = Order.objects.filter(status__in=['Accepted By Tailor','Completed'])
            allids = []
            for data in data:
                oid = data.id
                allids.append(oid)
            users = AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user,order_id__in=allids,status="Incomplete").order_by('-id')
            context=[]
            for user in users:
                order = Order.objects.get(id=user.order_id.id)
                d={
                    "order_id":order.id,
                    "status":order.status,
                    "customer_address":order.customer_delivery_address,
                    "order_date":order.order_date,
                    "tailor_address":order.tailor.location,
                }
                context.append(d)
            return Response({'status':'True', 'message':'My Upcoming Orders', 'data':context})
        else:
            return Response({'status':'True', 'message':'Empty'})
    

class DeliveryBoyAcceptOrder(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        if Order.objects.filter(id=id,status__in=['Accepted By Tailor','Completed']).exists():
            order = Order.objects.filter(id=id)
            check = Order.objects.get(id=id)
            if check.status =='Accepted By Tailor':
                order.update(status='Preparing To Pickup For Service', delivery_boy=request.user)
            else:
                order.update(status='Preparing To Pickup For Delivery', delivery_boy=request.user)
            user = AllDeliveryBoyAddData.objects.filter(order_id=id,status="Incomplete").exclude(delivery_boy_id=request.user)
            user.delete()
            return Response({'status':'True', 'message':'Order Accepted By You'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})

            
class DeliveryBoyRejectOrder(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, id):
        if Order.objects.filter(id=id,status__in=['Accepted By Tailor','Completed']).exists():
            user = AllDeliveryBoyAddData.objects.get(order_id=id, delivery_boy_id=request.user, status="Incomplete")
            user.delete()
            return Response({'status':'True', 'message':'Order Rejected By You'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})


class DeliveryBoyAccptedOrderList(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user,status="Incomplete").exists():
            delivery=AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user,status="Incomplete").order_by("-id")
            context = []
            for deliveries in delivery:
                data=Order.objects.filter(id=deliveries.order_id.id,status__in=['Preparing To Pickup For Service','Picked For Service','Preparing To Pickup For Delivery','Picked For Delivery'])
                for data in data:
                    da = data.service.values('service')
                    tservice=[]
                    for di in da:
                        services = Service.objects.get(id=di['service'])
                        tservice.append(services.name)
                    if data.status=="Preparing To Pickup For Service":
                        d={
                            "order_id":data.id,
                            "name":f"{data.customer.first_name} {data.customer.last_name}",
                            "phone_number":data.customer.phone,
                            "pickup_address":data.customer_delivery_address,
                            "deliver_address":data.tailor.location,
                            "date":data.order_date,
                            "Items":tservice,
                            "status":data.status
                        }
                    elif data.status == 'Picked For Service':
                        d={
                            "order_id":data.id,
                            "date":data.order_date,
                            "name":f"{data.tailor.first_name} {data.tailor.last_name}",
                            "phone_number":data.tailor.phone,
                            "pickup_address":data.customer_delivery_address,
                            "deliver_address":data.tailor.location,
                            "Items":tservice,
                            "status":data.status
                        }
                    elif data.status == "Preparing To Pickup For Delivery":
                        d={
                            "order_id":data.id,
                            "date":data.completed_date,
                            "name":f"{data.tailor.first_name} {data.tailor.last_name}",
                            "phone_number":data.tailor.phone,
                            "pickup_address":data.tailor.location,
                            "deliver_address":data.customer_delivery_address,
                            "Items":tservice,
                            "status":data.status
                        }
                    else:
                        d={
                            "order_id":data.id,
                            "name":f"{data.customer.first_name} {data.customer.last_name}",
                            "phone_number":data.customer.phone,
                            "pickup_address":data.tailor.location,
                            "deliver_address":data.customer_delivery_address,
                            "date":data.completed_date,
                            "Items":tservice,
                            "status":data.status
                        }
                    context.append(d)
            return Response({'status':'True', 'message':'My Orders', 'data':context})
        else:
            return Response({'status':'False', 'message':'Empty'})


class DeliveryBoyPickedForService(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, id):
        if Order.objects.filter(id=id, status__in=["Preparing To Pickup For Service","Preparing To Pickup For Delivery"]).exists():
            statuss = Order.objects.get(id=id)
            order = Order.objects.filter(id=id, delivery_boy=request.user)
            if statuss.status == "Preparing To Pickup For Service":
                order.update(status="Picked For Service")
                Notification.objects.create(title='Picked Up', message='Your Order has been picked by our Delivery Boy.',recipient = statuss.customer,order_id=statuss)
            else:
                order.update(status="Picked For Delivery")
            return Response({'status':'True', 'message':'Order Picked By You'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})
    

class DeliveryBoyDeliveredService(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,id):
        if Order.objects.filter(id=id,status__in=["Picked For Service","Picked For Delivery"]).exists():
            statuss=Order.objects.get(id=id)
            order=Order.objects.filter(id=id, delivery_boy=request.user)
            if statuss.status=="Picked For Service":
                order.update(status="Order In Progress", pickup_date=datetime.datetime.now())
                complete=AllDeliveryBoyAddData.objects.filter(order_id=id, delivery_boy_id=request.user,status='Incomplete')
                complete.update(status="PickCompleted")
            else:
                order.update(status="Delivered", delivery_date=datetime.datetime.now())
                complete=AllDeliveryBoyAddData.objects.filter(order_id=id, delivery_boy_id=request.user, status='Incomplete')
                complete.update(status="DelCompleted")
                Notification.objects.create(title='Delivered', message='Your order has been delivered , thanks for using our services.',recipient = statuss.customer,order_id=statuss)
            return Response({'status':'True', 'message':'Order Delivered By You'})
        return Response({'status':'False', 'message':'You Can Not Change This Order'})


class DeliveryBoyCompeleteDeliveryList(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user, status__in=['DelCompleted','PickCompleted']).exists():
            history = AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user, status__in=['DelCompleted','PickCompleted']).order_by('-id')
            context = []
            for history in history:
                order=Order.objects.get(id=history.order_id.id)
                if history.status=="DelCompleted":
                    date=order.delivery_date
                    order_type="Deliver Order"
                else:
                    date=order.pickup_date
                    order_type="Pickup Order"
                d={
                    "Order":order_type,
                    "order_id":order.id,
                    "delivered_date":date,
                    "status": "Completed"
                }
                context.append(d)
            return Response({'status':'True', 'message':'My Orders', 'data':context})
        else:
            return Response({'status':'False', 'message':'Empty'})


class ReceiveNotification(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if Notification.objects.filter(recipient=request.user).exists():
            print(request.user)
            notify=Notification.objects.filter(recipient=request.user).order_by('-id')
            print(notify)
            serializer=NotificationSeializer(notify,many=True)
            notify.update(is_seen=True)
            return Response({'status':'True', 'message':'Notifications', "data": serializer.data})
        return Response({'status':'False', 'message':'Empty',})
    

class DeliveryBoyTotalEarning(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user, status__in=['DelCompleted','PickCompleted']):
            history = AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user, status__in=['DelCompleted','PickCompleted']).order_by('-id')
            total_count = history.count()
            earn = AllDeliveryBoyAddData.objects.all()
            value = earn.values('prize').first().get('prize')
            context = []
            for history in history:
                order=Order.objects.get(id=history.order_id.id)
                if history.status == "DelCompleted":
                    date=order.delivery_date
                    order_type="Deliver Order"
                else:
                    date=order.pickup_date
                    order_type="Pickup Order"
                d={
                    "Order":order_type,
                    "order_id":order.id,
                    "delivered_date":date,
                    "Earning":value
                }
                context.append(d)
            total_earning=total_count*float(value)
            if Earning.objects.filter(order=request.user,profile_type='Delivery Boy').exists():
                earn=Earning.objects.filter(order=request.user)
                context2 = []
                for ear in earn:
                    price2=ear.requested_amount
                    context2.append(float(price2))
                total_withdrow_amount=sum(context2)
                remain_price=total_earning-total_withdrow_amount
            else:
                remain_price=total_earning
            return Response({'status':'True', 'message':'Notifications',"total_earn":total_earning ,'remaining_balance':remain_price,"data":context})
        return Response({'status':'False', 'message':'Empty',})


class DeliveryBoyRequestEarning(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        requested_amount=request.data.get('requested_amount')
        if AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user).exclude(status='Incomplete').exists():
            count = AllDeliveryBoyAddData.objects.filter(delivery_boy_id=request.user).exclude(status='Incomplete').count()
            earn = AllDeliveryBoyAddData.objects.all()
            value = earn.values('prize').first().get('prize')
            total_amount = count*float(value)
            if Earning.objects.filter(order=request.user,profile_type='Delivery Boy').exists():
                earn=Earning.objects.filter(order=request.user)
                context = []
                for ear in earn:
                    price2 = ear.requested_amount
                    context.append(float(price2))
                total_withdrow_amount = sum(context)
                remain_price = total_amount-total_withdrow_amount
            else:
                remain_price=total_amount
                print(remain_price)
            if remain_price >= float(requested_amount):
                Earning.objects.create(order=request.user, request_date=datetime.datetime.now(), requested_amount=requested_amount, profile_type='Delivery Boy')
                return Response({'status':'True', 'message':'You Have Requested Your Earning'})
            return Response({'status':'False', 'message':'You have no efficent balance'})
        return Response({'status':'False', 'message':'You have no deliveries'})


class DeleteSingleNotification(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, id):
        try:
            notification = Notification.objects.get(id=id, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({'status':'False', 'message':'Notification Not Found'})
        notification.delete()
        return Response({'status':'True', 'message':'Notifications Deleted'})


class DeleteAllNotification(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        if Notification.objects.filter(recipient=request.user).exists():
            notification = Notification.objects.filter(recipient=request.user)
            notification.delete()
            return Response({'status':'True', 'message':'All Notifications Delete Successfully'})
        return Response({'status':'False', 'message':'Notification Not Found'})


class NotificationCount(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if Notification.objects.filter(recipient=request.user).exists():
            notification = Notification.objects.filter(recipient=request.user, is_seen=False).count()
            return Response({'status':'True', 'data':notification})
        return Response({'status':'False', 'data':0})


class TailorShowMeasurement(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,id):
        service = SelectedService.objects.filter(id=id)
        serializer = TailerMeasurementSerializer(service,many=True)
        return Response({'status':'True', 'data':serializer.data})


    
class Tailor_get_measurement(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        print(request.data.get('id'))
        services=SelectedService.objects.filter(id__in=request.data.get('id'))
        context=[]
        for service in services:
            print(service.service.id)
            d={
                "id":service.id,
                "name":service.service.name,
                "type":service.service.type,
            }
            context.append(d)
        return Response({'status':'True',"data":context})


class TermandCondition(APIView):
    def get(self,request):
        if TermsAndConditions.objects.all().exists():
            serializer=TermsAndConditionsSerializer(TermsAndConditions.objects.all(), many=True)
            return Response({'status':'True', 'data':serializer.data})
        return Response({'status':'False', 'msg':"Empty"})
    
class PrivacyandPolicy(APIView):
    def get(self,request):
        if PrivacyPolicy.objects.all().exists():
            serializer=PrivacyAndPolicySerializer(PrivacyPolicy.objects.all(), many=True)
            return Response({'status':'True', 'data':serializer.data})
        return Response({'status':'False', 'msg':"Empty"})




