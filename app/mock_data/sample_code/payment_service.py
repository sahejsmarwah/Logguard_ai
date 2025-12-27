class PaymentService:
    def process_payment(self, payment_request):
        # BUG: auth failure not handled
        if not payment_request:
            raise ValueError("Invalid payment request")

        return "Payment processed"
