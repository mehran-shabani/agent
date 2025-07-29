from django.contrib import admin
from .models import CustomUser, SubscriptionPlan, Subscription
from django.contrib.auth.admin import UserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # نمایش فیلدهای اضافی
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات تکمیلی', {'fields': ('is_doctor',)}),
    )
    list_display = UserAdmin.list_display + ('is_doctor',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'days', 'price')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    readonly_fields = ('is_active',)
