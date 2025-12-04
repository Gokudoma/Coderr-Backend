from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    """
    Tests for user registration endpoints.
    """

    def test_registration_customer_success(self):
        """
        Ensure we can register a new customer user.
        """
        url = reverse('registration') 
        data = {
            "username": "testcustomer",
            "email": "customer@example.com",
            "password": "strongpassword123",
            "repeated_password": "strongpassword123",
            "type": "customer"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'testcustomer')
        self.assertEqual(response.data['email'], 'customer@example.com')
        
        self.assertTrue(User.objects.filter(email='customer@example.com').exists())
        user = User.objects.get(email='customer@example.com')
        self.assertEqual(user.type, 'customer')

    def test_registration_business_success(self):
        """
        Ensure we can register a new business user.
        """
        url = reverse('registration')
        data = {
            "username": "bizuser",
            "email": "biz@example.com",
            "password": "strongpassword123",
            "repeated_password": "strongpassword123",
            "type": "business"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email='biz@example.com')
        self.assertEqual(user.type, 'business')


class UserProfileTests(APITestCase):
    """
    Tests for Login and Profile endpoints.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            type='business',
            location='Berlin',
            tel='123456789'
        )
        # Diese URLs existieren noch nicht -> Test wird hier fehlschlagen (RED Phase)
        self.login_url = reverse('login')
        self.profile_detail_url = reverse('profile-detail', kwargs={'pk': self.user.pk})
        self.business_list_url = reverse('profile-business-list')
        self.customer_list_url = reverse('profile-customer-list')

    def test_login_success(self):
        """
        Ensure valid credentials return a token.
        """
        data = {
            "username": "test@example.com", 
            "password": "password123"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_get_own_profile_detail(self):
        """
        Ensure authenticated user can view their profile.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['location'], 'Berlin')

    def test_update_own_profile(self):
        """
        Ensure user can update their own profile.
        """
        self.client.force_authenticate(user=self.user)
        data = {"location": "Munich", "tel": "987654321"}
        response = self.client.patch(self.profile_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.location, "Munich")
        self.assertEqual(self.user.tel, "987654321")

    def test_list_business_profiles(self):
        """
        Ensure we can list all business profiles.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.business_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1) 
        self.assertEqual(response.data[0]['type'], 'business')