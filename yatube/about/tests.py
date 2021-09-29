from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_page_exists_at_desired_location(self):
        page_status_codes = {
            HTTPStatus.OK: '/about/tech/',
            HTTPStatus.OK: '/about/author/',
        }
        for status, adress in page_status_codes.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_page_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
