from rest_framework import serializers
from core.models import *
import datetime
import json
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    device_token = serializers.CharField(required=False)
    class Meta:
        fields = ['phone', 'device_token']


class UserProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name', 'location']


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


class ServiceSerializer(serializers.ModelSerializer):
    selected_service_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    price = serializers.CharField(read_only=True)
    class Meta:
        model = Service
        fields = ['id', 'selected_service_id', 'name', 'type', 'price']


class OrderSerializer(serializers.ModelSerializer):
    total_price = serializers.FloatField()
    item_name = serializers.CharField()
    class Meta:
        model = Order
        exclude = ['created_at', 'updated_at','tailor_price']


# class CustomerPlaceOrderSerializer(serializers.ModelSerializer):
#     selected_service = serializers.PrimaryKeyRelatedField(queryset=SelectedService, many=True)
#     customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(profile_type='Customer'))
#     class Meta:
#         model = Order
#         fields = ['tailor', 'customer', 'customer_delivery_address', 'selected_service']



class CustomerCancelOrderSerializer(serializers.ModelSerializer):
    canceled_date = serializers.DateField(default=timezone.now)
    status = serializers.CharField(default='Canceled')
    class Meta:
        model = Order
        fields = ['cancel_reason', 'status', 'canceled_date']


class TailorOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['created_at', 'updated_at']


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['sleeve', 'waist', 'neck', 'shoulder', 'hip', 'waist_to_heap', 'waist_to_ankle', 'length_of_arm', 'round_arm', 'shoulder_to_waist', 'knee', 'back_width', 'thigh', 'calf', 'leg_length', 'ankle', 'waist_to_floor', 'crotch_depth', 'elbow_width', 'additional_information']
                  

class CustomerPlaceOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'customer', 'tailor', 'service', 'customer_delivery_address']


# class ServiceDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SelectedService
#         fields = ['sleeve', 'waist', 'neck', 'shoulder', 'hip', 'waist_to_heap', 'waist_to_ankle', 'length_of_arm', 'round_arm', 'shoulder_to_waist', 'knee', 'back_width', 'thigh', 'calf', 'leg_length', 'ankle', 'waist_to_floor', 'crotch_depth', 'elbow_width', 'additional_information', 'description']
                  

class ServiceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectedService
        fields = ['quantity', 'price', 'sleeve', 'waist', 'neck', 'shoulder', 'hip', 'waist_to_heap', 'waist_to_ankle', 'length_of_arm', 'round_arm', 'shoulder_to_waist', 'knee', 'back_width', 'thigh', 'calf', 'leg_length', 'ankle', 'waist_to_floor', 'crotch_depth', 'elbow_width', 'additional_information', 'description']
   

class OrderPreviewSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    class Meta:
        model = SelectedService
        fields = ['name', 'type', 'quantity', 'price']
 

class EarningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Earning
        fields = ['id', 'order', 'requested_amount', 'image', 'status', 'paid_date']    


class DeliveryOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'customer_delivery_address', 'order_date']


class NotificationSeializer(serializers.ModelSerializer):
    class Meta:
        model=Notification
        fields=['id','order_id','title','message','recieved_date' ]


class DelievryBoyEarningSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllDeliveryBoyAddData
        fields = ['order_id',]


class NearByTailorSerializer(serializers.ModelSerializer):
    latitude = serializers.CharField()
    longitude = serializers.CharField()
    class Meta:
        model = User
        fields = ['id', 'phone', 'location', 'latitude', 'longitude']
    

class TailerMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelectedService
        exclude = ['service', 'quantity', 'price']


class TermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndConditions
        fields = '__All__'


class PrivacyAndPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['privacy_policy']
    
