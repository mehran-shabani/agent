# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import SubscriptionPlan, Subscription, BoxMoney
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from django.utils import timezone

# لیست پلن‌ها
class SubscriptionPlanListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

# مشاهده سابسکرایب فعلی کاربر
class UserSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response({'detail': 'کاربر اشتراک فعال ندارد.'}, status=status.HTTP_404_NOT_FOUND)

# خرید پلن
class PurchaseSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'detail': 'plan_id الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plan = SubscriptionPlan.objects.get(pk=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({'detail': 'پلن مورد نظر یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        box_money = request.user.box_money
        if not box_money.has_sufficient_balance(plan.price):
            return Response({'detail': 'موجودی کیف پول کافی نیست.'}, status=status.HTTP_402_PAYMENT_REQUIRED)
        
        # کسر موجودی
        box_money.deduct_amount(int(plan.price))

        # ایجاد یا تمدید اشتراک
        now = timezone.now()
        try:
            subscription = Subscription.objects.get(user=request.user)
            # تمدید: اگر اشتراک فعال است، تاریخ پایان جدید از انتهای فعلی محاسبه می‌شود
            if subscription.is_active:
                subscription.end_date += timezone.timedelta(days=plan.days)
            else:
                subscription.plan = plan
                subscription.start_date = now
                subscription.end_date = now + timezone.timedelta(days=plan.days)
            subscription.plan = plan  # اگر کاربر پلن جدید می‌خرد
            subscription.save()
        except Subscription.DoesNotExist:
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                start_date=now,
                end_date=now + timezone.timedelta(days=plan.days)
            )
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)