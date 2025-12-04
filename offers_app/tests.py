from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from offers_app.models import Offer, OfferDetail, Order, Review

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

        # URLs
        self.offer_list_url = reverse('offer-list')
        self.offer_detail_url = reverse('offer-detail', kwargs={'pk': self.offer.pk})

    def test_list_offers(self):
        response = self.client.get(self.offer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertTrue(len(response.data['results']) > 0)
        else:
            self.assertTrue(len(response.data) > 0)

    def test_create_offer_as_business_user(self):
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
        self.assertEqual(Offer.objects.count(), 2)

    def test_create_offer_as_customer_forbidden(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {"title": "Customer Offer"}
        response = self.client.post(self.offer_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_offer_as_owner(self):
        self.client.force_authenticate(user=self.business_user)
        data = {"title": "Updated Title"}
        response = self.client.patch(self.offer_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "Updated Title")

    def test_delete_offer_as_owner(self):
        self.client.force_authenticate(user=self.business_user)
        response = self.client.delete(self.offer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Offer.objects.count(), 0)


class OrderAndReviewTests(APITestCase):
    """
    Tests for Order and Review logic.
    """

    def setUp(self):
        # Users
        self.business_user = User.objects.create_user(
            username='biz_order', email='biz_order@test.com', password='pw', type='business'
        )
        self.customer_user = User.objects.create_user(
            username='cust_order', email='cust_order@test.com', password='pw', type='customer'
        )
        
        # Setup Offer & Detail to buy
        self.offer = Offer.objects.create(
            user=self.business_user, title="Web Design", description="Cool stuff"
        )
        self.detail = OfferDetail.objects.create(
            offer=self.offer,
            title="Premium",
            revisions=3,
            delivery_time_in_days=7,
            price=150.00,
            offer_type="premium"
        )

        # URLs
        self.order_list_url = reverse('order-list') 
        self.review_list_url = reverse('review-list') 

    def test_customer_can_create_order(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {"offer_detail_id": self.detail.id}
        
        response = self.client.post(self.order_list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        
        order = Order.objects.first()
        self.assertEqual(order.title, self.detail.title)
        self.assertEqual(order.price, self.detail.price)
        self.assertEqual(order.business_user, self.business_user)
        self.assertEqual(order.status, 'in_progress')

    def test_business_cannot_create_order(self):
        self.client.force_authenticate(user=self.business_user)
        data = {"offer_detail_id": self.detail.id}
        response = self.client.post(self.order_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_business_can_update_order_status(self):
        order = Order.objects.create(
            customer_user=self.customer_user,
            business_user=self.business_user,
            title="Snapshot Title",
            revisions=1,
            delivery_time_in_days=1,
            price=10.00,
            offer_type="basic",
            status="in_progress"
        )
        
        self.client.force_authenticate(user=self.business_user)
        url = reverse('order-detail', kwargs={'pk': order.pk})
        data = {"status": "completed"}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "completed")

    def test_create_review(self):
        self.client.force_authenticate(user=self.customer_user)
        data = {
            "business_user": self.business_user.id,
            "rating": 5,
            "description": "Great job!"
        }
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)


class StatEndpointsTests(APITestCase):
    """
    Tests for statistical endpoints (Base Info, Order Counts).
    """
    def setUp(self):
        self.business_user = User.objects.create_user(
            username='stat_biz', email='stat@biz.com', password='pw', type='business'
        )
        self.customer_user = User.objects.create_user(
            username='stat_cust', email='stat@cust.com', password='pw', type='customer'
        )
        
        # Create Data for Stats
        # 1. Offer
        offer = Offer.objects.create(user=self.business_user, title="Offer", description="Desc")
        # 2. Orders (1 in_progress, 1 completed)
        Order.objects.create(
            customer_user=self.customer_user, business_user=self.business_user,
            title="Order 1", revisions=0, delivery_time_in_days=1, price=10, 
            status='in_progress', offer_type='basic'
        )
        Order.objects.create(
            customer_user=self.customer_user, business_user=self.business_user,
            title="Order 2", revisions=0, delivery_time_in_days=1, price=10, 
            status='completed', offer_type='basic'
        )
        # 3. Review (5 Stars)
        Review.objects.create(
            business_user=self.business_user, reviewer=self.customer_user,
            rating=5, description="Good"
        )

    def test_base_info_public(self):
        url = reverse('base-info')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['review_count'], 1)
        self.assertEqual(response.data['offer_count'], 1)
        self.assertEqual(response.data['average_rating'], 5.0)

    def test_order_count(self):
        self.client.force_authenticate(user=self.business_user)
        url = reverse('order-count', kwargs={'pk': self.business_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 1) # Only in_progress

    def test_completed_order_count(self):
        self.client.force_authenticate(user=self.business_user)
        url = reverse('completed-order-count', kwargs={'pk': self.business_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completed_order_count'], 1) # Only completed


class OfferUnhappyPathTests(APITestCase):
    """
    Tests for validation errors and permission denials in Offers/Orders/Reviews.
    """
    def setUp(self):
        self.business = User.objects.create_user(username='biz_fail', email='biz_fail@t.com', password='pw', type='business')
        self.customer = User.objects.create_user(username='cust_fail', email='cust_fail@t.com', password='pw', type='customer')
        self.review_list_url = reverse('review-list')
        self.order_list_url = reverse('order-list')

    def test_review_duplicate_prevention(self):
        """
        Test that a user cannot review the same business twice.
        """
        self.client.force_authenticate(user=self.customer)
        data = {"business_user": self.business.id, "rating": 5, "description": "First"}
        
        # 1. Erste Bewertung OK
        self.client.post(self.review_list_url, data, format='json')
        
        # 2. Zweite Bewertung -> 400 Bad Request
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_invalid_id(self):
        """
        Test creating order with non-existent offer detail ID.
        """
        self.client.force_authenticate(user=self.customer)
        data = {"offer_detail_id": 9999} # Existiert nicht
        response = self.client.post(self.order_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)