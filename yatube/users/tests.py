from django.test import Client, TestCase
from django.urls import reverse


class TaskURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_users_login_exists_at_desired_location(self):
        response = self.guest_client.get('/auth/login/')
        self.assertEqual(response.status_code, 200)

    def test_users_logout_exists_at_desired_location(self):
        response = self.guest_client.get('/auth/logout/')
        self.assertEqual(response.status_code, 200)

    def test_users_signup_exists_at_desired_location(self):
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, 200)

    def test_users_password_change_exists_at_desired_location(self):
        response = self.guest_client.get('/auth/password_change/')
        self.assertEqual(response.status_code, 200)

    def test_users_password_reset_exists_at_desired_location(self):
        response = self.guest_client.get('/auth/password_reset/')
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        # Шаблоны по адресам
        templates_url_names = {
            'users/login.html': '/auth/login/',
            'users/logged_out.html': '/auth/logout/',
            'users/signup.html': '/auth/signup/',
            'users/password_change_form.html': '/auth/password_change/',
            'users/password_reset_form.html': '/auth/password_reset/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'users/login.html': reverse('users:login'),
            'users/logged_out.html': reverse('users:logout'),
            'users/password_change_form.html': reverse(
                'users:password_change'
            ),
            'users/password_reset_form.html': reverse('users:password_reset'),
            'users/signup.html': reverse('users:signup'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
