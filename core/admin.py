from django.contrib import admin
from .models import *
from django.contrib.auth.models import Group
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm


admin.site.site_title = "Tailor Find"
admin.site.site_header = "Tailor Find Administration"
admin.site.index_title = "Tailor Find Administration"
admin.site.site_url = '/'


class UserCreationForm(BaseUserCreationForm):
    password1 = None
    password2 = None
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=True, help_text="Phone Number With Country Code e.g. (+1123763989)")

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Phone is already exists")
        return phone

    def clean(self):
        password = None
        self.cleaned_data['password1'] = password
        self.cleaned_data['password2'] = password
        print('password:', password)
    

class UserModelAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    list_display = ('id', 'phone', 'first_name', 'last_name', 'profile_type', 'action', 'is_active', 'created_at', 'updated_at',)
    list_display_links = ['id', 'phone', 'first_name', 'last_name',]
    list_filter = ('is_superuser', 'is_active', 'profile_type', 'created_at', 'updated_at')
    fieldsets = (
        ('User Credentials', {'fields': ('phone', 'password', 'device_token')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'profile_type', 'location')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Measurement', {'fields': ('sleeve', 'waist', 'neck', 'shoulder', 'hip', 'waist_to_heap', 'waist_to_ankle', 'length_of_arm', 'round_arm', 'shoulder_to_waist', 'knee', 'back_width', 'thigh', 'calf', 'leg_length', 'ankle', 'waist_to_floor', 'crotch_depth', 'elbow_width', 'additional_information')}),
        ('Important Dates', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'device_token', 'first_name', 'last_name', 'profile_type', 'location', 'is_staff', 'is_superuser', 'sleeve', 'waist', 'neck', 'shoulder', 'hip', 'waist_to_heap', 'waist_to_ankle', 'length_of_arm', 'round_arm', 'shoulder_to_waist', 'knee', 'back_width', 'thigh', 'calf', 'leg_length', 'ankle', 'waist_to_floor', 'crotch_depth', 'elbow_width', 'additional_information'),
        }),
    )
    search_fields = ('phone', 'first_name', 'last_name', 'location')
    ordering = ('id', 'phone', 'first_name', 'last_name', 'created_at', 'updated_at')
    list_per_page = 20
    filter_horizontal = ()
    readonly_fields = ('created_at', 'updated_at')
    def action(self, obj):
        if obj.id:
            return mark_safe("<a class='button btn' style='color:green; padding:0 1rem; ' href='/admin/core/user/{}/change/'>Edit</a>".format(obj.id)
                             + "    " + "<a class='button btn' style='color:red; padding:0 1rem; ' href='/admin/core/user/{}/delete/'>Delete</a>".format(obj.id))
        else:
            social_button = '<a  href="#">---</a>'
            return mark_safe(u''.join(social_button))
admin.site.register(User, UserModelAdmin)
admin.site.unregister(Group)


@admin.register(SelectedService)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'service', 'quantity', 'price', 'created_at', 'updated_at']
    search_fields = ('service__name', 'quantity', 'price')
    ordering = ('id', 'service', 'quantity', 'price')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['service__type', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')



@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'price', 'category', 'created_at', 'updated_at']
    search_fields = ('name', 'type', 'price', 'category')
    ordering = ('id', 'name', 'type', 'price', 'category')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'tailor', 'delivery_boy', 'status']
    search_fields = ('customer__phone', 'tailor__phone', 'delivery_boy__phone')
    ordering = ('id', 'customer', 'tailor', 'delivery_boy', 'status')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['customer', 'tailor', 'delivery_boy', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone', 'first_name', 'last_name', 'subject', 'created_at', 'updated_at']
    search_fields = ('phone', 'first_name', 'last_name', 'subject',)
    ordering = ('id', 'phone', 'first_name', 'last_name', 'subject', 'created_at', 'updated_at')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['phone', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')



@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'image', 'status', 'created_at', 'updated_at']
    search_fields = ('order__tailor__phone',)
    ordering = ('id', 'order', 'image', 'status', 'created_at', 'updated_at')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['status', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AllDeliveryBoyAddData)
class AllDeliveryBoyAddDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'delivery_boy_id', 'status', 'created_at', 'updated_at']
    search_fields = ('order_id__customer__phone', 'delivery_boy_id__phone')
    ordering = ('id', 'order_id', 'delivery_boy_id', 'status', 'created_at', 'updated_at')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['status', 'created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DeliveryBoyEarning)
class AllDeliveryBoyAddDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'prize', 'created_at', 'updated_at']
    search_fields = ('prize',)
    ordering = ('id', 'prize', 'created_at', 'updated_at')
    list_per_page = 20
    filter_horizontal = ()
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'title', 'message', 'recieved_date', 'created_at', 'updated_at']
    search_fields = ('title',)
    ordering = ('id','sender', 'title', 'message', 'recieved_date', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    list_per_page = 10
    filter_horizontal = ()
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'created_at', 'updated_at','img']
    search_fields = ('description',)
    ordering = ('id', 'description','created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    list_per_page = 10
    filter_horizontal = ()
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'created_at', 'updated_at','img']
    search_fields = ('description',)
    ordering = ('id', 'description','created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    list_per_page = 10
    filter_horizontal = ()
    readonly_fields = ('created_at', 'updated_at')


