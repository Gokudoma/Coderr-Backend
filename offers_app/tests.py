from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail, Order

# Holt das aktuell aktive User-Model (CustomUser)
User = get_user_model()


class OfferModelTest(TestCase):
    """
    Tests for Offer and Order models logic (Database level).
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
        Test creating an offer with nested details directly in DB.
        """
        offer = Offer.objects.create(
            user=self.business_user,
            title="Logo Design",
            description="Professional logos"
        )
        
        detail = OfferDetail.objects.create(
            offer=offer,
            title="Basic Package",
            revisions=3,
            delivery_time_in_days=3,
            price=100.00,
            features=["Source File", "High Res"],
            offer_type="basic"
        )

        self.assertEqual(offer.user, self.business_user)
        self.assertEqual(detail.offer, offer)
        self.assertEqual(offer.details.count(), 1)

    def test_create_order(self):
        """
        Test creating an order directly in DB.
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


class OfferAPITests(APITestCase):
    """
    Integration tests for Offer API endpoints (Request/Response level).
    """

    def setUp(self):
        # Create Users
        self.business_user = User.objects.create_user(
            username='biz_api',
            email='biz_api@test.com',
            password='password123',
            type='business'
        )
        self.customer_user = User.objects.create_user(
            username='cust_api',
            email='cust_api@test.com',
            password='password123',
            type='customer'
        )

        # Create a sample Offer for testing updates/deletes
        self.offer = Offer.objects.create(
            user=self.business_user,
            title="Existing Offer",
            description="Description"
        )
        self.detail = OfferDetail.objects.create(
            offer=self.offer,
            title="Basic",
            revisions=1,
            delivery_time_in_days=3,
            price=50.00,
            features=["Feature 1"],
            offer_type="basic"
        )

        # URLs (Assuming router uses 'offer' basename)
        self.offer_list_url = reverse('offer-list')
        self.offer_detail_url = reverse('offer-detail', kwargs={'pk': self.offer.pk})

    def test_list_offers(self):
        """
        Ensure we can list offers.
        """
        response = self.client.get(self.offer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if pagination is active (results key) or just list
        if 'results' in response.data:
            self.assertTrue(len(response.data['results']) > 0)
        else:
            self.assertTrue(len(response.data) > 0)

    def test_create_offer_as_business_user(self):
        """
        Ensure a business user can create an offer with nested details.
        """
        self.client.force_authenticate(user=self.business_user)
        data = {
            "title": "New Design Offer",
            "description": "Best designs",
            "details": [
                {
                    "title": "Basic",
                    "revisions": 2,
                    "delivery_time_in_days": 2,
                    "price": 99.99,
                    "features": ["Logo"],
                    "offer_type": "basic"
                }
            ]
        }
        response = self.client.post(self.offer_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Offer.objects.count(), 2) # 1 existing + 1 new
        self.assertEqual(Offer.objects.last().details.count(), 1)

    def test_create_offer_as_customer_forbidden(self):
        """
        Ensure a customer cannot create an offer (403 Forbidden).
        """
        self.client.force_authenticate(user=self.customer_user)
        data = {"title": "Customer Offer"}
        response = self.client.post(self.offer_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_offer_as_owner(self):
        """
        Ensure the owner can update their offer.
        """
        self.client.force_authenticate(user=self.business_user)
        data = {"title": "Updated Title"}
        response = self.client.patch(self.offer_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "Updated Title")

    def test_delete_offer_as_owner(self):
        """
        Ensure the owner can delete their offer.
        """
        self.client.force_authenticate(user=self.business_user)
        response = self.client.delete(self.offer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Offer.objects.count(), 0)