from django.shortcuts import render, redirect, HttpResponse
from django.views import View
from django.contrib import messages
from .models import *
from django.db.models import Q
from django.db.models import Sum
import math
import datetime
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout


class LoginView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return render (request, 'login.html')
        if not request.user.is_superuser:
            messages.error(request, 'Only Admin Can Login')
            return redirect ('login')
        return redirect ('dashboard')
    def post(self, request):
        if not request.user.is_authenticated:
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            user = authenticate(phone=phone, password=password)
            if user is not None:
                if user.is_superuser:
                    login(request, user)
                    return redirect ('dashboard')
                messages.error(request, 'Only Admin Can Login')
                return redirect ('login')
            messages.error(request, 'User Does Not Exists')
            return redirect ('login')
        return redirect ('dashboard')
    

@method_decorator(login_required, name='dispatch')
class SettingView(View):
    def get(self, request):
        if request.user.is_superuser:
          return render (request, 'setting.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            id = request.user.id
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            location = request.POST.get('location')
            phone = request.POST.get('phone')
            if not User.objects.filter(phone=phone).exclude(phone=request.user.phone):
                User.objects.filter(id=id).update(phone=phone, location=location, first_name=first_name, last_name=last_name)
                messages.success(request, 'User Detail Updated')
                return JsonResponse({'message':'User Detail Updated'})
            messages.error(request, 'Phone Already Exists')
            return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    def post(self, request):
        if request.user.is_superuser:
            old_password = request.POST.get('oldPassword')
            new_password = request.POST.get('newPassword')
            confirm_password = request.POST.get('confirmPassword')
            if old_password and new_password and confirm_password:
                if request.user.check_password(old_password):
                    if new_password == confirm_password:
                        user = User.objects.get(phone=request.user.phone)
                        user.set_password(new_password)
                        user.save()
                        messages.success(request, 'Password Change Successfully')
                        return JsonResponse({'message':'Password Change Successfully'})
                    messages.error(request, 'New Password and Confirm Password Did Not Match')
                    return JsonResponse({'message':'New Password and Confirm Password Did Not Match'})
                messages.error(request, 'Old Password Is Incorrect')
                return JsonResponse({'message':'Old Password Is Incorrect'})
            messages.error(request, 'We required Old Oassword and New Password and Confirm Password fields')
            return JsonResponse({'message':'We required Old Oassword and New Password and Confirm Password fields'})
        return redirect ('login')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        if request.user.is_superuser:
            tailor = User.objects.filter(profile_type='Tailor').count()
            customer = User.objects.filter(profile_type='Customer').count()
            delivery_boy = User.objects.filter(profile_type='Delivery Boy').count()
            total_order = Order.objects.all().count()
            pending_order = Order.objects.filter(status='Pending').count()
            return render (request, 'dashboard.html', {'total_order':total_order, 'pending_order':pending_order, 'tailor':tailor, 'customer':customer, 'delivery_boy':delivery_boy})
        return redirect ('login')


class ActivateUser(View):
    def get(self, request):
        user_id = request.GET.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            if user.is_active:
                user.is_active = not user.is_active
                user.save()
                return JsonResponse({'message': 'User Deactivated Successfully'})
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({'message': 'User Activated Successfully'})
        except User.DoesNotExist:
            return JsonResponse({'message': 'User not found'})


@method_decorator(login_required, name='dispatch')
class ManageTailorView(View):
    def get(self, request):
        if request.user.is_superuser:
            tailors = User.objects.filter(profile_type='Tailor')
            return render (request, 'manage-tailors.html', {'tailors':tailors})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class TailorDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            tailor = User.objects.get(id=id)
            pending_orders = Order.objects.filter(tailor=tailor, status='Pending')
            completed_orders = Order.objects.filter(tailor=tailor, status__in=['Completed','Preparing To Pickup For Delivery','Picked For Delivery','Delivered'])
            accepted_orders = Order.objects.filter(tailor=tailor, status__in=['Accepted By Tailor',"Preparing To Pickup For Service","Picked For Service","Order In Progress"])
            withdraws = Earning.objects.filter(order=tailor).order_by('-id')
            paids = Earning.objects.filter(status='Paid', order=tailor)
            pendings = Earning.objects.filter(status__in=['Pending'], order=tailor)
            earnings = Order.objects.filter(tailor=tailor)
            total_pending_orders = pending_orders.count()
            for pending_order in pending_orders:
                pending_order.pending_order_price = completed_order.tailor_price
                pending_order.pending_order_quantity = pending_order.service.aggregate(Sum('quantity'))['quantity__sum']
            complete_context = []
            for completed_order in completed_orders:
                completed_order.completed_order_price = completed_order.tailor_price
                completed_order.completed_order_quantity = completed_order.service.aggregate(Sum('quantity'))['quantity__sum']
                complete_context.append(completed_order.completed_order_price)
            total_sum = sum(complete_context)
            for accepted_order in accepted_orders:
                accepted_order.accepted_order_price = completed_order.tailor_price
                accepted_order.accepted_order_quantity = accepted_order.service.aggregate(Sum('quantity'))['quantity__sum']
            withdraw_amount_list = []
            for withdraw in withdraws:
                withdraw_amount=float(withdraw.requested_amount)
                withdraw_amount_list.append(withdraw_amount)
            total_withdraw_amount = sum(withdraw_amount_list)
            pending_amount_list = []
            for pending in pendings:
                pending_price = float(pending.requested_amount)
                pending_amount_list.append(pending_price)
            pending_amount = math.fsum(pending_amount_list)
            paid_amount_list = []
            for paid in paids:
                paid_amount=float(paid.requested_amount)
                paid_amount_list.append(paid_amount)
            total_paid_amount=sum(paid_amount_list)
            for earning in earnings:
                earning.earning_price = earning.service.aggregate(Sum('price'))
                earning.earning_quantity = earning.service.aggregate(Sum('quantity'))['quantity__sum']
            if Earning.objects.filter(order=tailor).exists():
                earn=Earning.objects.filter(order=tailor)
                remain_price=total_sum-total_withdraw_amount
            else:
                remain_price=total_sum
            return render (request, 'tailor-detail.html', {'tailor':tailor, 'total_pending_orders':total_pending_orders, 'pending_orders':pending_orders, 'completed_orders':completed_orders, 'accepted_orders':accepted_orders, 'model':Service,'total_completed_amount':total_sum,'total_withdraw_amount':total_withdraw_amount,"withdraws":withdraws,'total_paid_amount':total_paid_amount,'pending_amount':pending_amount,'earnings':earnings,'remain_price':remain_price})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class CreateTailorView(View):
    def get(self, request):
        if request.user.is_superuser:
          return render (request, 'create-tailor.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            if not User.objects.filter(phone=phone):
                User.objects.create(phone=phone, first_name=first_name, last_name=last_name, location=location, profile_type='Tailor')
                messages.success(request, 'Tailor Has Created Successfully')
                return JsonResponse({'message':'Tailor Has Created Successfully'})
            else:
                messages.error(request, 'Phone Already Exists')
                return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class UpdateTailorView(View):
    def get(self, request, id):
        if request.user.is_superuser:
          tailor = User.objects.get(id=id)
          return render (request, 'update-tailor.html', {'tailor':tailor})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            user = User.objects.get(id=id)
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            if not User.objects.filter(phone=phone).exclude(phone=user.phone):
                User.objects.filter(id=user.id).update(phone=phone, first_name=first_name, last_name=last_name, location=location)
                messages.success(request, 'Tailor Updated Successfully')
                return JsonResponse({'message':'Tailor Updated Successfully'})
            messages.error(request, 'Phone Already Exists')
            return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeleteTailorView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            User.objects.filter(id=id).delete()
            messages.error(request, 'Tailor Has Deleted')
            return redirect ('manage-tailors')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class ManageCustomerView(View):
    def get(self, request):
        if request.user.is_superuser:
            customers = User.objects.filter(profile_type='Customer')
            return render (request, 'manage-customers.html', {'customers':customers})
        return redirect ('login')



@method_decorator(login_required, name='dispatch')
class CustomerDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            customer = User.objects.get(id=id)
            pending_orders = Order.objects.filter(customer=customer, status='Pending')
            completed_orders = Order.objects.filter(customer=customer, status='Completed')
            canceled_orders = Order.objects.filter(customer=customer, status='Canceled')
            picked_for_delivery_orders = Order.objects.filter(customer=customer, status='Picked For Delivery')
            delivered_orders = Order.objects.filter(customer=customer, status='Delivered')
            total_pending_orders = pending_orders.count()
            total_completed_orders = delivered_orders.count()
            total_cancel_orders = canceled_orders.count()
            for pending_order in pending_orders:
                pending_order_price = pending_order.service.aggregate(Sum('price'))
                pending_order.pending_order_price = pending_order_price
            for completed_order in completed_orders:
                completed_order_price = completed_order.service.aggregate(Sum('price'))
                completed_order.completed_order_price = completed_order_price
            for canceled_order in canceled_orders:
                canceled_order_price = canceled_order.service.aggregate(Sum('price'))
                canceled_order.canceled_order_price = canceled_order_price
            for picked_for_delivery_order in picked_for_delivery_orders:
                picked_for_delivery_order_price = picked_for_delivery_order.service.aggregate(Sum('price'))
                picked_for_delivery_order.picked_for_delivery_order_price = picked_for_delivery_order_price
            for delivered_order in delivered_orders:
                delivered_order_price = delivered_order.service.aggregate(Sum('price'))
                delivered_order.delivered_order_price = delivered_order_price
            return render (request, 'customer-detail.html', {'customer':customer, 'total_pending_orders':total_pending_orders, 'pending_orders':pending_orders, 'completed_orders':completed_orders, 'canceled_orders':canceled_orders, 'picked_for_delivery_orders':picked_for_delivery_orders, 'delivered_orders':delivered_orders,'total_completed_orders':total_completed_orders,'total_cancel_orders':total_cancel_orders})
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class CustomerMeasurementDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            customer = User.objects.get(id=id)
            return render (request, 'measurement.html', {'customer':customer})
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class CreateCustomerView(View):
    def get(self, request):
        if request.user.is_superuser:
          return render (request, 'create-customer.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            if not User.objects.filter(phone=phone):
                User.objects.create(phone=phone, first_name=first_name, last_name=last_name, location=location, profile_type='Customer')
                messages.success(request, 'Customer Has Created Successfully')
                return JsonResponse({'message':'Customer Has Created Successfully'})
            messages.error(request, 'Phone Already Exists')
            return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class UpdateCustomerView(View):
    def get(self, request, id):
        if request.user.is_superuser:
          customer = User.objects.get(id=id)
          return render (request, 'update-customer.html', {'customer':customer})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            user = User.objects.get(id=id)
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            if not User.objects.filter(phone=phone).exclude(phone=user.phone):
                User.objects.filter(id=user.id).update(phone=phone, first_name=first_name, last_name=last_name, location=location)
                messages.success(request, 'Customer Updated Successfully')
                return JsonResponse({'message':'Customer Updated Successfully'})
            messages.error(request, 'Phone Already Exists')
            return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeleteCustomerView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            User.objects.filter(id=id).delete()
            messages.error(request, 'Customer Has Deleted')
            return redirect ('manage-customers')
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class ManageDeliveryBoyView(View):
    def get(self, request):
        if request.user.is_superuser:
            delivery_boys = User.objects.filter(profile_type='Delivery Boy')
            return render (request, 'manage-delivery-boys.html', {'delivery_boys':delivery_boys})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeliveryBoyDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            delivery_boy= User.objects.get(id=id)
            picked_for_delivery_orders = Order.objects.filter(delivery_boy=delivery_boy, status__in=['Picked For Delivery','Picked For Service',"Preparing To Pickup For Delivery", "Picked For Delivery"])
            delivered_orders = AllDeliveryBoyAddData.objects.filter(delivery_boy_id=delivery_boy,status__in=['DelCompleted','PickCompleted']).order_by('-id')
            total_picked_for_delivery_orders = Order.objects.filter(delivery_boy=delivery_boy, status__in=['Picked For Delivery','Picked For Service']).count()
            pending = Earning.objects.filter(order=delivery_boy,status='Pending')
            paid = Earning.objects.filter(order=delivery_boy,status='Paid')
            pencontext = []
            for pending in pending:
                request_amount=float(pending.requested_amount)
                pencontext.append(request_amount)
            total_pending_amount = sum(pencontext)
            paidcontext = []
            for paid in paid:
                request_amount = float(paid.requested_amount)
                paidcontext.append(request_amount)
            total_paid_amount = sum(paidcontext)
            total_dlivery=delivered_orders.count()
            earn = DeliveryBoyEarning.objects.all()
            value = earn.values('prize').first().get('prize')
            total_earning = total_dlivery*float(value)
            if Earning.objects.filter(order=delivery_boy,profile_type='Delivery Boy').exists():
                earn = Earning.objects.filter(order=delivery_boy)
                context = []
                for ear in earn:
                    price2=ear.requested_amount
                    context.append(float(price2))
                total_withdrow_amount = sum(context)
                remain_price=total_earning-total_withdrow_amount
            else:
                remain_price = total_earning
            return render (request, 'delivery-boy-detail.html', {'delivery_boy':delivery_boy, 'picked_for_delivery_orders':picked_for_delivery_orders, 'delivered_orders':delivered_orders, 'total_picked_for_delivery_orders':total_picked_for_delivery_orders,'total_earning':total_earning,'remain_price':remain_price,'total_withdrow_amount':total_withdrow_amount,'total_pending_amount':total_pending_amount,'total_paid_amount':total_paid_amount})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class CreateDeliveryBoyView(View):
    def get(self, request):
        if request.user.is_superuser:
          return render (request, 'create-delivery-boy.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            if not User.objects.filter(phone=phone):
                User.objects.create(phone=phone, first_name=first_name, last_name=last_name, location=location, profile_type='Delivery Boy')
                messages.success(request, 'Delivery Boy Has Created Successfully')
                return JsonResponse({'message':'Delivery Boy Has Created Successfully'})
            messages.error(request, 'Phone Already Exists')
            return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class UpdateDeliveryBoyView(View):
    def get(self, request, id):
        if request.user.is_superuser:
          delivery_boy = User.objects.get(id=id)
          return render (request, 'update-delivery-boy.html', {'delivery_boy':delivery_boy})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            user = User.objects.get(id=id)
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            if not User.objects.filter(phone=phone).exclude(phone=user.phone):
                User.objects.filter(id=user.id).update(phone=phone, first_name=first_name, last_name=last_name, location=location)
                messages.success(request, 'Delivery Boy Updated Successfully')
                return JsonResponse({'message':'Delivery Boy Updated Successfully'})
            messages.error(request, 'Phone Already Exists')
            return JsonResponse({'message':'Phone Already Exists'})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeleteDeliveryBoyView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            User.objects.filter(id=id).delete()
            messages.error(request, 'Delivery Boy Has Deleted')
            return redirect ('manage-delivery-boys')
        return redirect ('login')
    

    
@method_decorator(login_required, name='dispatch')
class ServicesView(View):
    def get(self, request):
        if request.user.is_superuser:
            services = Service.objects.all()
            return render (request, 'services.html', {'services':services})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class CreateServiceView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'create-service.html', {'model':Service})
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            name = request.POST.get('name')
            type = request.POST.get('type')
            price = float(request.POST.get('price'))
            category = request.POST.get('category')
            Service.objects.create(name=name, type=type, price=price, category=category)
            messages.success(request, 'Service Created Successfully')
            return redirect('services')
        return redirect ('login')



@method_decorator(login_required, name='dispatch')
class UpdateServiceView(View):
    def get(self, request, id):
        if request.user.is_superuser:
          service = Service.objects.get(id=id)
          return render (request, 'update-service.html', {'service':service, 'model':Service})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            name = request.POST.get('name')
            type = request.POST.get('type')
            price = float(request.POST.get('price'))
            category = request.POST.get('category')
            Service.objects.filter(id=id).update(name=name, price=price, type=type, category=category)
            messages.success(request, 'Service Updated Successfully')
            return redirect('update-service', id)
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeleteServerView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            Service.objects.filter(id=id).delete()
            messages.error(request, 'Service Has Deleted')
            return redirect ('services')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class OrdersView(View):
    def get(self, request):
        if request.user.is_superuser:
            orders = Order.objects.all()
            total = orders.count()
            return render (request, 'orders.html', {'orders':orders, 'total':total})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class OrderDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.get(id=id)
            total_service = order.service.aggregate(Sum('quantity'))['quantity__sum']
            total_service_price = order.service.aggregate(Sum('price'))['price__sum']
            return render (request, 'order-detail.html', {'order':order, 'total_service':total_service, 'total_service_price':total_service_price})
        return redirect ('login')

    

@method_decorator(login_required, name='dispatch')
class UpdateOrderView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.get(id=id)
            customers = User.objects.filter(profile_type='Customer')
            tailors = User.objects.filter(profile_type='Tailor')
            delivery_boys = User.objects.filter(profile_type='Delivery Boy')
            services = Service.objects.all()
            selected_customer = order.customer
            selected_tailor = order.tailor
            selected_delivery_boy = order.delivery_boy
            return render (request, 'update-order.html', {'order':order, 'customers':customers, 'tailors':tailors, 'delivery_boys':delivery_boys, 'services':services, 'selected_customer':selected_customer, 'selected_tailor':selected_tailor, 'selected_delivery_boy':selected_delivery_boy, 'model':Order})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            delivery_boy_id = request.POST.get('delivery_boy')
            status = request.POST.get('status')
            cancel_reason = request.POST.get('cancel_reason')
            pickup_date = request.POST.get('pickup_date')
            completed_date = request.POST.get('completed_date')
            delivery_date = request.POST.get('delivery_date')
            canceled_date = request.POST.get('canceled_date')
            if not pickup_date:
                pickup_date = None
            if not completed_date:
                completed_date = None
            if not delivery_date:
                delivery_date = None
            if not canceled_date:
                canceled_date = None
            if delivery_boy_id:
                delivery_boy = User.objects.get(id=delivery_boy_id)
            else:
                delivery_boy = None
            order_li =Order.objects.get(id=id)
            order_li.delivery_boy=delivery_boy
            order_li.status=status
            order_li.pickup_date = pickup_date
            order_li.completed_date = completed_date
            order_li.delivery_date = delivery_date
            order_li.canceled_date = canceled_date
            order_li.cancel_reason = cancel_reason
            order_li.save()
            messages.success(request, 'Order Updated Successfully')
            return redirect('update-order', id)
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class UpdateOrderStatusView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            order = Order.objects.get(id=id)
            customers = User.objects.filter(profile_type='Customer')
            tailors = User.objects.filter(profile_type='Tailor')
            delivery_boys = User.objects.filter(profile_type='Delivery Boy')
            services = Service.objects.all()
            selected_customer = order.customer
            selected_tailor = order.tailor
            selected_delivery_boy = order.delivery_boy
            selected_services = order.service.all()
            selected_service_ids = []
            for selected_service in selected_services:
                selected_service_ids.append(selected_service.id)
            return render (request, 'update-order-status.html', {'order':order, 'customers':customers, 'tailors':tailors, 'delivery_boys':delivery_boys, 'services':services, 'selected_customer':selected_customer, 'selected_tailor':selected_tailor, 'selected_delivery_boy':selected_delivery_boy, 'selected_service_ids':selected_service_ids, 'model':Order})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            delivery_boy_id = request.POST.get('delivery_boy')
            status = request.POST.get('status')
            cancel_reason = request.POST.get('cancel_reason')
            pickup_date = request.POST.get('pickup_date')
            completed_date = request.POST.get('completed_date')
            delivery_date = request.POST.get('delivery_date')
            canceled_date = request.POST.get('canceled_date')
            if not pickup_date:
                pickup_date = None
            if not completed_date:
                completed_date = None
            if not delivery_date:
                delivery_date = None
            if not canceled_date:
                canceled_date = None
            if delivery_boy_id:
                delivery_boy = User.objects.get(id=delivery_boy_id)
            else:
                delivery_boy = None
            order_li =Order.objects.get(id=id)
            order_li.delivery_boy=delivery_boy
            order_li.status=status
            order_li.pickup_date = pickup_date
            order_li.completed_date = completed_date
            order_li.delivery_date = delivery_date
            order_li.canceled_date = canceled_date
            order_li.cancel_reason = cancel_reason
            order_li.save()
            messages.success(request, 'Order Updated Successfully')
            return redirect('update-order-status', id)
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeleteOrderView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            Order.objects.filter(id=id).delete()
            messages.error(request, 'Order Has Deleted')
            return redirect ('orders')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class EnquiriesView(View):
    def get(self, request):
        if request.user.is_superuser:
            enquiries = Enquiry.objects.all()
            return render(request, 'enquiry.html', {'enquiries':enquiries})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class EnquiryDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            enquiry = Enquiry.objects.get(id=id)
            return render (request, 'enquiry-detail.html', {'enquiry':enquiry})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class CreateEnquiryView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'create-enquiry.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone = request.POST.get('phone')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            Enquiry.objects.create(first_name=first_name, last_name=last_name, phone=phone, subject=subject, message=message)
            messages.success(request, 'Enquiry Created Successfully')
            return redirect('enquiries')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class UpdateEnquiryView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            enquiry = Enquiry.objects.get(id=id)
            return render (request, 'update-enquiry.html', {'enquiry':enquiry})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone = request.POST.get('phone')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            Enquiry.objects.filter(id=id).update(first_name=first_name, last_name=last_name, phone=phone, subject=subject, message=message)
            messages.success(request, 'Enquiry Updated Successfully')
            return redirect('enquiries')
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class DeleteEnquiryView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            Enquiry.objects.filter(id=id).delete()
            messages.error(request, 'Enquiry Has Deleted')
            return redirect ('enquiries')
        return redirect ('login')
    


@method_decorator(login_required, name='dispatch')
class NotificationsView(View):
    def get(self, request):
        if request.user.is_superuser:
            notifications = Notification.objects.all()
            return render(request, 'notification.html', {'notifications':notifications})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class NotificationDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            notification = Notification.objects.get(id=id)
            return render (request, 'notification-detail.html', {'notification':notification})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')

class CreateNotificationView(View):
    def get(self, request):
        if request.user.is_superuser:
            users = User.objects.all()
            return render (request, 'create-notification.html', {'users':users})
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            sender=request.user
            title = request.POST.get('title')
            message = request.POST.get('message')
            recipient=request.POST.get('recipient')
            if recipient == 'all':
                data=User.objects.filter(is_superuser=False)
                for data in data:
                    Notification.objects.create(sender=sender,title=title,message=message,recipient=data)
            else:
                data=User.objects.get(id=recipient)
                Notification.objects.create(sender=sender, title=title, message=message,recipient=data)
            messages.success(request, 'Notification Created Successfully')
            return redirect('notifications')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class UpdateNotificationView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            notification = Notification.objects.get(id=id)
            users = User.objects.all()
            selected_sender = notification.sender
            selected_recipients = notification.recipient.all()
            selected_is_seens = notification.is_seen.all()
            selected_recipient_ids = []
            selected_is_seens_ids = []
            for selected_recipient in selected_recipients:
                selected_recipient_ids.append(selected_recipient.id)
            for selected_is_seen in selected_is_seens:
                selected_is_seens_ids.append(selected_is_seen.id)
            return render (request, 'update-notification.html', {'notification':notification, 'users':users, 'selected_sender':selected_sender, 'selected_recipient_ids':selected_recipient_ids, 'selected_is_seens_ids':selected_is_seens_ids})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            sender_id = request.POST.get('sender')
            if sender_id:
                sender = User.objects.get(id=sender_id)
            else:
                sender = None
            recipient = User.objects.filter(id__in=request.POST.getlist(('recipient')))
            is_seen = User.objects.filter(id__in=request.POST.getlist(('is_seen')))
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification = Notification.objects.get(id=id)
            notification.sender=sender
            notification.title=title
            notification.message=message
            notification.recipient.set(recipient)
            notification.is_seen.set(is_seen)
            notification.save()
            messages.success(request, 'Notification Updated Successfully')
            return redirect('notifications')
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class DeleteNotificationView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            Notification.objects.filter(id=id).delete()
            messages.error(request, 'Notification Has Deleted')
            return redirect ('notifications')
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class EarningsView(View):
    def get(self, request):
        if request.user.is_superuser:
            earnings = Earning.objects.all()
            return render(request, 'earning.html', {'earnings':earnings})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class EarningDetailView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            earning = Earning.objects.get(id=id)
            total_service = earning.order.service.aggregate(Sum('quantity'))['quantity__sum']
            earning_price = earning.order.service.aggregate(Sum('price'))['price__sum']
            return render (request, 'earning-detail.html', {'earning':earning, 'total_service':total_service, 'earning_price':earning_price})
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class CreateEarningView(View):
    def get(self, request):
        if request.user.is_superuser:
            orders = User.objects.filter(profile_type='Tailor')
            return render (request, 'create-earning.html', {'orders':orders, 'model':Earning})
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            order = User.objects.get(id=request.POST.get('order'))
            status = request.POST.get('status')
            request_date = request.POST.get('request_date')
            paid_date = request.POST.get('paid_date')
            if not request_date:
                request_date = None
            if not paid_date:
                paid_date = None
            if not Earning.objects.filter(order=order):
                Earning.objects.create(order=order, status=status, request_date=request_date, paid_date=paid_date)
                messages.success(request, 'Earning Created Successfully')
                return redirect('earnings')
            messages.error(request, 'Order Has Already An Earning')
            return redirect('earnings')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class UpdateEarningView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            earning = Earning.objects.get(id=id)
            return render (request, 'update-earning.html', {'earning':earning, 'model':Earning})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            earning = Earning.objects.get(id=id)
            image = request.FILES.get('image')
            status = request.POST.get('status')
            print(status)
            if status=="Pending":
                if paid_date=="":
                    paid_date=None
                if image:   
                    earning.image=image
                else:
                    earning.status=status
                    earning.paid_date=paid_date
                    earning.save()
            else:
                if image is not None:
                    earning.image=image
                    earning.status=status
                    earning.save()
                    messages.success(request, 'Earning Updated Successfully')
                    return redirect('earnings')
                else:
                    messages.warning(request, 'Payment Image is Required')
                    return redirect('update-earning',id)
            messages.success(request, 'Earning Updated Successfully')
            return redirect('earnings')




@method_decorator(login_required, name='dispatch')
class SelectOrderView(View):
    def get(self, request):
        if request.user.is_superuser:
            order_id = request.GET.get('order_id')
            order = Order.objects.get(id=order_id)
            tailor = order.tailor.phone
            total_service_dict = order.service.aggregate(Sum('quantity')).values()
            amount_dict = order.service.aggregate(Sum('price')).values()
            amount = list(amount_dict)[0]
            total_service = list(total_service_dict)[0]
            data = {'tailor':tailor, 'total_service':total_service, 'amount':amount}
            return JsonResponse (data)
        return redirect ('login')



@method_decorator(login_required, name='dispatch')
class UpdateEarningStatusView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            earning = Earning.objects.get(id=id)
            total_service = earning.order.service.aggregate(Sum('quantity'))['quantity__sum']
            earning_price = earning.order.service.aggregate(Sum('price'))['price__sum']
            return render (request, 'update-earning-status.html', {'earning':earning, 'total_service':total_service, 'earning_price':earning_price, 'model':Earning})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            earning = Earning.objects.get(id=id)
            image = request.FILES.get('image')
            clear_image = request.POST.get('clear_image')
            status = request.POST.get('status')
            request_date = request.POST.get('request_date')
            paid_date = request.POST.get('paid_date')
            if not request_date:
                request_date = None
            if not paid_date:
                paid_date = None
            if image and clear_image:
                messages.error(request, 'Please either submit a file or check the clear checkbox, not both.')
                return redirect('update-earning-status', id)
            elif image:
                earning.image=image
                earning.status=status
                earning.save()
            elif clear_image:
                earning.image=image
                earning.status=status
                earning.save()
            else:
                earning.image=earning.image
                earning.status=status
                earning.save()
            messages.success(request, 'Earning Updated Successfully')
            return redirect('update-earning-status', id)
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeleteEarningView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            Earning.objects.filter(id=id).delete()
            messages.error(request, 'Earning Has Deleted')
            return redirect ('earnings')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class PrivacyPolicyView(View):
    def get(self, request):
        if request.user.is_superuser:
            privacy_policies = PrivacyPolicy.objects.all().order_by('-id')
            return render(request, 'privacy-policy.html', {'privacy_policies':privacy_policies})
        return redirect ('login')
    
    

@method_decorator(login_required, name='dispatch')
class CreatePrivacyPolicyView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'create-privacy-policy.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            privacy_policy = request.POST.get('description')
            img = request.FILES.get('img')
            PrivacyPolicy(description=privacy_policy,img=img).save()
            messages.success(request, 'Privacy Policy Created Successfully')
            return redirect('privacy-policies')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class UpdatePrivacyPolicyView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            privacy_policy = PrivacyPolicy.objects.get(id=id)
            return render (request, 'update-privacy-policy.html', {'privacy_policy':privacy_policy})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            privacy_policy = request.POST.get('description')
            img = request.FILES.get('img')
            update_privacy_policy = PrivacyPolicy.objects.get(id=id)
            update_privacy_policy.description = privacy_policy
            update_privacy_policy.img = img
            update_privacy_policy.save()
            messages.success(request, 'Privacy Policy Updated Successfully')
            return redirect('privacy-policies')
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class DeletePrivacyPolicyView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            PrivacyPolicy.objects.filter(id=id).delete()
            messages.error(request, 'Privacy Policy Has Deleted')
            return redirect ('privacy-policies')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class TermsAndConditionsView(View):
    def get(self, request):
        if request.user.is_superuser:
            terms_and_conditions = TermsAndConditions.objects.all().order_by('-id')
            return render(request, 'terms-and-conditions.html', {'terms_and_conditions':terms_and_conditions})
        return redirect ('login')
    
    

@method_decorator(login_required, name='dispatch')
class CreateTermsAndConditionsView(View):
    def get(self, request):
        if request.user.is_superuser:
            return render (request, 'create-terms-and-conditions.html')
        return redirect ('login')
    def post(self, request):
        if request.user.is_superuser:
            terms_and_conditions = request.POST.get('description')
            img = request.FILES.get('img')
            TermsAndConditions(description=terms_and_conditions,img=img).save()
            messages.success(request, 'Terms And Conditions Created Successfully')
            return redirect('terms-and-conditions')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class UpdateTermsAndConditionsView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            terms_and_conditions = TermsAndConditions.objects.get(id=id)
            return render (request, 'update-terms-and-conditions.html', {'terms_and_conditions':terms_and_conditions})
        return redirect ('login')
    def post(self, request, id):
        if request.user.is_superuser:
            description = request.POST.get('description')
            img = request.FILES.get('img')
            update_terms_and_conditions = TermsAndConditions.objects.get(id=id)
            update_terms_and_conditions.description = description
            update_terms_and_conditions.img = img
            update_terms_and_conditions.save()
            messages.success(request, 'Terms And Conditions Updated Successfully')
            return redirect('terms-and-conditions')
        return redirect ('login')


@method_decorator(login_required, name='dispatch')
class DeleteTermsAndConditionsView(View):
    def get(self, request, id):
        if request.user.is_superuser:
            TermsAndConditions.objects.filter(id=id).delete()
            messages.success(request, 'Terms And Conditions Has Deleted')
            return redirect ('terms-and-conditions')
        return redirect ('login')
    

@method_decorator(login_required, name='dispatch')
class DeliveryBoyEarningPrice(View):
    def get(self,request):
        return render(request,'delivery-earining.html')
    def post(self,request):
        price = request.POST.get('price')
        DeliveryBoyEarning.objects.create(prize=price)
        return redirect('delievry-boy-price-view')
    

@method_decorator(login_required, name='dispatch')
class DelievryBoyEarningView(View):
    def get(self, request):
        earn = DeliveryBoyEarning.objects.all()
        return render(request,'delivery-boy-earning-view.html', {'earn':earn})
    

@method_decorator(login_required, name='dispatch')
class DeliveryBoyEarningUpdate(View):
    def get(self, request, id):
        earn = DeliveryBoyEarning.objects.get(id=id)
        return render(request,'update-delivery-boy-earning.html', {'earn':earn})
    def post(self,request,id):
        data = DeliveryBoyEarning.objects.get(id=id)
        price = request.POST.get('prize')
        data.prize = price
        data.save()
        return redirect('delievry-boy-price-view')
    

@method_decorator(login_required, name='dispatch')
class DelieveryBoyEarninigDelete(View):
    def get(self, request, id):
        earn = DeliveryBoyEarning.objects.get(id=id)
        earn.delete()
        return redirect('delievry-boy-price-view')
        

class TermandConditions(View):
    def get(self, request):
        data = TermsAndConditions.objects.all()
        return render(request,'web-view/terms-and-conditions.html', {'data':data})
    

class Privacyandpolicies(View):
    def get(self, request):
        data = PrivacyPolicy.objects.all()
        return render(request,'web-view/privacy-and-policy.html', {'data':data})
    





