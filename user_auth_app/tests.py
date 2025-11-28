from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
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
        # Wir erwarten, dass die URL 'registration' heißt (laut urls.py Konvention)
        url = reverse('registration') 
        data = {
            "username": "testcustomer",
            "email": "customer@example.com",
            "password": "strongpassword123",
            "repeated_password": "strongpassword123",
            "type": "customer"
        }
        response = self.client.post(url, data, format='json')
        
        # Check Response Status & Structure
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'testcustomer')
        self.assertEqual(response.data['email'], 'customer@example.com')
        self.assertIn('user_id', response.data)
        
        # Check Database
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