from django.contrib import admin
from .models import Tier, PaymentDiscountSnapshot, TeacherDiscountAbsorption, TeacherPayoutSummary, BlockchainTransaction, TokenBalance


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
	list_display = ("name", "min_stake_teo", "teacher_split_percent", "platform_split_percent", "is_active")
	list_filter = ("is_active",)
	search_fields = ("name",)


@admin.register(PaymentDiscountSnapshot)
class PaymentDiscountSnapshotAdmin(admin.ModelAdmin):
	list_display = (
		"order_id",
		"course",
		"teacher",
		"student",
		"price_eur",
		"discount_percent",
		"absorption_policy",
		"created_at",
	)
	search_fields = ("order_id", "course__title", "student__email", "teacher__email")
	list_filter = ("absorption_policy", "created_at")

# Register other useful models
admin.site.register(TeacherDiscountAbsorption)
admin.site.register(TeacherPayoutSummary)
admin.site.register(BlockchainTransaction)
admin.site.register(TokenBalance)
