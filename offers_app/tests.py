from django.contrib.auth import get_user_model
from django.test import TestCase

# Diese Imports werden fehlschlagen, bis wir die Models schreiben -> TDD Red Phase
from offers_app.models import Offer, OfferDetail, Order


User = get_user_model()


class OfferModelTest(TestCase):
    """
    Tests for Offer and Order models logic.
    """

    def setUp(self):
        self.business_user = User.objects.create_user(
            username='business',
            email='business@test.com',
            password='password123',
            type='business'
        )
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='password123',
            type='customer'
        )

    def test_create_offer_with_details(self):
        """
        Test creating an offer with nested details.
        """
        # 1. Offer erstellen (ohne Preis/Details, da diese im Detail-Objekt liegen)
        offer = Offer.objects.create(
            user=self.business_user,
            title="Logo Design",
            description="Professional logos"
        )
        
        # 2. OfferDetail erstellen und mit Offer verknüpfen
        detail = OfferDetail.objects.create(
            offer=offer,
            title="Basic Package",
            revisions=3,
            delivery_time_in_days=3,
            price=100.00,
            features=["Source File", "High Res"],
            offer_type="basic"
        )

        # Checks
        self.assertEqual(offer.user, self.business_user)
        self.assertEqual(detail.offer, offer)
        # Hinweis: offer.details.count() funktioniert erst, wenn 'related_name="details"' im Model gesetzt ist
        
    def test_create_order(self):
        """
        Test creating an order linking customer and business.
        """
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user,
            title="Order for Logo",
            status="in_progress",
            price=100.00,
            revisions=3,
            delivery_time_in_days=3,
            offer_type="basic"
        )

        self.assertEqual(order.status, "in_progress")
        self.assertEqual(order.customer_user, self.customer_user)