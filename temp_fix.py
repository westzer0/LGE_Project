class UserSamplePurchasedItems(models.Model):
    user = models.ForeignKey(UserSample, on_delete=models.CASCADE, related_name='user_purchased_items')
